import json
import math
from typing import Dict, List, Tuple

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
SECTION_AZIMUTH_DEG = 330.0


def unit_vec(azimuth_deg: float, dip_deg: float) -> Tuple[float, float, float]:
    az, dip = math.radians(azimuth_deg), math.radians(dip_deg)
    return (
        math.sin(az) * math.cos(dip),
        math.cos(az) * math.cos(dip),
        math.sin(dip),
    )


def point_at_depth(collar: Dict, depth_m: float) -> List[float]:
    ex, nx, uz = unit_vec(collar["azimuth"], collar["dip"])
    return [
        collar["easting"] + ex * depth_m,
        collar["northing"] + nx * depth_m,
        collar["elev_m"] + uz * depth_m,
    ]


def grade_color(grade_pct: float) -> str:
    if grade_pct >= 20:
        return "#ff00ff"
    if grade_pct >= 10:
        return "#ff4d00"
    if grade_pct >= 5:
        return "#ff9a00"
    if grade_pct >= 1:
        return "#00c8ff"
    return "#4d7cff"


def terrain(e0: float, n0: float, span: float = 300.0, steps: int = 26):
    tris = []
    for i in range(steps):
        for j in range(steps):
            e1 = e0 - span / 2 + span * (i / steps)
            e2 = e0 - span / 2 + span * ((i + 1) / steps)
            n1 = n0 - span / 2 + span * (j / steps)
            n2 = n0 - span / 2 + span * ((j + 1) / steps)

            def zf(e, n):
                return 2240 + 0.06 * (e - e0) - 0.08 * (n - n0) + 6 * math.sin((e - e0) / 40) * math.cos((n - n0) / 55)

            p11 = [e1, n1, zf(e1, n1)]
            p21 = [e2, n1, zf(e2, n1)]
            p12 = [e1, n2, zf(e1, n2)]
            p22 = [e2, n2, zf(e2, n2)]
            tris.append([p11, p21, p22])
            tris.append([p11, p22, p12])
    return tris


def build_payload():
    by_hole = {c["hole"]: c for c in COLLARS}

    hole_lines = []
    for c in COLLARS:
        points = [point_at_depth(c, d) for d in [i * c["depth_m"] / 60 for i in range(61)]]
        hole_lines.append({"id": c["hole"], "type": "hole", "color": "#202020", "width": 2.3, "points": points, "meta": c})

    interval_lines, rows = [], []
    total_sb = 0.0
    for iv in INTERVALS:
        c = by_hole[iv["hole"]]
        a, b = point_at_depth(c, iv["from_m"]), point_at_depth(c, iv["to_m"])
        length = iv["to_m"] - iv["from_m"]
        true_width = length * TRUE_WIDTH_FACTOR
        volume = STRIKE_EXTENSION_M * true_width * true_width
        rock_tonnes = volume * DENSITY_T_PER_M3
        sb_tonnes = rock_tonnes * (iv["grade_pct"] / 100)
        total_sb += sb_tonnes
        rows.append({**iv, "length_m": length, "true_width_m": true_width, "volume_m3": volume, "rock_tonnes": rock_tonnes, "contained_sb_tonnes": sb_tonnes})
        interval_lines.append({"id": iv["hole"], "type": "interval", "color": grade_color(iv["grade_pct"]), "width": 4.8, "grade": iv["grade_pct"], "points": [a, b], "meta": iv})

    e_mean = sum(c["easting"] for c in COLLARS) / len(COLLARS)
    n_mean = sum(c["northing"] for c in COLLARS) / len(COLLARS)
    z_mean = sum(c["elev_m"] for c in COLLARS) / len(COLLARS)
    strike_vec = unit_vec(SECTION_AZIMUTH_DEG, 0)
    strike_line = {
        "id": "strike_extension",
        "type": "strike",
        "color": "#ffd100",
        "width": 3.5,
        "points": [
            [e_mean, n_mean, z_mean - 22],
            [e_mean + strike_vec[0] * STRIKE_EXTENSION_M, n_mean + strike_vec[1] * STRIKE_EXTENSION_M, z_mean - 22],
        ],
    }

    return {
        "center": [e_mean, n_mean, z_mean],
        "holes": hole_lines,
        "intervals": interval_lines,
        "strike": strike_line,
        "terrain_triangles": terrain(e_mean, n_mean),
        "contained_sb": {
            "assumptions": {
                "density_t_per_m3": DENSITY_T_PER_M3,
                "true_width_factor": TRUE_WIDTH_FACTOR,
                "strike_extension_m": STRIKE_EXTENSION_M,
            },
            "intervals": rows,
            "total_contained_sb_tonnes": total_sb,
        },
    }


def html(payload: Dict) -> str:
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Little Emma 3D Drill Model</title>
<style>
html,body{{margin:0;height:100%;overflow:hidden;font-family:Segoe UI,Arial,sans-serif;background:#eef2f5;color:#0e1b2a}}
#c{{display:block;width:100vw;height:100vh}}
#hud{{position:fixed;left:10px;top:10px;background:#ffffffee;border:1px solid #cdd6df;border-radius:10px;padding:10px 12px;max-width:420px;line-height:1.35}}
#controls{{margin-top:8px;display:grid;grid-template-columns:1fr 1fr;gap:4px}}
button{{padding:6px 8px;border:1px solid #9fb0bf;border-radius:6px;background:#f7fbff;cursor:pointer}}
.small{{font-size:12px;color:#3b4c5f}}
</style></head>
<body>
<canvas id='c'></canvas>
<div id='hud'>
  <div><b>Little Emma – Offline 3D Drillhole Model</b></div>
  <div>Contained Sb (conceptual): <b>{payload['contained_sb']['total_contained_sb_tonnes']:,.1f} t</b></div>
  <div>Strike azimuth: <b>{SECTION_AZIMUTH_DEG:.0f}°</b> | Density: <b>{DENSITY_T_PER_M3} t/m³</b></div>
  <div class='small'>Mouse: drag rotate · wheel zoom · right-drag pan. Fully offline (no CDN dependencies).</div>
  <div id='controls'>
    <button onclick='state.autorotate=!state.autorotate'>Toggle auto-rotate</button>
    <button onclick='resetView()'>Reset view</button>
    <button onclick='state.showTerrain=!state.showTerrain'>Toggle terrain</button>
    <button onclick='state.showIntervals=!state.showIntervals'>Toggle intervals</button>
  </div>
</div>
<script>
const data={json.dumps(payload)};
const canvas=document.getElementById('c');const ctx=canvas.getContext('2d');
const state={{yaw:0.9,pitch:-0.55,zoom:5.3,panX:0,panY:0,autorotate:true,showTerrain:true,showIntervals:true}};
const center={{x:data.center[0],y:data.center[1],z:data.center[2]}};
function resetView(){{state.yaw=0.9;state.pitch=-0.55;state.zoom=5.3;state.panX=0;state.panY=0;}}
function sub(p){{return [p[0]-center.x,p[1]-center.y,p[2]-center.z];}}
function rot(v){{
  const cy=Math.cos(state.yaw), sy=Math.sin(state.yaw), cp=Math.cos(state.pitch), sp=Math.sin(state.pitch);
  let x=v[0]*cy-v[1]*sy, y=v[0]*sy+v[1]*cy, z=v[2];
  let y2=y*cp-z*sp, z2=y*sp+z*cp; return [x,y2,z2];
}}
function project(v){{const d=520/(state.zoom+v[1]+620); return [v[0]*d+canvas.width*0.5+state.panX,-v[2]*d+canvas.height*0.52+state.panY,d,v[1]];}}
function drawLine(a,b,color,w){{ctx.strokeStyle=color;ctx.lineWidth=w;ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.stroke();}}
function render(){{
  canvas.width=innerWidth;canvas.height=innerHeight;ctx.clearRect(0,0,canvas.width,canvas.height);
  const drawItems=[];
  if(state.showTerrain){{
    for(const tri of data.terrain_triangles){{
      const p=tri.map(t=>project(rot(sub(t))));
      const depth=(p[0][3]+p[1][3]+p[2][3])/3;
      drawItems.push({{depth,type:'tri',p}});
    }}
  }}
  for(const line of data.holes){{
    for(let i=1;i<line.points.length;i++){{
      const a=project(rot(sub(line.points[i-1]))), b=project(rot(sub(line.points[i])));
      drawItems.push({{depth:(a[3]+b[3])/2,type:'line',a,b,color:line.color,w:line.width}});
    }}
  }}
  if(state.showIntervals){{
    for(const line of data.intervals){{
      const a=project(rot(sub(line.points[0]))), b=project(rot(sub(line.points[1])));
      drawItems.push({{depth:(a[3]+b[3])/2,type:'line',a,b,color:line.color,w:line.width}});
    }}
  }}
  const sa=project(rot(sub(data.strike.points[0]))), sb=project(rot(sub(data.strike.points[1])));
  drawItems.push({{depth:(sa[3]+sb[3])/2,type:'line',a:sa,b:sb,color:data.strike.color,w:3.8}});

  drawItems.sort((a,b)=>a.depth-b.depth);
  for(const it of drawItems){{
    if(it.type==='tri'){{
      const p=it.p; const shade=Math.max(40,Math.min(180,110+p[0][1]*0.06));
      ctx.fillStyle=`rgba(${{shade}},${{shade+20}},${{shade}},0.34)`;
      ctx.beginPath();ctx.moveTo(p[0][0],p[0][1]);ctx.lineTo(p[1][0],p[1][1]);ctx.lineTo(p[2][0],p[2][1]);ctx.closePath();ctx.fill();
    }} else drawLine(it.a,it.b,it.color,it.w);
  }}
}}

let dragging=false,rightDrag=false,lastX=0,lastY=0;
canvas.onmousedown=(e)=>{{dragging=true;rightDrag=(e.button===2);lastX=e.clientX;lastY=e.clientY;}};
canvas.oncontextmenu=(e)=>e.preventDefault();
onmouseup=()=>dragging=false;
onmousemove=(e)=>{{if(!dragging) return; const dx=e.clientX-lastX,dy=e.clientY-lastY; lastX=e.clientX;lastY=e.clientY;
  if(rightDrag){{state.panX+=dx;state.panY+=dy;}} else {{state.yaw+=dx*0.006;state.pitch+=dy*0.006;state.pitch=Math.max(-1.45,Math.min(1.45,state.pitch));}}
}};
onwheel=(e)=>{{state.zoom=Math.max(2.1,Math.min(16,state.zoom+e.deltaY*0.004));}};
function tick(){{if(state.autorotate)state.yaw+=0.003;render();requestAnimationFrame(tick);}} tick();
</script></body></html>"""


def main():
    payload = build_payload()
    with open("contained_sb_estimate.json", "w", encoding="utf-8") as f:
        json.dump(payload["contained_sb"], f, indent=2)
    with open("drillhole_model_3d.html", "w", encoding="utf-8") as f:
        f.write(html(payload))
    print("Generated offline-capable drillhole_model_3d.html + contained_sb_estimate.json")


if __name__ == "__main__":
    main()
