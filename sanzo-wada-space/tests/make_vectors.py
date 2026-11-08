"""Generate reference vectors exclusively from the bundled unmodified module."""
import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE))
import wada
wada.DATA=str(BASE/'data')
colors=wada.load_colors('clean')
extra=['#000000','#ffffff','#ff0000','#00ff00','#0000ff','#123456','#abcdef','#808080','#010203','#fefdfc','#00b7c2','#00978d','#1e0e3f','#ff00ff','#ffff00','#00ffff','#654321','#aabbcc','#112233','#cc8844','#998877','#ff8000']
vectors=[]
for code in [c['hex'] for c in colors]+extra:
 rgb=wada.hex_to_rgb(code)
 vectors.append({'hex':code,'lab':wada.rgb_to_lab(rgb),'neighbors':[{'name':c['name'],'d00':round(d00,1),'d76':round(d76,1)} for d00,d76,c in wada.nearest_colors(colors,rgb,3)]})
payload={'source_version':'1.3.0','vectors':vectors,'warnings':{c['name']:wada.warnings_for([c],wada.known_anomalies()[0]) for c in colors}}
(BASE/'tests/vectors.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(str(len(vectors))+' vectors generated')
