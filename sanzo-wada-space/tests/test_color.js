'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const base=path.resolve(__dirname,'..'),C=require('../color.js');
const read=p=>JSON.parse(fs.readFileSync(path.join(base,p),'utf8'));
const colors=read('data/clean/colors.json'),reference=read('tests/vectors.json');
for(const v of reference.vectors){
 const rgb=[1,3,5].map(i=>parseInt(v.hex.slice(i,i+2),16));
 C.rgbToLab(rgb).forEach((x,i)=>assert.ok(Math.abs(x-v.lab[i])<1e-10));
 const actual=C.nearest(colors,v.hex);
 v.neighbors.forEach((n,i)=>{assert.equal(actual[i].color.name,n.name,v.hex);assert.equal(Number(actual[i].d00.toFixed(1)),n.d00,v.hex);assert.equal(Number(actual[i].d76.toFixed(1)),n.d76,v.hex);});
}
assert.ok(Math.abs(C.delta2000([50,2.6772,-79.7751],[50,0,-82.7485])-2.0425)<.00005);
require('../texts.js');assert.deepEqual(globalThis.WADA_TEXTS.warnings,reference.warnings);
console.log(reference.vectors.length+' vectors, Lab, 3 neighbors, both distances and warnings: OK');
