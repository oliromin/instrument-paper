"""Rebuild the text of every evaluated unit from the named external corpora.

The repository publishes identifiers, predictions and results, never the texts.
This script reconstructs each unit's text from the external inputs listed in
data/external_inputs.json and confirms it against the SHA-256 of its
NFC-normalised text stored in the unit file.  A unit whose rebuilt text does not
reproduce the stored hash is reported and the script exits with status 1.

    python analysis/rebuild_texts.py --inputs /path/to/external/inputs

The inputs folder is searched recursively.  A file is found by the name given in
data/external_inputs.json or, when no file carries that name, by its size and
SHA-256, so the files can keep whatever names they were downloaded under.  Texts
are written to texts/ (not tracked) for the analysis scripts that need them.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import unicodedata
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')


def nfc_sha(text):
    return hashlib.sha256(unicodedata.normalize('NFC', text).encode('utf-8')).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b''):
            h.update(chunk)
    return h.hexdigest()


def read_csv(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path) and os.path.exists(path + '.gz'):
        fh = io.TextIOWrapper(gzip.open(path + '.gz', 'rb'), encoding='utf-8', newline='')
    else:
        fh = open(path, encoding='utf-8', newline='')
    with fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------- locating inputs

class Inputs:
    def __init__(self, folder):
        self.folder = folder
        self.spec = {d['name']: d for d in
                     json.load(open(os.path.join(DATA, 'external_inputs.json'), encoding='utf-8'))['inputs']}
        self.by_name, self.by_size = {}, defaultdict(list)
        for base, _dirs, files in os.walk(folder):
            for f in files:
                p = os.path.join(base, f)
                self.by_name.setdefault(f, p)
                try:
                    self.by_size[os.path.getsize(p)].append(p)
                except OSError:
                    pass
        self.found, self.missing = {}, []

    def path(self, name):
        if name in self.found:
            return self.found[name]
        spec = self.spec[name]
        candidates = ([self.by_name[name]] if name in self.by_name else []) + \
            [p for p in self.by_size.get(spec['bytes'], []) if p != self.by_name.get(name)]
        for p in candidates:
            if os.path.getsize(p) == spec['bytes'] and file_sha(p) == spec['sha256']:
                self.found[name] = p
                print('  input %-44s %s' % (name, os.path.relpath(p, self.folder)), flush=True)
                return p
        self.found[name] = None
        self.missing.append(name)
        print('  input %-44s NOT FOUND (no file with the recorded SHA-256)' % name, flush=True)
        return None


# ---------------------------------------------------------------- corpus readers

def leipzig(path, corpus):
    """sentence id -> text, and source id -> sentence ids, from a Leipzig archive."""
    sent, src = {}, defaultdict(list)
    with tarfile.open(path) as tf:
        for m in tf:
            if m.name.endswith(corpus + '-sentences.txt'):
                for line in tf.extractfile(m):
                    p = line.decode('utf-8').rstrip('\r\n').split('\t', 1)
                    if len(p) == 2:
                        sent[p[0]] = p[1].strip()
            elif m.name.endswith(corpus + '-inv_so.txt'):
                for line in tf.extractfile(m):
                    p = line.decode('utf-8').rstrip('\r\n').split('\t')
                    if len(p) >= 2:
                        src[p[0]].append(p[1].strip())
    return sent, src


def leipzig_unit(sent, src, length, unit_id):
    """L1 is one sentence; LN is the first N sentences of one source document,
    in sentence-id order, joined by single spaces."""
    if length == 'L1':
        return sent.get(unit_id)
    n = int(length[1:])
    sids = sorted(src.get(unit_id, []), key=int)[:n]
    if len(sids) < n:
        return None
    return ' '.join(sent.get(s, '') for s in sids).strip()


def ili_lines(path):
    """one-based line number -> text, as the shared-task file is read."""
    out = {}
    with open(path, encoding='utf-8') as fh:
        for ln, line in enumerate(fh, 1):
            p = line.rstrip('\n').split('\t')
            if len(p) >= 2 and p[0].strip():
                out[ln] = p[0].strip()
    return out


def segment(text):
    """The fixed sentence segmenter: danda, double danda, or . ! ? followed by
    whitespace or end of text closes a sentence; the terminator stays with it."""
    text = unicodedata.normalize('NFC', text)
    parts, buf = [], []
    i = 0
    while i < len(text):
        ch = text[i]
        buf.append(ch)
        if ch in '।॥':
            parts.append(''.join(buf))
            buf = []
        elif ch in '.!?':
            nxt = text[i + 1] if i + 1 < len(text) else ''
            if nxt == '' or nxt.isspace():
                parts.append(''.join(buf))
                buf = []
        i += 1
    if buf:
        parts.append(''.join(buf))
    out = []
    for p in parts:
        for line in p.split('\n'):
            s = line.strip()
            if s:
                out.append(s)
    return out


DEVA = re.compile(r'[ऀ-ॿ]')


def deva_purity(s):
    alpha = [c for c in s if c.isalpha()]
    if not alpha:
        return 0.0
    return sum(1 for c in alpha if DEVA.match(c)) / len(alpha)


def filtered_sentences(text):
    """Segmented sentences with at least six tokens and 90% Devanagari letters."""
    return [s for s in segment(text) if len(s.split()) >= 6 and deva_purity(s) >= 0.9]


def normalised(text):
    return ' '.join(unicodedata.normalize('NFC', text).split())


TAGS = re.compile(r'<[^>]{1,40}>')
SPACES = re.compile(r'\s+')
WIKI_SPLIT = re.compile(r'(?<=[।?!])\s+')


def clean(text):
    """Annotation tags removed and whitespace collapsed, as the reader sample was built."""
    return SPACES.sub(' ', TAGS.sub(' ', text or '')).strip()


# ---------------------------------------------------------------- the rebuild

class Rebuild:
    def __init__(self, inputs, out):
        self.inputs, self.out = inputs, out
        self.cache = {}
        self.report = {}

    def load(self, name, reader):
        if name not in self.cache:
            p = self.inputs.path(name)
            self.cache[name] = reader(p) if p else None
        return self.cache[name]

    def leipzig(self, corpus):
        return self.load(corpus + '.tar.gz', lambda p: leipzig(p, corpus))

    def angika(self):
        return self.load('angika_wikipedia_extracts.json', lambda p: json.load(open(p, encoding='utf-8')))

    def parquet(self, name):
        def read(p):
            import pyarrow.parquet as pq
            return pq.read_table(p, columns=['text'])['text'].to_pylist()
        return self.load(name, read)

    def ili(self, split):
        name = {'train': 'vardial2018_train.txt', 'dev': 'vardial2018_dev.txt',
                'test': 'vardial2018_gold.txt'}[split]
        return self.load(name, ili_lines)

    def pull(self, name):
        return self.load(name, lambda p: json.load(open(p, encoding='utf-8')))

    # each unit file: key columns, and a function row -> text or None
    def finish(self, label, rows, keys, textfn):
        ok = bad = absent = 0
        failures = []
        path = os.path.join(self.out, label + '.jsonl.gz')
        with gzip.open(path, 'wt', encoding='utf-8') as fh:
            for r in rows:
                t = textfn(r)
                if t is None:
                    absent += 1
                    continue
                if nfc_sha(t) != r['text_sha256']:
                    bad += 1
                    if len(failures) < 5:
                        failures.append({k: r[k] for k in keys})
                    continue
                ok += 1
                fh.write(json.dumps({**{k: r[k] for k in keys}, 'text': t}, ensure_ascii=False) + '\n')
        self.report[label] = {'units': len(rows), 'reproduced': ok, 'hash_mismatch': bad,
                              'input_missing': absent, 'first_mismatches': failures}
        print('%-28s units %7d   reproduced %7d   mismatched %d   not rebuilt %d'
              % (label, len(rows), ok, bad, absent), flush=True)

    def run(self):
        # Panel 1 (Leipzig Wikipedia): L1 and L5, and the L20 cells
        def lz(r):
            c = self.leipzig(r['corpus'])
            return leipzig_unit(*c, r['length'], r['unit_id']) if c else None
        self.finish('panel1_units', read_csv('panel1_units.csv'), ['lang', 'length', 'unit_id'], lz)
        self.finish('panel1_l20_units', read_csv('panel1_l20_units.csv'),
                    ['regime', 'corpus', 'lang', 'length', 'unit_id'], lz)

        # Panel 2: A news (Leipzig), B the ILI shared task, C Angika Wikipedia
        def p2(r):
            if r['regime'] == 'A':
                return lz(r)
            if r['regime'] == 'B':
                split, ln = r['unit_id'].split(':')
                lines = self.ili(split)
                return lines.get(int(ln)) if lines else None
            arts = self.angika()
            if arts is None:
                return None
            aid, part = r['unit_id'].split(':')
            sents = segment(arts[int(aid)]['x'])
            if part == 'D':
                return ' '.join(sents).strip()
            if part.startswith('s'):
                return sents[int(part[1:])]
            return ' '.join(sents[:int(part[1:])]).strip()
        self.finish('panel2_units', read_csv('panel2_units.csv'),
                    ['regime', 'corpus', 'lang', 'length', 'unit_id'], p2)

        # the unfiltered ILI test set
        def ili(r):
            lines = self.ili('test')
            return lines.get(int(r['unit_id'])) if lines else None
        self.finish('ili_test_units', read_csv('ili_test_units.csv'), ['unit_id', 'lang'], ili)

        # nested sampled-source units: the stored sentence ids, in order
        def nested(r):
            c = self.leipzig(r['corpus'])
            if not c:
                return None
            return ' '.join(c[0].get(s, '') for s in r['sentence_ids'].split()).strip()
        self.finish('nested_units', read_csv('nested_units.csv'),
                    ['source', 'corpus', 'lang', 'length', 'unit_id'], nested)

        # the reader-judged sample: harvested pulls, located by record
        def reader(r):
            d = self.pull(r['source_file'])
            if d is None:
                return None
            loc = r['source_record'].split(':')
            if loc[0] == 'row':
                return d['rows'][loc[1]][int(loc[2])]['text']
            text = clean(d['docs'][int(loc[1])]['text'])
            if len(loc) == 2:
                return text
            return WIKI_SPLIT.split(text)[int(loc[3])].strip()
        self.finish('reader_sample', read_csv('reader_sample.csv'), ['uid'], reader)

        # the Angika Wikipedia extract: articles, and the sentences the lexical groups read
        def article(r):
            arts = self.angika()
            return arts[int(r['article'])]['x'] if arts else None
        self.finish('angika_extract_articles', read_csv('angika_extract_articles.csv'), ['article'], article)

        def extract_sentence(r):
            arts = self.angika()
            if arts is None:
                return None
            return normalised(arts[int(r['article'])]['x'])[int(r['start']):int(r['end'])]
        self.finish('angika_extract_sentences', read_csv('angika_extract_sentences.csv'), ['sentence'], extract_sentence)

        # released-split populations and their references
        parquet = {'anp_split': 'fineweb2_anp_Deva_train_000_00000.parquet',
                   'awa_split': 'fineweb2_awa_Deva_train_000_00000.parquet'}
        seg_cache = {}

        def released(r):
            loc = r['source_record'].split(':')
            if r['population'] == 'angika':
                arts = self.angika()
                if arts is None:
                    return None
                if len(loc) == 2:
                    return arts[int(loc[1])]['x']
                a, b = loc[3].split('-')
                return normalised(arts[int(loc[1])]['x'])[int(a):int(b)]
            if loc[0] == 'ili':
                lines = self.ili(loc[1])
                return lines.get(int(loc[2])) if lines else None
            docs = self.parquet(parquet[r['population']])
            if docs is None:
                return None
            if len(loc) == 2:
                return docs[int(loc[1])]
            key = (r['population'], int(loc[1]))
            if key not in seg_cache:
                seg_cache[key] = filtered_sentences(docs[int(loc[1])])
            return seg_cache[key][int(loc[3])]
        self.finish('released_split_units', read_csv('released_split_units.csv'),
                    ['population', 'arm', 'unit_id'], released)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--inputs', default=os.environ.get('INSTRUMENT_INPUTS'),
                    help='folder holding the external inputs (or set INSTRUMENT_INPUTS)')
    ap.add_argument('--out', default=os.path.join(ROOT, 'texts'))
    a = ap.parse_args()
    if not a.inputs or not os.path.isdir(a.inputs):
        sys.exit('give --inputs <folder holding the external corpora>')
    os.makedirs(a.out, exist_ok=True)
    print('locating inputs under', a.inputs, flush=True)
    rb = Rebuild(Inputs(a.inputs), a.out)
    rb.run()
    report = {'inputs_found': {k: bool(v) for k, v in rb.inputs.found.items()},
              'units': rb.report}
    json.dump(report, open(os.path.join(a.out, 'rebuild_report.json'), 'w'), indent=1)
    total = sum(v['units'] for v in rb.report.values())
    done = sum(v['reproduced'] for v in rb.report.values())
    bad = sum(v['hash_mismatch'] for v in rb.report.values())
    print('\n%d of %d unit texts reproduce their stored hash; %d mismatched; %d not rebuilt'
          % (done, total, bad, total - done - bad))
    if bad or done < total:
        sys.exit(1)


if __name__ == '__main__':
    main()
