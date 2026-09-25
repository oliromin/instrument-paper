# Cross-identifier comparison on Panel 1

Status: pre-specified. Fixed on 6 September 2026, before any identifier other than the three GlotLID releases was obtained or run.

Governs the seven-identifier comparison on Panel 1 (Sections 3.3, 4.2 and 4.3; Appendix A) and the accepted-label and script rules used throughout the paper.

## Panel

Panel 1 as fixed in protocol 01, read unchanged.

## Input

The unit text with newlines replaced by single spaces, and no other normalisation, for every identifier.

## Identifiers

langid.py (py3langid), CLD3 (gcld3), fastText lid.176, OpenLID (201 labels), and GlotLID v1, v2 and v3. Each identifier is reported separately and never pooled with another.

Predictions come only from each identifier's own prediction path. For fastText models this is multilinePredict at k = 1. The artefact identity of each is recorded: file, size and SHA-256, or package and version.

An identifier that cannot be obtained is recorded as such. No substitute is used.

## Label rules

**Retention.** A unit of language X is retained if the emitted label's base code, script suffix removed, is in X's accepted set, and the label carries no script suffix or the suffix Deva. The accepted sets are:

- Nepali: nep, npi, ne
- Hindi: hin, hi
- Marathi: mar, mr
- Sanskrit: san, sa
- Newari: new, nwx
- Maithili: mai

**Macrolanguage labels.** A macrolanguage label outside these sets (bh, bih) counts for a member language only on an identifier that carries no label for that member.

**Script.** For labels with a script suffix, the suffix decides. For labels without one, a label is Devanagari if its code is in the fixed list:

anp awa bfy bgc bgd bh bho bhb bih bjj bns bra dty gbm gom hi hin hne hoj kfy khn kok mag mai mar mr mup mwr ne nep new noe npi nwx raj rwr san sa sck the thl unr wbr xnr

Sindhi and Santali are not counted as Devanagari.

**Hindi-belt neighbourhood.** The labels whose base code is in:

anp awa bfy bgc bh bho bhb bih bjj bns bra gbm hne hoj kfy mag mai mup mwr noe raj rwr unr wbr xnr

Label counts are read from each identifier's emitted label list, not from its documentation.

**Unsupported cells.** A cell whose language the identifier cannot emit is recorded as unsupported and excluded from every comparison. It is not scored as zero.

## Pre-specified expectations and conditions

1. An identifier with no Hindi-belt label does not send more than 25% of Hindi to any single non-Hindi label.
2. Across the seven identifiers, the Spearman correlation between Hindi retention and the Hindi-belt label count is −0.5 or lower, at each length.
3. No identifier with five or more Hindi-belt labels retains Hindi at 0.90 or above at both lengths.
4. On identifiers with at least two Hindi-belt labels, Hindi has the largest loss among the panel languages the identifier supports.
5. No more than 5% of any cell's loss leaves Devanagari.
6. The Hindi-belt label count is not collinear with release year: absolute Spearman correlation below 0.9. The release years are fixed as langid.py 2011, lid.176 2016, CLD3 2018, OpenLID 2023, GlotLID v1 2023, GlotLID v2 2024 and GlotLID v3 2024.

The GlotLID results were known when these rules were fixed. Conditions 2 to 4 are therefore tests only on the four other identifiers. Conditions 3 and 4 were recorded in advance as expected to fail on GlotLID v1.

Correlations over seven identifiers are descriptive. No significance test is computed.

## Outcome

Conditions 1, 5 and 6 held.

- Condition 1: the largest single non-Hindi destination on langid.py and CLD3 is 0.0080.
- Condition 5: no unit of any identifier leaves Devanagari.
- Condition 6: the correlation is +0.889.

Conditions 2, 3 and 4 failed.

- Condition 2: the correlations are −0.473 at L1 and −0.547 at L5.
- Condition 3: failed on GlotLID v1 and v2.
- Condition 4: failed on GlotLID v1, on v2 at L5, and on lid.176. lid.176 retains all Hindi and loses 0.374 of Maithili and 0.199 of Newari.

The paper makes no claim that retention decreases in the number of neighbourhood labels.

## Amendment, 6 September 2026, before any retention was computed

The accepted sets above are applied as written, including nep for Nepali on identifiers that also carry npi. The macrolanguage rule applies only to labels outside those sets.
