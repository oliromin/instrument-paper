# Character n-gram proximity to the published Angika training file

Status: post hoc in motivation, pre-specified in execution. Part A was prompted by the register null of protocol 15 and fixed on 16 September 2026, before any proximity score was computed. Part B is a further post hoc check, prompted by the observation in part A that units routed to Angika are shorter than units retained. It was fixed on 17 September 2026, before any length-standardised gap was computed.

Governs the n-gram proximity analysis (Section 6.5; Appendix F).

## A. Proximity

**Cells.** The two Hindi L1 cells of protocol 15, with the stored GlotLID v3 predictions. No model is run.

**Score.** For each unit, the mean log-probability per character n-gram under a model of the published GlotLID v3.1 Angika file, minus the same under a model of the published Hindi file (protocol 10).

- Character trigrams to pentagrams, with a leading and trailing space.
- Add-one smoothing over the union vocabulary of the two reference files.
- The Hindi reference is sampled from the Hindi file to match the Angika file in characters, by reservoir sampling at seed 20260912.

**Expectations.** The three of protocol 15, on this instrument:

1. the Wikipedia cell sits nearer the Angika file than the news cell;
2. within each cell, retention falls as proximity to the Angika file rises, and units routed to Angika sit nearer the Angika file than units retained;
3. reweighting the news cell to the Wikipedia cell's proximity distribution absorbs a substantial share of the gap.

**Reweighting.** Eight equal-width buckets over the pooled score range. Intervals: 1,999 replicates at seed 20260912, source clusters resampled in both cells (1,871 and 1,954 clusters).

## B. Length standardisation

**Expectation.** If the routed-versus-retained gap is a length effect, it disappears once token length is held fixed.

**Rule.**

- Five token bands: 10 or fewer, 11 to 14, 15 to 19, 20 to 29, and 30 or more.
- Each cell's gap is weighted by that cell's own band occupancy.
- A band contributes only if it holds at least 10 routed and 10 retained units.
- Intervals: 1,999 replicates at seed 20260912, source clusters resampled as in part A.
- As a cross-check, the score is regressed on routing status and log token count.
- The three published figures of part A must reproduce before anything is added.

## Outcome

- A. The reference files contribute 196,708 and 239,536 n-gram types, a union of 351,270.
  - Expectation 1 held: the Wikipedia cell sits nearer the Angika file by 0.121.
  - Expectation 2 held. Retention falls from 0.560 to 0.370 across Wikipedia proximity deciles and from 0.875 to 0.695 across news deciles. Routed units sit nearer the Angika file by 0.048 (Wikipedia) and 0.078 (news).
  - Expectation 3 held in part: reweighting absorbs 0.112 of the 0.325 gap, interval [0.070, 0.159]. This is reported as a partial account.
- B. The expectation did not hold. The part A figures reproduced.
  - Routed units are shorter (median 13 against 20 tokens on Wikipedia, 14 against 16 on news), but longer units score nearer the Angika file.
  - Standardised gaps are 0.054 [0.032, 0.077] and 0.088 [0.061, 0.114], slightly larger than the raw gaps. The gap is positive in all ten cell-by-band combinations.
  - The regression gives routing coefficients of 0.054 and 0.086.
  - Both the raw and the standardised gaps are reported.
