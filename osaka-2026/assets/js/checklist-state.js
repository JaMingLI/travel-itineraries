/* Pure checklist default migration. Preserve completed tasks and edited fields. */
(function(root){
 'use strict';
 function defaults(seed){return Object.fromEntries(seed.tasks.map(task=>[task.id,Object.fromEntries(['title','note','due','group'].map(field=>[field,task[field]]))]))}
 function migrate(tasks,data,seed){
  const current=new Map(seed.tasks.map(task=>[task.id,task]));
  const previous=data.defaults||seed.previousDefaults||{};
  let changed=0;
  const result=tasks.map(task=>{
   const next={...task},fresh=current.get(task.id),old=previous[task.id];
   if(fresh&&old)for(const field of ['title','note','due','group']){
    if(Object.prototype.hasOwnProperty.call(old,field)&&next[field]===old[field]&&next[field]!==fresh[field]){next[field]=fresh[field];changed++}
   }
   return next;
  });
  return {tasks:result,changed};
 }
 const api={defaults,migrate};
 if(typeof module==='object'&&module.exports)module.exports=api;else root.TripChecklistState=api;
})(typeof window==='undefined'?{}:window);
