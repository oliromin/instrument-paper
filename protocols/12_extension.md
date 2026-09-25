# Reader-sample reuse, nested units, source concentration and OpenLID-v3

Status: pre-specified. Fixed on 13 September 2026, before any of the computations below. The results of protocols 01 to 09 and the reader agreement of protocol 04 (564 of 569, 183 of 198) were known, so these analyses extend the study with declared foreknowledge and are not independent confirmatory tests.

Governs the reader-confirmed routing (Section 5; Appendix H), the nested units (Section 6.1; Appendix I), the source-concentration checks (Section 6.2; Appendix I) and the contemporary comparison (Section 8; Appendix J).

No new human judgment is collected. The reader judgments of protocol 04 are reused only on the units they were given for.

## A. Reader sample

- The two readers' answers are reconciled against the stage-one key and texts. Answers are taken as recorded; none is repaired.
- Primary subset: units on which reader 1 matches the provenance label. Secondary subset: units on which both readers match it. Mixed, uncertain, mismatched and blank answers are reported as their own categories.
- The reader subsets are not representative of all panel inputs, and no verification rate is transferred to another population.
- GlotLID v1, v2 and v3, verified by SHA-256, and OpenLID-v3 read all 600 units, in both languages and every domain. Each model uses its native prediction path, with newlines replaced by spaces. OpenLID-v3 is read under common and under its published recommended preprocessing, top-1, with no threshold. Nothing is tuned on these labels.

## B. Nested units

- Built from the original 2,000 Hindi L20 source IDs of each of Leipzig Wikipedia and news: the first 1, 5 and 20 eligible sampled sentences of each source, from the same archives.
- A source is kept only if all three lengths pass the panel filters. The L20 text must reproduce the stored panel unit before any model is run; otherwise the limitation is reported instead.
- The same sources enter every length, and resampling is paired across lengths: 4,999 replicates, seed 20260913 (protocol 08).
- No claim is made about consecutive original passages, an isolated token-count effect or a population-wide causal effect of length.

## C. Source concentration

For the six original Hindi Wikipedia and news cells (L1, L5, L20): the number and largest size of source clusters, GlotLID v3 retention weighted by unit, weighted equally by cluster, and with the largest cluster left out, and the count of exact text duplicates. These are sensitivities with their own estimands. They do not replace the original rates.

## D. OpenLID-v3

OpenLID-v3, identified by repository revision and SHA-256, reads Panel 1, the Regime C Angika L1 row, the original Hindi Wikipedia and news cells, the nested units and the reader sample. Its label coverage is read from the binary. Hindi retention and destination composition are reported separately. The historical models remain the basis for release comparisons.

## Outcome

- A. Reader 1 confirms 279 Hindi and 285 Nepali units; both readers confirm 86 and 93. On reader-1-confirmed Hindi, GlotLID v1, v2 and v3 retain 0.996, 0.957 and 0.774, and v3 sends 59 units to Angika. The existing v3 labels reproduce on all 600 units.
- B. Both L20 reconstructions are exact. 1,760 Wikipedia and 1,334 news sources pass at all three lengths (240 and 666 excluded), giving 9,282 nested units. GlotLID v3 retention rises from L1 to L20 by 0.077 on Wikipedia and 0.150 on news, with paired intervals [0.048, 0.105] and [0.127, 0.172].
- C. The largest L1 cluster holds 4 units, and the L5 and L20 cells have one unit per source. Equal-cluster weighting and leaving out the largest cluster move no cell by more than 0.007.
- D. OpenLID-v3 carries 195 labels, including Hindi, Nepali, Maithili and Awadhi but not Angika or Newari. It retains 0.965 (common) and 0.957 (recommended) of Panel 1 Hindi L1, and 271 and 266 of the 279 reader-confirmed Hindi units.
