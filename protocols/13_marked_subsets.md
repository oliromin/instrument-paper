# Maithili and Newari retention on marker-selected subsets

Status: post hoc. The question arose from the Panel 1 results. Rules were fixed on 8 September 2026, before any Maithili or Newari marker was derived and before any retention on a subset of the panel was computed. The all-unit retentions of protocols 01 and 02 were known, so the conditions are stated relative to them.

Governs the marked-subset restriction (Section 4.4) and the Maithili and Newari marker lists (data/maithili_markers.json, data/newari_markers.json).

## Question

lid.176 loses a large share of the Maithili and Newari cells to Hindi at L1. If those units are Hindi text on the Maithili and Newari wikis, the loss reflects corpus content rather than the identifier. The test restricts each cell to units carrying that language's own distinctive markers.

## Material

- The Leipzig Maithili (10K), Newari (30K) and Hindi (300K) Wikipedia subsets from which Panel 1 was drawn. Ground truth is provenance.
- Markers are derived on held-out material. Every sentence drawn into the panel is excluded, together with every sentence of every source behind an L5 unit.
- The Hindi contrast is 120,000 sentences drawn from the held-out Hindi remainder at seed 20260908.
- A whole-subset derivation, without the hold-out, is reported as a sensitivity only.

## Marker rule

- Counts are sentence-level document frequencies of whole whitespace-delimited tokens, exact match, punctuation kept.
- Target-distinctive markers: zero Hindi document frequency and at least 20 in the target set, the top 25 by target frequency.
- Hindi-distinctive markers: at least 200 in the Hindi contrast, the top 25 by log-odds against the target, with 0.5 added to each count.
- A unit is target-marked if it carries a target marker, otherwise Hindi-marked if it carries a Hindi marker, otherwise neither.
- No marker is added, removed or edited after the lists are computed.

## Measurement

For Maithili and Newari at L1 and L5, per group: retention under every identifier with a binomial 95% interval, and the destination composition of the loss. Predictions are the stored Panel 1 predictions; no model is run. Accepted labels are those of protocol 02. Marked cells below 300 units are reported with their interval but evaluate no condition.

## Conditions

1. Maithili: if lid.176 retains more than 0.8130 of the marked L1 subset (half the all-unit loss), the loss is carried by unmarked units, and the result is not used as evidence.
2. Newari: the same rule at 0.9005.
3. Direction: if less than 0.50 of a language's marked-subset loss under lid.176 goes to a Hindi label, its loss is not described as going into Hindi.
4. Coverage: if the marked share of an L1 cell is below 0.30, that language's result is descriptive only.
5. Comparability: if fewer than 15 tokens meet the zero-count rule for a language, the marker instrument is not comparable to the Angika one and that language is not analysed.

## Checks

- lid.176 must retain at least 0.98 of the Hindi L1 panel units that carry a Hindi marker from either list.
- The all-unit retentions recomputed from the stored predictions must equal those of Appendix A.

The marker lists are published with their counts on both sides.

## Outcome

- Derivation sets hold 4,839 Maithili and 15,782 Newari sentences. 114 Maithili and 250 Newari tokens meet the zero-count rule; condition 5 did not fire. Both lists consist mainly of copulas, postpositions and function words.
- The marked subsets are 1,686 (0.843) of the Maithili L1 cell and 1,624 (0.812) of the Newari L1 cell; condition 4 did not fire.
- lid.176 retains 0.6845 of marked Maithili and 0.8701 of marked Newari; conditions 1 and 2 did not fire.
- 0.6992 of the marked Maithili loss goes to Hindi. For Newari the share is 0.2607, with about 0.725 going to Marathi, so condition 3 fired for Newari and its loss is not described as going into Hindi.
- GlotLID v3 retains 1.0000 of marked Maithili and 0.9994 of marked Newari.
- Both checks held: lid.176 retains 1.0000 of the 1,874 marked Hindi units, and every all-unit retention reproduced.
- The marked subsets are selected by the marker instrument and are not samples of Maithili or Newari writing.
