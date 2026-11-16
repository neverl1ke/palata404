'use strict';
// Test driver based solely on visible work-order evidence. It does not read the
// model's private answer generators or submit a legacy answer for a new task.
function difference(a,b){const values=new Map(b.map(x=>[x.id,x.value]));return a.filter(x=>x.value!==values.get(x.id)).map(x=>x.id);}
function toggleTowards(current,wanted,op){const remove=current.find(x=>!wanted.includes(x));if(remove)return{op,value:remove};const add=wanted.find(x=>!current.includes(x));return add?{op,value:add}:{op:'submit'};}
function nextOperation(b){
 if(!b)return null;
 switch(b.kind){
  case 'inspection':{
   const hidden=b.items.find(x=>!x.inspected);if(hidden)return{op:'inspect',value:hidden.id};
   const match=b.items.find(x=>x.details?.kit===b.request.kit&&x.details?.lot===b.request.lot&&x.details?.seal==='целая');
   if(!match)throw Error('The inspected containers do not contain the requested intact kit.');
   return toggleTowards(b.selected,[match.id],'select');
  }
  case 'packing':{
   const desired=b.request.components.map(type=>b.items.find(x=>x.type===type&&x.size===b.request.size&&x.condition==='чистая упаковка'));
   if(desired.some(x=>!x))throw Error('No clean packing selection matches the written request.');
   return toggleTowards(b.selected,desired.map(x=>x.id),'select');
  }
  case 'delivery':return{op:'deliver'};
  case 'compare':return toggleTowards(b.marked,difference(b.documents[0].fields,b.documents[1].fields),'mark');
  case 'diagnostic':{
   if(!b.inspected)return{op:'inspect',value:'connector'};
   if(!b.tested)return{op:'test'};
   const report=!b.connector.connected?'disconnected':b.indicator==='on'&&/вызов принят/.test(b.response||'')?'working':'noResponse';
   if(!b.reports.some(x=>x.id===report))throw Error('No report describes the observed call response.');
   return b.selected[0]===report?{op:'submit'}:{op:'select',value:report};
  }
  case 'timeline':{
   const desired=b.cards.slice().sort((a,z)=>a.time.localeCompare(z.time)).map(x=>x.id);
   const mismatch=b.order.findIndex((x,i)=>desired[i]!==x);
   if(mismatch>=0)return{op:'remove',value:b.order[mismatch]};
   return b.order.length<desired.length?{op:'place',value:desired[b.order.length]}:{op:'submit'};
  }
  case 'baseline':return{op:'record'};
  case 'difference':return toggleTowards(b.marked,difference(b.baseline,b.current),'mark');
  default:throw Error('Unknown workbench kind '+b.kind);
 }
}
module.exports={nextOperation};
