"""Shared loaders.

Identifiers, predictions and source clusters come from data/.  Unit texts come
from texts/, which analysis/rebuild_texts.py writes from the external corpora;
scripts that need no text do not need texts/.  External files read directly
(the Leipzig archives and the two GlotLID training files) are found through
INSTRUMENT_INPUTS, as in rebuild_texts.py.
"""
import csv
import gzip
import io
import json
import os
import tarfile
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
RESULTS = os.path.join(ROOT, 'results')
TEXTS = os.path.join(ROOT, 'texts')

P1_CORPUS = {
    'nep': 'nep_wikipedia_2021_100K',
    'hin': 'hin_wikipedia_2021_300K',
    'mar': 'mar_wikipedia_2021_30K',
    'san': 'san_wikipedia_2021_30K',
    'new': 'new_wikipedia_2021_30K',
    'mai': 'mai_wikipedia_2021_10K',
}

# Accepted labels for the Hindi reference language, per identifier, following
# the paper's protocol (base code hin/hi, Devanagari where script-tagged).
HINDI_LABELS = {
    'v1': {'hin'},
    'v2': {'hin_Deva'},
    'v3': {'hin_Deva'},
    'openlid': {'hin_Deva'},
    'cld3': {'hi'},
    'langid': {'hi'},
    'lid176': {'hi'},
}

ANGIKA_LABEL = {'v1': None, 'v2': None, 'v3': 'anp_Deva',
                'openlid': None, 'cld3': None, 'langid': None, 'lid176': None}


# ---------------------------------------------------------------- files

def read_csv(name):
    """Rows of data/<name> as dicts of strings (reads <name>.gz when only that exists)."""
    path = os.path.join(DATA, name)
    if not os.path.exists(path) and os.path.exists(path + '.gz'):
        fh = io.TextIOWrapper(gzip.open(path + '.gz', 'rb'), encoding='utf-8', newline='')
    else:
        fh = open(path, encoding='utf-8', newline='')
    with fh:
        return list(csv.DictReader(fh))


def load_json(path):
    """JSON from a path relative to the repository root."""
    with open(os.path.join(ROOT, path), encoding='utf-8') as fh:
        return json.load(fh)


def write_result(name, obj, indent=1):
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, name), 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, indent=indent)


def truth(x):
    return x == 'true'


def texts(unit_set):
    """Rows of texts/<unit_set>.jsonl.gz, in unit-file order."""
    path = os.path.join(TEXTS, unit_set + '.jsonl.gz')
    if not os.path.exists(path):
        raise SystemExit('%s is missing: run analysis/rebuild_texts.py --inputs <folder> first' % path)
    with gzip.open(path, 'rt', encoding='utf-8') as fh:
        return [json.loads(l) for l in fh]


_INPUTS = None


def external(name):
    """Path of an external input named in data/external_inputs.json."""
    global _INPUTS
    if _INPUTS is None:
        import rebuild_texts
        folder = os.environ.get('INSTRUMENT_INPUTS')
        if not folder or not os.path.isdir(folder):
            raise SystemExit('set INSTRUMENT_INPUTS to the folder holding the external inputs')
        _INPUTS = rebuild_texts.Inputs(folder)
    p = _INPUTS.path(name)
    if p is None:
        raise SystemExit('external input %s not found under INSTRUMENT_INPUTS' % name)
    return p


# ---------------------------------------------------------------- panels

def panel1_texts():
    """(lang, length, unit_id) -> text for the 19,764 Panel 1 units."""
    return {(r['lang'], r['length'], r['unit_id']): r['text'] for r in texts('panel1_units')}


def panel1_preds(model):
    """(lang, length, unit_id) -> prediction on Panel 1."""
    return {(r['lang'], r['length'], r['unit_id']): r['pred']
            for r in read_csv('panel1_predictions_%s.csv' % model)}


def panel2_rows():
    """Panel 2 units with their rebuilt texts, in unit-file order."""
    t = {(r['regime'], r['corpus'], r['lang'], r['length'], r['unit_id']): r['text']
         for r in texts('panel2_units')}
    rows = []
    for r in read_csv('panel2_units.csv'):
        r = dict(r)
        r['text'] = t[(r['regime'], r['corpus'], r['lang'], r['length'], r['unit_id'])]
        if not r['source_url']:
            del r['source_url']
        rows.append(r)
    return rows


def panel2_preds(model):
    return {(r['regime'], r['lang'], r['length'], r['unit_id']): r['pred']
            for r in read_csv('panel2_predictions_%s.csv' % model)
            if r['panel'] == 'panel2'}


def panel_clusters(panel, regime, lang, length):
    """unit_id -> recovered source cluster for one panel cell.  Clusters are
    Leipzig source documents grouped by URL and joined through shared
    sentences; they cover the Panel 1 cells and the Panel 2 news cells."""
    return {r['unit_id']: r['cluster'] for r in read_csv('panel_source_clusters.csv')
            if (r['panel'], r['regime'], r['lang'], r['length']) == (panel, regime, lang, length)}


def news_clusters():
    """unit_id -> source cluster for the Hindi news L1 cell (Panel 2, regime A):
    2,000 units in 1,954 clusters."""
    return panel_clusters('panel2', 'A', 'hin', 'L1')


def leipzig_clusters(corpus):
    """sentence_id -> cluster key over a whole Leipzig corpus, read from its archive.

    Leipzig ships ``-inv_so.txt`` as ``source_id \\t sentence_id`` and
    ``-sources.txt`` as ``source_id \\t url \\t date``.  Source IDs sharing a
    URL are grouped into one cluster, and a sentence attached to several
    sources joins those sources into a single cluster (union-find).
    """
    url, sent_sources = {}, {}
    with tarfile.open(external(corpus + '.tar.gz')) as tf:
        for m in tf:
            if m.name.endswith(corpus + '-sources.txt'):
                for line in tf.extractfile(m):
                    p = line.decode('utf-8').rstrip('\r\n').split('\t')
                    if len(p) >= 2:
                        url[p[0]] = p[1]
            elif m.name.endswith(corpus + '-inv_so.txt'):
                for line in tf.extractfile(m):
                    p = line.decode('utf-8').rstrip('\r\n').split('\t')
                    if len(p) >= 2:
                        sent_sources.setdefault(p[1], []).append(p[0])

    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    by_url = {}
    for sid, u in url.items():
        by_url.setdefault(u, []).append(sid)
    for group in by_url.values():
        for other in group[1:]:
            union(group[0], other)
    for sources in sent_sources.values():
        for other in sources[1:]:
            union(sources[0], other)
    return {sent: find(sources[0]) for sent, sources in sent_sources.items()}


def leipzig_sentences(corpus):
    """sentence_id -> text over a whole Leipzig corpus, read from its archive."""
    out = {}
    with tarfile.open(external(corpus + '.tar.gz')) as tf:
        for m in tf:
            if m.name.endswith(corpus + '-sentences.txt'):
                for line in tf.extractfile(m):
                    p = line.decode('utf-8').rstrip('\r\n').split('\t', 1)
                    if len(p) == 2:
                        out[p[0]] = p[1]
    return out


def norm(text):
    """Normalisation for exact matching: NFC plus whitespace collapse."""
    return ' '.join(unicodedata.normalize('NFC', text).split())
