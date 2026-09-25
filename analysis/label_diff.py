"""What changed in the label inventory between GlotLID v2 and v3, and whether
any reference language other than Hindi loses material to a label new in v3.

The label lists are the ones read from the hash-verified binaries and stored in
``data/model_labels.json``; nothing here consults the published documentation.  The
routing test reuses the stored Panel 1 predictions, so no model is rerun.

Writes ``results/label_diff.json``.
"""
import collections

import common as C

ACCEPTED = {'hin': {'hin'}, 'nep': {'nep', 'npi'}, 'mar': {'mar'},
            'san': {'san'}, 'new': {'new'}, 'mai': {'mai'}}
NAMES = {'hin': 'Hindi', 'nep': 'Nepali', 'mar': 'Marathi', 'san': 'Sanskrit',
         'new': 'Newari', 'mai': 'Maithili'}


def labels(model):
    return {'labels': C.load_json('data/model_labels.json')[model],
            'sha256': C.load_json('data/model_identities.json')[model]['sha256']}


def script_of(label):
    return label.split('_')[1] if '_' in label else '?'


def base_of(pred):
    return pred.split('_')[0]


def main():
    v2, v3 = labels('v2'), labels('v3')
    s2, s3 = set(v2['labels']), set(v3['labels'])
    added, removed = s3 - s2, s2 - s3
    # und_* are placeholder classes for unseen Unicode categories, not languages.
    placeholders = {l for l in added if l.startswith('und_')}
    genuine = added - placeholders

    out = {'v2_sha256': v2['sha256'], 'v3_sha256': v3['sha256'],
           'v2_count': len(s2), 'v3_count': len(s3),
           'added': len(added), 'placeholders_added': len(placeholders),
           'genuine_added': len(genuine), 'removed': len(removed),
           'genuine_added_by_script':
               dict(collections.Counter(script_of(l) for l in genuine)),
           'v2_labels_by_script':
               dict(collections.Counter(script_of(l) for l in s2)),
           'genuine_added_devanagari': sorted(l for l in genuine
                                              if script_of(l) == 'Deva'),
           'removed_labels': sorted(removed),
           'cells': {}}

    print('v2 %d labels, v3 %d labels' % (len(s2), len(s3)))
    print('  added %d, of which %d are und_* placeholders and %d are languages'
          % (len(added), len(placeholders), len(genuine)))
    print('  removed %d' % len(removed))
    print('  new Devanagari language labels: %s'
          % ', '.join(out['genuine_added_devanagari']))

    texts = C.panel1_texts()
    preds = {m: C.panel1_preds(m) for m in ('v1', 'v2', 'v3')}
    cells = collections.defaultdict(list)
    for (lang, length, uid) in texts:
        cells[(lang, length)].append(uid)

    print('\nPanel 1: retention by release, and the share of each cell that v3'
          ' sends to a label new in v3')
    for length in ('L1', 'L5'):
        for lang in ('hin', 'nep', 'mar', 'san', 'new', 'mai'):
            ids = cells.get((lang, length))
            if not ids:
                continue
            accept = ACCEPTED[lang]
            r = {m: sum(1 for u in ids
                        if base_of(preds[m][(lang, length, u)]) in accept) / len(ids)
                 for m in ('v1', 'v2', 'v3')}
            lost = [preds['v3'][(lang, length, u)] for u in ids
                    if base_of(preds['v3'][(lang, length, u)]) not in accept]
            to_new = [q for q in lost if q in genuine]
            d = {'n': len(ids), 'v1': r['v1'], 'v2': r['v2'], 'v3': r['v3'],
                 'v2_to_v3_change': r['v3'] - r['v2'],
                 'lost_units': len(lost), 'lost_to_new_labels': len(to_new),
                 'share_of_cell_to_new_labels': len(to_new) / len(ids),
                 'destinations': collections.Counter(lost).most_common(5)}
            out['cells']['%s_%s' % (lang, length)] = d
            print('  %-4s %-9s n=%4d  v1 %.3f v2 %.3f v3 %.3f  change %+.3f'
                  '   to new labels %.3f  (%s)'
                  % (length, NAMES[lang], d['n'], r['v1'], r['v2'], r['v3'],
                     d['v2_to_v3_change'], d['share_of_cell_to_new_labels'],
                     ', '.join('%s %d' % (l, c) for l, c in d['destinations'][:2])
                     or 'no losses'))

    C.write_result('label_diff.json', out)


if __name__ == '__main__':
    main()
