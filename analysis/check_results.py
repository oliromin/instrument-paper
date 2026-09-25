"""Numbers-only check of the paper against the data.

    python analysis/check_results.py            identifier-only analyses
    python analysis/check_results.py --texts    also the analyses that read unit
                                                texts or external files (needs
                                                texts/ and INSTRUMENT_INPUTS)

1. Recompute.  Every analysis is rerun from data/ into a scratch copy of the
   repository, and each value it writes is compared with the committed file in
   results/ (floating-point values to a relative 1e-12).
2. Tables.  Every table is regenerated from the recomputed results and compared
   with paper/tables/, cell by cell.
3. Reported figures.  Each figure the text of the paper reports is recomputed
   from the results and rounded half-up to the number of decimals printed; the
   rounded value must equal the printed value, and the printed value must
   occur in the paper's source (its text, tables or appendices).

Exits with status 1 on any failure.
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from decimal import Decimal, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# script, result files it writes, whether it needs texts/ or external inputs
ANALYSES = [
    ('source_clusters.py', ['source_mapping.json'], True),
    ('panels.py', ['panel_analysis.json'], False),
    ('released_splits.py', ['released_split_analysis.json'], False),
    ('nested_reader.py', ['nested_reader_analysis.json'], False),
    ('openlid_v3.py', ['openlid_v3.json'], False),
    ('composition.py', ['composition.json'], False),
    ('label_diff.py', ['label_diff.json'], False),
    ('reader_crosscheck.py', ['reader_crosscheck.json'], False),
    ('reader_agreement.py', ['reader_agreement.json'], False),
    ('runner_up.py', ['runner_up.json'], False),
    ('angika_groups.py', ['angika_groups.json'], False),
    ('marked_subsets.py', ['marked_subsets.json'], True),
    ('nested_construction.py', ['nested_construction.json'], True),
    ('overlap.py', ['overlap.json'], True),
    ('register.py', ['register.json'], True),
    ('decompose.py', ['decomposition.json'], True),
    ('ngram.py', ['ngram.json'], True),
    ('ngram_length.py', ['ngram_units.json', 'ngram_length.json'], True),
    ('ngram_decompose.py', ['ngram_decomposition.json'], False),
    ('training_file.py', ['training_file.json'], True),
]


# Results that need model binaries to regenerate (analysis/training_file.py --v1 --v2);
# they are read as committed.
MODEL_RUNS = ['training_file_identifiers.json']


def half_up(x, printed):
    d = len(printed.split('.')[1]) if '.' in printed else 0
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))


def compare(a, b, path=''):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append('%s/%s present in only one file' % (path, k))
            else:
                out += compare(a[k], b[k], '%s/%s' % (path, k))
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return ['%s length %d against %d' % (path, len(a), len(b))]
        for i, (x, y) in enumerate(zip(a, b)):
            out += compare(x, y, '%s[%d]' % (path, i))
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if not (math.isnan(a) and math.isnan(b)) and abs(a - b) > 1e-12 * max(1, abs(a), abs(b)):
            out.append('%s %r against %r' % (path, a, b))
    elif a != b:
        out.append('%s %r against %r' % (path, a, b))
    return out


# ---------------------------------------------------------------- reported figures
# (what is reported, the value as printed, how it is computed from the results)
def figures(R):
    comp = R['composition']['models']
    over, reg, dec = R['overlap'], R['register'], R['decomposition']
    grp, run, ng, ngd, ngl = R['angika_groups'], R['runner_up'], R['ngram'], R['ngram_decomposition'], R['ngram_length']
    ol3, ld, nest = R['openlid_v3'], R['label_diff'], R['nested_reader_analysis']['nested']
    oc, orr = ol3['common'], ol3['recommended']
    ms = R['marked_subsets']['results']
    ang, ret = reg['wikipedia_by_outcome']['angika'], reg['wikipedia_by_outcome']['retained']
    side = {r['cell']: r for r in reg['angika_side']}
    train = side['anp_Deva published training file, filtered sentences']
    ctrl = side['marker-selected Angika control L1']
    F = []
    for k, p6, p7, arow in (('v3', '0.978', '0.976', '0.001'), ('v2', '0.990', '0.972', '0.018'),
                            ('v1', '0.966', '0.872', '0.111'), ('lid176', '0.723', '0.427', '0.958'),
                            ('langid', '0.828', '0.487', '0.834'), ('cld3', '0.626', '0.443', '0.654'),
                            ('openlid', '0.917', '0.851', '0.059')):
        F += [(k + ' six-source bucket share', p6, comp[k]['precision6']),
              (k + ' seven-source bucket share', p7, comp[k]['precision7']),
              (k + ' Angika row to Hindi', arow, comp[k]['angika_row_to_hindi'])]
    F += [('v3 minus v2 seven-source share', '0.004', comp['v3']['precision7'] - comp['v2']['precision7']),
          ('v2 minus v3 Hindi retention', '0.462', comp['v2']['hindi_retention'] - comp['v3']['hindi_retention']),
          ('largest seven-source loss, percentage points', '34', 100 * max(abs(comp[k]['delta']) for k in comp)),
          ('present units', '1554', over['n_present']),
          ('present retention', '0.478', over['retained_present']),
          ('absent retention', '0.487', over['retained_absent']),
          ('present minus absent', '-0.008', over['difference']),
          ('present interval low', '0.452', over['ci_retained_present'][0]),
          ('present interval high', '0.503', over['ci_retained_present'][1]),
          ('absent interval low', '0.441', over['ci_retained_absent'][0]),
          ('absent interval high', '0.533', over['ci_retained_absent'][1]),
          ('difference interval low', '-0.063', over['ci_difference'][0]),
          ('difference interval high', '0.043', over['ci_difference'][1]),
          ('Wikipedia function-word rate', '0.111', reg['cells'][0]['mean_fw_rate']),
          ('news function-word rate', '0.104', reg['cells'][1]['mean_fw_rate']),
          ('Wikipedia no-match share', '0.112', reg['cells'][0]['zero_fw_share']),
          ('news no-match share', '0.153', reg['cells'][1]['zero_fw_share']),
          ('Wikipedia rare-token rate', '0.114', reg['cells'][0]['mean_rtr']),
          ('news rare-token rate', '0.127', reg['cells'][1]['mean_rtr']),
          ('Wikipedia template share', '0.172', reg['cells'][0]['tpl_share']),
          ('news template share', '0.117', reg['cells'][1]['tpl_share']),
          ('Wikipedia template retention', '0.453', reg['wikipedia_tpl']['template']['retention']),
          ('Wikipedia other retention', '0.486', reg['wikipedia_tpl']['other']['retention']),
          ('Wikipedia template difference', '-0.032', reg['wikipedia_tpl_difference']),
          ('template difference interval low', '-0.091', reg['wikipedia_tpl_difference_ci'][0]),
          ('template difference interval high', '0.027', reg['wikipedia_tpl_difference_ci'][1]),
          ('news template retention', '0.803', reg['news_tpl']['template']['retention']),
          ('news other retention', '0.805', reg['news_tpl']['other']['retention']),
          ('news no function words, retention', '0.732', reg['news_by_fw']['0']['retention']),
          ('news four or more, retention', '0.877', reg['news_by_fw']['4']['retention']),
          ('held-out template sentences', '262659', reg['heldout_sentences']),
          ('Hindi file distinct types', '546551', reg['published_vocab_types']),
          ('raw retention gap', '0.325', dec['raw_gap']),
          ('smallest share absorbed', '-0.018', min(o['share_of_gap_absorbed'] for o in dec['observables'].values())),
          ('largest share absorbed', '0.006', max(o['share_of_gap_absorbed'] for o in dec['observables'].values())),
          ('Angika training sentences', '3970', train['n']),
          ('Angika training function-word rate', '0.019', train['mean_fw_rate']),
          ('Angika training no-match share, per cent', '81.8', 100 * train['zero_fw_share']),
          ('Angika training rare-token rate', '0.399', train['mean_rtr']),
          ('Angika training file matching the extract', '0.286', R['training_file']['extract_match_share']),
          ('Angika training file one-sided marked share', '0.786', R['training_file']['angika_marked_share']),
          ('extract one-sided marked share', '0.674', R['training_file']['extract_angika_marked_one_sided_share']),
          ('extract one-sided marked count', '3251', R['training_file']['extract_angika_marked_one_sided']),
          ('v1 reference share to Hindi', '0.109', R['training_file']['reference_to_hindi_stored']['v1']),
          ('v2 reference share to Hindi', '0.020', R['training_file']['reference_to_hindi_stored']['v2']),
          ('v1 training-file share to Hindi', '0.252', R['training_file_identifiers']['v1']['file_to_hindi']),
          ('v2 training-file share to Hindi', '0.176', R['training_file_identifiers']['v2']['file_to_hindi']),
          ('n-gram types, Angika file', '196708', ng['angika_types']),
          ('n-gram types, Hindi reference', '239536', ng['hindi_types']),
          ('absorbed Hindi function-word rate', '0.122', ang['mean_fw_rate']),
          ('absorbed Hindi rare-token rate', '0.101', ang['mean_rtr'])]
    for i, v in enumerate(('0.491', '0.415', '0.506', '0.485', '0.608')):
        F.append(('Wikipedia function-word bucket %d retention' % i, v, reg['wikipedia_by_fw'][str(i)]['retention']))
    F += [('v3 Angika-marked to Hindi', '0.0009', grp['v3']['angika_marked']['to_hindi']),
          ('v3 Hindi-marked to Hindi', '0.2599', grp['v3']['hindi_marked']['to_hindi']),
          ('v3 Hindi-marked to Angika', '0.7375', grp['v3']['hindi_marked']['to_angika']),
          ('v3 unmarked to Hindi', '0.3232', grp['v3']['neither']['to_hindi']),
          ('v3 whole extract to Hindi', '0.0896', grp['v3']['ALL']['to_hindi']),
          ('Angika-marked sentences', '3269', grp['v3']['angika_marked']['n']),
          ('Hindi-marked sentences', '1158', grp['v3']['hindi_marked']['n']),
          ('extract sentences', '4823', grp['v3']['ALL']['n']),
          ('v1 separation factor', '9.1', grp['v1']['hindi_marked']['to_hindi'] / grp['v1']['angika_marked']['to_hindi']),
          ('runner-up maximum score', '0.4944', run['L1']['runnerup_max']),
          ('median margin, one sentence', '0.853', run['L1']['margin_median']),
          ('share with margin above 0.5, per cent', '77.6', 100 * run['L1']['share_margin_gt_0.5']),
          ('median margin, five sentences', '0.610', run['L5']['margin_median']),
          ('Hindi runner-up, five sentences, per cent', '99.9', 100 * run['L5']['runnerup_is_hindi_share']),
          ('Wikipedia minus news n-gram proximity', '0.121', ng['wikipedia_minus_news']),
          ('n-gram share of gap absorbed', '0.112', ngd['share_of_gap_absorbed']),
          ('n-gram share interval low', '0.070', ngd['share_ci'][0]),
          ('n-gram share interval high', '0.159', ngd['share_ci'][1]),
          ('news reweighted by n-gram proximity', '0.769', ngd['news_reweighted']),
          ('Wikipedia lowest-proximity decile retention', '0.560', ng['wikipedia_deciles'][0]['retention']),
          ('Wikipedia highest-proximity decile retention', '0.370', ng['wikipedia_deciles'][-1]['retention']),
          ('news lowest-proximity decile retention', '0.875', ng['news_deciles'][0]['retention']),
          ('news highest-proximity decile retention', '0.695', ng['news_deciles'][-1]['retention']),
          ('n-gram union vocabulary', '351270', ngl['vocab'])]
    for cell, std, lo, hi, ols_ in (('wikipedia', '0.054', '0.032', '0.077', '0.054'),
                                    ('news', '0.088', '0.061', '0.114', '0.086')):
        c = ngl['cells'][cell]
        F += [(cell + ' standardized within-cell gap', std, c['standardised_gap']),
              (cell + ' standardized gap interval low', lo, c['standardised_gap_ci'][0]),
              (cell + ' standardized gap interval high', hi, c['standardised_gap_ci'][1]),
              (cell + ' regression coefficient on routing', ols_, c['ols_routed'])]
    F += [('OpenLID-v3 label count', '195', ol3['label_count']),
          ('OpenLID-v3 Panel 1 Hindi retention, common', '0.965', oc['panel1_hin_L1']),
          ('OpenLID-v3 Panel 1 Hindi retention, recommended', '0.957', orr['panel1_hin_L1']),
          ('OpenLID-v3 six-source share, common', '0.740', oc['composition_six']),
          ('OpenLID-v3 six-source share, recommended', '0.754', orr['composition_six']),
          ('OpenLID-v3 seven-source share, common', '0.683', oc['composition_seven']),
          ('OpenLID-v3 without Newari, common', '0.993', oc['composition_six_no_newari']),
          ('OpenLID-v3 without Newari, recommended', '0.994', orr['composition_six_no_newari']),
          ('OpenLID-v3 Angika row to Hindi, common', '0.108', oc['angika_row_to_hindi']),
          ('OpenLID-v3 reader Hindi retained, common', '271', oc['reader_confirmed_hi']['retained']),
          ('OpenLID-v3 reader Hindi retained, recommended', '266', orr['reader_confirmed_hi']['retained']),
          ('OpenLID-v3 reader Hindi units', '279', oc['reader_confirmed_hi']['n']),
          ('OpenLID-v3 reader Nepali retained, recommended', '285', orr['reader_confirmed_ne']['retained']),
          ('OpenLID-v3 both-confirmed Hindi retained', '85', oc['reader_both_hi']['retained']),
          ('OpenLID-v3 nested Wikipedia L1, common', '0.974', nest['ol3|Wikipedia']['lengths']['L1']['rate']),
          ('OpenLID-v3 nested news L1, common', '0.980', nest['ol3|News']['lengths']['L1']['rate']),
          ('v2 labels', '1848', ld['v2_count']), ('v3 labels', '2102', ld['v3_count']),
          ('labels added', '302', ld['added']), ('genuine language labels added', '145', ld['genuine_added']),
          ('labels removed', '48', ld['removed']),
          ('Hindi L1 share to new v3 labels', '0.5075', ld['cells']['hin_L1']['share_of_cell_to_new_labels']),
          ('Newari L1 share to new v3 labels', '0.0160', ld['cells']['new_L1']['share_of_cell_to_new_labels']),
          ('Maithili marked subset units', '1686', ms['mai|L1|lid176|target_marked']['n']),
          ('lid.176 Maithili marked retention', '0.6845', ms['mai|L1|lid176|target_marked']['retention']),
          ('lid.176 Maithili marked loss to Hindi', '0.6992', ms['mai|L1|lid176|target_marked']['hindi_share_of_loss']),
          ('lid.176 Newari marked loss to Hindi', '0.2607', ms['new|L1|lid176|target_marked']['hindi_share_of_loss'])]
    nl = [c for c in ('nep_L1', 'mar_L1', 'san_L1', 'new_L1', 'mai_L1')]
    F += [('non-Hindi units to new v3 labels', '61', sum(ld['cells'][c]['lost_to_new_labels'] for c in nl)),
          ('of those, to Angika', '56', sum(n for c in nl for l, n in ld['cells'][c]['destinations'] if l == 'anp_Deva'))]
    return F


def printed_forms(p):
    forms = {p}
    if '.' not in p and p.lstrip('-').isdigit() and len(p.lstrip('-')) > 3:
        n = int(p)
        forms |= {f'{n:,}', f'{n:,}'.replace(',', '{,}')}
    return forms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--texts', action='store_true', help='also rerun the analyses that read texts or external files')
    a = ap.parse_args()
    fails = []
    tmp = tempfile.mkdtemp()
    try:
        for d in ('analysis', 'data'):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(tmp, d), ignore=shutil.ignore_patterns('__pycache__'))
        if os.path.isdir(os.path.join(ROOT, 'texts')):
            os.symlink(os.path.join(ROOT, 'texts'), os.path.join(tmp, 'texts'))
        os.makedirs(os.path.join(tmp, 'results'))
        for o in MODEL_RUNS:   # written only when the model binaries are supplied
            shutil.copy(os.path.join(ROOT, 'results', o), os.path.join(tmp, 'results', o))
        print('1. recomputing results')
        for script, outputs, heavy in ANALYSES:
            if heavy and not a.texts:
                for o in outputs:   # carried over unchanged when not recomputed
                    shutil.copy(os.path.join(ROOT, 'results', o), os.path.join(tmp, 'results', o))
                print('   %-24s not rerun (needs --texts)' % script)
                continue
            r = subprocess.run([sys.executable, script], cwd=os.path.join(tmp, 'analysis'),
                               capture_output=True, text=True)
            if r.returncode:
                fails.append(script + ' failed')
                print('   %-24s FAILED\n%s' % (script, r.stderr[-2000:]))
                continue
            for o in outputs:
                new = json.load(open(os.path.join(tmp, 'results', o)))
                old = json.load(open(os.path.join(ROOT, 'results', o)))
                if o == 'nested_reader_analysis.json' and not os.path.isdir(os.path.join(ROOT, 'texts')):
                    for v in old['source_sensitivity'].values():
                        v.pop('exact_duplicate_excess', None)
                d = compare(new, old)
                print('   %-24s %-30s %s' % (script, o, 'agrees' if not d else '%d differences' % len(d)))
                for x in d[:5]:
                    print('       ', x)
                if d:
                    fails.append(o)
        print('2. regenerating tables')
        out = os.path.join(tmp, 'tables')
        subprocess.run([sys.executable, 'make_tables.py', out], cwd=os.path.join(tmp, 'analysis'), check=True,
                       capture_output=True)
        for f in sorted(os.listdir(os.path.join(ROOT, 'paper', 'tables'))):
            old = open(os.path.join(ROOT, 'paper', 'tables', f), encoding='utf-8').read().split('\n')
            new = open(os.path.join(out, f), encoding='utf-8').read().split('\n')
            bad = [(i + 1, x, y) for i, (x, y) in enumerate(zip(old, new)) if x != y] + (
                [('rows', len(old), len(new))] if len(old) != len(new) else [])
            print('   %-30s %s' % (f, 'every cell agrees' if not bad else '%d rows differ' % len(bad)))
            for b in bad[:3]:
                print('       paper:  %s\n       recomputed: %s' % (b[1], b[2]))
            if bad:
                fails.append('table ' + f)
        print('3. reported figures')
        R = {os.path.splitext(f)[0]: json.load(open(os.path.join(tmp, 'results', f)))
             for f in os.listdir(os.path.join(tmp, 'results')) if f.endswith('.json')}
        tex = ''.join(open(os.path.join(base, f), encoding='utf-8').read()
                      for base in (os.path.join(ROOT, 'paper'), os.path.join(ROOT, 'paper', 'tables'),
                                   os.path.join(ROOT, 'paper', 'appendix'))
                      for f in sorted(os.listdir(base)) if f.endswith('.tex'))
        n = 0
        for label, printed, value in figures(R):
            got = half_up(value, printed)
            ok = got == printed and any(f in tex for f in printed_forms(printed))
            n += 1
            if not ok:
                fails.append(label)
                print('   FAIL %-50s printed %s, recomputed %s%s' % (label, printed, got,
                      '' if any(f in tex for f in printed_forms(printed)) else ', not found in the text'))
        labels = {x[0] for x in figures(R)}
        print('   %d of %d reported figures agree' % (n - sum(1 for f in fails if f in labels), n))
    finally:
        shutil.rmtree(tmp)
    print('\n' + ('all checks pass' if not fails else '%d checks fail: %s' % (len(fails), ', '.join(fails[:10]))))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
