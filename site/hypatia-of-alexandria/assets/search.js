
const sq=document.getElementById('sq'),out=document.getElementById('results'),D=window.SEARCH_INDEX||[];
const esc=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function run(){const v=sq.value.toLowerCase().trim(),terms=v.split(/\s+/).filter(Boolean);
 history.replaceState(null,'',v?'?q='+encodeURIComponent(sq.value.trim()):location.pathname);
 if(!terms.length){out.innerHTML='';return;}
 const hits=D.map(d=>{const h=(d.t+' '+d.x).toLowerCase();if(!terms.every(w=>h.includes(w)))return null;
   const score=terms.reduce((s,w)=>s+(d.t.toLowerCase().includes(w)?5:0)+h.split(w).length-1,0);return [score,d];}).filter(Boolean).sort((a,b)=>b[0]-a[0]);
 out.innerHTML='<p class=meta>'+hits.length+' result'+(hits.length==1?'':'s')+'</p>'+hits.slice(0,100).map(([s,d])=>{
   const i=Math.max(0,d.x.toLowerCase().indexOf(terms[0])-80);let snip=esc((i?'…':'')+d.x.slice(i,i+240)+'…');
   terms.forEach(w=>{snip=snip.replace(new RegExp('('+w.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','ig'),'<mark>$1</mark>');});
   return '<div class="card result" data-s><h3><a href="'+d.u+'">'+esc(d.t)+'</a></h3><div class=meta>'+esc(d.p)+'</div><p>'+snip+'</p></div>';}).join('');}
sq.addEventListener('input',run);sq.value=new URLSearchParams(location.search).get('q')||'';run();
