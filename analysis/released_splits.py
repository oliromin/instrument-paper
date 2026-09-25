"""Released-split readings: assignment rates of the Angika- and Awadhi-labelled
FineWeb-2 partitions and of their marker-selected and ILI references, and the
deterministic length-bin comparison.

Reads data/released_split_predictions_<model>.csv.gz (unit, population, arm,
source cluster, prediction, character and token length).  No text is needed.
Writes results/released_split_analysis.json.
"""
import collections

import numpy as np

import common as C
from panels import ratio_boot, ci


def read(t):
    rows = C.read_csv('released_split_predictions_%s.csv' % t)
    for r in rows:
        r['chars'] = int(r['chars'])
        r['tokens'] = int(r['tokens'])
        r['cluster'] = r['cluster'] or None
    return rows


def masks(a,edges):
    x=np.array([r['chars'] for r in a])
    return [(x>=lo)&((x<hi) if i<len(edges)-2 else (x<=hi)) for i,(lo,hi) in enumerate(zip(edges[:-1],edges[1:]))]
def bins(a,b):
    qa=np.quantile([r['chars'] for r in a],[.05,.95]);qb=np.quantile([r['chars'] for r in b],[.05,.95]);lo=max(qa[0],qb[0]);hi=min(qa[1],qb[1])
    if hi<=lo:return {'edges':[],'reason':'No 5th--95th percentile common support'}
    edges=np.exp(np.linspace(np.log(lo),np.log(hi),7));edges[0]=lo;edges[-1]=hi
    edges=list(edges)
    def sufficient(rr,m):
        sel=[r for r,k in zip(rr,m) if k]
        if len(sel)<50:return False
        return any(r['cluster'] is None for r in sel) or len({r['cluster'] for r in sel})>=30
    while len(edges)>2:
        ma,mb=masks(a,edges),masks(b,edges)
        deficient=[i for i,(m,n) in enumerate(zip(ma,mb)) if not (sufficient(a,m) and sufficient(b,n))]
        if not deficient:break
        i=deficient[0];nb=len(edges)-1
        if i==0:delete=1
        elif i==nb-1:delete=i
        elif i+0.5<=nb/2:delete=i
        else:delete=i+1
        del edges[delete]
    return {'edges':edges,'initial_bins':6,'retained_bins':len(edges)-1,'coverage_a':float(np.mean([(lo<=r['chars']<=hi) for r in a])),'coverage_b':float(np.mean([(lo<=r['chars']<=hi) for r in b])),'length_quantiles_a':[float(x) for x in qa],'length_quantiles_b':[float(x) for x in qb],'resolution_adequate':len(edges)-1>=3}
def main():
    pred={t:read(t) for t in ['v1','v2','openlid']}
    aggregate={}
    for t,rows in pred.items():
        groups=collections.defaultdict(list)
        for r in rows:groups[(r['population'],r['arm'])].append(r)
        for (pop,arm),rr in groups.items():
            c=collections.Counter(r['pred'] for r in rr);n=len(rr)
            st={'n':n,'to_hindi':sum(v for p,v in c.items() if p.split('_')[0] in ['hin','hi'])/n,'to_awadhi':sum(v for p,v in c.items() if p.split('_')[0]=='awa')/n,'destinations':dict(c),'median_chars':float(np.median([r['chars'] for r in rr]))}
            if pop=='angika':
                bb,g=ratio_boot([r['cluster'] for r in rr],[r['pred'].split('_')[0]=='hin' for r in rr]);st['clusters']=g;st['conditional_ci']=ci(bb[:,0])
            aggregate[t+'|'+pop+'|'+arm]=st
    curves={}
    for arm in ['sentence','document']:
        pa=[r for r in pred['v1'] if r['population']=='angika' and r['arm']==arm]
        pb=[r for r in pred['v1'] if r['population']=='anp_split' and r['arm']==arm]
        design=bins(pa,pb);rrout=[]
        for i,(lo,hi) in enumerate(zip(design['edges'][:-1],design['edges'][1:])):
            cell={'lo':lo,'hi':hi,'models':{}}
            for t in ['v1','v2']:
                groups=[];boots=[]
                for pop in ['angika','anp_split']:
                    rr=[r for r in pred[t] if r['population']==pop and r['arm']==arm and r['chars']>=lo and (r['chars']<hi or (i==len(design['edges'])-2 and r['chars']<=hi))]
                    val=np.array([r['pred'].split('_')[0]=='hin' for r in rr]);cl=[r['cluster'] for r in rr]
                    bb,g=ratio_boot(cl,val)
                    groups.append({'n':len(rr),'clusters':g,'rate':float(val.mean()),'conditional_ci':ci(bb[:,0])});boots.append(bb[:,0])
                cell['models'][t]={'control':groups[0],'split':groups[1],'gap':groups[1]['rate']-groups[0]['rate'],'gap_pointwise_ci':ci(boots[1]-boots[0])}
            rrout.append(cell)
        curves[arm]={'design':design,'bins':rrout,'interval_scope':'pointwise conditional article-resampling sensitivity; support held fixed'}
        print('Angika',arm,design,'gaps',[[x['models'][t]['gap'] for x in rrout] for t in ['v1','v2']],flush=True)
    awalen={}
    for ili in ['vardial2018/train','vardial2018/dev','vardial2018/test']:
        pa=[r for r in pred['v1'] if r['population']==ili]
        pb=[r for r in pred['v1'] if r['population']=='awa_split' and r['arm']=='sentence']
        design=bins(pa,pb);bo=[]
        for i,(lo,hi) in enumerate(zip(design['edges'][:-1],design['edges'][1:])):
            row={'lo':lo,'hi':hi,'models':{}}
            for t in pred:
                st={}
                for pop in [ili,'awa_split']:
                    rr=[r for r in pred[t] if r['population']==pop and r['arm']=='sentence' and r['chars']>=lo and (r['chars']<hi or (i==len(design['edges'])-2 and r['chars']<=hi))]
                    st['anchor' if pop==ili else 'split']={'n':len(rr),'to_hindi':sum(r['pred'].split('_')[0]=='hin' for r in rr)/len(rr),'to_awadhi':sum(r['pred'].split('_')[0]=='awa' for r in rr)/len(rr)}
                row['models'][t]=st
            bo.append(row)
        awalen[ili]={'design':design,'bins':bo,'cluster_limit':'ILI parent documents unavailable; descriptive bins only'}
    result={'aggregate':aggregate,'angika_length':curves,'awadhi_length':awalen}
    C.write_result('released_split_analysis.json', result, indent=2)
    print('Released-split analysis saved',flush=True)
if __name__=='__main__':main()
