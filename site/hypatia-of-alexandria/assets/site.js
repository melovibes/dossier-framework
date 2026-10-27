
const b=document.getElementById('navbtn'),n=document.querySelector('nav.side');b&&b.addEventListener('click',()=>n.classList.toggle('open'));
// Filter targets: explicit [data-s] cards (claims, sources); otherwise table rows and text blocks in <main> (timeline, chapters).
const q=document.getElementById('q');
const items=()=>{const m=document.querySelector('main')||document.body,c=m.querySelectorAll('[data-s]');
return c.length?[...c]:[...m.querySelectorAll('tbody tr, li, p, blockquote, pre, dl')].filter(e=>!e.parentElement.closest('li, p, blockquote, pre, dl')&&!e.classList.contains('kicker')&&!e.classList.contains('meta'));};
q&&q.addEventListener('input',()=>{const v=q.value.toLowerCase().trim();
items().forEach(e=>e.classList.toggle('hide',!!v&&!e.textContent.toLowerCase().includes(v)));});
document.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement!==q){e.preventDefault();q.focus();}});
