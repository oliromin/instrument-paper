"""Panel 1 retention on marker-selected Maithili and Newari subsets (post hoc).

A unit is target-marked if it carries at least one target-distinctive marker
(data/maithili_markers.json, data/newari_markers.json); otherwise Hindi-marked
if it carries a Hindi-distinctive marker; otherwise neither.  Matching is
whole whitespace-delimited token, exact, with punctuation left on.  No model is
run: every figure joins the stored Panel 1 predictions to the marker groups.

Retention: base code in the language's accepted set and script suffix absent or
Deva; a macrolanguage label counts only where the identifier carries no member
label.  Writes results/marked_subsets.json.
"""
import math
from collections import Counter, defaultdict

import common as C

ORDER = ['langid', 'lid176', 'cld3', 'openlid', 'v1', 'v2', 'v3']
ACCEPT = {'nep': {'nep', 'npi', 'ne'}, 'hin': {'hin', 'hi'}, 'mar': {'mar', 'mr'},
          'san': {'san', 'sa'}, 'new': {'new', 'nwx'}, 'mai': {'mai'}}
MACRO = {'mai': {'bh', 'bih'}}
GROUPS = ('target_marked', 'hindi_marked', 'neither')


def base(label):
    return label.split('_')[0]


def script(label):
    p = label.split('_')
    return p[1] if len(p) > 1 else None


def accepted(lang, codes):
    a = set(ACCEPT[lang])
    if lang in MACRO and not (a & codes):
        a |= MACRO[lang]
    return a


def retained(label, acc):
    return base(label) in acc and script(label) in (None, 'Deva')


def cell(keys, pred, acc, hin_acc):
    n = len(keys)
    labs = [pred[k] for k in keys]
    ret = sum(1 for l in labs if retained(l, acc))
    lost = [l for l in labs if not retained(l, acc)]
    to_hin = sum(1 for l in lost if retained(l, hin_acc))
    p = ret / n
    return {'n': n, 'retention': p, 'ci': 1.96 * math.sqrt(p * (1 - p) / n),
            'n_lost': len(lost),
            'hindi_share_of_loss': (to_hin / len(lost)) if lost else float('nan'),
            'top_destinations': Counter(lost).most_common(4)}


def group_of(text, tgt, hin):
    toks = set(text.split())
    if toks & tgt:
        return 'target_marked'
    if toks & hin:
        return 'hindi_marked'
    return 'neither'


def main():
    units = C.panel1_texts()
    preds = {t: C.panel1_preds(t) for t in ORDER}
    labels = C.load_json('data/model_labels.json')
    codes = {t: {base(l) for l in labels[t]} for t in ORDER}
    markers = {'mai': C.load_json('data/maithili_markers.json'),
               'new': C.load_json('data/newari_markers.json')}
    results = {}
    for lang in ('hin', 'nep', 'mar', 'san', 'new', 'mai'):
        for length in ('L1', 'L5'):
            keys = [k for k in units if k[0] == lang and k[1] == length]
            for t in ORDER:
                acc = accepted(lang, codes[t])
                if acc & codes[t]:
                    results[(lang, length, t, 'all')] = cell(keys, preds[t], acc, accepted('hin', codes[t]))
    groups = {}
    for lang in ('mai', 'new'):
        tgt, hin = set(markers[lang]['target_markers']), set(markers[lang]['hindi_markers'])
        for length in ('L1', 'L5'):
            g = defaultdict(list)
            for k in (k for k in units if k[0] == lang and k[1] == length):
                g[group_of(units[k], tgt, hin)].append(k)
            groups[(lang, length)] = g
            for gr in GROUPS:
                if not g[gr]:
                    continue
                for t in ORDER:
                    acc = accepted(lang, codes[t])
                    if acc & codes[t]:
                        results[(lang, length, t, gr)] = cell(g[gr], preds[t], acc, accepted('hin', codes[t]))
    # Positive control: Hindi L1 units carrying a Hindi marker from either list.
    hin_all = set(markers['mai']['hindi_markers']) | set(markers['new']['hindi_markers'])
    ctrl = [k for k in units if k[0] == 'hin' and k[1] == 'L1' and set(units[k].split()) & hin_all]
    out = {'results': {'|'.join(k): v for k, v in results.items()},
           'group_sizes': {'%s|%s' % k: {gr: len(v[gr]) for gr in GROUPS} for k, v in groups.items()},
           'hindi_control': cell(ctrl, preds['lid176'], accepted('hin', codes['lid176']),
                                 accepted('hin', codes['lid176']))}
    C.write_result('marked_subsets.json', out)
    for lang in ('mai', 'new'):
        m = results[(lang, 'L1', 'lid176', 'target_marked')]
        print(lang, 'L1 lid.176 marked subset: n', m['n'], 'retention %.4f' % m['retention'],
              'Hindi share of loss %.4f' % m['hindi_share_of_loss'], m['top_destinations'])


if __name__ == '__main__':
    main()
