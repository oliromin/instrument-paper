"""Score every OpenLID-v3 unit with the published binary.

    python analysis/score_openlid_v3.py /path/to/openlid-v3.bin [--out fresh]

The 39,646 units (29,764 panel units, 9,282 nested units and 600 reader-judged
units) are read from texts/, which rebuild_texts.py writes.  The binary's
SHA-256 must equal the published value (data/model_identities.json) before any
unit is scored.  Each unit is scored under common preprocessing (newlines to
spaces) and under the repository's recommended preprocessing, top-1 label and
score, no confidence cutoff.  The output goes to <out>/openlid_v3_predictions.csv
and is compared, unit by unit, with data/openlid_v3_predictions.csv.
"""
import argparse
import csv
import hashlib
import os
import sys

import common as C
import units


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('model')
    ap.add_argument('--out', default=os.path.join(C.ROOT, 'fresh'))
    a = ap.parse_args()
    import fasttext
    import regex
    nonword = regex.compile(r"[^\p{Word}\p{Zs}]|\d")
    spaces = regex.compile(r"\s\s+")

    def common(t):
        return t.replace('\n', ' ')

    def recommended(t):
        t = t.strip().replace('\n', ' ').lower()
        t = regex.sub(spaces, " ", t)
        return regex.sub(nonword, "", t)

    expect = C.load_json('data/model_identities.json')['openlid_v3']['sha256']
    digest = sha256(a.model)
    print('model', a.model, os.path.getsize(a.model), digest)
    if digest != expect:
        sys.exit('SHA-256 mismatch; refusing to score')
    m = fasttext.load_model(a.model)

    def top1(text):
        try:
            lab, prob = m.predict(text, k=1)
            return lab[0].replace('__label__', ''), float(prob[0])
        except ValueError:          # numpy 2 incompatibility in the wrapper
            prob, lab = m.f.predict(text + '\n', 1, 0.0, 'strict')[0]
            return lab.replace('__label__', ''), float(prob)

    os.makedirs(a.out, exist_ok=True)
    fields = ['set', 'regime', 'source', 'lang', 'length', 'unit_id', 'pred', 'score',
              'recommended_pred', 'recommended_score']
    same = n = 0
    with open(os.path.join(a.out, 'openlid_v3_predictions.csv'), 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, lineterminator='\n')
        w.writerow(fields)
        for r, text in units.openlid_v3_inputs():
            p, s = top1(common(text))
            rp, rs = top1(recommended(text))
            w.writerow([r['set'], r['regime'], r['source'], r['lang'], r['length'], r['unit_id'], p, repr(s), rp, repr(rs)])
            n += 1
            same += (p, rp) == (r['pred'], r['recommended_pred'])
    print('%d units scored; %d carry the stored labels under both preprocessings' % (n, same))


if __name__ == '__main__':
    main()
