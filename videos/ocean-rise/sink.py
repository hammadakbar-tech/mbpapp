import numpy as np, json, sys
d=sys.argv[1]
fl=np.load(d+'/fl.npy'); fl[~np.isfinite(fl)]=1e5; ids=np.load(d+'/ids.npy'); z=np.load(d+'/z.npy')
H,W=fl.shape; lat=np.linspace(90,-90,H); wl=np.cos(np.radians(lat))
cs=json.load(open(d+'/countries.json')); gj=json.load(open(d+'/countries.geojson'))
out=[]
for c,ft in zip(cs,gj['features']):
    p=ft['properties']
    if c['type'] not in ('Sovereign country','Country','Sovereignty'): continue
    m=ids==c['i']; r,cc=np.nonzero(m)
    if len(r)<4:
        out.append(dict(name=c['name'],iso=p['ISO_A2_EH'].lower(),npx=len(r),half=None,lx=c['lx'],ly=c['ly'],pop=p['POP_EST'],i=c['i'])); continue
    v=fl[r,cc]; w=wl[r]; o=np.argsort(v); cw=np.cumsum(w[o])/w.sum()
    half=float(v[o][np.searchsorted(cw,0.5)])
    out.append(dict(name=c['name'],iso=p['ISO_A2_EH'].lower(),npx=len(r),half=max(half,0.5),top=float(z[r,cc].max()),lx=c['lx'],ly=c['ly'],pop=p['POP_EST'],i=c['i'],
        bbox=[float(c2) for c2 in (cc.min()/10-180,90-r.min()/10,cc.max()/10-180,90-r.max()/10)]))
json.dump(out,open(d+'/sink.json','w'))
ok=sorted([o for o in out if o['half'] is not None],key=lambda o:o['half'])
print(len(out),len(ok),'small:',[ (o['name'],o['npx']) for o in out if o['half'] is None])
for o in ok: print(f"{o['half']:7.0f} {o['name']}({o['iso']})", end=' |')
