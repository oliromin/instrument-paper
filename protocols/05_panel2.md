# Panel 2 and the Panel 1 L20 cells

Status: pre-specified. Fixed on 8 September 2026, before any Panel 2 source was downloaded or any model was run against it.

Governs Panel 2, the Panel 1 L20 cells and the source-by-length profiles (Sections 3.2, 4.1 and 6; Appendices B and C). Panel 1 is not rebuilt, and no quantity averages across the two panels.

## Source rows and ground truth

Ground truth never comes from a language-identification output. For that reason FineWeb-2's hin_Deva split is excluded as a Hindi source.

**Regime A, news.** The Leipzig news subsets at the largest published size: hin_news_2022_1M, with nep_news_2020_300K and mar_news_2020_300K as controls. Sanskrit, Newari and Maithili have no Leipzig news subset.

**Regime B, the VarDial 2018 ILI shared task** (kmi-linguistics/vardial2018). Hindi, Awadhi, Bhojpuri, Braj and Magahi, with the task's own gold labels. The train, dev and test splits are kept separate and never pooled.

**Regime C, Angika Wikipedia.** The 1,028-article extract. A unit joins the row when the marker tagger (protocol 06) tags it Angika-marked. The row is therefore selected by a marker instrument and is not independent of it.

## Filters

Panel 1's filters, applied to the assembled unit at each length.

## Lengths

- L1: one sentence.
- L5: the first 5 sentences of one source document.
- L20: the first 20 sentences of one source document.
- LD: a whole article (Regime C only).

A length a source cannot support is recorded as unavailable. Sentences are never concatenated across documents.

Regime B supports L1 only. Leipzig publishes sampled sentences rather than documents, so LD is unavailable for Regime A.

Panel 1 gains an L20 cell for each language from the same Leipzig files.

## Draw

2,000 units per cell, uniformly without replacement, seed 20260908, drawn before any model is run. Where the filtered pool is smaller, the whole pool is used.

The ILI test cells are taken whole. The entire unfiltered ILI test set is also scored, so that it can be compared with the shared task.

## Pre-specified expectations and conditions

These are read on GlotLID v3 Hindi.

1. News L1 retention bands: at or below 0.60, the effect is present at Wikipedia strength. Above 0.60 and at or below 0.85, it is present and attenuated. Above 0.85, it is a Wikipedia artefact.
2. At least half of the news L1 loss lands on a Hindi-belt label.
3. News L20 retention stays at or below 0.70, and the L1-to-L20 rise is at most 0.15.
4. OpenLID's news loss at L20 is at most half its L1 loss, and GlotLID v3's is at least 0.80 of its L1 loss.
5. At build time: the news L1 pool shares no more than 1% exact text with Panel 1's Hindi L1 pool, and draws no material share of its sources from Wikipedia.
6. At build time: a cell with fewer than 300 filtered units is reported with its interval and not used to evaluate a threshold.
7. At build time: the Angika-marked share of the filtered Regime C pool at L1 is at least 0.50.

The belt languages as sources (Awadhi, Bhojpuri, Braj, Magahi, Angika) are exploratory and carry no conditions.

## Amendments, 8 September 2026, before any Panel 2 retention was computed

**ILI composition.** Half of the ILI test Hindi class is social-media text: 0.510 carry a mention, hashtag or URL. No other ILI cell carries any. The ILI Hindi cells are therefore reported separately, with train and dev read as literature and test as mixed.

**Accepted codes for the new source languages.** Awadhi awa, Bhojpuri bho, Braj bra, Magahi mag, Angika anp, under Panel 1's script rule. bh and bih count for Bhojpuri and Magahi only on an identifier carrying no member label. hin is never retention for these languages.

## Outcome

- Condition 1: news L1 retention is 0.805, in the attenuated band. The ILI literature cells give 0.867 (train) and 0.862 (dev).
- Condition 2 held: 0.977 of the news loss lands on a belt label, 0.933 on anp_Deva.
- Condition 3 failed on its first clause, with news L20 retention at 0.926. The rise is 0.121. Wikipedia L20 retention is 0.612.
- Condition 4 failed on its second clause: GlotLID v3's L20 news loss is 0.380 of its L1 loss.
- Condition 5 held: 4 shared sentences in 884,969, and 6 Wikipedia URLs among 73,412 sources.
- Condition 6 applied to five cells: Angika L20 (31), and Panel 1 L20 for Maithili (21), Marathi (59), Newari (119) and Sanskrit (278).
- Condition 7 held, at 0.665.
