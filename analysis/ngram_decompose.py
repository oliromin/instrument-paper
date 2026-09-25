"""Share of the Wikipedia-minus-news retention gap absorbed by n-gram proximity.

The news cell is reweighted to the Wikipedia cell's distribution of the
Angika-minus-Hindi n-gram score (eight equal-width buckets over the pooled
score range), and the residual gap is compared with the raw gap.  Per-unit
scores come from results/ngram_units.json, written by ngram_length.py.

Intervals: 1,999 replicates at seed 20260912, resampling recovered source
clusters within each cell (1,871 Wikipedia clusters, 1,954 news clusters).
"""
import json
import os
import random

import common as C

SEED = 20260912
REPS = 1999
BUCKETS = 8


def rate(rows):
    return sum(1 for r in rows if r['retained']) / len(rows)


def make_bucket(lo, hi):
    width = (hi - lo) / BUCKETS

    def b(s):
        return min(int((s - lo) / width), BUCKETS - 1)
    return b


def reweighted(source, target, key):
    tgt = {}
    for r in target:
        tgt[key(r['s'])] = tgt.get(key(r['s']), 0) + 1
    total = sum(tgt.values())
    src = {}
    for r in source:
        src.setdefault(key(r['s']), []).append(r)
    num = den = 0.0
    for k, w in tgt.items():
        b = src.get(k)
        if not b:
            continue
        num += (w / total) * rate(b)
        den += w / total
    return num / den


def share(wiki, news, key):
    gap = rate(news) - rate(wiki)
    return 1 - (reweighted(news, wiki, key) - rate(wiki)) / gap, gap


def groups(rows, clusters):
    g = {}
    for r in rows:
        g.setdefault(clusters.get(r['uid'], 'unit:' + r['uid']), []).append(r)
    return list(g.values())


def main():
    units = C.load_json('results/ngram_units.json')
    wiki, news = units['wikipedia'], units['news']
    pooled = [r['s'] for r in wiki + news]
    key = make_bucket(min(pooled), max(pooled))
    point, gap = share(wiki, news, key)
    adj = reweighted(news, wiki, key)

    gw = groups(wiki, C.panel_clusters('panel1', 'P1', 'hin', 'L1'))
    gn = groups(news, C.news_clusters())
    rng = random.Random(SEED)
    shares = []
    for _ in range(REPS):
        w = [u for g in (gw[rng.randrange(len(gw))] for _ in gw) for u in g]
        n = [u for g in (gn[rng.randrange(len(gn))] for _ in gn) for u in g]
        if abs(rate(n) - rate(w)) < 1e-9:
            continue
        shares.append(share(w, n, key)[0])
    shares.sort()
    out = {'buckets': BUCKETS, 'raw_gap': gap, 'news_reweighted': adj,
           'share_of_gap_absorbed': point,
           'share_ci': [shares[int(0.025 * (len(shares) - 1))],
                        shares[int(0.975 * (len(shares) - 1))]],
           'resampling': 'source clusters in both cells',
           'clusters': {'wikipedia': len(gw), 'news': len(gn)},
           'replicates': REPS, 'seed': SEED}
    C.write_result('ngram_decomposition.json', out)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
