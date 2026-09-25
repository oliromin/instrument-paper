# Source-cluster resampling and the classification of reported rates

Status: fixed on 12 September 2026, before any interval was computed. Applied retrospectively to predictions already stored.

Governs every interval reported for a sampled panel, marker-selected control or Hindi-bucket composition (Section 3.4).

## Classes of reported rate

Every rate the paper reports falls into one of five classes:

- a frozen-artifact census proportion;
- a sampled panel rate;
- a marker-selected control rate;
- a conditional resampling statistic;
- a historical aggregate whose unit-level predictions were not kept.

Census proportions receive no sampling interval.

## Source identity

A Leipzig L1 unit is a sentence. Its source document comes from the archive's sentence-to-source table.

- An L5 or L20 unit is its own source document.
- Sources attached to the same selected sentence are joined, as are sources with the same URL.
- Angika Wikipedia units cluster by article.
- ILI units have no recoverable source and are reported descriptively, without resampling.

## Resampling

4,999 replicates, seed 20260912. Source clusters are resampled with replacement within each language, source and length cell. Every selected unit of a sampled cluster is kept, and the original unit-weighted ratio is recomputed.

- **Pairing.** The same cluster multiplicities apply to every identifier and release, so differences between releases are paired.
- **Mixtures.** For a fixed-mixture bucket composition, each replicate preserves the observed language-cell weights.
- **Intervals.** Intervals are 95% percentile intervals. They are conditional on the designed panel and its source pool. They are not web-population intervals and do not correct provenance error.
- **Degenerate cells.** A cell with zero observed errors is reported as an observed zero, with no population inference.
- **Protocol outcomes.** New intervals do not change the outcome of any earlier protocol condition.
