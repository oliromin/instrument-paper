# Confidence scores of GlotLID v3 on the Hindi Panel 1 units

Status: pre-specified. Fixed on 7 September 2026, before the model was loaded for this measurement.

Governs the confidence-survival counts (Section 7; Appendix C, table of confidence scores).

## Question

FineWeb-2 keeps a document for a label only if its score clears a per-label threshold tau = max{0.3, min{0.9, Med(X) − sigma(X)}}.

- A score of 0.9 or above clears every threshold this rule can produce.
- A score below 0.3 clears none.
- Between the two, the outcome depends on a score distribution that is not published, and it is not decided here.

The score is the model's softmax output, the quantity the rule is applied to. It is not treated as a calibrated probability.

## Population and instrument

The 2,000 Hindi units at L1 and the 2,000 at L5 of Panel 1, unchanged. GlotLID v3 (model_v3.bin, SHA-256 a818b6bd…cafc9e). The input is the same as the panel run.

## Prediction path

The single-string predict path at k = 5. The batch path is not used, because it returns incorrect probabilities for k greater than 1.

For each unit, record the top label and its score, the top five labels with their scores, and the score of hin_Deva if it is among the five.

## Check

The top label of every unit must equal the label stored for that unit in the panel run. If any unit differs, nothing is reported.

## Pre-specified conditions

1. If more than half of the units labelled anp_Deva score 0.9 or above, the misrouted material clears every threshold the rule can produce.
2. If more than half score below 0.3, it clears none.
3. If neither holds, the outcome is undecidable on public data.
4. The scores of units retained as Hindi are reported alongside, descriptively, with no threshold.

## Outcome

The check passed on all 4,000 units. Nineteen scores exceed 1 by at most 1e−5. This is a numerical feature of the fastText output.

- Condition 1 holds at L1, where 574 of 1,015 units score 0.9 or above (0.566). It does not hold at L5, where 277 of 952 do (0.291).
- Condition 2 holds at neither length: no unit scores below 0.3.
- At L5 the majority of units lies between 0.3 and 0.9.

Median scores at L1 are 0.925 for units assigned to Angika and 0.871 for units retained as Hindi.
