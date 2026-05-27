import json
import math

COLLARS = [
    {"hole": "ACP26DD010", "northing": 4216642, "easting": 420812, "elev_m": 2250.0, "depth_m": 51.82, "azimuth": 60.0, "dip": -80.0},
    {"hole": "ACP26DD008", "northing": 4216677, "easting": 420835, "elev_m": 2252.0, "depth_m": 67.67, "azimuth": 240.0, "dip": -50.0},
    {"hole": "ACP26DD007", "northing": 4216677, "easting": 420835, "elev_m": 2252.0, "depth_m": 60.96, "azimuth": 240.0, "dip": -80.0},
    {"hole": "ACP26DD006", "northing": 4216677, "easting": 420835, "elev_m": 2252.0, "depth_m": 67.67, "azimuth": 60.0, "dip": -60.0},
    {"hole": "ACP26DD005", "northing": 4216677, "easting": 420835, "elev_m": 2252.0, "depth_m": 76.20, "azimuth": 60.0, "dip": -80.0},
    {"hole": "ACP26DD003", "northing": 4216756, "easting": 420805, "elev_m": 2259.0, "depth_m": 55.63, "azimuth": 60.0, "dip": -80.0},
    {"hole": "ACP26DD001", "northing": 4216692, "easting": 420764, "elev_m": 2255.0, "depth_m": 60.96, "azimuth": 270.0, "dip": -80.0},
]
INTERVALS = [
    {"hole": "ACP26DD010", "from_m": 25.91, "to_m": 35.94, "grade_pct": 3.10},
    {"hole": "ACP26DD010", "from_m": 29.20, "to_m": 31.82, "grade_pct": 12.54},
    {"hole": "ACP26DD010", "from_m": 30.66, "to_m": 30.97, "grade_pct": 66.47},
    {"hole": "ACP26DD008", "from_m": 40.23, "to_m": 42.37, "grade_pct": 3.02},
    {"hole": "ACP26DD007", "from_m": 35.05, "to_m": 35.81, "grade_pct": 0.18},
    {"hole": "ACP26DD006", "from_m": 44.20, "to_m": 45.11, "grade_pct": 4.03},
    {"hole": "ACP26DD005", "from_m": 31.15, "to_m": 39.62, "grade_pct": 2.67},
    {"hole": "ACP26DD005", "from_m": 36.88, "to_m": 39.08, "grade_pct": 9.69},
]
DENSITY_T_PER_M3 = 3.6
TRUE_WIDTH_FACTOR = 0.7
STRIKE_EXTENSION_M = 120.0

def vec(az, dip):
    a, d = math.radians(az), math.radians(dip)
    return (math.sin(a)*math.cos(d), math.cos(a)*math.cos(d), math.sin(d))

def pt(c, m):
    v = vec(c['azimuth'], c['dip'])
    return [c['easting'] + v[0]*m, c['northing'] + v[1]*m, c['elev_m'] + v[2]*m]

def estimate():
    rows=[]; total=0.0
    for iv in INTERVALS:
        l=iv['to_m']-iv['from_m']; tw=l*TRUE_WIDTH_FACTOR
        vol=STRIKE_EXTENSION_M*tw*tw; rock=vol*DENSITY_T_PER_M3
        sb=rock*(iv['grade_pct']/100.0); total+=sb
        rows.append({**iv,'length_m':l,'true_width_m':tw,'volume_m3':vol,'rock_tonnes':rock,'contained_sb_tonnes':sb})
    return total, rows

def holes_json():
    by={c['hole']:c for c in COLLARS}
    out=[]
    for c in COLLARS:
        out.append({'type':'hole','id':c['hole'],'start':pt(c,0.0),'end':pt(c,c['depth_m'])})
    for iv in INTERVALS:
        c=by[iv['hole']]
        out.append({'type':'interval','id':iv['hole'],'grade_pct':iv['grade_pct'],'start':pt(c,iv['from_m']),'end':pt(c,iv['to_m'])})
    return out

def html(model, total_sb):
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>3D Drillhole Model</title>
<style>body{{margin:0;font-family:Arial}}#info{{position:absolute;left:8px;top:8px;background:#ffffffdd;padding:8px}}</style></head>
<body><div id="info"><b>Little Emma Concept Model</b><br>Contained Sb (conceptual): {total_sb:,.0f} t<br>Strike target azimuth: 330°</div>
<script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
<script src="https://unpkg.com/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
<script>
const data={json.dumps(model)};
const scene=new THREE.Scene();scene.background=new THREE.Color(0xf4f6f8);
const camera=new THREE.PerspectiveCamera(60,innerWidth/innerHeight,0.1,5000);camera.position.set(180,120,180);
const renderer=new THREE.WebGLRenderer({{antialias:true}});renderer.setSize(innerWidth,innerHeight);document.body.appendChild(renderer.domElement);
const controls=new THREE.OrbitControls(camera,renderer.domElement);
scene.add(new THREE.AmbientLight(0xffffff,0.8));const dl=new THREE.DirectionalLight(0xffffff,1.2);dl.position.set(200,300,150);scene.add(dl);
let cx=0,cy=0,cz=0,c=0;for(const d of data){{cx+=d.start[0];cy+=d.start[1];cz+=d.start[2];c++;}}cx/=c;cy/=c;cz/=c;
function p(a){{return new THREE.Vector3(a[0]-cx,a[2]-cz,a[1]-cy)}}
for(const d of data){{
 const g=new THREE.BufferGeometry().setFromPoints([p(d.start),p(d.end)]);
 const col=d.type==='hole'?0x222222:(d.grade_pct>10?0xff00ff:d.grade_pct>3?0xff7f00:0x00b4ff);
 const l=new THREE.Line(g,new THREE.LineBasicMaterial({{color:col,linewidth:4}}));scene.add(l);
}}
// topography mesh (approximate reconstruction)
const terrain=new THREE.PlaneGeometry(420,420,50,50);terrain.rotateX(-Math.PI/2);
const pos=terrain.attributes.position;for(let i=0;i<pos.count;i++){{const x=pos.getX(i),z=pos.getZ(i);pos.setY(i, 8*Math.sin(x/40)*Math.cos(z/60)-0.02*z+0.015*x);}}pos.needsUpdate=true;
scene.add(new THREE.Mesh(terrain,new THREE.MeshLambertMaterial({{color:0x98b39f,transparent:true,opacity:0.45,side:THREE.DoubleSide}})));
// strike extension
const s1=new THREE.Vector3(0,-15,0), s2=new THREE.Vector3(-60,-15,104);
scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([s1,s2]),new THREE.LineBasicMaterial({{color:0xffd000}})));
function animate(){{requestAnimationFrame(animate);renderer.render(scene,camera);}}animate();
addEventListener('resize',()=>{{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);}});
</script></body></html>'''

def main():
    total, rows = estimate()
    payload = {"assumptions":{"density_t_per_m3":DENSITY_T_PER_M3,"true_width_factor":TRUE_WIDTH_FACTOR,"strike_extension_m":STRIKE_EXTENSION_M},"intervals":rows,"total_contained_sb_tonnes":total}
    open('contained_sb_estimate.json','w').write(json.dumps(payload,indent=2))
    model=holes_json()
    open('drillhole_model_3d.html','w').write(html(model,total))
    print('Generated drillhole_model_3d.html + contained_sb_estimate.json')

if __name__=='__main__':main()
