"""Destination composition of the Hindi-labelled bucket, six and seven source
languages, with conditional source-cluster resampling.

The six-language figure reproduces the manuscript's Panel 1 L1 result.  The
seven-language variant adds the Panel 2 Regime C Angika L1 cell as a seventh
source row at the same cell size, so that the class which absorbs the Hindi
loss is represented on the source side of the mixture.
"""
import random

import common as C

SEED = 20260912
REPS = 4999
MODELS = ['langid', 'cld3', 'lid176', 'openlid', 'v1', 'v2', 'v3']
LANGS = ['hin', 'nep', 'mar', 'san', 'new', 'mai']


def build_cells():
    """cell -> list of (cluster_key, is_hindi_source, {model: pred})."""
    texts = C.panel1_texts()
    preds = {m: C.panel1_preds(m) for m in MODELS}
    clusters = {lang: C.panel_clusters('panel1', 'P1', lang, 'L1')
                for lang in C.P1_CORPUS}

    cells = {}
    for lang in LANGS:
        rows = []
        cmap = clusters[lang]
        for (lg, length, uid) in texts:
            if lg != lang or length != 'L1':
                continue
            rows.append((cmap.get(uid, 'unmapped:' + uid),
                         lang == 'hin',
                         {m: preds[m][(lg, length, uid)] for m in MODELS}))
        cells[lang] = rows

    # Seventh row: Panel 2 Regime C Angika L1.  Cluster = source article.
    p2preds = {m: C.panel2_preds(m) for m in MODELS}
    rows = []
    for r in C.panel2_rows():
        if r['regime'] != 'C' or r['length'] != 'L1':
            continue
        uid = r['unit_id']
        rows.append((uid.split(':')[0], False,
                     {m: p2preds[m][('C', 'anp', 'L1', uid)] for m in MODELS}))
    cells['anp'] = rows
    return cells


def composition(cells, langs, model):
    """Hindi-sourced share of the Hindi-labelled bucket, mixture-weighted."""
    acc = HL = 0.0
    for lang in langs:
        rows = cells[lang]
        n = len(rows)
        if not n:
            continue
        hit = sum(1 for _, _, p in rows if p[model] in C.HINDI_LABELS[model])
        num = sum(1 for _, src, p in rows
                  if src and p[model] in C.HINDI_LABELS[model])
        HL += n * hit / n
        acc += n * num / n
    return acc / HL if HL else float('nan')


def boot(cells, langs, model, reps=REPS, seed=SEED):
    """Conditional source-cluster resampling that preserves the designed
    mixture weights: within each cell clusters are resampled to the original
    cluster count and the cell's resampled rate is reweighted to its original
    unit count."""
    rng = random.Random(seed)
    grouped = {}
    for lang in langs:
        g = {}
        for ck, src, p in cells[lang]:
            g.setdefault(ck, []).append((src, p))
        grouped[lang] = (len(cells[lang]), list(g.values()))

    out = []
    for _ in range(reps):
        acc = HL = 0.0
        for lang in langs:
            n, groups = grouped[lang]
            if not groups:
                continue
            draw = [groups[rng.randrange(len(groups))] for _ in range(len(groups))]
            units = [u for grp in draw for u in grp]
            m = len(units)
            if not m:
                continue
            hit = sum(1 for _, p in units if p[model] in C.HINDI_LABELS[model])
            num = sum(1 for src, p in units
                      if src and p[model] in C.HINDI_LABELS[model])
            HL += n * hit / m
            acc += n * num / m
        out.append(acc / HL if HL else float('nan'))
    out.sort()
    lo = out[int(0.025 * (len(out) - 1))]
    hi = out[int(0.975 * (len(out) - 1))]
    return lo, hi


def retention(cells, lang, model):
    rows = cells[lang]
    return sum(1 for _, _, p in rows
               if p[model] in C.HINDI_LABELS[model]) / len(rows)


def main():
    cells = build_cells()
    six = LANGS
    seven = LANGS + ['anp']

    res = {'seed': SEED, 'replicates': REPS,
           'cell_sizes': {k: len(v) for k, v in cells.items()},
           'cluster_counts': {k: len({c for c, _, _ in v})
                              for k, v in cells.items()},
           'models': {}}

    for m in MODELS:
        p6 = composition(cells, six, m)
        p7 = composition(cells, seven, m)
        l6, h6 = boot(cells, six, m)
        l7, h7 = boot(cells, seven, m)
        anp_to_hin = sum(1 for _, _, p in cells['anp']
                         if p[m] in C.HINDI_LABELS[m]) / len(cells['anp'])
        res['models'][m] = {
            'precision6': p6, 'ci6': [l6, h6],
            'precision7': p7, 'ci7': [l7, h7],
            'delta': p7 - p6,
            'angika_row_to_hindi': anp_to_hin,
            'hindi_retention': retention(cells, 'hin', m),
        }
        print('%-8s  P6=%.4f [%.4f,%.4f]   P7=%.4f [%.4f,%.4f]   d=%+.4f   '
              'anp->hin=%.4f' % (m, p6, l6, h6, p7, l7, h7, p7 - p6, anp_to_hin))

    C.write_result('composition.json', res)
    print('\ncell sizes', res['cell_sizes'])
    print('cluster counts', res['cluster_counts'])


if __name__ == '__main__':
    main()
