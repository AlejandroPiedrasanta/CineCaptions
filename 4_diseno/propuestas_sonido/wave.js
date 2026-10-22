function rnd(s){return()=>{s=(s*9301+49297)%233280;return s/233280}}
function waves(){document.querySelectorAll('[data-wave]').forEach((el,k)=>{const n=+el.dataset.wave,r=rnd(k*77+13),h=el.clientHeight||40;let out='';for(let i=0;i<n;i++){const env=0.35+0.65*Math.abs(Math.sin(i/9+k))*(r()>.08?1:.15);out+=`<b style="height:${Math.max(2,h*env*(0.3+0.7*r()))}px"></b>`}el.innerHTML=out})}
window.addEventListener('load',waves);
