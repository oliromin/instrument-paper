# Label inventories of GlotLID v2 and v3

Status: post hoc. The question arose from the Hindi result of protocol 01. Rules were fixed on 17 September 2026, before any routing to new labels was computed.

Governs the label-inventory comparison (Section 4.1; Appendix E).

## Inventories

- The label lists of GlotLID v2 and v3 are read from the binaries, verified by SHA-256 (data/model_identities.json).
- Added and removed labels are the set differences between the two lists.
- The und_ placeholders for unseen Unicode categories are separated from genuine language classes before any routing outcome is inspected.
- Genuine additions are reported by script.

## Routing

For each Panel 1 cell at L1 and L5, the share of units that v3 sends to any genuine new class, and their destinations. The stored Panel 1 predictions are used; no model is run.

## Expectation

A second Panel 1 cell, besides Hindi, loses a substantial share of its units to a class new in v3.

## Outcome

- v2 carries 1,848 labels and v3 carries 2,102. v3 adds 302 and removes 48.
  - 157 of the additions are placeholders, so 145 are genuine language classes: 109 Latin, 11 Cyrillic, 7 Devanagari and 5 Arabic, with the rest in ones and twos.
  - The Devanagari additions are Angika, Bodo, Dogri, Doteli, Goan Konkani, Kukna and Sindhi.
  - The removals are macrolanguage retirements, among them ara_Arab, zho_Hani and nep_Deva.
- The expectation did not hold, and the result is reported as a null. The shares of each L1 cell sent to a new class are:
  - Hindi 0.5075
  - Newari 0.0160
  - Nepali 0.0050
  - Sanskrit 0.0045
  - Marathi 0.0040
  - Maithili 0.0010

  At L5, the Nepali, Marathi and Sanskrit cells lose nothing to a new class.
- Not predicted, and reported as an observation: of the 61 units the five non-Hindi L1 cells send to new classes, 56 go to Angika.
