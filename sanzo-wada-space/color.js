/* Same D50 matrix and Sharma 2005 equations as the bundled Python reference. */
(function(root){
'use strict';
const rad=x=>x*Math.PI/180, deg=x=>x*180/Math.PI, cos=x=>Math.cos(rad(x)), sin=x=>Math.sin(rad(x));
function rgbToLab(rgb){
 const [r,g,b]=rgb.map(v=>{v/=255;return v<=0.04045?v/12.92:((v+0.055)/1.055)**2.4;});
 const f=t=>t>216/24389?t**(1/3):(24389/27*t+16)/116;
 const x=f((.4360747*r+.3850649*g+.1430804*b)/.9642),y=f(.2225045*r+.7168786*g+.0606169*b),z=f((.0139322*r+.0971045*g+.7141733*b)/.8249);
 return [116*y-16,500*(x-y),200*(y-z)];
}
function delta76(a,b){return Math.sqrt(a.reduce((s,v,i)=>s+(v-b[i])**2,0));}
function delta2000([L1,a1,b1],[L2,a2,b2]){
 const C1=Math.hypot(a1,b1),C2=Math.hypot(a2,b2),Cm=(C1+C2)/2,G=.5*(1-Math.sqrt(Cm**7/(Cm**7+25**7)));
 const a1p=(1+G)*a1,a2p=(1+G)*a2,C1p=Math.hypot(a1p,b1),C2p=Math.hypot(a2p,b2);
 const hue=(b,a,c)=>c?(deg(Math.atan2(b,a))+360)%360:0,h1=hue(b1,a1p,C1p),h2=hue(b2,a2p,C2p);
 const dL=L2-L1,dC=C2p-C1p;let dh=0;
 if(C1p*C2p){dh=h2-h1;if(dh>180)dh-=360;else if(dh< -180)dh+=360;}
 const dH=2*Math.sqrt(C1p*C2p)*sin(dh/2),Lm=(L1+L2)/2,Cmp=(C1p+C2p)/2;
 let hm=h1+h2;if(C1p*C2p){if(Math.abs(h1-h2)<=180)hm/=2;else if(hm<360)hm=(hm+360)/2;else hm=(hm-360)/2;}
 const T=1-.17*cos(hm-30)+.24*cos(2*hm)+.32*cos(3*hm+6)-.20*cos(4*hm-63);
 const theta=30*Math.exp(-(((hm-275)/25)**2)),RC=2*Math.sqrt(Cmp**7/(Cmp**7+25**7));
 const SL=1+.015*(Lm-50)**2/Math.sqrt(20+(Lm-50)**2),SC=1+.045*Cmp,SH=1+.015*Cmp*T,RT=-sin(2*theta)*RC;
 return Math.sqrt((dL/SL)**2+(dC/SC)**2+(dH/SH)**2+RT*(dC/SC)*(dH/SH));
}
function nearest(colors,code){
 if(typeof code!=='string'||!/^#?[0-9a-f]{6}$/i.test(code.trim()))throw Error('Saisir un code HEX de six chiffres, par exemple #00978d.');
 code='#'+code.trim().replace(/^#/,'').toLowerCase();
 const rgb=[1,3,5].map(i=>parseInt(code.slice(i,i+2),16)),lab=rgbToLab(rgb),exact=colors.find(c=>c.hex.toLowerCase()===code);
 const result=colors.filter(c=>!exact||c.name!==exact.name).map(c=>({color:c,d00:delta2000(lab,c.lab),d76:delta76(lab,c.lab)})).sort((a,b)=>a.d00-b.d00);
 if(exact)result.unshift({color:exact,d00:0,d76:0});return result.slice(0,3);
}
const api={rgbToLab,delta76,delta2000,nearest};root.WadaColor=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
