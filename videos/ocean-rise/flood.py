import numpy as np, json, sys, time
from scipy import ndimage
d=sys.argv[1]
z=np.load(d+'/z.npy'); ids=np.load(d+'/ids.npy'); names=json.load(open(d+'/names.json'))
H,W=z.shape
levels=np.concatenate([np.arange(0,300,1),np.arange(300,1000,5),np.arange(1000,2801,10)]).astype(np.float32)
fl=np.full(z.shape,np.inf,np.float32)
seed=z<-1000
t=time.time()
for L in levels:
    m=(z<L)&~np.isfinite(fl) | np.isfinite(fl)
    lab,n=ndimage.label(m)
    keep=np.unique(lab[seed]); keep=keep[keep>0]
    flooded=np.isin(lab,keep)
    new=flooded&~np.isfinite(fl)
    fl[new]=np.maximum(z[new],L-(levels[1]-levels[0]) if L<300 else z[new])  # approx
    fl[new]=np.minimum(fl[new],L)
print('flood',time.time()-t)
np.save(d+'/fl.npy',fl)
g=json.load(open(d+'/countries.geojson'))
out=[]
for i,ft in enumerate(g['features'],1):
    p=ft['properties']; m=ids==i
    if m.sum()>0: e=float(fl[m].max()); npx=int(m.sum())
    else:
        x,y=p['LABEL_X'],p['LABEL_Y']; r=int((90-y)/180*H); c=int((x+180)/360*W)%W
        e=float(fl[r-1:r+2,c-1:c+2].max()); npx=0
    out.append(dict(i=i,name=p['NAME'],type=p['TYPE'],elim=e,npx=npx,lx=p['LABEL_X'],ly=p['LABEL_Y'],pop=p['POP_EST']))
json.dump(out,open(d+'/countries.json','w'),indent=0)
sov=[o for o in out if o['type'] in('Sovereign country','Country','Sovereignty')]
print(len(sov),'sov; elim<=0:',[o['name'] for o in sov if o['elim']<=0])
for L in [1,10,50,100,200,500,1000,1500,2000,2500]: print(L,sum(o['elim']>L for o in sov))
