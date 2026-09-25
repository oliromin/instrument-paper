"""Character n-gram proximity of Hindi units to the two published training files.

GlotLID is a fastText classifier, which represents text as a bag of character
n-grams, so n-gram proximity is close to the representation the model actually
uses.  The question is whether Hindi Wikipedia units sit nearer the published
Angika file than Hindi news units do, which is what an account in which the
Angika class learned a region shaped around Wikipedia-register Hindi would
predict.

The Angika file is 1.2 MB and the Hindi file 234 MB, so the Hindi side is
size-matched by character count before any counting; otherwise coverage would
be a measure of file size.  Scores are mean log probability per n-gram under
add-one smoothed unigram models over the union vocabulary, and the reported
quantity is the Angika-minus-Hindi difference: higher means nearer Angika.
"""
import collections
import json
import math
import os
import random

import common as C

SEED = 20260912
NMIN, NMAX = 3, 5
ANP_FILE = 'anp_Deva_wikipedia.txt'   # external inputs, found through INSTRUMENT_INPUTS
HIN_FILE = 'hin_Deva_leipzigwiki.txt'


def grams(text):
    t = ' ' + ' '.join(text.split()) + ' '
    for n in range(NMIN, NMAX + 1):
        for i in range(len(t) - n + 1):
            yield t[i:i + n]


def counts_from_lines(lines):
    c = collections.Counter()
    for line in lines:
        c.update(grams(line))
    return c


def main():
    anp_lines = [l.strip() for l in open(C.external(ANP_FILE), encoding='utf-8') if l.strip()]
    anp_chars = sum(len(l) for l in anp_lines)

    rng = random.Random(SEED)
    reservoir = []
    total = 0
    with open(C.external(HIN_FILE), encoding='utf-8') as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            total += 1
            if sum(len(x) for x in reservoir) < anp_chars:
                reservoir.append(s)
            else:
                j = rng.randrange(total)
                if j < len(reservoir):
                    reservoir[j] = s
    hin_chars = sum(len(l) for l in reservoir)
    print('Angika file: %d lines, %d chars' % (len(anp_lines), anp_chars))
    print('Hindi sample: %d lines, %d chars (size-matched)'
          % (len(reservoir), hin_chars))

    ca = counts_from_lines(anp_lines)
    ch = counts_from_lines(reservoir)
    vocab = set(ca) | set(ch)
    V = len(vocab)
    ta = sum(ca.values()) + V
    th = sum(ch.values()) + V
    print('n-gram types: Angika %d, Hindi %d, union %d' % (len(ca), len(ch), V))

    la = {g: math.log((ca.get(g, 0) + 1) / ta) for g in vocab}
    lh = {g: math.log((ch.get(g, 0) + 1) / th) for g in vocab}
    ua, uh = math.log(1 / ta), math.log(1 / th)

    def score(text):
        gs = list(grams(text))
        if not gs:
            return 0.0
        return sum(la.get(g, ua) - lh.get(g, uh) for g in gs) / len(gs)

    texts = C.panel1_texts()
    v3p1 = C.panel1_preds('v3')
    v3p2 = C.panel2_preds('v3')

    wiki, news = [], []
    for (lg, ln, uid), t in texts.items():
        if lg == 'hin' and ln == 'L1':
            p = v3p1[(lg, ln, uid)]
            wiki.append({'s': score(t), 'retained': p.startswith('hin'),
                         'angika': p == 'anp_Deva'})
    for r in C.panel2_rows():
        if r['regime'] == 'A' and r['lang'] == 'hin' and r['length'] == 'L1':
            p = v3p2[('A', 'hin', 'L1', r['unit_id'])]
            news.append({'s': score(r['text']), 'retained': p.startswith('hin'),
                         'angika': p == 'anp_Deva'})

    def mean(xs):
        return sum(xs) / len(xs) if xs else float('nan')

    def summ(rows, lab):
        a = [r['s'] for r in rows if r['angika']]
        k = [r['s'] for r in rows if r['retained']]
        d = {'cell': lab, 'n': len(rows), 'mean': mean([r['s'] for r in rows]),
             'mean_routed_to_angika': mean(a), 'mean_retained': mean(k),
             'within_gap': mean(a) - mean(k)}
        print('%-10s n=%4d  mean %+.4f   routed %+.4f   retained %+.4f   '
              'within-gap %+.4f' % (lab, len(rows), d['mean'],
                                    d['mean_routed_to_angika'],
                                    d['mean_retained'], d['within_gap']))
        return d

    w = summ(wiki, 'wikipedia')
    n = summ(news, 'news')
    across = w['mean'] - n['mean']
    print('\nWikipedia minus news, mean Angika-proximity: %+.4f' % across)
    print('(positive would mean Wikipedia units sit nearer the Angika file)')

    # Does proximity predict routing?  Decile check within each cell.
    def deciles(rows, lab):
        rs = sorted(rows, key=lambda r: r['s'])
        k = max(1, len(rs) // 10)
        out = []
        for i in range(0, len(rs), k):
            b = rs[i:i + k]
            if len(b) < k // 2:
                break
            out.append({'mean_score': mean([x['s'] for x in b]),
                        'retention': sum(1 for x in b if x['retained']) / len(b),
                        'n': len(b)})
        print('\n%s retention by Angika-proximity decile (low to high):' % lab)
        print('  ' + '  '.join('%.3f' % o['retention'] for o in out))
        return out

    res = {'seed': SEED, 'ngram_range': [NMIN, NMAX],
           'angika_chars': anp_chars, 'hindi_sample_chars': hin_chars,
           'angika_types': len(ca), 'hindi_types': len(ch),
           'vocab': V, 'wikipedia': w, 'news': n,
           'wikipedia_minus_news': across,
           'wikipedia_deciles': deciles(wiki, 'wikipedia'),
           'news_deciles': deciles(news, 'news')}

    C.write_result('ngram.json', res)


if __name__ == '__main__':
    main()
