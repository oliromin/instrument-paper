# Reading the Angika-labelled released split

Status: post hoc. Designed after the Panel 1 results. Rules were fixed on 7 September 2026, before the FineWeb-2 anp_Deva split was read.

Governs the released-split reading and the Angika reference audit (Section 9.1; Appendix G). The length comparison that replaced the design in part C is protocol 09.

## Material

The whole FineWeb-2 anp_Deva train split: 57,997 documents. Revision af9c1333…b9, SHA-256 e0cad859…abcfc.

The reference is the 1,028-article Angika Wikipedia extract. The articles in which at least half of the filtered sentences are Angika-marked (868 articles) serve at article level. The 3,269 Angika-marked extract sentences serve at sentence level.

Segmentation and marker tagging are as in protocol 06. The markers are not re-derived on any audited material.

## A. Marker split of the released split

The share of Angika-marked, Hindi-marked and neither sentences, reported separately at document and sentence level. The Hindi-marked share is a lower bound.

A validity condition was fixed on a FineWeb-2 hin_Deva control. The control is 200 blocks of 100 consecutive rows at seed 20260907, because the split cannot be sampled row by row. If fewer than 80% of control sentences are Hindi-marked, no Hindi verdict from the marker route is reported.

**Outcome.** The control share was 0.688, so the validity condition failed. No Hindi-marked share of the split is reported.

## B. Identifier read of the released split

All documents are read by five identifiers that carry no Angika label: langid.py, CLD3, lid.176, GlotLID v1 and GlotLID v2. GlotLID v3 produced the split and enters no quantity.

Before the split is read, GlotLID v1 and v2 are run on the 3,269 Angika-marked reference sentences. They must reproduce their earlier shares to Hindi, 0.1089 and 0.0202, within 0.05. Otherwise nothing is reported.

Expectations:

1. The median share to Hindi across the five identifiers is at least 0.80.
2. GlotLID v1 and v2 each send at least 0.60 of the split to Hindi.
3. All five identifiers agree on Hindi for at least 0.60 of documents.

A reader stage is commissioned only if expectation 1 or 3 fails.

**Outcome.** The positive control reproduced. The shares to Hindi were:

- lid.176: 0.9995
- CLD3: 0.9983
- langid.py: 0.9956
- GlotLID v1: 0.9905
- GlotLID v2: 0.9816

All five agree on 0.9773 of documents. Expectations 1 to 3 held, so no reader stage was commissioned.

The per-document predictions of langid.py, CLD3 and lid.176 were not kept. Their shares survive as aggregates only.

## C. Length-matched contrast

GlotLID v1 and v2 read the 868 reference articles and the split, at document level and at sentence level. The split's sentences are a 50,000-sentence sample at seed 20260907. Shares to Hindi are compared within fixed character bins (250, 500, 1,000, 2,000 and 4,000), for bins holding at least 100 units of each population, and at least three such bins are required.

**Outcome.** v1 and v2 sent 0.0829 and 0.0104 of the reference articles to Hindi. Only two bins held 100 units of each population, because the two populations barely overlap in length. The within-bin comparison was therefore reported as unavailable, and the length comparison was redesigned in protocol 09.
