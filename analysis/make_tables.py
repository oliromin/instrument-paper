"""Regenerate every table of the paper from the results files.

Each number is rounded from the stored value with the half-up convention the
paper declares (Decimal quantize, ROUND_HALF_UP), so a table cell always agrees
with the machine-readable result it prints.  Writes paper/tables/*.tex; pass a
folder to write elsewhere (check_results.py does, to compare).
"""
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

import common as C

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(C.ROOT, 'paper', 'tables')
NAMES = {'v1': 'GlotLID v1', 'v2': 'GlotLID v2', 'v3': 'GlotLID v3', 'langid': 'langid.py', 'lid176': 'lid.176',
         'cld3': 'CLD3', 'openlid': 'OpenLID'}
LANG = {'hin': 'Hindi', 'nep': 'Nepali', 'mar': 'Marathi', 'san': 'Sanskrit', 'new': 'Newari', 'mai': 'Maithili',
        'awa': 'Awadhi', 'anp': 'Angika', 'bho': 'Bhojpuri', 'bra': 'Braj', 'mag': 'Magahi'}


def fmt(x, n=3):
    return str(Decimal(str(x)).quantize(Decimal('1').scaleb(-n), rounding=ROUND_HALF_UP))


def rate(d):
    return fmt(Decimal(d['k']) / Decimal(d['n']))


def interval(d):
    return '[' + ', '.join(fmt(x) for x in d['ci']) + ']' if 'ci' in d else '---'


def write(name, text):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + '.tex'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def table(name, cols, head, rows):
    text = r'\begin{tabular}{' + cols + '}\n\\toprule\n' + ' & '.join(head) + r' \\' + '\n\\midrule\n'
    text += '\n'.join(' & '.join(str(x) for x in row) + r' \\' for row in rows)
    text += '\n\\bottomrule\n\\end{tabular}\n'
    write(name, text)


P = C.load_json('results/panel_analysis.json')
A = C.load_json('results/released_split_analysis.json')
D = C.load_json('results/nested_reader_analysis.json')
RC = C.load_json('data/fineweb2_row_counts.json')['summary']


def cell(source, lang, length):
    return next(v for k, v in P['cells'].items() if source in k and k.split('|')[3] == lang and k.endswith('|' + length))


def panel_tables():
    rows = []
    for t in ['openlid', 'v1', 'v2']:
        d = A['aggregate'][t + '|awa_split|document']
        s = A['aggregate'][t + '|awa_split|sentence']
        rows.append([NAMES[t], fmt(d['to_hindi']), fmt(d['to_awadhi']), fmt(s['to_hindi']), fmt(s['to_awadhi'])])
    table('awadhi_audit', 'lrrrr', ['Identifier', r'\multicolumn{2}{c}{Documents ($n=1{,}902$)}',
                                    r'\multicolumn{2}{c}{Sentences ($n=50{,}000$)}'],
          [['', 'Hindi', 'Awadhi', 'Hindi', 'Awadhi']] + rows)
    rows = []
    for sp in ['train', 'dev', 'test']:
        for t in ['openlid', 'v1', 'v2']:
            d = A['aggregate'][t + '|vardial2018/' + sp + '|sentence']
            rows.append([sp, NAMES[t], f"{d['n']:,}", fmt(d['to_hindi']), fmt(d['to_awadhi'])])
    table('awadhi_controls', 'llrrr', ['ILI split', 'Identifier', '$n$', 'Hindi', 'Awadhi'], rows)
    rows = []
    for lang in ['anp', 'awa', 'bho', 'mai', 'hin']:
        a, b = RC[lang + '_Deva'], RC[lang + '_Deva_removed']
        rows.append([LANG[lang], f"{a['documents']:,}", f"{b['documents']:,}",
                     fmt(b['documents'] / (a['documents'] + b['documents']), 4),
                     fmt(b['stored_bytes'] / (a['stored_bytes'] + b['stored_bytes']), 4)])
    table('removal_counts', 'lrrrr', ['Label', 'Retained docs', 'Removed docs', 'Doc fraction', 'File-byte fraction'], rows)
    rows = []
    for source in ['wikipedia', 'news']:
        for le in ['L1', 'L5', 'L20']:
            c = cell(source, 'hin', le)
            s = c['statistics']
            d = c['paired_changes']['v3-v1']
            rows.append([source.title(), le, str(c['n']), rate(s['v1']['retention']), rate(s['v2']['retention']),
                         rate(s['v3']['retention']), interval(s['v3']['retention']), fmt(d['value']), interval(d)])
    table('hindi_release_contrasts', 'llrrrrlrl',
          ['Source', 'Unit', '$n$', 'v1', 'v2', 'v3', 'v3 interval', r'$v3-v1$', 'Paired interval'], rows)
    rows = []
    for lang in ['hin', 'nep', 'mar', 'san', 'new', 'mai']:
        for le in ['L1', 'L5']:
            c = cell('wikipedia', lang, le)
            rows.append([LANG[lang], le, str(c['n'])] + [rate(c['statistics'][t]['retention']) if c['statistics'][t]['carried']
                                                           else '---' for t in ['langid', 'lid176', 'cld3', 'openlid', 'v1', 'v2', 'v3']])
    table('panel1_retention', 'llrrrrrrrr',
          ['Language', 'Unit', '$n$', 'langid', 'lid.176', 'CLD3', 'OpenLID', 'v1', 'v2', 'v3'], rows)
    rows = []
    for k, c in P['cells'].items():
        if k.startswith('panel1|'):
            continue
        _, reg, corp, lang, le = k.split('|')
        source = ('News' if reg == 'A' else ('ILI ' + corp.split('/')[-1] if reg == 'B'
                                             else ('Angika wiki' if reg == 'C' else 'Wiki ext.')))
        rows.append([source, LANG[lang], le, str(c['n'])] + [rate(c['statistics'][t]['retention']) if c['statistics'][t]['carried']
                                                              else '---' for t in ['openlid', 'v1', 'v2', 'v3']])
    table('panel2_retention', 'lllrrrrr', ['Source', 'Language', 'Unit', '$n$', 'OpenLID', 'v1', 'v2', 'v3'], rows)
    rows = []
    for le in ['L1', 'L5']:
        for gr in ['angika', 'hindi']:
            c = P['confidence'][le + '|' + gr]
            rows.append([le, 'Angika' if gr == 'angika' else 'Hindi', str(c['n']), fmt(c['median']), str(c['at_ceiling']),
                         fmt(c['survival_at_ceiling']), interval(c)])
    table('confidence_scores', 'llrrrll', ['Unit', 'Assigned label', '$n$', 'Median score', r'$s\geq0.9$', 'Share',
                                           r'95\% interval'], rows)
    rows = []
    for arm in ['sentence', 'document']:
        for b in A['angika_length'][arm]['bins']:
            for t in ['v1', 'v2']:
                m = b['models'][t]
                rows.append([arm, fmt(b['lo'], 2) + '--' + fmt(b['hi'], 2), t, str(m['control']['n']), str(m['split']['n']),
                             fmt(m['control']['rate']), fmt(m['split']['rate']), fmt(m['gap']),
                             '[' + ', '.join(fmt(x) for x in m['gap_pointwise_ci']) + ']'])
    table('angika_length_bins', 'llrrrrrrl',
          ['Unit', 'Characters', 'Model', '$n_A$', '$n_S$', '$q_A$', '$q_S$', 'Gap', 'Pointwise interval'], rows)


def reader_nested_tables():
    rows = []
    for subset, sname in [('confirmed', 'Reader 1 confirms'), ('both_confirmed', 'Both confirm')]:
        for lang, lname in [('hi', 'Hindi'), ('ne', 'Nepali')]:
            recs = [D['human'][f'{t}|{subset}|{lang}|ALL'] for t in ['v1', 'v2', 'v3']]
            rows.append([sname, lname, str(recs[0]['n'])] + [f"{r['retained']} ({fmt(r['retention'])})" for r in recs]
                        + [str(recs[2]['to_angika'])])
    table('human_summary', 'llrrrrr', ['Subset', 'Language', '$n$', 'v1', 'v2', 'v3', r'v3 $\to$ Angika'], rows)
    rows = []
    domains = {'formal_written': 'Wikipedia extracts', 'formal_written_sentence': 'Wikipedia sentences',
               'read_speech_fleurs': 'FLEURS transcripts', 'read_speech_iv': 'IV read transcripts',
               'extempore': 'IV extempore', 'conversation': 'IV conversation'}
    for domain, name in domains.items():
        rr = [D['human'][f'{t}|confirmed|hi|{domain}'] for t in ['v1', 'v2', 'v3']]
        rows.append([name, rr[0]['n']] + [f"{x['retained']}/{x['n']}" for x in rr] + [rr[2]['to_angika']])
    table('human_domains', 'lrrrrr', ['Source', '$n$', 'v1', 'v2', 'v3', r'v3 $\to$ Angika'], rows)
    rows = []
    for t in ['v1', 'v2']:
        rr = [A['aggregate'][f'{t}|{pop}|{arm}']['to_hindi']
              for pop, arm in [('anp_split', 'document'), ('angika', 'document'), ('angika', 'sentence')]]
        rows.append([NAMES[t]] + [fmt(x, 4) for x in rr])
    table('angika_audit', 'lrrr', ['Identifier', 'Split documents', 'Control articles', 'Control sentences'], rows)
    rows = []
    for source in ['Wikipedia', 'News']:
        for t in ['v1', 'v2', 'v3', 'ol3', 'ol3_recommended']:
            x = D['nested'][t + '|' + source]
            delta = x['L20_minus_L1']
            ivl = '[' + ', '.join(fmt(v) for v in delta['ci']) + ']'
            name = 'OL3 (rec.)' if t == 'ol3_recommended' else ('OL3 (common)' if t == 'ol3' else NAMES[t])
            rows.append([source, name, x['n']] + [fmt(x['lengths'][le]['rate']) for le in ['L1', 'L5', 'L20']]
                        + [fmt(delta['value']), ivl])
    table('nested_summary', 'llrrrrrl', ['Source', 'Model', '$n$', 'L1', 'L5', 'L20', r'$\Delta$', 'Paired interval'], rows)
    rows = []
    for source in ['Wikipedia', 'News']:
        for le in ['L1', 'L5', 'L20']:
            s = D['source_sensitivity']['v3|' + source + '|' + le]
            rows.append([source, le, s['clusters'], s['largest_cluster_n']]
                        + [fmt(s[f]) for f in ['unit_rate', 'equal_cluster_rate', 'without_largest_rate']])
    table('source_sensitivity', 'llrrrrr', ['Source', 'Unit', 'Clusters', 'Max size', 'Unit wt.', 'Equal cluster',
                                            'Drop largest'], rows)
    ol3 = C.load_json('results/openlid_v3.json')
    rows = []
    for source in ['Wikipedia', 'News']:
        for le in ['L1', 'L5', 'L20']:
            a = ol3['common']['original_cells'][source + '_' + le]
            b = ol3['recommended']['original_cells'][source + '_' + le]
            rows.append([source, le, a['n'], fmt(a['retention']), fmt(b['retention'])])
    table('openlid_v3_retention', 'llrrr', ['Source', 'Unit', 'Hindi $n$', 'Common input', 'Recommended input'], rows)


def sgn(x, n=3):
    """Signed value for a table column: minus sign kept, positive values padded."""
    s = fmt(x, n)
    if s.startswith('-'):
        return '$%s$' % s
    return r'$\phantom{-}%s$' % s


def ci(pair, n=3):
    return '[%s, %s]' % (sgn(pair[0], n), sgn(pair[1], n))


def register():
    reg = C.load_json('results/register.json')
    dec = C.load_json('results/decomposition.json')
    w, n = reg['cells']
    obs = dec['observables']
    names = (('function_word_count', 'function-word count'), ('token_count', 'token count'),
             ('stub_template_match', 'stub-template match'), ('rare_token_rate', 'rare-token rate'))
    # the smallest shares need a fourth decimal to keep their sign readable
    digits = 4 if any(abs(o['share_of_gap_absorbed']) < 5e-4 or
                      any(abs(c) < 5e-4 for c in o['share_ci']) for o in obs.values()) else 3
    rows = [r'\begin{tabular}{lcc}', r'\toprule', r'& Hindi Wikipedia & Hindi news\\', r'\midrule',
            r'Units & 2{,}000 & 2{,}000\\',
            r'GlotLID v3 retention & %s & %s\\' % (fmt(w['retention']), fmt(n['retention'])),
            r'\addlinespace',
            r'Function-word rate & %s & %s\\' % (fmt(w['mean_fw_rate']), fmt(n['mean_fw_rate'])),
            r'Units with no function-word match & %s & %s\\' % (fmt(w['zero_fw_share']), fmt(n['zero_fw_share'])),
            r'Rare-token rate & %s & %s\\' % (fmt(w['mean_rtr']), fmt(n['mean_rtr'])),
            r'Stub-template match & %s & %s\\' % (fmt(w['tpl_share']), fmt(n['tpl_share'])),
            r'Median tokens & %d & %d\\' % (w['median_tokens'], n['median_tokens']),
            r'\addlinespace',
            r'\multicolumn{3}{l}{\emph{Share of the %s retention gap absorbed by reweighting}}\\' % fmt(dec['raw_gap'])]
    for key, label in names:
        o = obs[key]
        rows.append(r'\quad %s & \multicolumn{2}{c}{%s %s}\\' % (label, sgn(o['share_of_gap_absorbed'], digits),
                                                                ci(o['share_ci'], digits)))
    rows += [r'\bottomrule', r'\end{tabular}', '']
    write('register', '\n'.join(rows))


def seven():
    comp = C.load_json('results/composition.json')['models']
    ol3 = C.load_json('results/openlid_v3.json')['common']
    order = (('langid', r'\texttt{langid.py}'), ('cld3', 'CLD3'), ('lid176', r'\texttt{lid.176}'),
             ('openlid', 'OpenLID'), ('ol3', 'OpenLID-v3'), ('v1', 'GlotLID v1'),
             ('v2', 'GlotLID v2'), ('v3', 'GlotLID v3'))
    rows = [r'\begin{tabular}{lcccc}', r'\toprule',
            r' & Hindi & \multicolumn{2}{c}{Hindi-sourced share of the Hindi bucket} & Angika row\\',
            r'\cmidrule(lr){3-4}',
            r'Identifier & retention & six sources & seven sources & $\rightarrow$ Hindi\\', r'\midrule']
    for k, label in order:
        if k == 'ol3':
            rows.append(r'%s & %s & %s & %s & %s\\' % (label, fmt(ol3['panel1_hin_L1']), fmt(ol3['composition_six']),
                                                       fmt(ol3['composition_seven']), fmt(ol3['angika_row_to_hindi'])))
            continue
        m = comp[k]
        rows.append(r'%s & %s & %s [%s, %s] & %s [%s, %s] & %s\\' % (
            label, fmt(m['hindi_retention']), fmt(m['precision6']), fmt(m['ci6'][0]), fmt(m['ci6'][1]),
            fmt(m['precision7']), fmt(m['ci7'][0]), fmt(m['ci7'][1]), fmt(m['angika_row_to_hindi'])))
    rows += [r'\bottomrule', r'\end{tabular}', '']
    write('seven_language', '\n'.join(rows))


def angika_groups():
    g = C.load_json('results/angika_groups.json')

    def row(label, key, pad):
        v1, v3 = g['v1'][key], g['v3'][key]
        n = f"{v1['n']:,}".replace(',', '{,}')
        return '%s & %s & %s & --- & %s & %s\\\\' % (label, n.rjust(pad), fmt(v1['to_hindi']), fmt(v3['to_hindi']),
                                                       fmt(v3['to_angika']))
    rows = [r'\begin{tabular}{lrcccc}', r'\toprule',
            r'& & \multicolumn{2}{c}{GlotLID v1} & \multicolumn{2}{c}{GlotLID v3}\\',
            r'\cmidrule(lr){3-4}\cmidrule(lr){5-6}',
            r'Lexical group & $n$ & $\rightarrow$ Hindi & $\rightarrow$ Angika & $\rightarrow$ Hindi & $\rightarrow$ Angika\\',
            r'\midrule',
            row('Angika-marked', 'angika_marked', 0),
            row('Hindi-marked ', 'hindi_marked', 0),
            row('Unmarked     ', 'neither', 5),
            r'\midrule',
            row('Whole extract', 'ALL', 0),
            r'\bottomrule', r'\end{tabular}', '']
    write('angika_groups', '\n'.join(rows))


if __name__ == '__main__':
    panel_tables()
    reader_nested_tables()
    register()
    seven()
    angika_groups()
    print('tables written to', OUT)
