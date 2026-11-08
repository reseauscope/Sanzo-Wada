'use strict';
async function verifySnapshot(snapshot){
 if(!globalThis.crypto?.subtle)throw Error('Web Crypto indisponible : ouvrir cette page dans un navigateur récent en fichier local ou en HTTPS.');
 const receipt=snapshot.receipt,files=snapshot.files;
 const required=['wada.py','data/colors.json','data/combinations.json','data/manifest.json','data/LICENSE.md','data/clean/colors.json','data/clean/combinations.json','data/clean/cleaning.json'];
 const keys=Object.keys(receipt.sha256).filter(k=>!k.startsWith('dataset/')).sort();
 if(receipt.source_version!=='1.3.0'||JSON.stringify(keys)!==JSON.stringify([...required].sort())||JSON.stringify(Object.keys(files).sort())!==JSON.stringify(keys))throw Error('Reçu incomplet ou version incorrecte.');
 const decoded={};
 for(const key of required){
  const bytes=Uint8Array.from(atob(files[key]),c=>c.charCodeAt(0));
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
  if(hash!==receipt.sha256[key])throw Error('Copie embarquée divergente : '+key);
  decoded[key]=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
 }
 const rawHash='555f11c32eb8133078fd470dd7d5320533aaa8b636f12fa06a8dd3d0ee2703b4',journal=JSON.parse(decoded['data/clean/cleaning.json']);
 if(receipt.sha256['data/colors.json']!==rawHash||JSON.parse(decoded['data/manifest.json']).sha256!==rawHash||journal.clean_version!=='1.3.0'||journal.corrections.length!==4)throw Error('Provenance invalide.');
 for(const n of ['colors.json','combinations.json'])if(journal.output_sha256[n]!==receipt.sha256['data/clean/'+n])throw Error('Journal divergent.');
 const colors=JSON.parse(decoded['data/clean/colors.json']);
 if(colors.length!==159)throw Error('159 couleurs attendues.');
 return colors;
}
function start(colors){
 const $=id=>document.getElementById(id),text=WADA_TEXTS;
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const combos=new Map();colors.forEach(c=>c.combinations.forEach(id=>{if(!combos.has(id))combos.set(id,[]);combos.get(id).push(c);}));
 if(combos.size!==348||Array.from({length:348},(_,i)=>i+1).some(i=>!combos.has(i)))throw Error('Combinaisons incomplètes.');
 const warn=cs=>[...new Set(cs.flatMap(c=>text.warnings[c.name]||[]))].map(w=>'<div class="warning" role="note"><p>'+esc(w)+'</p></div>').join('');
 const swatches=cs=>'<div class="swatches" style="grid-template-columns:repeat('+cs.length+',minmax(0,1fr))">'+cs.map(c=>'<figure class="swatch"><div class="paint" style="background:'+esc(c.hex)+'" role="img" aria-label="Aplat '+esc(c.hex)+'"></div><figcaption class="caption"><strong>'+esc(c.name)+'</strong>'+(c.name_source?'<br><small>Nom source : '+esc(c.name_source)+'</small>':'')+'<br>CMYK : '+esc(Array.isArray(c.cmyk)?'['+c.cmyk.join(', ')+']':c.cmyk)+'<br>HEX : '+esc(c.hex)+"<br>HEX : approximation d'écran</figcaption></figure>").join('')+'</div>';
 const card=id=>'<article class="card" data-combination="'+id+'"><h3>Combinaison n° '+id+'</h3>'+swatches(combos.get(id))+warn(combos.get(id))+'</article>';
 const gallery=ids=>'<p>'+ids.length+' combinaisons. '+esc(text.ORDER)+'</p><div class="gallery">'+ids.map(card).join('')+'</div>';
 function combo(){const n=Number($('number').value);$('combo-result').innerHTML=Number.isInteger(n)&&n>=1&&n<=348?card(n):'<p role="alert">Choisir un entier de 1 à 348.</p>';}
 function color(){const c=colors.find(c=>c.name===$('name').value);$('color-result').innerHTML='<article class="card"><h3>'+esc(c.name)+'</h3>'+swatches([c])+warn([c])+'</article>'+gallery([...c.combinations].sort((a,b)=>a-b));}
 function nearest(){try{const code='#'+$('code').value.trim().replace(/^#/,'').toLowerCase(),ns=WadaColor.nearest(colors,$('code').value);$('nearest-result').innerHTML='<p>'+esc(text.METHOD)+'</p>'+(ns[0].color.hex===code?'<p><strong>correspondance_exacte : '+esc(ns[0].color.name)+'</strong></p>':'')+ns.map(n=>'<article class="card"><h3>'+esc(n.color.name)+'</h3><p>ΔE00 : '+n.d00.toFixed(1)+' ; ΔE76 : '+n.d76.toFixed(1)+'</p>'+swatches([{name:'HEX saisi',hex:code,cmyk:'non fourni'},n.color])+warn([n.color])+'</article>').join('');}catch(e){$('nearest-result').innerHTML='<p role="alert">'+esc(e.message)+'</p>';}}
 function all(){const size=$('size').value,ch=$('chapter').value;const ids=[...combos.keys()].sort((a,b)=>a-b).filter(id=>(size==='Toutes'||combos.get(id).length===Number(size))&&(ch==='Tous'||combos.get(id).some(c=>c.swatch===Number(ch)-1)));$('gallery-result').innerHTML=gallery(ids);}
 $('order').textContent=text.ORDER;$('provenance').textContent=text.PROVENANCE;
 colors.forEach(c=>{const o=document.createElement('option');o.value=c.name;o.textContent=c.name;$('name').append(o);});$('name').value='Burnt Sienna';
 $('combo-form').addEventListener('submit',e=>{e.preventDefault();combo();});$('number').addEventListener('change',combo);$('name').addEventListener('change',color);$('hex-form').addEventListener('submit',e=>{e.preventDefault();nearest();});for(const id of ['size','chapter'])$(id).addEventListener('change',all);
 combo();color();nearest();all();$('status').hidden=true;$('application').hidden=false;
}
if(typeof module!=='undefined')module.exports={verifySnapshot};
if(typeof document!=='undefined')verifySnapshot(globalThis.WADA_SNAPSHOT).then(start).catch(e=>{document.getElementById('application').hidden=true;const s=document.getElementById('status');s.hidden=false;s.setAttribute('role','alert');s.textContent='Erreur de données : '+e.message;});
