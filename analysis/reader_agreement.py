"""Reader-sample bookkeeping: reader-1 categories, agreement of reader 1 with
the provenance label, agreement between the two readers on the overlap, and
the two-reader confirmed count, from data/reader_sample.csv.
Writes results/reader_agreement.json.
"""
import collections
import json

import common as C

def main():
    rows = C.read_csv('reader_sample.csv')
    counts = collections.Counter(r['reader1'] or 'blank' for r in rows)
    overlap = [r for r in rows if r['reader1'] and r['reader2']]
    out = {'reader1_categories': dict(counts),
           'provenance_agreement_n': sum(r['reader1'] in ('Hindi', 'Nepali') for r in rows),
           'provenance_agreement_k': sum(C.truth(r['confirmed']) for r in rows),
           'inter_reader_n': len(overlap),
           'inter_reader_k': sum(r['reader1'] == r['reader2'] for r in overlap),
           'both_confirmed': sum(C.truth(r['both_confirmed']) for r in rows),
           'panel_text_matches': sum(C.truth(r['panel_text_match']) for r in rows),
           'stage1_n': len(rows)}
    C.write_result('reader_agreement.json', out)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
