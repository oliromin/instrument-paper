"""Reading of the published GlotLID v3.1 Angika training file (protocol 10).

    python analysis/training_file.py
    python analysis/training_file.py --v1 /path/model_v1.bin --v2 /path/model_v2.bin

Arm A needs only the external file and the rebuilt extract texts: the file is
segmented and filtered as in protocol 06, exact duplicates are dropped, and the
script reports the Angika-marked share of its sentences and the share that
exact-match a sentence of the 1,028-article extract.  Arm B runs GlotLID v1 and
v2, each refused unless its SHA-256 equals the recorded one; each must first
reproduce its share to Hindi on the Angika-marked extract sentences
(data/angika_extract_sentences.csv) before the file is read.  Arm C, panel
membership in the Hindi file, is computed by overlap.py.

Writes results/training_file.json and, when the binaries are given,
results/training_file_identifiers.json.
"""
import argparse
import json
import unicodedata

import common as C
import predict as P
import register as R

ANP_FILE = 'anp_Deva_wikipedia.txt'
HINDI = {'hin', 'hin_Deva'}


def norm(t):
    return ' '.join(unicodedata.normalize('NFC', t).split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--v1', help='path of GlotLID v1 (model_v1.bin)')
    ap.add_argument('--v2', help='path of GlotLID v2 (model_v2.bin)')
    a = ap.parse_args()

    sents = R.training_file_sentences(C.external(ANP_FILE))
    anp = set(C.load_json('data/angika_markers.json')['anp'])
    marked = [s for s in sents if set(s.split()) & anp]
    extract = {r['sentence']: r['text'] for r in C.texts('angika_extract_sentences')}
    in_extract = {norm(t) for t in extract.values()}
    matched = [s for s in sents if norm(s) in in_extract]
    ext_marked = [t for t in extract.values() if set(t.split()) & anp]
    out = {'file': ANP_FILE, 'sentences': len(sents),
           'angika_marked': len(marked), 'angika_marked_share': len(marked) / len(sents),
           'extract_match': len(matched), 'extract_match_share': len(matched) / len(sents),
           'extract_sentences': len(extract), 'extract_angika_marked_one_sided': len(ext_marked),
           'extract_angika_marked_one_sided_share': len(ext_marked) / len(extract)}

    rows = C.read_csv('angika_extract_sentences.csv')
    ref_ids = [r['sentence'] for r in rows if r['group'] == 'angika_marked']
    out['reference_to_hindi_stored'] = {
        m: sum(r['pred_' + m] in HINDI for r in rows if r['group'] == 'angika_marked') / len(ref_ids)
        for m in ('v1', 'v2')}
    ids = C.load_json('data/model_identities.json')
    read = {}
    for m, path in (('v1', a.v1), ('v2', a.v2)):
        if not path:
            continue
        predict = P.backend_fasttext(path, ids[m]['sha256'])
        ref = [lab for lab, _ in predict([extract[i].replace('\n', ' ') for i in ref_ids])]
        ref_share = sum(lab in HINDI for lab in ref) / len(ref)
        stored_share = out['reference_to_hindi_stored'][m]
        entry = {'reference_n': len(ref), 'reference_to_hindi': ref_share,
                 'reference_reproduced': abs(ref_share - stored_share) <= 0.01}
        if entry['reference_reproduced']:
            labs = [lab for lab, _ in predict([s.replace('\n', ' ') for s in sents])]
            entry['file_to_hindi'] = sum(lab in HINDI for lab in labs) / len(labs)
            entry['excess_over_reference'] = entry['file_to_hindi'] - ref_share
        read[m] = entry

    C.write_result('training_file.json', out)
    print(json.dumps(out, indent=1))
    if read:
        C.write_result('training_file_identifiers.json', read)
        print(json.dumps(read, indent=1))


if __name__ == '__main__':
    main()
