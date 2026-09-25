"""Routing of the Angika Wikipedia extract's sentences by lexical group.

The 4,823 filtered sentences of the 1,028-article extract carry the marker
tagger's group (Angika-marked, Hindi-marked, neither) and each GlotLID
release's prediction (data/angika_extract_sentences.csv).  Writes the share of
each group routed to Hindi and to Angika, per release, to
results/angika_groups.json.
"""
import json

import common as C

HINDI = {'hin', 'hin_Deva'}
ANGIKA = {'anp', 'anp_Deva'}


def main():
    rows = C.read_csv('angika_extract_sentences.csv')
    out = {}
    for m in ('v1', 'v2', 'v3'):
        d = {}
        for g in ('neither', 'angika_marked', 'hindi_marked', 'ALL'):
            sel = rows if g == 'ALL' else [r for r in rows if r['group'] == g]
            d[g] = {'n': len(sel),
                    'to_hindi': sum(r['pred_' + m] in HINDI for r in sel) / len(sel),
                    'to_angika': sum(r['pred_' + m] in ANGIKA for r in sel) / len(sel)}
        out[m] = d
    C.write_result('angika_groups.json', out)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
