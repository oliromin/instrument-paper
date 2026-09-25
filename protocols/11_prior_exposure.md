# Retention of panel Hindi inside and outside the published Hindi training file

Status: pre-specified. Fixed on 16 September 2026, before any retention was computed on either subgroup. The overall retention (0.480) and the subgroup sizes were known.

Governs the prior-exposure analysis (Section 6.3).

## Subgroups

Panel 1's 2,000 Hindi L1 units, split by the membership test of protocol 10:

- IN: 1,554 units found in the file.
- OUT: 446 units not found.

Exact matching misses edited copies, so the test is a lower bound and attenuates any difference.

## Confound check, read first

The median token counts and mean Devanagari purity of IN and OUT. If the medians differ by more than 3 tokens or the purity by more than 0.02, any retention difference is reported as confounded.

## Quantities

GlotLID v3 retention on IN and on OUT, from the stored Panel 1 predictions, with v1 and v2 as context. No model is run.

## Conditions

1. If OUT retention exceeds IN retention by 0.15 or more, the loss is concentrated in text seen in training, and OUT retention replaces the headline figure.
2. If IN retention exceeds OUT retention by 0.15 or more, the model retains seen text better, and OUT retention is the generalisation figure.
3. If neither holds, membership in the training file does not protect the text.

## Outcome

- The confound check did not fire: the median token counts are 16 and 17, and the mean purities 0.9988 and 0.9980.
- GlotLID v3 retains 0.478 of IN and 0.487 of OUT, a difference of −0.008. Neither condition 1 nor condition 2 holds.
- The paper reports these rates with the source-cluster intervals of protocol 08.
