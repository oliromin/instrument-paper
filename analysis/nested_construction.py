"""Construction of the nested sampled-source units.

For every original Hindi L20 unit (2,000 Wikipedia and 2,000 news sources),
the first 1, 5 and 20 sentences of the same Leipzig source document form the
L1, L5 and L20 units.  A source is kept only if all three pass the panel
filters (at least six tokens, 90% Devanagari letters).  The script confirms
that the rebuilt L20 string equals the original L20 unit, that the kept
sources and sentence IDs equal data/nested_units.csv, and writes
results/nested_construction.json.  Needs texts/ and the two Hindi Leipzig
archives (INSTRUMENT_INPUTS).
"""
import collections
import json
import sys
import tarfile
import unicodedata

import common as C


def keep(s):
    letters = [c for c in s if unicodedata.category(c).startswith('L')]
    return (len(s.split()) >= 6 and bool(letters)
            and sum(0x900 <= ord(c) <= 0x97f for c in letters) / len(letters) >= .9)


def main():
    spec = {d['name']: d for d in C.load_json('data/external_inputs.json')['inputs']}
    l20 = {}
    for s in ('panel2_units', 'panel1_l20_units'):
        for r in C.texts(s):
            if r['lang'] == 'hin' and r['length'] == 'L20':
                l20.setdefault(r['corpus'], []).append(r)
    stored = collections.defaultdict(dict)
    for r in C.read_csv('nested_units.csv'):
        stored[r['source']][(r['unit_id'], r['length'])] = r['sentence_ids'].split()
    info, ok = {}, True
    for source, corpus in [('Wikipedia', 'hin_wikipedia_2021_300K'), ('News', 'hin_news_2022_1M')]:
        originals = l20[corpus]
        wanted = {r['unit_id'] for r in originals}
        sent, src = {}, collections.defaultdict(list)
        with tarfile.open(C.external(corpus + '.tar.gz')) as tf:
            for m in tf:
                if m.name.endswith('-sentences.txt'):
                    for line in tf.extractfile(m):
                        p = line.decode('utf-8').rstrip('\n').split('\t', 1)
                        if len(p) == 2:
                            sent[p[0]] = p[1].strip()
                elif m.name.endswith('-inv_so.txt'):
                    for line in tf.extractfile(m):
                        p = line.decode('utf-8').rstrip('\n').split('\t')
                        if len(p) >= 2 and p[0] in wanted:
                            src[p[0]].append(p[1])
        built = {}
        exact = True
        for r in originals:
            sids = sorted(src[r['unit_id']], key=int)[:20]
            strings = {le: ' '.join(sent.get(s, '') for s in sids[:n]).strip() for le, n in [('L1', 1), ('L5', 5), ('L20', 20)]}
            exact &= strings['L20'] == r['text']
            if all(keep(t) for t in strings.values()):
                for le, n in [('L1', 1), ('L5', 5), ('L20', 20)]:
                    built[(r['unit_id'], le)] = sids[:n]
        match = built == stored[source]
        ok &= exact and match
        info[source] = {'original_L20_n': len(originals), 'joint_eligible_sources': len(built) // 3,
                        'excluded_by_shorter_filters': len(originals) - len(built) // 3,
                        'L20_reconstruction_exact': exact, 'matches_nested_units_file': match,
                        'archive_sha256': spec[corpus + '.tar.gz']['sha256']}
        print(source, info[source], flush=True)
    C.write_result('nested_construction.json', info)
    if not ok:
        sys.exit(1)


if __name__ == '__main__':
    main()
