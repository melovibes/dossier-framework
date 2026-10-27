
const b=document.getElementById('navbtn'),n=document.querySelector('nav.side');b&&b.addEventListener('click',()=>n.classList.toggle('open'));
const q=document.getElementById('q');q&&q.addEventListener('input',()=>{const v=q.value.toLowerCase().trim();
document.querySelectorAll('[data-s]').forEach(e=>e.classList.toggle('hide',v&&!e.textContent.toLowerCase().includes(v)));});
document.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement!==q){e.preventDefault();q.focus();}});
