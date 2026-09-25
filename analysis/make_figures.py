"""Regenerate every figure of the paper from the results files.

Writes paper/figures/*.pdf, or to the folder given as the first argument.
Values come from results/panel_analysis.json, released_split_analysis.json and
nested_reader_analysis.json, and from data/confidence_scores_v3.csv.  The
figures are set in a Times-like serif (Times New Roman, else Liberation Serif
or TeX Gyre Termes) with TrueType embedding; on a system without those faces
the text renders in a substitute, the plotted values do not change.
"""
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

import common as C

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(C.ROOT, 'paper', 'figures')
P = C.load_json('results/panel_analysis.json')
A = C.load_json('results/released_split_analysis.json')
D = C.load_json('results/nested_reader_analysis.json')
NAMES = {'v1': 'GlotLID v1', 'v2': 'GlotLID v2', 'v3': 'GlotLID v3', 'langid': 'langid.py', 'lid176': 'lid.176',
         'cld3': 'CLD3', 'openlid': 'OpenLID'}
LANG = {'hin': 'Hindi', 'nep': 'Nepali', 'mar': 'Marathi', 'san': 'Sanskrit', 'new': 'Newari', 'mai': 'Maithili'}
COL = {'v1': '#356b82', 'v2': '#b27a24', 'v3': '#b64238'}
SERIF = ['Times New Roman', 'Liberation Serif', 'TeX Gyre Termes', 'DejaVu Serif']


def cell(source, lang, length):
    return next(v for k, v in P['cells'].items() if source in k and k.split('|')[3] == lang and k.endswith('|' + length))


def path(name):
    os.makedirs(OUT, exist_ok=True)
    return os.path.join(OUT, name)


def base_style():
    plt.rcdefaults()
    plt.rcParams.update({'font.family': 'serif', 'font.serif': SERIF, 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.labelsize': 10, 'legend.fontsize': 9, 'pdf.fonttype': 42,
                         'savefig.bbox': 'tight'})


def source_length():
    """Hindi retention by release, source and unit length."""
    base_style()
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.05), sharey=True)
    for ax, source in zip(axs, ['wikipedia', 'news']):
        for t in ['v1', 'v2', 'v3']:
            cs = [cell(source, 'hin', l)['statistics'][t]['retention'] for l in ['L1', 'L5', 'L20']]
            ys = [c['value'] for c in cs]
            err = np.array([[y - c['ci'][0], c['ci'][1] - y] for y, c in zip(ys, cs)]).T
            ax.errorbar([1, 5, 20], ys, yerr=err, marker='o', ms=4, lw=1.5, capsize=3, label=NAMES[t], color=COL[t])
        ax.set_xscale('log')
        ax.set_xticks([1, 5, 20], ['1', '5', '20'])
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xlabel('Sampled sentences per unit')
        ax.set_title(source.title(), loc='left', fontweight='bold')
        ax.set_ylim(.42, 1.025)
        ax.grid(axis='y', alpha=.18)
    axs[0].set_ylabel('Hindi retention')
    axs[1].legend(loc='lower right', frameon=False)
    fig.tight_layout()
    fig.savefig(path('source_length.pdf'))
    plt.close(fig)


def angika_length():
    """Matched Angika sentence profiles; document support cannot sustain a curve."""
    base_style()
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.1), sharey=True)
    for ax, t in zip(axs, ['v1', 'v2']):
        for pop, color, label in [('split', '#b64238', 'Released anp_Deva sentences'),
                                  ('control', '#356b82', 'Angika-marked sentences')]:
            bins_ = A['angika_length']['sentence']['bins']
            xs = [np.sqrt(b['lo'] * b['hi']) for b in bins_]
            ys = [b['models'][t][pop]['rate'] for b in bins_]
            er = np.array([[y - b['models'][t][pop]['conditional_ci'][0], b['models'][t][pop]['conditional_ci'][1] - y]
                           for y, b in zip(ys, bins_)]).T
            ax.errorbar(xs, ys, yerr=er, marker='o', ms=4, lw=1.3, capsize=3, color=color, label=label)
        ax.set_xscale('log')
        ax.set_xticks([35, 50, 75, 100, 150], ['35', '50', '75', '100', '150'])
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xlabel('Unit length in characters (log scale)')
        ax.set_title(NAMES[t], loc='left', fontweight='bold')
        ax.set_ylim(-.035, 1.045)
        ax.grid(axis='y', alpha=.18)
    axs[0].set_ylabel('Share assigned to Hindi')
    axs[0].legend(loc='center right', frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path('angika_length.pdf'))
    plt.close(fig)


def retention_composition():
    """Hindi retention against the Hindi share of the Hindi-labelled bucket."""
    base_style()
    fig, ax = plt.subplots(figsize=(7.3, 3.4))
    offset = {'v1': (-30, -25), 'v2': (-35, 10), 'v3': (10, -12), 'cld3': (-38, -17), 'lid176': (-45, 8),
              'langid': (-46, 6), 'openlid': (9, -8)}
    for t in ['langid', 'lid176', 'cld3', 'openlid', 'v1', 'v2', 'v3']:
        x = cell('wikipedia', 'hin', 'L1')['statistics'][t]['retention']
        y = P['hindi_buckets'][t + '|L1']
        color = COL.get(t, '#687e84')
        ax.errorbar(x['value'], y['value'], xerr=[[x['value'] - x['ci'][0]], [x['ci'][1] - x['value']]],
                    yerr=[[y['value'] - y['ci'][0]], [y['ci'][1] - y['value']]], fmt='o', ms=5, capsize=2, color=color)
        ax.annotate(NAMES[t], (x['value'], y['value']), xytext=offset[t], textcoords='offset points', fontsize=9, color=color)
    ax.set_xlim(.43, 1.03)
    ax.set_ylim(.57, 1.06)
    ax.set_xlabel('Hindi retention')
    ax.set_ylabel('Hindi share of Hindi-labelled panel units')
    ax.grid(alpha=.15)
    fig.tight_layout()
    fig.savefig(path('retention_composition.pdf'))
    plt.close(fig)


def confidence_survival():
    """The confidence-survival function of the Hindi units, by assigned label."""
    base_style()
    conf = C.read_csv('confidence_scores_v3.csv')
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.0), sharey=True)
    for ax, le in zip(axs, ['L1', 'L5']):
        for label, color, title in [('anp_Deva', '#b64238', 'Assigned to Angika'), ('hin_Deva', '#356b82', 'Retained as Hindi')]:
            scores = np.array([float(r['score']) for r in conf if r['length'] == le and r['pred'] == label])
            xs = np.unique(np.r_[.3, scores[(scores > .3) & (scores < .9)], .9])
            ys = [(scores >= x).mean() for x in xs]
            ax.plot(xs, ys, color=color, lw=1.6, label=title)
            ax.plot(.9, ys[-1], 'o', color=color, ms=4)
        ax.set_xlabel('Confidence threshold')
        ax.set_title('One sentence' if le == 'L1' else 'Five sampled sentences', loc='left', fontweight='bold')
        ax.set_xlim(.3, .912)
        ax.set_ylim(.19, 1.03)
        ax.grid(axis='y', alpha=.18)
    axs[0].set_ylabel('Fraction passing the confidence threshold')
    axs[0].legend(loc='lower left', frameon=False)
    fig.tight_layout()
    fig.savefig(path('confidence_survival.pdf'))
    plt.close(fig)


def fmt(v):
    return str(Decimal(str(v)).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP))


def release_controls():
    """Panel 1 L1 retention across the three GlotLID releases: all six cells,
    and the five controls enlarged with their own markers and direct labels."""
    plt.rcdefaults()
    ink, muted = '#1f1f1e', '#6b6a64'
    style = {'nep': ('#2a78d6', 'o', '-'), 'mar': ('#eb6834', 's', '--'), 'san': ('#1baf7a', '^', '-.'),
             'new': ('#eda100', 'D', ':'), 'mai': ('#e87ba4', 'v', (0, (5, 1, 1, 1)))}
    V = {lg: [cell('wikipedia', lg, 'L1')['statistics'][t]['retention']['value'] for t in ('v1', 'v2', 'v3')]
         for lg in LANG}
    x = [0, 1, 2]
    plt.rcParams.update({'font.family': 'serif', 'font.serif': SERIF, 'pdf.fonttype': 42, 'font.size': 8.5,
                         'axes.edgecolor': muted, 'axes.labelcolor': ink, 'xtick.color': ink, 'ytick.color': ink})
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.3, 3.2), gridspec_kw={'width_ratios': [1, 1.25]})
    for lg, (c, m, ls) in style.items():
        a.plot(x, V[lg], color=c, marker=m, ls=ls, lw=1.2, ms=5, alpha=.9, label=LANG[lg])
    a.plot(x, V['hin'], color=ink, marker='o', lw=2.4, ms=6, label='Hindi', zorder=5)
    for i, y in list(enumerate(V['hin']))[1:]:
        a.annotate(fmt(y), (x[i], y), textcoords='offset points', xytext=(-8, -11) if i < 2 else (-9, 0),
                   ha='right' if i == 2 else 'center', va='center', color=ink, fontsize=7.5)
    a.set_ylim(.43, 1.03)
    a.set_ylabel('Retention on Wikipedia sentences (L1)')
    a.set_title('All six reference cells', loc='left', fontsize=8.5, color=ink)
    a.axhspan(.955, 1.0, color='#e9e8e2', zorder=0)
    a.text(2.05, .93, 'enlarged\nat right', fontsize=7, color=muted, va='top', ha='right')
    for lg, (c, m, ls) in style.items():
        b.plot(x, V[lg], color=c, marker=m, ls=ls, lw=1.4, ms=6, label=LANG[lg])
    ends = sorted(style, key=lambda lg: V[lg][2])
    ys, gap = [], 0.0023
    for lg in ends:
        y = V[lg][2]
        if ys and y - ys[-1] < gap:
            y = ys[-1] + gap
        ys.append(y)
    for lg, y in zip(ends, ys):
        b.annotate(LANG[lg], (2, V[lg][2]), xytext=(2.12, y), textcoords='data', va='center', fontsize=7.5, color=ink)
    b.set_ylim(.955, 1.0)
    b.set_xlim(-.15, 2.55)
    b.set_title('Five controls, enlarged (0.955 to 1.000)', loc='left', fontsize=8.5, color=ink)
    for ax in (a, b):
        ax.set_xticks(x, ['GlotLID v1', 'GlotLID v2', 'GlotLID v3'])
        ax.grid(axis='y', alpha=.25)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)
    handles, labels = a.get_legend_handles_labels()
    order = [labels.index(n) for n in ['Hindi', 'Nepali', 'Marathi', 'Sanskrit', 'Newari', 'Maithili']]
    fig.legend([handles[i] for i in order], [labels[i] for i in order], ncol=6, frameon=False, loc='lower center',
               bbox_to_anchor=(.5, -.01), fontsize=7.5)
    fig.tight_layout(rect=(0, .07, 1, 1))
    fig.savefig(path('release_controls.pdf'))
    plt.close(fig)


def nested_retention():
    """Hindi retention on nested sampled-source units."""
    plt.rcdefaults()
    plt.rcParams.update({'font.family': 'serif', 'font.serif': SERIF, 'font.size': 8, 'axes.spines.top': False,
                         'axes.spines.right': False, 'pdf.fonttype': 42})
    fig, axes = plt.subplots(1, 2, figsize=(6.1, 2.65), sharey=True)
    for ax, source in zip(axes, ['Wikipedia', 'News']):
        for t, col, mk in [('v1', '#246d88', 'o'), ('v2', '#b97915', 's'), ('v3', '#c33a32', '^')]:
            x = D['nested'][t + '|' + source]
            rr = [x['lengths'][le] for le in ['L1', 'L5', 'L20']]
            val = np.array([r['rate'] for r in rr])
            cis = np.array([r['ci'] for r in rr])
            ax.errorbar([1, 5, 20], val, yerr=np.maximum(0, np.array([val - cis[:, 0], cis[:, 1] - val])),
                        fmt=mk + '-', markersize=3.5, lw=1, label=NAMES[t], color=col, capsize=2)
        ax.set_title('{} (n = {:,})'.format(source, x['n']), loc='left', fontweight='bold')
        ax.set_xticks([1, 5, 20])
        ax.set_ylim(.4, 1.025)
        ax.grid(axis='y', alpha=.18)
        ax.set_xlabel('Sampled sentences from the same source')
    axes[0].set_ylabel('Hindi retention')
    axes[1].legend(frameon=False, loc='lower right', fontsize=7)
    fig.tight_layout()
    fig.savefig(path('nested_retention.pdf'), bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    for f in (release_controls, source_length, retention_composition, confidence_survival, angika_length, nested_retention):
        f()
    print('figures written to', OUT)
