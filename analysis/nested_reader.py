"""Reader-judged units, nested sampled-source units and source-weighting
sensitivity.

Human subsets: GlotLID v1, v2, v3 and OpenLID-v3 retention on the 600
reader-judged units (reader-1 confirmed, both readers confirmed, and every
explicit reader-1 label), by source domain.  Nested units: retention at L1, L5
and L20 on the same sampled sources, with paired source resampling (4,999
replicates, seed 20260913; the GlotLID rows come first in the stream, then
OpenLID-v3 under common and recommended preprocessing).  Source sensitivity:
the original Hindi Wikipedia and news cells under unit weighting, equal-cluster
weighting and exclusion of the largest cluster.

Reads only identifier files; writes results/nested_reader_analysis.json.  The
exact-duplicate count of the source-sensitivity cells needs the rebuilt texts
and is added when texts/ exists.
"""
import collections
import os

import numpy as np

import common as C

RNG = np.random.default_rng(20260913)
B = 4999


def stats(rr, label, field='pred'):
    pp = [r[field] for r in rr]
    n = len(rr)
    bases = {p.split('_')[0] for p in label}
    hit = sum(p.split('_')[0] in bases and ('_' not in p or p.endswith('_Deva')) for p in pp)
    return {'n': n, 'retained': hit, 'retention': hit / n if n else None,
            'to_angika': sum(p == 'anp_Deva' for p in pp), 'destinations': dict(collections.Counter(pp))}


def hindi(p):
    return p.split('_')[0] in ['hi', 'hin'] and ('_' not in p or p.endswith('_Deva'))


def boot(cl, mat):
    u, idx = np.unique(cl, return_inverse=True)
    g = len(u)
    mat = np.asarray(mat, float)
    a = np.zeros((g, mat.shape[1]))
    d = np.bincount(idx)
    np.add.at(a, idx, mat)
    bs = []
    for i in range(0, B, 128):
        w = RNG.multinomial(g, np.ones(g) / g, size=min(128, B - i))
        bs.append((w @ a) / (w @ d)[:, None])
    return np.concatenate(bs)


def ci(x):
    return np.quantile(x, [.025, .975]).tolist()


def load_predictions():
    reader = {r['uid']: r for r in C.read_csv('reader_sample.csv')}
    for r in reader.values():
        for f in ('confirmed', 'both_confirmed'):
            r[f] = C.truth(r[f])
    url = {(r['source'], r['length'], r['unit_id']): r['source_url'] for r in C.read_csv('nested_units.csv')}
    pred = {}
    for t in ('v1', 'v2', 'v3'):
        rows = [dict(reader[r['uid']], set='human', pred=r['pred'])
                for r in C.read_csv('reader_sample_predictions_%s.csv' % t)]
        rows += [dict(r, set='nested', source_url=url[(r['source'], r['length'], r['unit_id'])])
                 for r in C.read_csv('nested_predictions_%s.csv' % t)]
        pred[t] = rows
    rows = []
    for r in C.read_csv('openlid_v3_predictions.csv'):
        if r['set'] == 'human':
            rows.append(dict(reader[r['unit_id']], set='human', pred=r['pred'], recommended_pred=r['recommended_pred']))
        elif r['set'] == 'nested':
            rows.append(dict(r, source_url=url[(r['source'], r['length'], r['unit_id'])]))
    pred['ol3'] = rows
    return pred


def main():
    pred = load_predictions()
    human, nested = {}, {}
    for t, rows in pred.items():
        for field in ['pred', 'recommended_pred'] if t == 'ol3' else ['pred']:
            tag = t if field == 'pred' else t + '_recommended'
            rr = [r for r in rows if r['set'] == 'human']
            for subset in ['confirmed', 'both_confirmed', 'reader_labeled']:
                for lang, label in [('hi', {'hin_Deva', 'hi'}), ('ne', {'npi_Deva', 'nep_Deva', 'ne'})]:
                    if subset != 'reader_labeled':
                        selected = [r for r in rr if r[subset] and r['lang'] == lang]
                    else:
                        selected = [r for r in rr if r['reader1'] == ('Hindi' if lang == 'hi' else 'Nepali')]
                    for domain in ['ALL'] + sorted({r['domain'] for r in selected}):
                        cell = selected if domain == 'ALL' else [r for r in selected if r['domain'] == domain]
                        human['|'.join([tag, subset, lang, domain])] = stats(cell, label, field)
            for source in ['Wikipedia', 'News']:
                nn = [r for r in rows if r['set'] == 'nested' and r['source'] == source]
                maps = {le: {r['unit_id']: r for r in nn if r['length'] == le} for le in ['L1', 'L5', 'L20']}
                ids = sorted(maps['L1'])
                assert set(ids) == set(maps['L5']) == set(maps['L20'])
                mat = np.array([[hindi(maps[le][uid][field]) for le in ['L1', 'L5', 'L20']] for uid in ids], float)
                cl = [maps['L1'][uid]['source_url'] or uid for uid in ids]
                bb = boot(cl, mat)
                nested[tag + '|' + source] = {
                    'n': len(ids), 'clusters': len(set(cl)),
                    'lengths': {le: {'k': int(mat[:, i].sum()), 'rate': float(mat[:, i].mean()), 'ci': ci(bb[:, i]),
                                     'to_angika': sum(maps[le][uid][field] == 'anp_Deva' for uid in ids)}
                                for i, le in enumerate(['L1', 'L5', 'L20'])},
                    'L20_minus_L1': {'value': float((mat[:, 2] - mat[:, 0]).mean()), 'ci': ci(bb[:, 2] - bb[:, 0])}}
    # Original Hindi cells: unit weighting, equal-cluster weighting, largest-cluster exclusion.
    lookup = {(r['corpus'], r['lang'], r['length'], r['unit_id']): r for r in C.read_csv('panel_source_clusters.csv')}
    corpus_of = {(r['lang'], r['length']): r['corpus'] for r in C.read_csv('panel1_units.csv')}
    texts = None
    if os.path.exists(os.path.join(C.TEXTS, 'panel1_units.jsonl.gz')):
        texts = {(corpus_of[(r['lang'], r['length'])], r['lang'], r['length'], r['unit_id']): r['text']
                 for r in C.texts('panel1_units')}
        for s in ('panel2_units', 'panel1_l20_units'):
            texts.update({(r['corpus'], r['lang'], r['length'], r['unit_id']): r['text'] for r in C.texts(s)})
    sens = {}
    for t in ['v1', 'v2', 'v3']:
        rr = [dict(r, corpus=corpus_of[(r['lang'], r['length'])]) for r in C.read_csv('panel1_predictions_%s.csv' % t)]
        rr += C.read_csv('panel2_predictions_%s.csv' % t)
        for source, corpus in [('Wikipedia', 'hin_wikipedia_2021_300K'), ('News', 'hin_news_2022_1M')]:
            for le in ['L1', 'L5', 'L20']:
                cell = [r for r in rr if r['lang'] == 'hin' and r['length'] == le and r['corpus'] == corpus]
                groups = collections.defaultdict(list)
                for r in cell:
                    groups[lookup[(corpus, 'hin', le, r['unit_id'])]['cluster']].append(hindi(r['pred']))
                ordered = sorted(groups, key=lambda g: (-len(groups[g]), g))
                largest = ordered[0]
                original = np.mean([hindi(r['pred']) for r in cell])
                drop = [v for g, vals in groups.items() if g != largest for v in vals]
                sens[t + '|' + source + '|' + le] = {
                    'n': len(cell), 'clusters': len(groups), 'largest_cluster_n': len(groups[largest]),
                    'unit_rate': float(original), 'equal_cluster_rate': float(np.mean([np.mean(v) for v in groups.values()])),
                    'without_largest_rate': float(np.mean(drop))}
                if texts is not None:
                    strings = [texts[(corpus, 'hin', le, r['unit_id'])] for r in cell]
                    sens[t + '|' + source + '|' + le]['exact_duplicate_excess'] = len(strings) - len(set(strings))
    result = {'human': human, 'nested': nested, 'source_sensitivity': sens,
              'bootstrap': {'replicates': B, 'seed': 20260913,
                            'nested_pairing': 'same source multiplicities across L1/L5/L20 within model'}}
    C.write_result('nested_reader_analysis.json', result, indent=2)
    for k, v in human.items():
        if k.endswith('ALL'):
            print('human', k, v['n'], v['retention'], v['to_angika'], flush=True)
    for k, v in nested.items():
        print('nested', k, v['n'], [(le, x['rate']) for le, x in v['lengths'].items()], flush=True)


if __name__ == '__main__':
    main()
