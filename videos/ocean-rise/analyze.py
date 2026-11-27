import h5py, numpy as np, json, sys
from PIL import Image, ImageDraw
d=sys.argv[1]
f=h5py.File(d+'/relief.grd'); z=f['z'][:].astype(np.float32)*f['z'].attrs.get('scale_factor',1)
z=z[::-1,:-1]  # north up, drop dup lon -> 1800x3600
H,W=z.shape; print(H,W,z.min(),z.max())
gj=json.load(open(d+'/countries.geojson'))
ids=Image.new('I',(W,H),0); dr=ImageDraw.Draw(ids)
names=[]
def px(c): return [((x+180)/360*W,(90-y)/180*H) for x,y in c]
for i,ft in enumerate(gj['features'],1):
    p=ft['properties']; names.append(p['NAME']); g=ft['geometry']
    polys=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
    for poly in polys:
        dr.polygon(px(poly[0]),fill=i)
ids=np.array(ids)
np.save(d+'/z.npy',z); np.save(d+'/ids.npy',ids.astype(np.int16))
json.dump(names,open(d+'/names.json','w'))
lat=np.linspace(90,-90,H); w=np.cos(np.radians(lat))[:,None]*np.ones((1,W))
res=[]
for i,n in enumerate(names,1):
    m=ids==i
    if m.sum()<3: continue
    zz=z[m]; ww=w[m]
    res.append((n,int(m.sum()),float(zz.max()),float(np.percentile(zz,50)),float(zz.min())))
res.sort(key=lambda r:-r[2])
for r in res[:25]: print(r)
for L in [1000,1500,2000,2500]:
    s=[r[0] for r in res if r[2]>L]; print(L,len(s))
lev=2500
print('area frac above 2500:')
out=[]
for i,n in enumerate(names,1):
    m=ids==i
    if m.sum()<3: continue
    out.append((n, float((z[m]>lev).mean())))
out.sort(key=lambda r:-r[1]); print(out[:15])
