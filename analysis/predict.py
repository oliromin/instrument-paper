"""Run one identifier over a unit set and compare with the stored predictions.

    python analysis/predict.py <backend> <model> <unit_set> [--artefact PATH] [--out fresh]

backend    fasttext | cld3 | langid
model      v1 | v2 | v3 | openlid | lid176 | cld3 | langid (names in data/model_identities.json)
unit_set   panel1 | panel2 | ili_test | nested | reader_sample | released_split

The input string is the unit's text with newlines replaced by single spaces
and no other normalisation.  Predictions come only from each model's own
prediction path: for fastText, multilinePredict at k = 1 (it returns corrupt
probabilities for k > 1, so it is never used above 1); a fastText binary is
refused unless its SHA-256 equals the recorded one.  Output rows follow the
stored prediction file of the unit set and go to <out>/; the script reports how
many units carry the stored label.  CLD3 runs with min_num_bytes=0 so that no
unit is refused for being short.
"""
import argparse
import csv
import hashlib
import os
import sys

import common as C
import units

STORED = {
    'panel1': ('panel1_predictions_%s.csv', ['lang', 'length', 'unit_id']),
    'panel2': ('panel2_predictions_%s.csv', ['panel', 'regime', 'corpus', 'lang', 'length', 'unit_id']),
    'ili_test': ('ili_test_predictions_%s.csv', ['unit_id', 'lang']),
    'nested': ('nested_predictions_%s.csv', ['source', 'length', 'unit_id']),
    'reader_sample': ('reader_sample_predictions_%s.csv', ['uid']),
    'released_split': ('released_split_predictions_%s.csv', ['population', 'arm', 'unit_id']),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 24), b''):
            h.update(b)
    return h.hexdigest()


def backend_fasttext(artefact, expect):
    import numpy as np
    import fasttext
    import fasttext.FastText as FT

    digest = sha256(artefact)
    if digest != expect:
        sys.exit('SHA-256 of %s is %s, not the recorded %s; refusing to run' % (artefact, digest, expect))

    def _predict(self, text, k=1, threshold=0.0, on_unicode_error='strict'):
        if isinstance(text, str):
            res = self.f.predict(text, k, threshold, on_unicode_error)
            return tuple(res[0]), np.asarray(res[1] if len(res) > 1 else [])
        res = self.f.multilinePredict(text, k, threshold, on_unicode_error)
        return res[0], [np.asarray(p) for p in res[1]]

    FT._FastText.predict = _predict
    m = fasttext.load_model(artefact)

    def predict(texts):
        labs, probs = m.predict(texts, k=1)
        return [(l[0].replace('__label__', ''), float(p[0])) for l, p in zip(labs, probs)]
    return predict


def backend_cld3(_artefact, _expect):
    import gcld3
    det = gcld3.NNetLanguageIdentifier(min_num_bytes=0, max_num_bytes=10000)

    def predict(texts):
        return [(det.FindLanguage(text=t).language, None) for t in texts]
    return predict


def backend_langid(_artefact, _expect):
    from py3langid.langid import classify

    def predict(texts):
        return [(classify(t)[0], None) for t in texts]
    return predict


BACKENDS = {'fasttext': backend_fasttext, 'cld3': backend_cld3, 'langid': backend_langid}


def unit_texts(unit_set):
    if unit_set == 'panel1':
        return units.panel1()
    if unit_set == 'panel2':
        return units.panel2()
    if unit_set == 'ili_test':
        return {(r['unit_id'], r['lang']): r['text'] for r in C.texts('ili_test_units')}
    if unit_set == 'nested':
        return {(r['source'], r['length'], r['unit_id']): r['text'] for r in C.texts('nested_units')}
    if unit_set == 'reader_sample':
        return {(r['uid'],): r['text'] for r in C.texts('reader_sample')}
    return {(r['population'], r['arm'], r['unit_id']): r['text'] for r in C.texts('released_split_units')}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('backend', choices=BACKENDS)
    ap.add_argument('model')
    ap.add_argument('unit_set', choices=STORED)
    ap.add_argument('--artefact', help='path of the fastText binary')
    ap.add_argument('--out', default=os.path.join(C.ROOT, 'fresh'))
    ap.add_argument('--batch', type=int, default=500)
    a = ap.parse_args()
    name, keys = STORED[a.unit_set]
    stored = C.read_csv(name % a.model)
    texts = unit_texts(a.unit_set)
    expect = C.load_json('data/model_identities.json')[a.model].get('sha256')
    if a.backend == 'fasttext' and not a.artefact:
        sys.exit('--artefact is required for the fastText backend')
    predict = BACKENDS[a.backend](a.artefact, expect)
    os.makedirs(a.out, exist_ok=True)
    header = list(stored[0].keys())
    same = 0
    with open(os.path.join(a.out, name % a.model), 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, header, lineterminator='\n')
        w.writeheader()
        for i in range(0, len(stored), a.batch):
            chunk = stored[i:i + a.batch]
            got = predict([texts[tuple(r[k] for k in keys)].replace('\n', ' ') for r in chunk])
            for r, (label, score) in zip(chunk, got):
                row = dict(r, pred=label)
                if 'score' in row:
                    row['score'] = '' if score is None else repr(score)
                w.writerow(row)
                same += label == r['pred']
    print('%s on %s: %d units, %d carry the stored label' % (a.model, a.unit_set, len(stored), same))


if __name__ == '__main__':
    main()
