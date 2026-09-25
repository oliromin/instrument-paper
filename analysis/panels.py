"""Panel retention, destinations, paired release differences, Hindi-bucket
composition, confidence survival and script closure, with conditional
source-cluster resampling that keeps the fixed panel mixtures.

Reads the Panel 1, Panel 2 and Panel 1 L20 unit files, the stored predictions
of all seven identifiers, the stored source clusters
(data/panel_source_clusters.csv, rebuilt from the Leipzig archives by
source_clusters.py) and the GlotLID v3 confidence scores.  No text is needed.
Writes results/panel_analysis.json.
"""
import collections
import json
import os

import numpy as np

import common as C

B = 4999
RNG = np.random.default_rng(20260912)
TAGS = ['langid', 'lid176', 'cld3', 'openlid', 'v1', 'v2', 'v3']
ACCEPT = {'hin': {'hi', 'hin'}, 'nep': {'ne', 'nep', 'npi'}, 'mar': {'mr', 'mar'}, 'san': {'sa', 'san'},
          'new': {'new', 'nwx'}, 'mai': {'mai'}, 'anp': {'anp'}, 'awa': {'awa'}, 'bho': {'bho'},
          'mag': {'mag'}, 'bra': {'bra'}}
BELT = set('anp awa bfy bgc bh bho bhb bih bjj bns bra gbm hne hoj kfy mag mai mup mwr noe raj rwr unr wbr xnr'.split())
DEVA = set('anp awa bfy bgc bgd bh bho bhb bih bjj bns bra dty gbm gom hi hin hne hoj kfy khn kok mag mai mar mr mup '
           'mwr ne nep new noe npi nwx raj rwr san sa sck the thl unr wbr xnr'.split())


def ci(x):
    return [float(z) for z in np.quantile(x, [.025, .975])]


def parts(p):
    x = p.split('_')
    return x[0], x[1] if len(x) > 1 else None


def good(p, codes):
    b, s = parts(p)
    return b in codes and s in (None, 'Deva')


LABELS = {t: {parts(x)[0] for x in C.load_json('data/model_labels.json')[t]} for t in TAGS}


def accepted(lang, t):
    a = ACCEPT[lang].copy()
    if lang in ['mai', 'bho', 'mag'] and not a & LABELS[t] and not LABELS[t] & {'mai', 'bho', 'mag'}:
        a |= {'bh', 'bih'}
    return a


def ratio_boot(clusters, numerators, denominators=None):
    """Unit-weighted ratios; all columns share each sampled source multiplicity."""
    numerators = np.asarray(numerators, dtype=float)
    if numerators.ndim == 1:
        numerators = numerators[:, None]
    if denominators is None:
        denominators = np.ones_like(numerators)
    denominators = np.asarray(denominators, dtype=float)
    u, ix = np.unique(clusters, return_inverse=True)
    g = len(u)
    a = np.zeros((g, numerators.shape[1]))
    d = np.zeros_like(a)
    np.add.at(a, ix, numerators)
    np.add.at(d, ix, denominators)
    vals = []
    for k in range(0, B, 128):
        w = RNG.multinomial(g, np.full(g, 1 / g), size=min(128, B - k))
        num = w @ a
        den = w @ d
        vals.append(np.divide(num, den, out=np.full_like(num, np.nan), where=den > 0))
    return np.concatenate(vals), g


def load_rows():
    p1 = [dict(r, panel='panel1', regime='P1') for r in C.read_csv('panel1_units.csv')]
    p2 = [dict(r, panel='panel2') for r in C.read_csv('panel2_units.csv')]
    ext = [dict(r, panel='panel1_ext') for r in C.read_csv('panel1_l20_units.csv')]
    return p1, p2, ext


def k(r):
    return (r['panel'], r['regime'], r['corpus'], r['lang'], r['length'], r['unit_id'])


def main():
    p1, p2, ext = load_rows()
    allrows = p1 + p2 + ext
    stored = {(r['panel'], r['regime'], r['corpus'], r['lang'], r['length'], r['unit_id']): r['cluster'] or None
              for r in C.read_csv('panel_source_clusters.csv')}
    for r in allrows:
        r['cluster'] = stored[k(r)]
    lookup = {k(r): r for r in allrows}
    corpus_of = {(r['lang'], r['length']): r['corpus'] for r in p1}
    pred = {}
    for t in TAGS:
        pp = [dict(r, panel='panel1', regime='P1', corpus=corpus_of[(r['lang'], r['length'])])
              for r in C.read_csv('panel1_predictions_%s.csv' % t)]
        pp += C.read_csv('panel2_predictions_%s.csv' % t)
        pred[t] = {k(r): r['pred'] for r in pp}
        assert set(lookup) == set(pred[t]), (t, len(lookup), len(pred[t]))
    cells = collections.defaultdict(list)
    for r in allrows:
        cells[k(r)[:-1]].append(r)
    summaries, boots, closure = {}, {}, {}
    for ck, rr in cells.items():
        name = '|'.join(ck)
        lang = ck[3]
        nn = len(rr)
        columns, names, stats = [], [], {}
        for t in TAGS:
            a = accepted(lang, t)
            pp = [pred[t][k(r)] for r in rr]
            carried = bool(a & LABELS[t])
            values = {'retention': np.array([good(p, a) for p in pp]),
                      'to_hindi': np.array([good(p, {'hin', 'hi'}) for p in pp]),
                      'to_angika': np.array([good(p, {'anp'}) for p in pp]),
                      'to_belt': np.array([good(p, BELT) for p in pp])}
            stats[t] = {'carried': carried, 'destinations': dict(collections.Counter(pp))}
            for metric, x in values.items():
                stats[t][metric] = {'k': int(x.sum()), 'n': nn, 'value': float(x.mean())}
                names.append(t + '/' + metric)
                columns.append(x)
            if ck[0] == 'panel1':
                lost = [p for p in pp if not good(p, a)] if carried else []
                outside = sum(not (parts(p)[1] == 'Deva' or (parts(p)[1] is None and parts(p)[0] in DEVA)) for p in lost)
                closure[name + '|' + t] = {'lost': len(lost), 'outside': outside, 'carried': carried}
        cls = [r['cluster'] for r in rr]
        if all(c is not None for c in cls) and len(set(cls)) >= 2:
            bb, g = ratio_boot(cls, np.array(columns).T)
            boots[name] = {nm: bb[:, i] for i, nm in enumerate(names)}
            for i, nm in enumerate(names):
                t, metric = nm.split('/')
                stats[t][metric]['ci'] = ci(bb[:, i])
            changes = {}
            for a, b in [('v3', 'v1'), ('v3', 'v2'), ('v2', 'v1')]:
                diff = boots[name][a + '/retention'] - boots[name][b + '/retention']
                changes[a + '-' + b] = {'value': stats[a]['retention']['value'] - stats[b]['retention']['value'],
                                        'ci': ci(diff)}
        else:
            g = len(set(c for c in cls if c is not None))
            changes = {}
        summaries[name] = {'n': nn, 'clusters': g, 'statistics': stats, 'paired_changes': changes,
                           'interval_scope': 'conditional source-cluster resampling' if changes else 'descriptive only'}
        print(name, nn, 'clusters', g, 'Hindi-v3-retention', stats['v3']['retention']['value'], flush=True)
    buckets = {}
    for length in ['L1', 'L5']:
        cc = [(name, s) for name, s in summaries.items() if name.startswith('panel1|') and name.endswith('|' + length)]
        for t in TAGS:
            numerator = sum(s['statistics'][t]['to_hindi']['k'] for name, s in cc if name.split('|')[3] == 'hin')
            denominator = sum(s['statistics'][t]['to_hindi']['k'] for name, s in cc)
            br = (sum(s['n'] * boots[name][t + '/to_hindi'] for name, s in cc if name.split('|')[3] == 'hin')
                  / sum(s['n'] * boots[name][t + '/to_hindi'] for name, s in cc))
            buckets[t + '|' + length] = {'value': numerator / denominator, 'numerator': numerator,
                                         'denominator': denominator, 'ci': ci(br)}
    conf = C.read_csv('confidence_scores_v3.csv')
    confout = {}
    for length in ['L1', 'L5']:
        rows = [r for r in conf if r['length'] == length]
        meta = {r['unit_id']: r for r in p1 if r['lang'] == 'hin' and r['length'] == length}
        clusters = [meta[r['unit_id']]['cluster'] for r in rows]
        for group in ['angika', 'hindi']:
            mask = np.array([r['pred'] == ('anp_Deva' if group == 'angika' else 'hin_Deva') for r in rows])
            score = np.array([float(r['score']) for r in rows])
            bb, g = ratio_boot(clusters, (mask & (score >= .9)).astype(float), mask.astype(float)[:, None])
            sub = score[mask]
            confout[length + '|' + group] = {'n': int(mask.sum()), 'at_ceiling': int((sub >= .9).sum()),
                                             'below_floor': int((sub < .3).sum()),
                                             'survival_at_ceiling': float((sub >= .9).mean()), 'ci': ci(bb[:, 0]),
                                             'median': float(np.median(sub)), 'min': float(sub.min()),
                                             'max': float(sub.max())}
            # Median uncertainty, resampling the complete cell before selecting the group.
            uu, ix = np.unique(clusters, return_inverse=True)
            gg = len(uu)
            order = np.argsort(sub)
            sorted_scores = sub[order]
            groupclusters = ix[mask][order]
            meds = []
            for z in range(0, B, 128):
                w = RNG.multinomial(gg, np.full(gg, 1 / gg), size=min(128, B - z))[:, groupclusters]
                cum = np.cumsum(w, axis=1)
                n = cum[:, -1]
                low = (n - 1) // 2
                high = n // 2
                li = (cum > low[:, None]).argmax(axis=1)
                hi = (cum > high[:, None]).argmax(axis=1)
                meds.extend((sorted_scores[li] + sorted_scores[hi]) / 2)
            confout[length + '|' + group]['median_ci'] = ci(meds)
    result = {'replicates': B, 'seed': 20260912, 'cells': summaries, 'hindi_buckets': buckets,
              'confidence': confout, 'script_closure': closure}
    mapping = os.path.join(C.RESULTS, 'source_mapping.json')
    if os.path.exists(mapping):
        result['source_mapping'] = json.load(open(mapping))
    C.write_result('panel_analysis.json', result, indent=2)
    print('Panel analysis saved', flush=True)


if __name__ == '__main__':
    main()
