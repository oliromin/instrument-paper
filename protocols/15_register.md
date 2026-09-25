# Register and the Wikipedia–news retention gap

Status: post hoc in motivation, pre-specified in execution. The analysis was prompted by the GlotLID v3 gap between the Hindi Wikipedia and news L1 cells (0.480 against 0.805). Instruments, buckets and expectations were fixed on 16 September 2026, before any register measure or retention by register was computed.

Governs the register analysis (Section 6.4; Appendix F).

## Cells

The Panel 1 Hindi Wikipedia L1 cell and the Leipzig Hindi news L1 cell, 2,000 units each, with the stored GlotLID v3 predictions. No model is run.

## Instruments

None is fitted to the retention outcome.

- **Function-word evidence.** Matches against the 25-token Hindi list of protocol 06, used unchanged. Reported as a rate per token, a count per unit and the share of units with no match.
- **Rare-token rate.** The share of a unit's tokens absent from the 10,000 most frequent types of the published GlotLID v3.1 Hindi training file (protocol 10). The vocabulary size is fixed here.
- **Stub-template match.** Whether a unit's final token trigram is among the 200 most frequent sentence-final trigrams of held-out Hindi Wikipedia. Every source cluster represented in the panel is excluded from the held-out set.
- **Token count**, as a comparison observable.

Tokens and markers are matched after edge punctuation is stripped from both. This normalisation was added after a first run showed that list entries carrying a danda could not match sentences ending in a full stop. All reported figures use it.

## Expectations

If the gap is a register effect:

1. the Wikipedia cell is lower in function-word evidence and higher in rare-token rate than the news cell;
2. within each cell, retention rises with function-word evidence;
3. reweighting the news cell to the Wikipedia cell's distribution of an observable absorbs a substantial share of the gap.

## Reweighting

Buckets: function-word count 0, 1, 2, 3 and 4 or more; six token-count bands; template match or not; five rare-token bands. News retention is recomputed under the Wikipedia cell's bucket weights. The share absorbed is the fall in the gap over the raw gap. Intervals: 1,999 replicates at seed 20260912, source clusters resampled in both cells.

## Outcome

None of the three expectations held.

1. Function-word rate is 0.111 on Wikipedia against 0.104 on news, the no-match share 0.112 against 0.153, and the rare-token rate 0.114 against 0.127. The Wikipedia cell has slightly more of the evidence, not less. The template share is higher on Wikipedia (0.172 against 0.117) but does not predict retention in either cell.
2. News retention rises from 0.732 with no function-word match to 0.877 with four or more. Wikipedia retention does not rise steadily (0.491, 0.415, 0.506, 0.485, 0.608).
3. Reweighting absorbs between −0.018 and 0.006 of the 0.325 gap, and no interval reaches 0.02.

The result is reported as a null, and the source contrast is left unexplained.
