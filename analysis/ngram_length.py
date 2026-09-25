"""Is the within-cell n-gram proximity gap a length effect?

Section 6.5 reports that Hindi units routed to Angika sit nearer the published
Angika file, in character n-gram terms, than the units retained as Hindi.  Those
routed units are also the shorter ones, so the gap could be an artefact of
length rather than of content.  This script reproduces the scores of
``ngram.py`` exactly --- same seed, same size-matched reservoir, same add-one
smoothed trigram-through-pentagram models --- records token and character counts
alongside each score, and then holds length fixed three ways: direct
standardisation of the gap to each cell's own token-length distribution, the gap
within five token bands, and a regression of the score on routing status and log
token count.  It also checks whether proximity still predicts routing at fixed
length, by comparing retention across score terciles computed inside each band.

Writes ``results/ngram_units.json`` (per-unit scores and lengths, which the
original run did not keep) and ``results/ngram_length.json``.
"""
import collections
import json
import math
import os
import random
import sys
import statistics

import numpy as np

import common as C

SEED = 20260912
NMIN, NMAX = 3, 5
REPLICATES = 1999
ANP_FILE = 'anp_Deva_wikipedia.txt'   # external inputs, found through INSTRUMENT_INPUTS
HIN_FILE = 'hin_Deva_leipzigwiki.txt'

BANDS = [(0, 10), (11, 14), (15, 19), (20, 29), (30, 10 ** 9)]
BAND_LABELS = ['<=10', '11-14', '15-19', '20-29', '30+']
MIN_PER_BAND = 10


def grams(text):
    t = ' ' + ' '.join(text.split()) + ' '
    for n in range(NMIN, NMAX + 1):
        for i in range(len(t) - n + 1):
            yield t[i:i + n]


def counts_from_lines(lines):
    c = collections.Counter()
    for line in lines:
        c.update(grams(line))
    return c


def band_of(tokens):
    for i, (lo, hi) in enumerate(BANDS):
        if lo <= tokens <= hi:
            return i
    return len(BANDS) - 1


def mean(xs):
    return float(np.mean(xs)) if len(xs) else float('nan')


def build_scorer():
    """Reproduces ngram.py's two reference models."""
    anp_lines = [l.strip() for l in open(C.external(ANP_FILE), encoding='utf-8') if l.strip()]
    anp_chars = sum(len(l) for l in anp_lines)

    # Reservoir sample of the Hindi file, size-matched by character count.  The
    # running total is maintained incrementally; the branch sequence, and hence
    # the RNG draw sequence, is identical to the original expression.
    rng = random.Random(SEED)
    reservoir, seen, cur = [], 0, 0
    with open(C.external(HIN_FILE), encoding='utf-8') as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            seen += 1
            if cur < anp_chars:
                reservoir.append(s)
                cur += len(s)
            else:
                j = rng.randrange(seen)
                if j < len(reservoir):
                    cur += len(s) - len(reservoir[j])
                    reservoir[j] = s
    hin_chars = sum(len(l) for l in reservoir)

    ca, ch = counts_from_lines(anp_lines), counts_from_lines(reservoir)
    vocab = set(ca) | set(ch)
    V = len(vocab)
    ta, th = sum(ca.values()) + V, sum(ch.values()) + V
    la = {g: math.log((ca.get(g, 0) + 1) / ta) for g in vocab}
    lh = {g: math.log((ch.get(g, 0) + 1) / th) for g in vocab}
    ua, uh = math.log(1 / ta), math.log(1 / th)

    def score(text):
        gs = list(grams(text))
        if not gs:
            return 0.0
        return sum(la.get(g, ua) - lh.get(g, uh) for g in gs) / len(gs)

    return score, {'angika_chars': anp_chars, 'hindi_sample_chars': hin_chars,
                   'vocab': V}


def collect(score):
    texts = C.panel1_texts()
    v3p1, v3p2 = C.panel1_preds('v3'), C.panel2_preds('v3')
    wiki, news = [], []
    for (lg, ln, uid), t in texts.items():
        if lg == 'hin' and ln == 'L1':
            p = v3p1[(lg, ln, uid)]
            wiki.append({'uid': uid, 's': score(t), 'tok': len(t.split()),
                         'ch': len(t), 'retained': p.startswith('hin'),
                         'angika': p == 'anp_Deva'})
    for r in C.panel2_rows():
        if r['regime'] == 'A' and r['lang'] == 'hin' and r['length'] == 'L1':
            p = v3p2[('A', 'hin', 'L1', r['unit_id'])]
            t = r['text']
            news.append({'uid': r['unit_id'], 's': score(t),
                         'tok': len(t.split()), 'ch': len(t),
                         'retained': p.startswith('hin'),
                         'angika': p == 'anp_Deva'})
    return {'wikipedia': wiki, 'news': news}


def raw_gap(rows):
    return (mean([r['s'] for r in rows if r['angika']])
            - mean([r['s'] for r in rows if r['retained']]))


def standardised_gap(rows):
    """Direct standardisation to the cell's own token-length distribution."""
    use = [r for r in rows if r['angika'] or r['retained']]
    num = den = 0.0
    bands = []
    for i in range(len(BANDS)):
        b = [r for r in use if band_of(r['tok']) == i]
        a = [r['s'] for r in b if r['angika']]
        k = [r['s'] for r in b if r['retained']]
        if len(a) < MIN_PER_BAND or len(k) < MIN_PER_BAND:
            bands.append({'band': BAND_LABELS[i], 'n_routed': len(a),
                          'n_retained': len(k), 'gap': None})
            continue
        g = mean(a) - mean(k)
        bands.append({'band': BAND_LABELS[i], 'n_routed': len(a),
                      'n_retained': len(k), 'gap': g})
        num += len(b) * g
        den += len(b)
    return (num / den if den else float('nan')), bands


def regression(rows):
    """score ~ 1 + routed + log(tokens)."""
    use = [r for r in rows if r['angika'] or r['retained']]
    X = np.column_stack([
        np.ones(len(use)),
        np.array([1.0 if r['angika'] else 0.0 for r in use]),
        np.log(np.array([max(r['tok'], 1) for r in use], dtype=float))])
    y = np.array([r['s'] for r in use])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    return float(beta[1]), float(beta[2])


def intervals(rows, cell, clusters):
    """Both cells resample recovered source clusters (1,871 Wikipedia and 1,954
    news clusters), as in Section 6.4."""
    rng = random.Random(SEED)
    use = [r for r in rows if r['angika'] or r['retained']]
    groups = {}
    for r in use:
        groups.setdefault(clusters[cell].get(r['uid'], 'unit:' + r['uid']), []).append(r)
    keys = list(groups)

    def draw():
        return [x for k in (rng.choice(keys) for _ in keys) for x in groups[k]]

    raw, std = [], []
    for _ in range(REPLICATES):
        s = draw()
        raw.append(raw_gap(s))
        std.append(standardised_gap(s)[0])

    def pct(v):
        return [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]
    return pct(raw), pct(std)


def retention_by_proximity_within_band(rows):
    """Score terciles computed inside each band, so no contrast is across
    lengths."""
    out = []
    for i in range(len(BANDS)):
        b = sorted((r for r in rows if band_of(r['tok']) == i), key=lambda r: r['s'])
        if len(b) < 60:
            out.append({'band': BAND_LABELS[i], 'n': len(b),
                        'retention_far': None, 'retention_near': None})
            continue
        k = len(b) // 3
        out.append({'band': BAND_LABELS[i], 'n': len(b),
                    'retention_far': sum(r['retained'] for r in b[:k]) / k,
                    'retention_near': sum(r['retained'] for r in b[-k:]) / k})
    return out


def main():
    if '--reuse-units' in sys.argv:
        # Rescore nothing: read the per-unit scores this script wrote earlier,
        # and carry over the scorer description recorded with them.
        units = C.load_json('results/ngram_units.json')
        prev = C.load_json('results/ngram_length.json')
        meta = {k: prev[k] for k in ('angika_chars', 'hindi_sample_chars', 'vocab')
                if k in prev}
    else:
        score, meta = build_scorer()
        print('Angika file %(angika_chars)d chars; size-matched Hindi reservoir '
              '%(hindi_sample_chars)d chars; union vocabulary %(vocab)d' % meta)
        units = collect(score)
        C.write_result('ngram_units.json', units, indent=None)
    clusters = {'wikipedia': C.panel_clusters('panel1', 'P1', 'hin', 'L1'),
                'news': C.news_clusters()}

    out = {'seed': SEED, 'replicates': REPLICATES, 'ngram_range': [NMIN, NMAX],
           'bands': BAND_LABELS, 'min_per_band': MIN_PER_BAND, 'cells': {}}
    out.update(meta)

    for cell in ('wikipedia', 'news'):
        rows = units[cell]
        routed = [r for r in rows if r['angika']]
        retained = [r for r in rows if r['retained']]
        g0 = raw_gap(rows)
        g1, bands = standardised_gap(rows)
        b_routed, b_logtok = regression(rows)
        ci_raw, ci_std = intervals(rows, cell, clusters)
        d = {'n': len(rows), 'n_routed': len(routed), 'n_retained': len(retained),
             'median_tokens_routed': statistics.median([r['tok'] for r in routed]),
             'median_tokens_retained': statistics.median([r['tok'] for r in retained]),
             'mean_routed': mean([r['s'] for r in routed]),
             'mean_retained': mean([r['s'] for r in retained]),
             'raw_gap': g0, 'raw_gap_ci': ci_raw,
             'standardised_gap': g1, 'standardised_gap_ci': ci_std,
             'share_of_raw_gap': g1 / g0,
             'ols_routed': b_routed, 'ols_log_tokens': b_logtok,
             'by_band': bands,
             'retention_by_proximity_within_band':
                 retention_by_proximity_within_band(rows)}
        out['cells'][cell] = d
        print('\n%s  n=%d  routed=%d  retained=%d' % (cell, d['n'], d['n_routed'],
                                                      d['n_retained']))
        print('  median tokens   routed %.0f   retained %.0f'
              % (d['median_tokens_routed'], d['median_tokens_retained']))
        print('  raw gap             %+.4f  [%+.4f, %+.4f]'
              % (g0, ci_raw[0], ci_raw[1]))
        print('  standardised gap    %+.4f  [%+.4f, %+.4f]   (%.0f%% of raw)'
              % (g1, ci_std[0], ci_std[1], 100 * g1 / g0))
        print('  regression on routed %+.4f   (log tokens %+.4f)'
              % (b_routed, b_logtok))
        print('  by band: ' + '  '.join(
            '%s %s' % (b['band'], 'n/a' if b['gap'] is None else '%+.4f' % b['gap'])
            for b in bands))
        print('  retention far->near proximity, within band: ' + '  '.join(
            '%s %s' % (r['band'], 'n/a' if r['retention_far'] is None else
                       '%.3f->%.3f' % (r['retention_far'], r['retention_near']))
            for r in d['retention_by_proximity_within_band']))

    out['wikipedia_minus_news'] = (mean([r['s'] for r in units['wikipedia']])
                                   - mean([r['s'] for r in units['news']]))
    print('\nreproduced wikipedia_minus_news %+.6f' % out['wikipedia_minus_news'])
    C.write_result('ngram_length.json', out)


if __name__ == '__main__':
    main()
