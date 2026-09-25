# Panel 1: construction and the three-release comparison

Status: pre-specified. Fixed on 6 September 2026, before any model was loaded.

Governs the Panel 1 cells (Sections 3.2, 4.1 to 4.3; Appendix A) and the GlotLID v1, v2, v3 retention comparison.

## Population and ground truth

Language is known by provenance. A unit was written on that language's own Wikipedia, as recorded in the Leipzig Corpora Collection 2021 Wikipedia subsets: nep_wikipedia_2021_100K, hin_wikipedia_2021_300K, mar_wikipedia_2021_30K, san_wikipedia_2021_30K, new_wikipedia_2021_30K, mai_wikipedia_2021_10K. No language-identification output is used to define ground truth.

These six are the Devanagari Wikipedia subsets Leipzig publishes. Angika, Bhojpuri, Awadhi and Magahi have none, so they appear only as destinations.

## Filters

Exact-duplicate removal within a cell. At least six whitespace tokens. At least 90% Devanagari among alphabetic characters (Unicode category L).

## Units

L1 is one sentence. L5 is the first five sentences of one Leipzig source document, in sentence-ID order, joined by single spaces.

## Draw

2,000 units per language and length, uniformly without replacement, seed 20260906, drawn before any model is loaded. Where the filtered pool is smaller, the whole pool is used and the count reported.

## Instruments

The three released GlotLID models are run identically and reported separately, never pooled. Predictions come only from the model's own predict path, at k = 1. The input is the unit text with newlines replaced by spaces.

Differences between releases are read as differences between releases, not as differences in training exposure, which no release publishes.

## Recorded

For each release, language and length: the full destination distribution over the emitted label set, retention, the share of the loss landing on a Devanagari label, and the share landing on another panel language.

## Pre-specified expectations and conditions

1. Losses stay on Devanagari labels. Fails if more than 5% of any cell's loss lands outside Devanagari.
2. Retention is ordered by the language's corpus size, used as a proxy for its weight in the confusable neighbourhood. Fails if the rank correlation is below 0.5 in any release at either length.
3. A language's inflow comes from its neighbours' losses rather than their size. Fails if a language in the lowest third by total loss supplies more to some bucket than one in the highest third.
4. A language whose confusable neighbourhood gains labels between releases loses retention. Fails if, across the two release steps, the change in retention and the change in the number of Devanagari labels its losses reach have a rank correlation below 0.5 in absolute value, or the wrong sign.
5. Length does not dominate. Fails if L1 and L5 retention differ by more than 20 points in any cell.
6. GlotLID v3 Nepali retention on this panel is not below 0.90.

## Outcome

Conditions 1, 5 and 6 held. No loss in any cell lands outside Devanagari. The largest L1 to L5 gap is 5.6 points. v3 Nepali retention is 0.9935.

Conditions 2, 3 and 4 failed.

- Condition 2: the corpus-size rank correlations are +0.371 and +0.200 (v1), −0.257 and −0.600 (v2), and −0.543 and −0.257 (v3), at L1 and L5 respectively.
- Condition 3: it failed on inflow counts of one and two units.
- Condition 4: the rank correlation is −0.364.

The paper makes no claim that rests on conditions 2 to 4.

Hindi retention falls from 0.9935 to 0.9415 to 0.4800 at L1 across v1, v2 and v3, while the other five L1 cells stay between 0.96 and 1.00 in every release.
