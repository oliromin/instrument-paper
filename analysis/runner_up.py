"""Runner-up labels and score margins for GlotLID v3 on the Hindi Panel 1 cells.

For each Hindi unit the stored top-five scores (data/confidence_scores_v3.csv)
give the runner-up label and the margin between the first and second scores.
Reported separately for units assigned to Angika and units retained as Hindi,
at one sentence (L1) and five sampled sentences (L5).  Writes
results/runner_up.json.
"""
import collections
import json
import statistics

import common as C


def main():
    rows = C.read_csv('confidence_scores_v3.csv')
    out = {}
    for length in ('L1', 'L5'):
        cell = [r for r in rows if r['length'] == length]
        for r in cell:
            r['top'] = json.loads(r['top5'])
            r['hin'] = float(r['hin_score_in_top5']) if r['hin_score_in_top5'] else 0.0
        ang = [r for r in cell if r['pred'] == 'anp_Deva']
        ret = [r for r in cell if r['pred'] == 'hin_Deva']
        second = [r['top'][1] for r in ang]
        margin = [r['top'][0][0] - r['top'][1][0] for r in ang]
        hs = [r['hin'] for r in ang]
        out[length] = {
            'n_angika': len(ang),
            'n_hindi': len(ret),
            'runnerup_top': collections.Counter(l for _, l in second).most_common(4),
            'runnerup_is_hindi_share': sum(l == 'hin_Deva' for _, l in second) / len(ang),
            'margin_median': statistics.median(margin),
            'margin_mean': statistics.mean(margin),
            'runnerup_median': statistics.median(p for p, _ in second),
            'runnerup_mean': statistics.mean(p for p, _ in second),
            'runnerup_max': max(p for p, _ in second),
            'hindi_score_median': statistics.median(hs),
            'hindi_score_mean': statistics.mean(hs),
            'hindi_score_max': max(hs),
            'share_hindi_ge_0.10': sum(h >= 0.10 for h in hs) / len(ang),
            'share_hindi_ge_0.40': sum(h >= 0.40 for h in hs) / len(ang),
            'share_margin_gt_0.5': sum(m > 0.5 for m in margin) / len(ang),
            'margin_median_retained': statistics.median(r['top'][0][0] - r['top'][1][0] for r in ret),
            'runnerup_top_retained': collections.Counter(r['top'][1][1] for r in ret).most_common(4),
        }
    C.write_result('runner_up.json', out)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
