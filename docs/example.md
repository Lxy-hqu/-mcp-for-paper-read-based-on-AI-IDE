# Reading example: Attention Is All You Need

[Home](../README.md) · [中文首页](../README.zh-CN.md) · [Usage](usage.md)

This is a condensed example from a source-reviewed reading, not a transcript of a real learner or a screenshot of an application.

**Source:** Vaswani et al., *Attention Is All You Need*, [arXiv:1706.03762v7](https://arxiv.org/abs/1706.03762v7). The paper was introduced in 2017; this PDF revision is dated 2023. The reading covered all 15 PDF pages and visually inspected pages 3–9 and 13–15. PDF page locators below are one-based.

## Rebuild the scientific story

The paper addresses how information moves across positions in sequence transduction. Its architecture preserves the encoder–decoder problem while replacing sequence-aligned recurrent computation with attention-based communication. The important chain is **a computational constraint → a communication mechanism → an architectural design → evidence under specific tasks and conditions**. See [PDF pages 2–3](https://arxiv.org/pdf/1706.03762v7#page=2).

The explanation distinguishes query/key compatibility from the information in values, then follows encoder self-attention, masked decoder self-attention and cross-attention. A useful understanding check is to predict what goes wrong if the decoder mask is removed. The architecture supports parallel computation across known target positions during training; it does not make autoregressive generation independent across unknown future tokens. See [page 3](https://arxiv.org/pdf/1706.03762v7#page=3).

## Explain a mechanism with its assumptions

For a single attention head, if queries have shape n_q×d_k, keys n_k×d_k, and values n_k×d_v, the score matrix has shape n_q×n_k. Normalizing over keys and mixing values gives n_q×d_v. The dimension argument is distinct from a proof of good model behavior. See [equation 1, page 4](https://arxiv.org/pdf/1706.03762v7#page=4).

Under simplified independent, zero-mean, unit-variance component assumptions, dot-product variance grows with d_k. Scaling controls that growth; actual learned inputs need not satisfy those assumptions, and the scaling is not an absolute guarantee against saturation.

## Preserve contradictory source evidence

The same PDF's Table 2 gives EN-FR **41.8**, while the prose on that page says **41.0**. The reading records both values and leaves the discrepancy unresolved. It does not silently choose a convenient number. See [page 8](https://arxiv.org/pdf/1706.03762v7#page=8).

The head-count variants in Table 3 use a development set. The table supports a bounded comparison of the tested settings; it does not establish that more heads are always better. Attention visualizations are illustrative observations, not a causal test of explanations. See [page 9](https://arxiv.org/pdf/1706.03762v7#page=9) and [pages 13–15](https://arxiv.org/pdf/1706.03762v7#page=13).

## Turn writing into reusable structure

An original abstracted pattern:

> To address [specific bottleneck], we introduce [mechanism] and evaluate [testable consequence] under [conditions].

The adaptation must supply the user's own problem, mechanism, observations and evaluation conditions. It does not inherit this paper's results. A paragraph can similarly move from a concrete constraint to its consequence, the needed capability, the design, the evidence, and the boundary of the conclusion.

## Suggest an experiment, with conditions

No user project materials were supplied in the demonstration. Suggestions therefore remain conditional: if a project has meaningful sequence order and an observed long-range dependency bottleneck, compare the existing aggregator, a single-head alternative and a multi-head alternative with matched data, capacity, compute and tuning budgets.

Measure task-appropriate error and actual resource cost. Keep the baseline if its performance is comparable at lower complexity. This is a proposed experiment, not an observed project improvement; a translation metric is not substituted for the user's task metric.

## Leave space for the researcher

Three saved thinking prompts:

1. Why does parallel training not imply independently generating an entire target sentence?
2. What assumption makes the dot-product variance argument work, and what does scaling fail to guarantee?
3. How would you separate a multi-head mechanism benefit from capacity or tuning-budget benefits in your project?

There are no user answers in this example. Each checkpoint stays **pending / unverified**. A later response after a hint or answer exposure must not be labeled independent mastery of that same question.

## What was actually checked

The reading included source extraction, page viewing, provenance records, links, and a small arithmetic attention/masking example. It did not run WMT training, reproduce BLEU, inspect all official code, or measure a human learning outcome. See the [validation scope](validation.md).
