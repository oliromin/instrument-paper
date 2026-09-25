# Angika markers, the marker tagger and the sentence segmenter

Status: post hoc. The markers and lexical groups were derived on 6 September 2026, after the Panel 1 results were in hand. The tagger rule and the segmenter were fixed on 7 September 2026, before any FineWeb-2 material was read.

Governs the lexical groups of the Angika Wikipedia extract (Section 9.1, table of lexical groups), the Regime C selection of protocol 05, and the segmentation used for the released splits (protocol 07) and the training-file read (protocol 10).

## Material

1,028 Angika Wikipedia articles (anp.wikipedia.org) and the Leipzig hin_wikipedia_2021_300K subset. Angika sentences are filtered with Panel 1's filters and deduplicated: 4,823 sentences.

## Markers

Token log-odds between the Angika sentences and 120,000 Leipzig Hindi sentences. The 25 most Angika-distinctive tokens and the 25 most Hindi-distinctive tokens form the two lists (data/angika_markers.json). They are not re-derived on any later material.

## Tagger

A sentence is Angika-marked if it contains an Angika marker. Otherwise it is Hindi-marked if it contains a Hindi marker. Otherwise it is neither.

Matching is by whole whitespace-delimited token, exact string, with punctuation left on. Angika precedence is unconditional.

## Segmenter

A text is split after each danda (U+0964) or double danda (U+0965), and after each full stop, question mark or exclamation mark that is followed by whitespace or the end of the text. The terminator stays with its sentence. Each piece is split at newlines and stripped of surrounding whitespace. No other normalisation is applied. Panel 1's filters are then applied to the sentences.

## Recorded

For GlotLID v1, v2 and v3, the share of each lexical group sent to Hindi and to Angika.

## Outcome

The stored groups of the 4,823 sentences are 3,269 Angika-marked, 1,158 Hindi-marked and 396 neither.

GlotLID v3 sends 0.991 of Angika-marked sentences to Angika and 0.0009 to Hindi. It sends 0.738 of Hindi-marked sentences to Angika.

GlotLID v1 and v2, which carry no Angika label, send 0.109 and 0.020 of Angika-marked sentences to Hindi. They send 0.995 and 0.936 of Hindi-marked sentences to Hindi.

Applied to the same sentences, the declared tagger rule agrees with the stored groups on 4,794 of 4,823 and marks 3,251 as Angika. Every disagreement is a marker fused to adjacent characters, which the rule does not match.
