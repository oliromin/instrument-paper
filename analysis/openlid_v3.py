"""Every OpenLID-v3 figure in the paper, from the per-unit predictions.

data/openlid_v3_predictions.csv holds one record per scored unit (39,646
records: 29,764 panel units, 9,282 nested units and 600 reader-judged units),
each with the top-1 label and score under common and recommended
preprocessing, produced by the published binary (SHA-256 01ec5bbf...8821; see
data/model_identities.json) with analysis/score_openlid_v3.py.  This script
derives the reported aggregates and writes results/openlid_v3.json.  The paired
nested-length intervals are computed with the GlotLID rows in
nested_reader.py, which shares their resampling stream.
"""
import collections

import common as C

LANGS = ['hin', 'nep', 'mar', 'san', 'new', 'mai']
PREPS = {'common': 'pred', 'recommended': 'recommended_pred'}


def main():
    rows = C.read_csv('openlid_v3_predictions.csv')
    hv = {r['uid']: r for r in C.read_csv('reader_sample.csv')}
    labels = C.load_json('data/model_labels.json')['openlid_v3']
    ident = C.load_json('data/model_identities.json')['openlid_v3']
    out = {'sha256': ident['sha256'], 'label_count': len(labels),
           'carries': {k: (k in labels) for k in
                       ('hin_Deva', 'npi_Deva', 'mai_Deva', 'awa_Deva', 'anp_Deva', 'new_Deva', 'bra_Deva')},
           'records': len(rows), 'by_set': collections.Counter(r['set'] for r in rows)}

    def cell(regime, lang, length):
        return [r for r in rows if r['set'] == 'panel' and r['regime'] == regime
                and r['lang'] == lang and r['length'] == length]

    def hin(r, f):
        return r[f].startswith('hin')

    for prep, f in PREPS.items():
        d = {}
        p1 = {lg: cell('P1', lg, 'L1') for lg in LANGS}
        p1['anp'] = cell('C', 'anp', 'L1')
        d['panel1_hin_L1'] = sum(hin(r, f) for r in p1['hin']) / len(p1['hin'])
        news = cell('A', 'hin', 'L1')
        d['news_hin_L1'] = sum(hin(r, f) for r in news) / len(news)
        d['angika_row_to_hindi'] = sum(hin(r, f) for r in p1['anp']) / len(p1['anp'])
        d['angika_top'] = collections.Counter(r[f] for r in p1['anp']).most_common(5)

        def comp(langs):
            bucket = sum(hin(r, f) for lg in langs for r in p1[lg])
            right = sum(hin(r, f) for r in p1['hin'])
            return right / bucket
        d['composition_six'] = comp(LANGS)
        d['composition_seven'] = comp(LANGS + ['anp'])
        d['composition_six_no_newari'] = comp([l for l in LANGS if l != 'new'])
        d['composition_seven_no_newari'] = comp([l for l in LANGS if l != 'new'] + ['anp'])
        hum = [r for r in rows if r['set'] == 'human']
        for lg, code in (('hi', 'hin'), ('ne', 'npi')):
            conf = [r for r in hum if C.truth(hv[r['unit_id']]['confirmed']) and hv[r['unit_id']]['lang'] == lg]
            d['reader_confirmed_%s' % lg] = {'n': len(conf),
                                            'retained': sum(r[f].startswith(code) for r in conf)}
        both = [r for r in hum if C.truth(hv[r['unit_id']]['both_confirmed']) and hv[r['unit_id']]['lang'] == 'hi']
        d['reader_both_hi'] = {'n': len(both), 'retained': sum(hin(r, f) for r in both)}
        orig = {}
        for name, reg in (('Wikipedia', 'P1'), ('News', 'A')):
            for ln in ('L1', 'L5', 'L20'):
                c = cell(reg, 'hin', ln)
                orig['%s_%s' % (name, ln)] = {'n': len(c), 'retention': sum(hin(r, f) for r in c) / len(c)}
        d['original_cells'] = orig
        nest = {}
        for src in ('Wikipedia', 'News'):
            for ln in ('L1', 'L5', 'L20'):
                c = [r for r in rows if r['set'] == 'nested' and r['source'] == src and r['length'] == ln]
                nest['%s_%s' % (src, ln)] = {'n': len(c), 'retained': sum(hin(r, f) for r in c)}
        d['nested'] = nest
        out[prep] = d
    C.write_result('openlid_v3.json', out)
    print('records', out['records'], dict(out['by_set']))
    for prep in PREPS:
        print(prep, {k: v for k, v in out[prep].items() if isinstance(v, float)})


if __name__ == '__main__':
    main()
