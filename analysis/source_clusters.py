"""Recover the source clusters of the Panel 1 and news units from the Leipzig
archives, and confirm them against data/panel_source_clusters.csv.

A cluster is a connected component of Leipzig source documents: a one-sentence
unit belongs to the source(s) its sentence is attached to (sentences attached
to several sources join them), multi-sentence units belong to their own source
document, and sources sharing a URL are joined.  The Angika Wikipedia units
cluster by article (the first field of the unit ID); the ILI units have no
recoverable source and carry none.

The cluster keys are component representatives, which can differ between runs;
the check compares the partitions of each cell.  Writes
results/source_mapping.json.  Needs the Leipzig archives (INSTRUMENT_INPUTS).
"""
import collections
import sys
import tarfile

import common as C


def source_clusters(corpus, rows):
    sids = {r['unit_id'] for r in rows if r['length'] == 'L1'}
    memberships = collections.defaultdict(set)
    urls = {}
    with tarfile.open(C.external(corpus + '.tar.gz')) as f:
        for m in f:
            if m.name.endswith('-inv_so.txt'):
                for line in f.extractfile(m):
                    p = line.decode('utf-8').strip().split('\t')
                    if len(p) >= 2 and p[1] in sids:
                        memberships[p[1]].add(p[0])
            elif m.name.endswith('-sources.txt'):
                for line in f.extractfile(m):
                    p = line.decode('utf-8').strip().split('\t')
                    if len(p) >= 2:
                        urls[p[0]] = p[1]
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(b)] = find(a)
    used = {r['unit_id'] for r in rows if r['length'] != 'L1'}
    for ss in memberships.values():
        ss = sorted(ss)
        used.update(ss)
        for s in ss[1:]:
            union(ss[0], s)
    seen = {}
    for s in sorted(used, key=int):
        url = urls.get(s)
        if url and url in seen:
            union(seen[url], s)
        elif url:
            seen[url] = s
    result, missing = {}, 0
    for r in rows:
        if r['length'] == 'L1':
            ss = memberships.get(r['unit_id'])
            if not ss:
                missing += 1
                continue
            source = sorted(ss)[0]
        else:
            source = r['unit_id']
        result[(r['length'], r['unit_id'])] = find(source)
    record = {'multi_source_L1': sum(len(v) > 1 for v in memberships.values()),
              'missing_source': missing, 'components': len(set(result.values()))}
    return result, record


def partition(pairs):
    g = collections.defaultdict(set)
    for unit, cl in pairs:
        g[cl].add(unit)
    return sorted(sorted(v) for v in g.values())


def main():
    rows = ([dict(r, panel='panel1', regime='P1') for r in C.read_csv('panel1_units.csv')]
            + [dict(r, panel='panel2') for r in C.read_csv('panel2_units.csv')]
            + [dict(r, panel='panel1_ext') for r in C.read_csv('panel1_l20_units.csv')])
    stored = collections.defaultdict(list)
    for r in C.read_csv('panel_source_clusters.csv'):
        stored[(r['panel'], r['regime'], r['corpus'], r['lang'], r['length'])].append((r['unit_id'], r['cluster']))
    record, bad = {}, []
    for corpus in sorted({r['corpus'] for r in rows if r['regime'] in ('P1', 'A')}):
        rr = [r for r in rows if r['corpus'] == corpus]
        clus, record[corpus] = source_clusters(corpus, rr)
        print('source mapping', corpus, record[corpus], flush=True)
        cells = collections.defaultdict(list)
        for r in rr:
            cells[(r['panel'], r['regime'], r['corpus'], r['lang'], r['length'])].append(
                (r['unit_id'], clus.get((r['length'], r['unit_id']))))
        for cell, pairs in cells.items():
            if partition(pairs) != partition(stored[cell]):
                bad.append(cell)
    for r in rows:
        if r['regime'] == 'C':
            assert dict(stored[(r['panel'], 'C', r['corpus'], r['lang'], r['length'])])[r['unit_id']] == r['unit_id'].split(':')[0]
    C.write_result('source_mapping.json', record)
    print('cells whose partition differs from the stored clusters:', bad or 'none')
    if bad:
        sys.exit(1)


if __name__ == '__main__':
    main()
