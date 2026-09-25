"""How much of the Wikipedia-minus-news retention gap each observable absorbs.

For each candidate observable the news cell is reweighted to the Wikipedia
cell's distribution of that observable (and the reverse), and the residual gap
is compared with the raw gap.  An observable that accounts for the source
contrast would drive the residual toward zero.

Intervals resample recovered source clusters within each cell: 1,871
Wikipedia clusters from the Leipzig mappings and 1,954 news clusters from the
stored Panel 2 source clusters.
"""
import collections
import random

import common as C
import register as R

SEED = 20260912
REPS = 1999


def bucket_fw(r):
    return min(r['fw_hits'], 4)


def bucket_tokens(r):
    for i, edge in enumerate((10, 14, 18, 24, 32)):
        if r['tokens'] < edge:
            return i
    return 5


def bucket_tpl(r):
    return int(r['tpl'])


def bucket_rtr(r):
    for i, edge in enumerate((0.05, 0.10, 0.15, 0.22)):
        if r['rtr'] < edge:
            return i
    return 4


def reweighted(source, target, key):
    tgt = collections.Counter(key(r) for r in target)
    total = sum(tgt.values())
    src = {}
    for r in source:
        src.setdefault(key(r), []).append(r)
    num = den = 0.0
    for k, w in tgt.items():
        b = src.get(k)
        if not b:
            continue
        num += (w / total) * (sum(1 for x in b if x['retained']) / len(b))
        den += w / total
    return num / den if den else float('nan')


def rate(rows):
    return sum(1 for r in rows if r['retained']) / len(rows)


def main():
    markers = R.hindi_markers()
    vocab, _ = R.published_vocab()
    texts = C.panel1_texts()
    v3p1 = C.panel1_preds('v3')
    clusters = C.leipzig_clusters(C.P1_CORPUS['hin'])
    wiki_ids = [uid for (lg, ln, uid) in texts if lg == 'hin' and ln == 'L1']
    templates, _ = R.heldout_templates({clusters.get(u) for u in wiki_ids},
                                       clusters)

    wiki = []
    for uid in wiki_ids:
        m = R.measure(texts[('hin', 'L1', uid)], markers, vocab, templates)
        m['retained'] = v3p1[('hin', 'L1', uid)].startswith('hin')
        m['cluster'] = clusters.get(uid, 'u:' + uid)
        wiki.append(m)

    v3p2 = C.panel2_preds('v3')
    nclusters = C.news_clusters()
    news = []
    for r in C.panel2_rows():
        if not (r['regime'] == 'A' and r['lang'] == 'hin' and r['length'] == 'L1'):
            continue
        m = R.measure(r['text'], markers, vocab, templates)
        m['retained'] = v3p2[('A', 'hin', 'L1', r['unit_id'])].startswith('hin')
        m['cluster'] = nclusters.get(r['unit_id'], 'u:' + r['unit_id'])
        news.append(m)

    keys = {'function_word_count': bucket_fw,
            'token_count': bucket_tokens,
            'stub_template_match': bucket_tpl,
            'rare_token_rate': bucket_rtr}

    byc = {}
    for r in wiki:
        byc.setdefault(r['cluster'], []).append(r)
    groups = list(byc.values())
    byn = {}
    for r in news:
        byn.setdefault(r['cluster'], []).append(r)
    ngroups = list(byn.values())
    rng = random.Random(SEED)

    out = {'seed': SEED, 'replicates': REPS,
           'resampling': 'source clusters in both cells',
           'wikipedia_retention': rate(wiki), 'news_retention': rate(news),
           'raw_gap': rate(news) - rate(wiki), 'observables': {}}

    for name, key in keys.items():
        adj = reweighted(news, wiki, key)
        share = 1 - (adj - rate(wiki)) / out['raw_gap']
        shares = []
        for _ in range(REPS):
            w = [u for g in (groups[rng.randrange(len(groups))]
                             for _ in range(len(groups))) for u in g]
            nn = [u for g in (ngroups[rng.randrange(len(ngroups))]
                              for _ in range(len(ngroups))) for u in g]
            g = rate(nn) - rate(w)
            if abs(g) < 1e-9:
                continue
            shares.append(1 - (reweighted(nn, w, key) - rate(w)) / g)
        shares.sort()
        out['observables'][name] = {
            'news_reweighted_to_wikipedia': adj,
            'residual_gap': adj - rate(wiki),
            'share_of_gap_absorbed': share,
            'share_ci': [shares[int(0.025 * (len(shares) - 1))],
                         shares[int(0.975 * (len(shares) - 1))]],
        }
        print('%-22s adjusted news=%.4f  residual=%.4f  absorbed=%+.3f '
              '[%+.3f,%+.3f]' % (name, adj, adj - rate(wiki), share,
                                 out['observables'][name]['share_ci'][0],
                                 out['observables'][name]['share_ci'][1]))

    C.write_result('decomposition.json', out)
    print('\nraw gap %.4f (news %.4f minus wikipedia %.4f)'
          % (out['raw_gap'], out['news_retention'], out['wikipedia_retention']))


if __name__ == '__main__':
    main()
