(()=>{
 'use strict';
 const seed=JSON.parse(document.getElementById('prep-checklist-seed').textContent);
 const KEY='osaka-2026-prepare-checklist-v1',groups=seed.groups,byId=new Map(groups.map(g=>[g.id,g.name]));
 const $=id=>document.getElementById(id),list=$('prep-list'),dialog=$('prep-editor');
 let tasks=seed.tasks.map(t=>({...t})),editing=null,lastSaved=null;
 function status(message,error=false){$('prep-save-status').textContent=message;$('prep-save-status').classList.toggle('prep-error',error)}
 function validate(data){
  if(!data||data.schema!==1||!Array.isArray(data.tasks)||data.tasks.length>500)throw Error('備份格式不正確（需要版本1的準備清單，最多500項）。');
  const seen=new Set();return data.tasks.map(t=>{
   if(!t||typeof t.id!=='string'||!/^[a-zA-Z0-9_-]{1,100}$/.test(t.id)||seen.has(t.id)||!byId.has(t.group)||typeof t.title!=='string'||!t.title.trim()||t.title.length>300||typeof t.note!=='string'||t.note.length>3000||typeof t.due!=='string'||t.due.length>80||typeof t.done!=='boolean')throw Error('備份中有無效或重複事項，沒有匯入任何資料。');
   seen.add(t.id);return {id:t.id,group:t.group,title:t.title.trim(),note:t.note,due:t.due,done:t.done};
  });
 }
 function payload(){return {schema:1,trip:'osaka-2026',savedAt:new Date().toISOString(),defaults:TripChecklistState.defaults(seed),tasks}}
 function save(){
  const data=payload();try{localStorage.setItem(KEY,JSON.stringify(data));lastSaved=data.savedAt;status('已儲存於此瀏覽器 · '+new Date(lastSaved).toLocaleTimeString('zh-TW',{hour:'2-digit',minute:'2-digit'}));return true}
  catch{status('無法儲存：目前變更僅暫存於本頁，請先匯出備份。',true);return false}
 }
 try{const raw=localStorage.getItem(KEY);if(raw){const data=JSON.parse(raw);const migrated=TripChecklistState.migrate(validate(data),data,seed);tasks=migrated.tasks;lastSaved=data.savedAt;const known=new Set(tasks.map(t=>t.id));const added=seed.tasks.filter(t=>!known.has(t.id));if(tasks.length+added.length>500)throw Error('事項超過上限');tasks.push(...added.map(t=>({...t})));if(added.length||migrated.changed){if(save())status('行程事項已同步，打勾與個人編輯紀錄已保留')}else status('已載入此瀏覽器的紀錄')}else{localStorage.setItem(KEY,JSON.stringify(payload()));status('自動儲存已啟用 · 此瀏覽器')}}catch{status('無法讀取既有紀錄或儲存空間；目前顯示預設清單，請先備份再操作。',true)}
 function node(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n}
 groups.forEach(g=>{for(const id of ['prep-group-filter','prep-edit-group']){const filterNames={esim:'eSIM設定',documents:'證件與入境',stay:'住宿與入住',booking:'訂位與票券',phone:'上網與聯絡',money:'付款與交通',packing:'行李與保險',departure:'出發與回程'};const o=node('option','',id==='prep-group-filter'?filterNames[g.id]:g.name);o.value=g.id;$(id).append(o)}});
 function render(){
  const open=new Set([...list.querySelectorAll('details.prep-group[open]')].map(n=>n.dataset.group));
  const first=!list.dataset.ready;list.dataset.ready='true';list.replaceChildren();
  const done=tasks.filter(t=>t.done).length;$('prep-progress-label').textContent=`已完成 ${done} / ${tasks.length} 項`;
  $('prep-progress').max=Math.max(tasks.length,1);$('prep-progress').value=done;
  const mode=$('prep-filter').value,group=$('prep-group-filter').value,q=$('prep-search').value.trim().toLocaleLowerCase();
  const visible=tasks.filter(t=>(mode==='all'||t.done===(mode==='done'))&&(group==='all'||t.group===group)&&[t.title,t.note,t.due].join(' ').toLocaleLowerCase().includes(q));
  $('prep-empty').hidden=visible.length>0;
  groups.forEach(g=>{
   const all=tasks.filter(t=>t.group===g.id),rows=visible.filter(t=>t.group===g.id);if(!rows.length)return;
   const section=node('details','prep-group');section.dataset.group=g.id;section.id='prep-group-'+g.id;section.open=!!q||mode!=='all'||group!=='all'||open.has(g.id)||(first&&g.id==='esim');
   const sum=node('summary');sum.append(node('strong','',g.name),node('span','',`${all.filter(t=>t.done).length} / ${all.length}`));section.append(sum);
   const ul=node('ul','prep-items');rows.forEach(t=>{
    const li=node('li','prep-item'+(t.done?' is-done':''));
    const main=node('div','prep-item-main'),label=node('label','prep-check-label'),cb=node('input');cb.type='checkbox';cb.checked=t.done;cb.dataset.taskId=t.id;
    const title=node('span','prep-task-title',t.title);label.append(cb,title);main.append(label);
    const edit=node('button','prep-edit-button','編輯');edit.type='button';edit.setAttribute('aria-label','編輯：'+t.title);edit.addEventListener('click',()=>editTask(t.id));main.append(edit);li.append(main);
    const sub=node('div','prep-item-sub');if(t.due)sub.append(node('span','prep-due',t.due));
    if(t.note){const more=node('details','prep-task-note');more.append(node('summary','','說明與備註'),node('p','',t.note));sub.append(more)}
    li.append(sub);ul.append(li);
    cb.addEventListener('change',()=>{t.done=cb.checked;save();render();list.querySelector(`[data-task-id="${t.id}"]`)?.focus()});
   });section.append(ul);list.append(section);
  });
 }
 function editTask(id){
  $('prep-edit-title').setCustomValidity('');editing=id;const t=tasks.find(t=>t.id===id);$('prep-editor-title').textContent=t?'編輯事項':'新增事項';
  $('prep-edit-title').value=t?.title||'';$('prep-edit-note').value=t?.note||'';$('prep-edit-due').value=t?.due||'';$('prep-edit-group').value=t?.group||($('prep-group-filter').value==='all'?'documents':$('prep-group-filter').value);
  dialog.showModal();$('prep-edit-title').focus();
 }
 const confirmBox=node('dialog','prep-editor');confirmBox.id='prep-confirm';confirmBox.setAttribute('aria-labelledby','prep-confirm-message');
 const confirmText=node('p');confirmText.id='prep-confirm-message';const confirmActions=node('div','prep-editor-actions'),no=node('button','','取消'),yes=node('button','','確定');no.type=yes.type='button';confirmActions.append(no,yes);confirmBox.append(confirmText,confirmActions);document.body.append(confirmBox);
 function ask(message){return new Promise(resolve=>{confirmText.textContent=message;let settled=false;const finish=value=>{if(settled)return;settled=true;confirmBox.close();no.onclick=yes.onclick=null;confirmBox.oncancel=null;resolve(value)};no.onclick=()=>finish(false);yes.onclick=()=>finish(true);confirmBox.oncancel=e=>{e.preventDefault();finish(false)};confirmBox.showModal();no.focus()})}
 $('prep-add').addEventListener('click',()=>{if(tasks.length>=500){alert('清單目前最多支援500項，無法再新增。請先匯出備份。');return}editTask(null)});
 $('prep-edit-cancel').addEventListener('click',()=>dialog.close());
 $('prep-edit-form').addEventListener('submit',e=>{
  e.preventDefault();const title=$('prep-edit-title').value.trim();if(!title){$('prep-edit-title').setCustomValidity('請輸入事項名稱');$('prep-edit-title').reportValidity();return}
  const t={id:editing||'custom-'+(globalThis.crypto?.randomUUID?.()||Date.now()+'-'+Math.random().toString(36).slice(2)),group:$('prep-edit-group').value,title,note:$('prep-edit-note').value,due:$('prep-edit-due').value.trim(),done:tasks.find(t=>t.id===editing)?.done||false};
  if(editing)tasks=tasks.map(old=>old.id===editing?t:old);else tasks.push(t);
  save();dialog.close();render();
 });
 $('prep-edit-title').addEventListener('input',()=>$('prep-edit-title').setCustomValidity(''));
 ['prep-filter','prep-group-filter'].forEach(id=>$(id).addEventListener('change',render));$('prep-search').addEventListener('input',render);
 $('prep-export').addEventListener('click',()=>{
  const blob=new Blob([JSON.stringify(payload(),null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=node('a');a.href=url;a.download='osaka-checklist-'+new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Taipei'}).format(new Date())+'.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
 });
 $('prep-import').addEventListener('click',()=>$('prep-import-file').click());
 $('prep-import-file').addEventListener('change',async e=>{
  const file=e.target.files[0];if(!file)return;
  try{if(file.size>1000000)throw Error('檔案超過1MB，請選擇清單匯出的JSON備份。');const imported=JSON.parse(await file.text());const next=TripChecklistState.migrate(validate(imported),imported,seed).tasks;const merged=new Map(tasks.map(t=>[t.id,t]));next.forEach(t=>merged.set(t.id,t));if(merged.size>500)throw Error("合併後超過500項，無法匯入。");if(!await ask(`將合併備份中的 ${next.length} 項：更新相同事項的內容與勾選狀態、加入新事項，保留現有全部事項。確定匯入？`))return;tasks=[...merged.values()];save();render()}
  catch(err){alert('匯入失敗：'+(err instanceof SyntaxError?'這不是有效的JSON檔案。':err.message))}finally{e.target.value=''}
 });
 render();
})();
