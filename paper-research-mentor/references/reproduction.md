# Reproduction boundaries

Start with reported/unknown configuration. Suggested defaults are separately labeled proposals. Never infer optimizer, seed, epochs or preprocessing from custom.

Reconstruct pseudocode, inputs/outputs, shapes or protocol before implementation. For ML produce paper-specific PyTorch model/training/config when sufficiently specified; isolate uncertain parts. Never substitute a fixed demo MLP.

If details are inadequate, provide a labeled toy mechanism or skeleton plus missing-detail list. Detect dependencies. Read official code as supplementary evidence; do not automatically execute downloaded code.

Levels: `skeleton` (structure only), `smoke_checked` (named shape/numerical checks actually run), `reproduced` (the relevant experiment and protocol actually run). A forward pass is not a benchmark reproduction.

Describe provenance/splits, controls, randomness, metrics, uncertainty and cost. Theory gets worked cases/conditions; biology gets method and measurement plans, never invented outcomes.
