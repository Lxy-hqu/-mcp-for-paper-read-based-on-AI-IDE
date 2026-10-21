# Deep reading and scientific critique

## Reconstruct before criticizing

Explain the real problem, baseline failure, hypothesis, design and the experiment testing it. Distinguish a mechanism, finding, dataset and delivered system. State what remains if each claimed contribution is removed.

For central methods: inputs/outputs, assumptions, component roles, data flow, training vs inference, alternatives, applicability and failures. Use paper-specific diagrams; adapt non-ML work to a protocol, causal mechanism or proof.

Academic summary: question, method, evidence, contribution, limit. Plain explanation: faithful analogy and where it breaks. Add a concrete toy example when useful, preserving the claim's meaning.

## Equations and proofs

Inventory central equations and visually verify notation. PDF text often corrupts superscripts, limits and normalization. Preserve uncertainty rather than silently repairing it.

For each central equation: meaning/role; symbol definitions, scalar/vector/matrix dimensions and units where applicable; assumptions; intermediate steps; intuition; numerical/dimensional/boundary check; algorithm connection. Distinguish the author's derivation from your reconstruction and external knowledge. Tensor shape is not a physical unit.

AST is a tool result for an explicitly entered expression, not a derivation proof. `math_tools.py` builds a safe arithmetic AST and optionally uses SymPy; unsupported LaTeX remains unresolved. For theory inspect theorem conditions and proof gaps instead of inventing training code.

## Figures, tables and experiments

Read axes, legends, units, sample counts, uncertainty and notes. Explain what each central graphic supports and cannot establish. Attach PDF page and figure/table number. Digitizing an illustration is not recovery of raw data.

Extract sampling, data/splits, grouping/temporal constraints, preprocessing, baseline tuning, reported hyperparameters, seeds/repetitions, metrics and costs. Keep relative percent and percentage points distinct; check denominator and population.

Ablations need capacity, compute, data, optimization and selection controls. A removal drop supports usefulness in that setting, not automatically the proposed causal mechanism. Propose missing tests without unsupported accusations.

For biology separate focal-system measurements, related-system literature and mechanism plausibility. For observation distinguish association, prediction and intervention. For engineering separate benchmarks, delivered software and future deployment plans.

Output a claim → result → interpretation → alternative → missing-test map. Identify the strongest/weakest inference, concrete failure cases and a test that could overturn an attractive interpretation. Avoid generic ritual limitations.
