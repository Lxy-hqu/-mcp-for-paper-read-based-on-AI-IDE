"""Restricted expression AST, optional symbolic operations. Never eval user text."""
from __future__ import annotations

import argparse
import ast
import json
import math
import sys

FUNCTIONS = {"sqrt", "sin", "cos", "tan", "exp", "log", "abs"}
OPS = {ast.Add: "add", ast.Sub: "subtract", ast.Mult: "multiply", ast.Div: "divide", ast.Pow: "power"}


def expression_tree(expression):
    if len(expression) > 2000:
        raise ValueError("Expression exceeds 2000 characters")
    if "\\" in expression or "$" in expression or "^" in expression:
        raise ValueError("LaTeX and ^ are unsupported; preserve original and explicitly transcribe arithmetic using **")
    try:
        root = ast.parse(expression, mode="eval")
    except (SyntaxError, RecursionError) as e:
        raise ValueError(f"Unsupported arithmetic syntax: {e}") from e
    if sum(1 for _ in ast.walk(root)) > 150:
        raise ValueError("Expression too complex for bounded symbolic helper")
    variables = set()

    def visit(node, depth=0):
        if depth > 25:
            raise ValueError("Expression nesting limit exceeded")
        if isinstance(node, ast.Expression):
            return visit(node.body, depth + 1)
        if isinstance(node, ast.Constant) and type(node.value) in {int, float}:
            if not math.isfinite(node.value) or abs(node.value) > 1e9:
                raise ValueError("Numeric literal outside bounded range")
            return {"type": "number", "value": node.value}
        if isinstance(node, ast.Name) and node.id.isascii() and not node.id.startswith("_") and len(node.id) <= 40:
            variables.add(node.id)
            return {"type": "symbol", "name": node.id}
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            if isinstance(node.op, ast.Pow) and (not isinstance(node.right, ast.Constant) or type(node.right.value) not in {int, float} or abs(node.right.value) > 20):
                raise ValueError("Power exponent must be an explicit number with magnitude <=20")
            return {"type": OPS[type(node.op)], "left": visit(node.left, depth + 1), "right": visit(node.right, depth + 1)}
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return {"type": "negative" if isinstance(node.op, ast.USub) else "positive", "value": visit(node.operand, depth + 1)}
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS and len(node.args) == 1 and not node.keywords:
            return {"type": "function", "name": node.func.id, "argument": visit(node.args[0], depth + 1)}
        raise ValueError(f"Unsupported expression construct: {type(node).__name__}")

    tree = visit(root)
    return {"original": expression, "status": "parsed", "variables": sorted(variables), "ast": tree,
            "limitation": "Arithmetic AST only; not a LaTeX parser, tensor-shape checker or proof"}


def symbolic(expression):
    result = expression_tree(expression)
    try:
        import sympy as s
    except ImportError:
        return {**result, "symbolic_status": "unavailable", "limitation": "Install optional sympy for symbolic output; AST is not a symbolic verification"}

    def convert(n):
        t = n["type"]
        if t == "number":
            return s.Integer(n["value"]) if type(n["value"]) is int else s.Float(n["value"])
        if t == "symbol":
            return s.Symbol(n["name"])
        if t == "function":
            fun = {"sqrt": s.sqrt, "sin": s.sin, "cos": s.cos, "tan": s.tan, "exp": s.exp, "log": s.log, "abs": s.Abs}[n["name"]]
            return fun(convert(n["argument"]), evaluate=False)
        if t in {"negative", "positive"}:
            return s.Mul(-1, convert(n["value"]), evaluate=False) if t == "negative" else convert(n["value"])
        a, b = convert(n["left"]), convert(n["right"])
        return {"add": lambda: s.Add(a, b, evaluate=False), "subtract": lambda: s.Add(a, s.Mul(-1, b, evaluate=False), evaluate=False),
                "multiply": lambda: s.Mul(a, b, evaluate=False), "divide": lambda: s.Mul(a, s.Pow(b, -1, evaluate=False), evaluate=False),
                "power": lambda: s.Pow(a, b, evaluate=False)}[t]()

    # Unevaluated construction avoids unbounded algebraic simplification of hostile inputs.
    expr = convert(result["ast"])
    return {**result, "symbolic_status": "constructed_unevaluated", "symbolic": str(expr), "latex": s.latex(expr),
            "limitation": "Unevaluated symbolic structure only; assumptions, domains and derivations remain unverified"}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["ast", "symbolic"])
    parser.add_argument("--expression", required=True)
    args = parser.parse_args()
    try:
        result = expression_tree(args.expression) if args.operation == "ast" else symbolic(args.expression)
        code = 0
    except (ValueError, OverflowError, RecursionError) as e:
        result, code = {"original": args.expression, "status": "unsupported", "reason": str(e)}, 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
