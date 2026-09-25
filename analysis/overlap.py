"""Prior exposure: retention of Hindi panel sentences that appear verbatim in
the identifier's published Hindi training file against those that do not,
with conditional source-cluster resampling and the present-minus-absent
difference.
"""
import random

import common as C

SEED = 20260912
REPS = 4999


def published_hindi_vocabsentences():
    path = C.external('hin_Deva_leipzigwiki.txt')
    seen = set()
    nonempty = 0
    with open(path, encoding='utf-8') as fh:
        for line in fh:
            s = line.strip()
            if s:
                nonempty += 1
                seen.add(C.norm(s))
    return seen, nonempty


def main():
    texts = C.panel1_texts()
    pred = C.panel1_preds('v3')
    clusters = C.panel_clusters('panel1', 'P1', 'hin', 'L1')

    published, nonempty = published_hindi_vocabsentences()
    print('published Hindi file: %d non-empty lines, %d distinct normalised'
          % (nonempty, len(published)))

    rows = []
    for (lg, length, uid), text in texts.items():
        if lg != 'hin' or length != 'L1':
            continue
        p = pred[(lg, length, uid)]
        rows.append({
            'cluster': clusters.get(uid, 'unmapped:' + uid),
            'present': C.norm(text) in published,
            'retained': p.startswith('hin'),
            'angika': p == 'anp_Deva',
        })

    present = [r for r in rows if r['present']]
    absent = [r for r in rows if not r['present']]
    print('present %d  absent %d' % (len(present), len(absent)))

    def rate(rs, key):
        return sum(1 for r in rs if r[key]) / len(rs) if rs else float('nan')

    point = {
        'n_present': len(present), 'n_absent': len(absent),
        'retained_present': rate(present, 'retained'),
        'retained_absent': rate(absent, 'retained'),
        'angika_present': rate(present, 'angika'),
        'angika_absent': rate(absent, 'angika'),
    }
    point['difference'] = point['retained_present'] - point['retained_absent']

    # clusters that contain both present and absent units
    byc = {}
    for r in rows:
        byc.setdefault(r['cluster'], []).append(r)
    mixed = sum(1 for g in byc.values()
                if any(x['present'] for x in g) and any(not x['present'] for x in g))
    point['clusters'] = len(byc)
    point['mixed_clusters'] = mixed

    rng = random.Random(SEED)
    groups = list(byc.values())
    dp, da, dd = [], [], []
    for _ in range(REPS):
        draw = [groups[rng.randrange(len(groups))] for _ in range(len(groups))]
        units = [u for g in draw for u in g]
        p = [u for u in units if u['present']]
        a = [u for u in units if not u['present']]
        if not p or not a:
            continue
        rp, ra = rate(p, 'retained'), rate(a, 'retained')
        dp.append(rp)
        da.append(ra)
        dd.append(rp - ra)

    def ci(v):
        v = sorted(v)
        return [v[int(0.025 * (len(v) - 1))], v[int(0.975 * (len(v) - 1))]]

    point['ci_retained_present'] = ci(dp)
    point['ci_retained_absent'] = ci(da)
    point['ci_difference'] = ci(dd)
    point['replicates_used'] = len(dd)

    for k, v in point.items():
        print('%-24s %s' % (k, v))

    C.write_result('overlap.json', point)


if __name__ == '__main__':
    main()
