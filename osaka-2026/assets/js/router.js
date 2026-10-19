(()=>{
 const pages=Array.from(document.querySelectorAll('.view-panel'));
 const tabs=Array.from(document.querySelectorAll('[data-view-target]'));
 const dayCards=Array.from(document.querySelectorAll('#days .case-card'));
 const dayButtons=Array.from(document.querySelectorAll('[data-trip-day]'));
 const picker=document.getElementById('app-day-picker');
 const menu=document.getElementById('trip-menu');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 let activeView='overview',day='1';
 const labels={overview:'旅途總覽',itinerary:'每日行程',map:'街道地圖',budget:'費用預算',prepare:'出發準備'};
 const saveDay=()=>{try{localStorage.setItem('osaka-app-day',day)}catch{}};
 function chooseDay(n,{notify=true}={}){
  if(!/^\d$/.test(n)||!document.getElementById('day-card-'+n))return;day=n;saveDay();picker.value=n;
  dayCards.forEach(c=>{const on=c.id==='day-card-'+day;c.hidden=!on;if(on){c.classList.add('open','is-visible');c.querySelector('.case-toggle').setAttribute('aria-expanded','true')}});
  dayButtons.forEach(b=>{const on=b.dataset.tripDay===day;b.classList.toggle('active',on);b.setAttribute('aria-pressed',String(on))});
  document.getElementById('app-prev-day').disabled=day==='1';document.getElementById('app-next-day').disabled=day==='8';
  if(notify)window.dispatchEvent(new CustomEvent('trip-day-change',{detail:{day,from:'app'}}));
 }
 function viewFor(el){return el?.closest('.view-panel')?.dataset.view||'overview'}
 function revealTarget(el){if(!el)return;let node=el;while(node&&node!==document.body){if(node.tagName==='DETAILS')node.open=true;if(node.matches?.('[data-disclosure]')){node.classList.add('open','is-visible');node.querySelector('.disclosure-toggle')?.setAttribute('aria-expanded','true')}node=node.parentElement}}
 function activate(view,{target=null,historyMode='push',scroll=true}={}){
  if(!labels[view])view='overview';activeView=view;
  pages.forEach(p=>p.hidden=p.dataset.view!==view);
  tabs.forEach(b=>{const on=b.dataset.viewTarget===view;b.classList.toggle('active',on);if(b.getAttribute('role')==='tab'){b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1}else{if(on)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')}});
  document.body.dataset.view=view;document.getElementById('app-current-title').textContent=labels[view];
  document.title=labels[view]+'｜大阪・京都 8 日';
  if(menu.open)menu.close();
  const el=target?document.getElementById(target):null;if(el)revealTarget(el);
  if(historyMode!=='none'){const hash='#'+(target||'view-'+view);if(location.hash!==hash)history[historyMode==='replace'?'replaceState':'pushState']({view},'',hash)}
  if(view==='map')requestAnimationFrame(()=>{window.dispatchEvent(new Event('resize'));window.dispatchEvent(new CustomEvent('trip-view-change',{detail:{view}}))});
  if(scroll)requestAnimationFrame(()=>{if(el)el.scrollIntoView({behavior:'auto',block:'start'});else window.scrollTo({top:0,behavior:'auto'})});
 }
 function goToId(id,{historyMode='push'}={}){const target=document.getElementById(id);if(!target)return;const match=id.match(/^day-(?:card|time)-(\d)$/);if(match)chooseDay(match[1]);activate(viewFor(target),{target:id,historyMode})}
 function fromHash(){const id=decodeURIComponent(location.hash.slice(1));if(id.startsWith('view-')&&labels[id.slice(5)])activate(id.slice(5),{historyMode:'none'});else if(document.getElementById(id))goToId(id,{historyMode:'none'});else activate('overview',{historyMode:'none'})}
 tabs.forEach(b=>b.addEventListener('click',()=>activate(b.dataset.viewTarget)));
 document.querySelectorAll('[role="tablist"]').forEach(list=>list.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;const ts=Array.from(list.querySelectorAll('[role="tab"]'));const i=ts.indexOf(document.activeElement);if(i<0)return;e.preventDefault();const n=e.key==='Home'?0:e.key==='End'?ts.length-1:(i+(e.key==='ArrowRight'?1:-1)+ts.length)%ts.length;ts[n].click();ts[n].focus()}));
 dayButtons.forEach(b=>b.addEventListener('click',()=>{chooseDay(b.dataset.tripDay);if(b.hasAttribute('data-open-itinerary'))activate('itinerary');else{history.replaceState({view:'itinerary'},'','#day-card-'+day);window.scrollTo({top:0,behavior:'auto'})}}));
 picker.addEventListener('change',()=>{chooseDay(picker.value);history.replaceState({view:'itinerary'},'','#day-card-'+day);window.scrollTo({top:0,behavior:'auto'})});
 document.getElementById('app-prev-day').addEventListener('click',()=>{chooseDay(String(Number(day)-1));history.replaceState(null,'','#day-card-'+day);window.scrollTo({top:0,behavior:'auto'})});
 document.getElementById('app-next-day').addEventListener('click',()=>{chooseDay(String(Number(day)+1));history.replaceState(null,'','#day-card-'+day);window.scrollTo({top:0,behavior:'auto'})});
 document.getElementById('open-trip-menu').addEventListener('click',()=>menu.showModal());document.getElementById('close-trip-menu').addEventListener('click',()=>menu.close());
 document.addEventListener('click',e=>{const a=e.target.closest('a[href^="#"]');if(!a)return;const id=a.getAttribute('href').slice(1);if(!id||!document.getElementById(id))return;e.preventDefault();goToId(id)});
 window.addEventListener('popstate',fromHash);window.addEventListener('hashchange',fromHash);
 window.addEventListener('trip-day-change',e=>{if(e.detail.from==='map'&&e.detail.day!=='all')chooseDay(e.detail.day,{notify:false})});
 document.querySelector('[data-expand-days]')?.addEventListener('click',()=>dayCards.filter(c=>!c.hidden).forEach(c=>{c.classList.add('open');c.querySelector('.case-toggle').setAttribute('aria-expanded','true')}));
 document.querySelector('[data-collapse-days]')?.addEventListener('click',()=>dayCards.filter(c=>!c.hidden).forEach(c=>{c.classList.remove('open');c.querySelector('.case-toggle').setAttribute('aria-expanded','false')}));
 try{const saved=localStorage.getItem('osaka-app-day');if(saved&&document.getElementById('day-card-'+saved))day=saved}catch{}
 let printTopics=[];window.addEventListener('beforeprint',()=>{printTopics=Array.from(document.querySelectorAll('.guide-topic')).map(el=>[el,el.open]);printTopics.forEach(([el])=>el.open=true)});window.addEventListener('afterprint',()=>printTopics.forEach(([el,open])=>el.open=open));
 chooseDay(day);fromHash();document.body.classList.add('trip-app-ready');
})();
