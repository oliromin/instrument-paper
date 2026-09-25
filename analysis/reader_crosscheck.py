"""Where the reader-confirmed Hindi units that GlotLID v3 sends to Angika went
under the two earlier releases.  Reads data/reader_sample.csv and the
per-release reader-sample predictions; writes results/reader_crosscheck.json.
"""
import collections
import json

import common as C


def main():
    units = {r['uid']: r for r in C.read_csv('reader_sample.csv')}
    P = {m: {r['uid']: r['pred'] for r in C.read_csv('reader_sample_predictions_%s.csv' % m)}
         for m in ('v1', 'v2', 'v3')}
    order = [r['uid'] for r in C.read_csv('reader_sample_predictions_v3.csv')]
    hin = [u for u in order if units[u]['lang'] == 'hi' and C.truth(units[u]['confirmed'])]
    ang = [u for u in hin if P['v3'][u] == 'anp_Deva']
    both = [u for u in ang if C.truth(units[u]['both_confirmed'])]
    res = {
        'reader1_confirmed_hindi': len(hin),
        'retained': {m: sum(P[m][u].startswith('hin') for u in hin) for m in P},
        'v3_to_angika': len(ang),
        'of_those_hindi_under': {m: sum(P[m][u].startswith('hin') for u in ang) for m in ('v1', 'v2')},
        'of_those_labels_under': {m: collections.Counter(P[m][u] for u in ang).most_common()
                                  for m in ('v1', 'v2')},
        'both_readers_v3_to_angika': len(both),
        'both_readers_hindi_under': {m: sum(P[m][u].startswith('hin') for u in both) for m in ('v1', 'v2')},
    }
    C.write_result('reader_crosscheck.json', res)
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
