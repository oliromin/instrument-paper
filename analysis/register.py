"""Register composition of the Hindi Wikipedia and news cells.

Question: how much of the Wikipedia-versus-news retention gap is accounted for
by the units' register - the proportion of formulaic stub material with high
name density and thin function-word evidence - rather than by "domain" as an
unanalysed label?

Three instruments, none of them fitted to the retention outcome:

  FW   Hindi function-word evidence.  The 25-token Hindi list stored in
       data/angika_markers.json, derived by contrasting token frequencies
       between Hindi and Angika reference text before this analysis existed.  It is Hindi-distinctive
       by construction, so its own association with retention is not evidence;
       what is evidence is how much of the source gap it absorbs.

  RTR  Rare-token rate.  The share of a unit's tokens absent from the most
       frequent V types of the identifier's own published Hindi training file.
       Proper nouns and place names concentrate in the tail of that
       distribution.  The reference is Wikipedia-derived, which favours the
       Wikipedia cell, so a higher Wikipedia RTR is measured against the
       direction of the confound.

  TPL  Stub-template match.  The 200 most frequent sentence-final token
       trigrams of held-out Hindi Wikipedia, where held-out excludes every
       source cluster represented in the evaluation panel.  Derivation follows
       the manuscript's existing practice for marker derivation.

Intervals resample recovered source clusters in both cells (Wikipedia from
the Leipzig mappings, news from the archived Panel 2 source keys).

The Angika side is measured on the published Angika training file after the
fixed segmenter, the panel filters and exact-duplicate removal (3,970
sentences), the same units Section 8.3 reads, and on the marker-selected
Regime C control.
"""
import collections
import json
import os
import random
import unicodedata

import common as C

SEED = 20260912
REPS = 4999
VOCAB_V = 10000      # fixed before inspecting any retention outcome
TPL_M = 200
# The published GlotLID v3.1 files are external inputs, not redistributed.
HIN_FILE = 'hin_Deva_leipzigwiki.txt'
ANP_FILE = 'anp_Deva_wikipedia.txt'


PUNCT = '\u0964\u0965.,;:!?\u201c\u201d"\'()[]{}\u2014\u2013-'


def tok(text):
    return text.split()


def strip_punct(w):
    return w.strip(PUNCT)


def tok_norm(text):
    """Whitespace tokens with edge punctuation removed.

    Seven of the 25 stored Hindi markers carry an attached danda.  The
    Wikipedia cell ends 91.6% of its units with a danda and the news cell ends
    69.9% of its units with a full stop, so raw token matching would credit
    Wikipedia with function-word evidence that the news cell cannot register.
    All function-word matching below therefore strips edge punctuation from
    both the tokens and the marker list.
    """
    return [w for w in (strip_punct(t) for t in text.split()) if w]


def segment(text):
    """The fixed sentence segmenter: terminator retained on the left."""
    text = unicodedata.normalize('NFC', text)
    parts, buf = [], []
    i = 0
    while i < len(text):
        ch = text[i]
        buf.append(ch)
        if ch in '\u0964\u0965':
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
            t = line.strip()
            if t:
                out.append(t)
    return out


def _deva_purity(s):
    alpha = [c for c in s if c.isalpha()]
    if not alpha:
        return 0.0
    return sum(1 for c in alpha if '\u0900' <= c <= '\u097f') / len(alpha)


def training_file_sentences(path):
    """Segment, apply the panel filters (six tokens, 0.90 Devanagari), and
    drop exact duplicates after whitespace normalisation."""
    raw = open(path, encoding='utf-8').read()
    kept, seen = [], set()
    for line in (l for l in raw.split('\n') if l.strip()):
        for s in segment(line):
            if len(s.split()) < 6 or _deva_purity(s) < 0.90:
                continue
            k = ' '.join(unicodedata.normalize('NFC', s).split())
            if k in seen:
                continue
            seen.add(k)
            kept.append(s)
    return kept


def hindi_markers():
    raw = C.load_json('data/angika_markers.json')['hin']
    return {strip_punct(w) for w in raw if strip_punct(w)}


def published_vocab(v=VOCAB_V):
    freq = collections.Counter()
    with open(C.external(HIN_FILE), encoding='utf-8') as fh:
        for line in fh:
            freq.update(tok_norm(line.strip()))
    return {w for w, _ in freq.most_common(v)}, freq


def heldout_templates(evaluated_clusters, clusters, m=TPL_M):
    tail = collections.Counter()
    kept = 0
    for sid, text in C.leipzig_sentences(C.P1_CORPUS['hin']).items():
        if clusters.get(sid) in evaluated_clusters:
            continue
        t = tok_norm(text)
        if len(t) >= 3:
            tail[tuple(t[-3:])] += 1
            kept += 1
    return {g for g, _ in tail.most_common(m)}, kept


def measure(text, markers, vocab, templates):
    t = tok(text)
    tn = tok_norm(text)
    n = len(tn) or 1
    fw = sum(1 for w in tn if w in markers)
    rare = sum(1 for w in tn if w not in vocab)
    return {
        'tokens': len(tn),
        'fw_hits': fw,
        'fw_rate': fw / n,
        'rtr': rare / n,
        'tpl': len(tn) >= 3 and tuple(tn[-3:]) in templates,
    }


def summarise(rows, label):
    n = len(rows)
    if not n:
        return {}
    ret = sum(1 for r in rows if r['retained']) / n
    return {
        'cell': label, 'n': n, 'retention': ret,
        'mean_fw_rate': sum(r['fw_rate'] for r in rows) / n,
        'mean_fw_hits': sum(r['fw_hits'] for r in rows) / n,
        'zero_fw_share': sum(1 for r in rows if r['fw_hits'] == 0) / n,
        'mean_rtr': sum(r['rtr'] for r in rows) / n,
        'tpl_share': sum(1 for r in rows if r['tpl']) / n,
        'median_tokens': sorted(r['tokens'] for r in rows)[n // 2],
    }


def by_fw(rows):
    out = {}
    for r in rows:
        k = min(r['fw_hits'], 4)
        out.setdefault(k, []).append(r)
    return {k: {'n': len(v),
                'retention': sum(1 for x in v if x['retained']) / len(v),
                'mean_tokens': sum(x['tokens'] for x in v) / len(v)}
            for k, v in sorted(out.items())}


def reweight(source, target):
    """Retention of `source` reweighted to `target`'s fw_hits distribution."""
    tgt = collections.Counter(min(r['fw_hits'], 4) for r in target)
    total = sum(tgt.values())
    src = {}
    for r in source:
        src.setdefault(min(r['fw_hits'], 4), []).append(r)
    num = den = 0.0
    for k, w in tgt.items():
        bucket = src.get(k)
        if not bucket:
            continue
        rate = sum(1 for x in bucket if x['retained']) / len(bucket)
        num += (w / total) * rate
        den += w / total
    return num / den if den else float('nan')


def main():
    markers = hindi_markers()
    vocab, freq = published_vocab()
    texts = C.panel1_texts()
    v3p1 = C.panel1_preds('v3')
    clusters = C.leipzig_clusters(C.P1_CORPUS['hin'])

    wiki_ids = [uid for (lg, ln, uid) in texts if lg == 'hin' and ln == 'L1']
    evaluated_clusters = {clusters.get(u) for u in wiki_ids}
    templates, heldout_n = heldout_templates(evaluated_clusters, clusters)
    print('held-out sentences for template derivation: %d' % heldout_n)
    print('published Hindi vocabulary: %d types, top %d retained'
          % (len(freq), len(vocab)))

    wiki = []
    for uid in wiki_ids:
        m = measure(texts[('hin', 'L1', uid)], markers, vocab, templates)
        m['retained'] = v3p1[('hin', 'L1', uid)].startswith('hin')
        m['angika'] = v3p1[('hin', 'L1', uid)] == 'anp_Deva'
        m['cluster'] = clusters.get(uid, 'unmapped:' + uid)
        wiki.append(m)

    v3p2 = C.panel2_preds('v3')
    news = []
    for r in C.panel2_rows():
        if not (r['regime'] == 'A' and r['lang'] == 'hin' and r['length'] == 'L1'):
            continue
        m = measure(r['text'], markers, vocab, templates)
        p = v3p2[('A', 'hin', 'L1', r['unit_id'])]
        m['retained'] = p.startswith('hin')
        m['angika'] = p == 'anp_Deva'
        news.append(m)

    res = {'seed': SEED, 'vocab_size': VOCAB_V, 'templates': TPL_M,
           'heldout_sentences': heldout_n,
           'published_vocab_types': len(freq),
           'cells': [summarise(wiki, 'hin_wikipedia_L1'),
                     summarise(news, 'hin_news_L1')]}

    for name, rows in (('wikipedia', wiki), ('news', news)):
        res[name + '_by_outcome'] = {
            'retained': summarise([r for r in rows if r['retained']], name + ':retained'),
            'angika': summarise([r for r in rows if r['angika']], name + ':angika'),
        }
        res[name + '_by_fw'] = by_fw(rows)
        res[name + '_tpl'] = {
            'template': summarise([r for r in rows if r['tpl']], name + ':tpl'),
            'other': summarise([r for r in rows if not r['tpl']], name + ':other'),
        }

    gap = res['cells'][1]['retention'] - res['cells'][0]['retention']
    news_at_wiki = reweight(news, wiki)
    wiki_at_news = reweight(wiki, news)
    res['decomposition'] = {
        'wikipedia_retention': res['cells'][0]['retention'],
        'news_retention': res['cells'][1]['retention'],
        'raw_gap': gap,
        'news_reweighted_to_wikipedia_fw': news_at_wiki,
        'residual_gap_after_reweight': news_at_wiki - res['cells'][0]['retention'],
        'share_of_gap_absorbed': 1 - (news_at_wiki - res['cells'][0]['retention']) / gap,
        'wikipedia_reweighted_to_news_fw': wiki_at_news,
        'residual_gap_reverse': res['cells'][1]['retention'] - wiki_at_news,
        'share_absorbed_reverse':
            1 - (res['cells'][1]['retention'] - wiki_at_news) / gap,
    }

    # Clustered interval for the Wikipedia-side template contrast
    rng = random.Random(SEED)
    byc = {}
    for r in wiki:
        byc.setdefault(r['cluster'], []).append(r)
    groups = list(byc.values())
    diffs = []
    for _ in range(REPS):
        draw = [groups[rng.randrange(len(groups))] for _ in range(len(groups))]
        units = [u for g in draw for u in g]
        a = [u for u in units if u['tpl']]
        b = [u for u in units if not u['tpl']]
        if a and b:
            diffs.append(sum(1 for x in a if x['retained']) / len(a)
                         - sum(1 for x in b if x['retained']) / len(b))
    diffs.sort()
    res['wikipedia_tpl_difference_ci'] = [
        diffs[int(0.025 * (len(diffs) - 1))], diffs[int(0.975 * (len(diffs) - 1))]]
    res['wikipedia_tpl_difference'] = (
        res['wikipedia_tpl']['template']['retention']
        - res['wikipedia_tpl']['other']['retention'])

    # The Angika side: published training file and marker-selected control
    anp_pub = training_file_sentences(C.external(ANP_FILE))
    anp_ctrl = []
    for r in C.panel2_rows():
        if r['regime'] == 'C' and r['length'] == 'L1':
            anp_ctrl.append(r['text'])

    def plain(texts_, label):
        rows = [measure(t, markers, vocab, templates) for t in texts_]
        n = len(rows)
        return {'cell': label, 'n': n,
                'mean_fw_rate': sum(r['fw_rate'] for r in rows) / n,
                'zero_fw_share': sum(1 for r in rows if r['fw_hits'] == 0) / n,
                'mean_rtr': sum(r['rtr'] for r in rows) / n,
                'tpl_share': sum(1 for r in rows if r['tpl']) / n}

    res['angika_side'] = [plain(anp_pub, 'anp_Deva published training file, filtered sentences'),
                          plain(anp_ctrl, 'marker-selected Angika control L1')]

    C.write_result('register.json', res)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == '__main__':
    main()
