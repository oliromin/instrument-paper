# Reading the published training files of the Angika and Hindi classes

Status: pre-specified. Fixed on 16 September 2026, before either file was downloaded.

Governs the reading of the published training collection (Section 9.3) and the membership test used in protocol 11.

## Material

Two files of the GlotLID corpus v3.1 (cis-lmu/glotlid-corpus), taken whole:

- v3.1/anp_Deva/anp_Deva_wikipedia.txt: 1,232,680 bytes, SHA-256 c0fe59f5…1df804.
- v3.1/hin_Deva/hin_Deva_leipzigwiki.txt: 233,956,634 bytes, SHA-256 e51c29ad…14176b6c.

The dataset card describes v3.1 as the GlotLID v3 training data with some edits. Every figure here is therefore a property of the published files, not of the material the model was trained on.

## Units

The segmenter and filters of protocol 06, with exact-duplicate removal after whitespace normalisation.

## Arm A: the Angika file

- The Angika-marked share of the file's sentences (tagger of protocol 06). This fails if it is below 0.40.
- The share of the file's sentences that exact-match a sentence of the 1,028-article extract. If above 0.80, the file is a re-measurement of the same material.
- The sentence count. Below 1,000, every share carries an interval.
- The tagger's Hindi side is not used.

## Arm B: identifier read of the Angika file

GlotLID v1 and v2, verified by SHA-256, each on its own prediction path. Each must first reproduce its share to Hindi on the 3,269 Angika-marked extract sentences (0.1089 and 0.0202) within 0.01. GlotLID v3 is not run on its own training material.

The file counts as not measurably contaminated if neither model's share to Hindi exceeds its reference share by more than 0.05.

## Arm C: panel membership in the Hindi file

The share of Panel 1's 2,000 Hindi L1 units that exact-match a line of the Hindi file after NFC normalisation and whitespace collapse. Below 0.05, the paper may not argue that the panel's Hindi was in training.

## Outcome

- Arm A: the file yields 3,970 sentences. The Angika-marked share is 0.786, and 0.286 of the sentences match the extract.
- Arm B: both references reproduced exactly. The shares to Hindi are 0.252 (v1) and 0.176 (v2), exceeding the references by 0.143 and 0.156.
- Arm C: 1,554 of 2,000 panel units (0.777) are in the Hindi file.
