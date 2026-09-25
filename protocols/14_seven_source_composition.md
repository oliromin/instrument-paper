# Hindi-bucket composition with a seventh, Angika, source row

Status: post hoc in motivation, pre-specified in execution. The analysis was prompted by the observation that the Panel 1 mixture has no Angika source row. The identity and size of the seventh row were fixed on 16 September 2026, before any composition was recomputed. No direction was predicted.

Governs the seven-source composition (Section 4.4; Appendix F).

## Quantity

For each identifier, the Hindi-sourced share of the units it labels Hindi (its Hindi-bucket precision), on two designed mixtures:

- six rows: the Panel 1 L1 cells for Hindi, Nepali, Marathi, Sanskrit, Newari and Maithili, 2,000 units each;
- seven rows: the same six rows plus the Regime C Angika L1 cell of protocol 05, 2,000 units drawn at seed 20260908 from a pool of 3,315 marker-selected sentences. The drawn units fall in 796 source articles.

Accepted labels are those of protocol 02. These are properties of the designed mixtures, not estimates for a web corpus.

## Inputs

The seven historical identifiers use the stored Panel 1 predictions for the six original rows and the stored Panel 2 predictions for the Angika row. No historical model is rerun. An OpenLID-v3 row was added later from the per-unit predictions of protocol 12 and is reported as point estimates.

## Check before the new row is added

The six-row precisions must reproduce the published values (GlotLID v3 0.9776, CLD3 0.6256, lid.176 0.7231, langid.py 0.8282), and the Hindi row must resolve to 1,871 source clusters.

## Intervals

Protocol 08: 4,999 replicates at seed 20260912, source clusters resampled within each row, row weights held fixed. The Angika row's clusters are its source articles.

## Outcome

The six-row check reproduced. Hindi-bucket precision, six rows to seven:

| Identifier | Six rows | Seven rows | Angika row sent to Hindi |
|---|---|---|---|
| GlotLID v3 | 0.978 | 0.976 | 0.001 |
| GlotLID v2 | 0.990 | 0.972 | 0.018 |
| GlotLID v1 | 0.966 | 0.872 | 0.111 |
| OpenLID | 0.917 | 0.851 | 0.059 |
| langid.py | 0.828 | 0.487 | 0.834 |
| CLD3 | 0.626 | 0.443 | 0.654 |
| lid.176 | 0.723 | 0.427 | 0.958 |

The fall in each identifier's precision broadly tracks the share of the Angika row it sends to Hindi.
