# Length characterisation of the Angika comparison, and the Awadhi released split

Status: hypothesis-informed. Fixed on 12 September 2026, before any new prediction or binwise rate was computed. The whole-split rates, the reference rates and the non-overlap found in protocol 07, part C, were known.

Governs the length comparison (Section 9.2; Appendix D) and the Awadhi case (Section 9.4; Appendix D).

## A. Angika length characterisation

**Populations.** The same as protocol 07, part C.

- The 868 reference articles and the 3,269 reference sentences.
- The 57,997 split documents.
- The 50,000-sentence draw at seed 20260907.

Repeated sentences map to their first parent document.

**Instruments.** GlotLID v1 and v2, verified by SHA-256. Each must reproduce its earlier reference sentence rate within 0.0001, or its new results are not reported.

**Bins.** Sentence and document arms are kept separate.

- Common support is the intersection of the two populations' 5th to 95th percentile character-length intervals, using NumPy's linear quantiles.
- The support starts as six equal-width bins in log length. Each bin includes its lower edge and excludes its upper edge, except the last, which includes both.
- A retained bin needs at least 50 units and 30 source documents from each population.
- The leftmost deficient bin is merged outward: leftward if its midpoint lies in the lower half of the bin sequence, rightward otherwise. An endpoint bin merges inward, and ties go left. This repeats until every bin qualifies or one remains.
- Fewer than three retained bins make the curve descriptive only.
- Edges are never re-chosen after rates are seen.

**Reported.** Per bin and model: the Hindi share in each population and the gap between them, with pointwise article-resampling intervals (protocol 08). A gap below 0.50 weakens a claim of large separation. A gap at or below 0.10 is convergence.

**Outcome.** The sentence arm keeps six bins over 32 to 177 characters. The gaps are 0.827 to 0.892 for v1 and 0.741 to 0.936 for v2. The document arm collapses to one bin (561 to 1,114 characters), with gaps of 0.824 and 0.968, and is not read as a curve.

## B. Awadhi released split

**Acquisition.** Before any Awadhi content is opened, the FineWeb-2 revision and file listing are frozen with their hashes. Only the retained awa_Deva train shard is read, and metadata only for the retained and removed shards of anp, awa, bho, mai and hin. Document counts come from Parquet footers, not from byte sizes.

**Instruments.** OpenLID and GlotLID v1 and v2. Each must reproduce its stored predictions on every retained ILI Awadhi unit exactly. GlotLID v3 is not run on the Awadhi split.

**Reported.** Shares to Hindi and to Awadhi for the whole split (1,902 documents), for a 50,000-sentence draw of its filtered sentences at seed 20260907, and for each ILI split separately. The same bin algorithm is used, without clustered intervals for ILI.

**Condition.** A whole-split Hindi share at or below 0.50, or an Awadhi share at or above 0.50, on a discriminating identifier is evidence against extending the Angika pattern to Awadhi.

**Outcome.** The whole-split shares to Awadhi are 0.865 (OpenLID), 0.746 (GlotLID v1) and 0.955 (GlotLID v2). The shares to Hindi are 0.093, 0.236 and 0.025. The Angika pattern does not extend to Awadhi. All three ILI comparisons keep six sentence bins.
