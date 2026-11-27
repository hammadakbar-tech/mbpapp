import numpy as np, json, sys, io, urllib.request, time
from PIL import Image, ImageDraw
d=sys.argv[1]
fl=np.load(d+'/fl.npy'); z=np.load(d+'/z.npy'); ids=np.load(d+'/ids.npy')
fl=np.where(np.isfinite(fl)&(fl<1e5),fl,z)          # above flood range: floods at own height
H,W=fl.shape; wl=np.cos(np.radians(np.linspace(90,-90,H)))
gj=json.load(open(d+'/countries.geojson')); S=json.load(open(d+'/sink.json'))
def wmed(v,w):
    o=np.argsort(v); c=np.cumsum(w[o])/w.sum(); return float(v[o][np.searchsorted(c,0.5)])
def fetch(lo0,la0,lo1,la1):
    u=("https://coastwatch.pfeg.noaa.gov/erddap/griddap/etopo180.csv?altitude%5B({}):1:({})%5D%5B({}):1:({})%5D"
       .format(la0,la1,lo0,lo1))
    for k in range(2):
        try: raw=urllib.request.urlopen(u,timeout=120).read().decode(); break
        except Exception as e: print('retry',e); time.sleep(3)
    else: return None
    a=np.loadtxt(io.StringIO(raw),delimiter=',',skiprows=2)
    return a
def work(s):
    if s['npx']>=4:
        m=ids==s['i']; r,c=np.nonzero(m); s['half']=max(wmed(fl[r,c],wl[r]),0.5)
    ft=gj['features'][s['i']-1]
    if s['npx']>=150 and s['half']>1: return
    g=ft['geometry']; polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
    polys=sorted(polys,key=lambda p:-len(p[0]))[:25]
    vals=[];ws=[]
    for p in polys:
        a=np.array(p[0]); lo0,la0=a.min(0)-0.03; lo1,la1=a.max(0)+0.03
        lo0=max(lo0,-180);lo1=min(lo1,180);la0=max(la0,-90);la1=min(la1,90)
        if (lo1-lo0)*(la1-la0)>25: continue
        arr=fetch(round(lo0,3),round(la0,3),round(lo1,3),round(la1,3))
        if arr is None or arr.ndim<2: continue
        lats=np.unique(arr[:,0]); lons=np.unique(arr[:,1])
        grid=arr[:,2].reshape(len(lats),len(lons))
        im=Image.new('L',(len(lons),len(lats)),0); dr=ImageDraw.Draw(im)
        px=[((x-lons[0])/(lons[-1]-lons[0]+1e-9)*(len(lons)-1),(y-lats[0])/(lats[-1]-lats[0]+1e-9)*(len(lats)-1)) for x,y in p[0]]
        dr.polygon(px,fill=1,outline=1); mk=np.array(im).astype(bool)&(grid>0)
        vals.append(grid[mk]); ws.append(np.full(mk.sum(),np.cos(np.radians(lats.mean()))))
    if vals and sum(len(v) for v in vals)>0:
        v=np.concatenate(vals); w=np.concatenate(ws)
        old=s['half']; s['half']=max(wmed(v,w),0.5); s['top']=float(v.max()); s['hires']=True
        print(f"{s['name']:22s} grid={old} hires={s['half']:.0f} top={s['top']:.0f} n={len(v)}",flush=True)
    elif s['half'] is None:
        print('NO DATA',s['name'])
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(12) as ex: list(ex.map(work,S))
json.dump(S,open(d+'/sink2.json','w'))
