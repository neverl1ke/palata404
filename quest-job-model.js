/* Persistent work orders for floor 10. Public boards contain evidence, never a
 * solution key. Operations return a new work state; a rejected submission cannot
 * change the saved order, complete a step, consume cargo or pay a reward. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.PalataQuestJobModel=api;})(globalThis,function(){
'use strict';
const ids=['k1','k2','k3','d1','d2','d3'];
const owner={tag:'k1',linen:'k2',linenReserve:'k2',deliver:'k2',copies:'k3',bell407:'d1',bell408:'d1',callReview:'d1',callService407:'d1',callService408:'d1',callRetest407:'d1',callRetest408:'d1',log:'d2',baseline:'d3',difference:'d3'};
const labels={time:'Время обхода',route:'Маршрут',mark:'Отметка на табличке'};
const safeArray=(value,allowed)=>[...new Set((Array.isArray(value)?value:[]).filter(x=>typeof x==='string'&&allowed.includes(x)))];
const clone=value=>JSON.parse(JSON.stringify(value));
const variant=n=>Number.isSafeInteger(n)&&n>=0?n%3:0;
const rotate=(list,n)=>list.slice(n%list.length).concat(list.slice(0,n%list.length));
const briefs={
 k1:{giver:'Клара',purpose:'Перед выдачей на пост нужно сверить комплект: совпадения одной бирки недостаточно.',deliverable:'Бирка подходящего контейнера с проверенной целой пломбой.'},
 k2:{giver:'Клара',purpose:'В палате 406 ждут чистое бельё. На полке лежат вещи из разных учётных комплектов.',deliverable:'Квитанция передачи чистых простыни и наволочки в палату 406.'},
 k3:{giver:'Клара',purpose:'Запись процедурной и её копия должны совпадать. Неизвестные сведения нельзя дописывать.',deliverable:'Лист с отмеченными расхождениями двух записей.'},
 d1:{giver:'Врач',purpose:'Нужно выяснить, доходят ли вызовы из палат 407 и 408 до поста, не подменяя наблюдение догадкой.',deliverable:'Два акта: подключение, индикатор и ответ поста в каждой палате.'},
 d2:{giver:'Врач',purpose:'Отдельные листки обхода нужно вернуть в журнал в подтверждённом порядке.',deliverable:'Лист обхода, восстановленный по времени записей.'},
 d3:{giver:'Врач',purpose:'Сначала зафиксируйте увиденное, затем сравните. Причины возможного расхождения пока неизвестны.',deliverable:'Карточка сравнения исходных и повторных показаний коридора A.'}
};
function brief(id,revision){if(typeof id!=='string'||!Object.hasOwn(briefs,id))return null;const result={...briefs[id]};if(id==='k3'&&(revision===undefined||revision===3)){result.purpose='Сопоставьте направление, лист процедуры и копию одной медицинской записи. Отделите подтверждённое расхождение от различия полей и неподтверждённых сведений.';result.deliverable='Лист сверки палаты, времени проведения и подтверждения имени исполнителя. Неизвестное имя не дописывается.';}if(id==='d1'&&(revision===undefined||revision===5)){result.purpose='Проверьте вызовы 407 и 408 в любом порядке. Техник уже на связи и обслужит неисправный узел здесь, после вашего акта.';result.deliverable='Два акта и контрольный ответ поста по каждому обслуженному вызову.';}if(id==='d1'&&revision===4){result.purpose='Проверьте оба вызова, получите разрешение врача для обнаруженных проблем и подтвердите результат после обслуживания персоналом.';result.deliverable='Два первичных акта и подтверждённые контрольные вызовы для обслуженных узлов. Награда одна, при окончательной сдаче.';}if(id==='d2'&&(revision===undefined||revision>=3))result.deliverable='Журнал с подтверждённым порядком событий; неразборчивое время остаётся неустановленным.';if(id==='d3'&&(revision===undefined||revision>=4)){result.purpose='Выберите один предмет и дважды выполните одно и то же наблюдение. Совпадение также является результатом.';result.deliverable='Карточка двух сохранённых наблюдений одного предмета.';}if(id==='k2'&&(revision===undefined||revision===5))result.purpose='Соберите комплект для 406 и помогите подготовить кровать. Если окно открыто, выберите, как удержать край ткани.';if(id==='k2'&&(revision===undefined||revision>=4))result.deliverable='Квитанция подготовки кровати 406: простыня и наволочка на своих местах.';return result;}
const callRooms=['ward407','ward408'];
const callConditions=['working','disconnected','noResponse','unassessed'];
const callEquipment=room=>({id:'CALL-'+room.slice(4),connector:'КС-2',postAddress:'ПОСТ-'+room.slice(4)});
function supportsRevision(id, revision){
 if(!ids.includes(id))return false;
 if(revision===2)return true;
 if(revision===3)return ['k2','k3','d1','d2','d3'].includes(id);
 if(revision===4&&['d2','d3'].includes(id))return true;
 return [4,5].includes(revision)&&['k2','d1'].includes(id);
}
function make(id, serial=0, equipment){
 const revision=['k2','d1'].includes(id)?5:['d2','d3'].includes(id)?4:id==='k3'?3:2;
 const orderVariant=variant(serial);
 const work=restoreWork(id,{},orderVariant,revision);
 if(id==='k2'&&revision===5)work.draftScene=bedDraft({required:serial===0});
 if(id==='d1'&&revision===5){
  work.order='d1:'+(serial+1);
  work.authorized=true;
  work.escortScheduled=true;
  work.postNotified=true;
  for(const room of callRooms){
   const source=equipment?.[room];
   work.initial[room]={
    condition:callConditions.includes(source?.condition)?source.condition:'unassessed',
    revision:Number.isSafeInteger(source?.revision)&&source.revision>=0?source.revision:0
   };
  }
 }
 return {revision,variant:orderVariant,work};
}
function bedDraft(raw){
 const required=raw?.required===true;
 const method=required&&['window','assistance'].includes(raw?.method)?raw.method:null;
 const spread=!!method&&raw?.spread===true;
 return {
  required,
  phase:spread?'complete':method?'ready':'pending',
  method,
  spread,
  windowState:method==='window'?'closed':'open'
 };
}
function restoreWork(id,raw,v,r=2){
 raw=raw&&typeof raw==='object'&&!Array.isArray(raw)?raw:{};
 const result={};
 if(id==='k1'){result.inspected=safeArray(raw.inspected,['pack-0','pack-1','pack-2','pack-3']);result.selected=safeArray(raw.selected,['pack-0','pack-1','pack-2','pack-3']).slice(0,1);}
 if(id==='k2'){result.selected=safeArray(raw.selected,['linen-0','linen-1','linen-2','linen-3','linen-4','linen-5']);if(r>=3){result.shortageNoted=raw.shortageNoted===true;result.reserveGranted=result.shortageNoted&&raw.reserveGranted===true;result.selectedReserve=safeArray(raw.selectedReserve,['reserve-same-size','reserve-small']).slice(0,1);result.selectedPiece=['sheet','pillowcase'].includes(raw.selectedPiece)?raw.selectedPiece:null;result.placed=safeArray(raw.placed,['sheet','pillowcase']);if(result.placed.includes(result.selectedPiece))result.selectedPiece=null;if(r>=4)result.preparationStarted=raw.preparationStarted===true;if(r===5)result.draftScene=bedDraft(raw.draftScene);}}
 if(id==='k3'){if(r===3){result.sourcesRead=raw.sourcesRead===true;result.conclusions=caseConclusions(raw.conclusions);}else result.marked=safeArray(raw.marked,['time','ward','signature','lot']);}
 if(id==='d1'){
  result.diagnostics={};for(const key of ['bell407','bell408']){const d=raw.diagnostics?.[key]||{};result.diagnostics[key]={inspected:d.inspected===true,tested:d.inspected===true&&d.tested===true,selected:safeArray(d.selected,r>=4?callConditions:['working','disconnected','noResponse']).slice(0,1)};}
  if(r>=4){result.order=typeof raw.order==='string'?raw.order:'d1:1';result.initial={};result.authorized=raw.authorized===true;result.services={};for(const room of callRooms){const d=raw.initial?.[room]||{},p=raw.services?.[room]||{};result.initial[room]={condition:callConditions.includes(d.condition)?d.condition:'unassessed',revision:Number.isSafeInteger(d.revision)&&d.revision>=0?d.revision:0};result.services[room]={inspected:p.inspected===true,selected:safeArray(p.selected,['service-a','service-b','service-c']).slice(0,1),performed:p.performed===true,tested:p.tested===true,confirmed:p.confirmed===true,authorization:p.authorization&&typeof p.authorization==='object'?clone(p.authorization):null,serviceRevision:Number.isSafeInteger(p.serviceRevision)&&p.serviceRevision>=0?p.serviceRevision:null,responseAddress:typeof p.responseAddress==='string'?p.responseAddress:null};}if(r===5){result.escortScheduled=raw.escortScheduled===true;result.postNotified=raw.postNotified===true;result.escalated=false;}}
 }
 if(id==='d2'){result.order=safeArray(raw.order,['entry-a','entry-b','entry-c','entry-d']);if(r>=3)result.reverseRead=safeArray(raw.reverseRead,['entry-b']);}
 if(id==='d3'&&r===4)return d3RestoreWork(raw);
 if(id==='d3'){result.baselineCaptured=raw.baselineCaptured===true;result.marked=safeArray(raw.marked,['time','route','mark']);if(r===3){result.baseline=restoreObservation(raw.baseline);result.observed=restoreObservation(raw.observed);result.observedTrip=Number.isSafeInteger(raw.observedTrip)&&raw.observedTrip>=0?raw.observedTrip:null;result.noChanges=raw.noChanges===true;}}
 return result;
}
function restore(id,raw){const v=variant(raw?.variant),r=supportsRevision(id,raw?.revision)?raw.revision:2;return{revision:r,variant:v,work:restoreWork(id,raw?.work,v,r)};}
function canonical(value){if(value===undefined)return '"__undefined__"';return JSON.stringify(value&&typeof value==='object'&&!Array.isArray(value)?Object.fromEntries(Object.keys(value).sort().map(k=>[k,JSON.parse(canonical(value[k]))])):Array.isArray(value)?value.map(x=>JSON.parse(canonical(x))):value);}
function validRecord(id,job){
 if(id==='k3'&&job?.revision===3){
  if(!job.work||typeof job.work!=='object'||Array.isArray(job.work)||typeof job.active!=='boolean'||!Number.isSafeInteger(job.count)||job.count<0||!Number.isSafeInteger(job.startTrip)||job.startTrip<0||!Number.isInteger(job.variant)||job.variant<0||job.variant>2||Object.keys(job).some(k=>!['active','done','count','startTrip','revision','variant','work'].includes(k))||!job.done||typeof job.done!=='object'||Array.isArray(job.done)||Object.entries(job.done).some(([key,value])=>key!=='copies'||value!==true))return false;
  const w=job.work;
  if(!w.conclusions||typeof w.conclusions!=='object'||Array.isArray(w.conclusions)||canonical(w)!==canonical(restoreWork(id,w,job.variant,3)))return false;
  if(!w.sourcesRead&&Object.keys(w.conclusions).length)return false;
  return !job.done.copies||caseAnswer(w);
 }
 if([3,4].includes(job?.revision)&&['d2','d3'].includes(id)){
  if(!job.work||typeof job.work!=='object'||Array.isArray(job.work)||typeof job.active!=='boolean'||!Number.isSafeInteger(job.count)||job.count<0||!Number.isSafeInteger(job.startTrip)||job.startTrip<0||Object.keys(job).some(k=>!['active','done','count','startTrip','revision','variant','work'].includes(k))||!job.done||typeof job.done!=='object'||Array.isArray(job.done)||Object.entries(job.done).some(([k,v])=>k!==(id==='d2'?'log':'difference')||v!==true))return false;
  const w=job.work;
  if(job.revision===4&&(!Number.isSafeInteger(job.variant)||job.variant!==variant(job.variant)))return false;
  if(canonical(w)!==canonical(restoreWork(id,w,variant(job.variant),job.revision)))return false;
  if(id==='d2')return !job.done.log||(w.reverseRead.includes('entry-b')&&same(w.order,['entry-a','entry-b','entry-c','entry-d'])&&w.order.every((x,i)=>x==='entry-'+String.fromCharCode(97+i)));
  if(job.revision===4)return d3ValidRecord(job);
  if(w.baselineCaptured!==!!w.baseline||w.baseline&&canonical(w.baseline)!==canonical(details(variant(job.variant),'patient',3))||w.observed&&(!w.baselineCaptured||canonical(w.observed)!==canonical(details(variant(job.variant),'trip',3))||!Number.isSafeInteger(w.observedTrip)||w.observedTrip<=job.startTrip)||!w.observed&&w.observedTrip!==null||w.noChanges&&w.marked.length||(!w.observed&&(w.noChanges||w.marked.length)))return false;
  return !job.done.difference||observationAnswer(w);
 }
 if(![4,5].includes(job?.revision))return true;if(!['k2','d1'].includes(id)||!job.work||typeof job.work!=='object'||Array.isArray(job.work)||Object.keys(job).some(k=>!['active','done','count','startTrip','revision','variant','work'].includes(k))||typeof job.active!=='boolean'||!Number.isSafeInteger(job.count)||job.count<0||!Number.isSafeInteger(job.startTrip)||job.startTrip<0||!job.done||typeof job.done!=='object'||Array.isArray(job.done)||Object.entries(job.done).some(([key,value])=>!(id==='k2'?['linen','deliver']:['bell407','bell408']).includes(key)||value!==true))return false;
 const w=job.work;if(canonical(w)!==canonical(restoreWork(id,w,variant(job.variant),job.revision)))return false;
 if(id==='k2'){
  if(!((!w.placed.length&&!w.selectedPiece)||w.preparationStarted)||w.reserveGranted&&!w.shortageNoted)return false;
  if(job.revision===4)return true;
  const draft=w.draftScene;
  if(draft.required!==(job.active?job.count===0:job.count===1))return false;
  if(w.preparationStarted&&!job.done.linen||job.done.deliver&&(!w.preparationStarted||w.placed.length!==2))return false;
  return !draft.required||((!draft.method||w.preparationStarted)&&draft.spread===w.placed.includes('sheet')&&(!w.placed.length&&!w.selectedPiece||!!draft.method));
 }
 if(w.order!=='d1:'+(job.active?job.count+1:job.count))return false;
 if(job.revision===5&&(!w.authorized||!w.escortScheduled||!w.postNotified))return false;
 for(const room of callRooms){const p=w.services[room],a=p.authorization,initial=w.initial[room];
  if(job.revision===5){
   const step='bell'+room.slice(4),diagnostic=w.diagnostics[step];
   if(job.done[step]&&(!diagnostic.inspected||!diagnostic.tested||diagnostic.selected[0]!==initial.condition))return false;
   if(!!a!==!!(job.done[step]&&initial.condition!=='working'))return false;
   if((p.inspected||p.selected.length||p.tested||p.confirmed)&&!a)return false;
   if(p.selected.length&&!p.inspected||p.performed&&!p.selected.length)return false;
   if(p.performed&&p.selected[0]!==serviceOptions(room,initial.condition,variant(job.variant)).find(record=>
    record.equipmentId===callEquipment(room).id&&record.connector===callEquipment(room).connector&&record.postAddress===callEquipment(room).postAddress)?.id)return false;
   if(!job.active&&(!job.done[step]||initial.condition!=='working'&&!p.confirmed))return false;
  }
  if(a&&(!w.authorized||Object.keys(a).sort().join(',')!=='order,revision,room'||a.order!==w.order||a.room!==room||a.revision!==initial.revision))return false;
  if(p.performed&&(!a||p.serviceRevision!==a.revision+1)||p.tested&&!p.performed||p.confirmed&&(!p.tested||p.responseAddress!==callEquipment(room).postAddress)||p.responseAddress!==null&&!callRooms.some(r=>callEquipment(r).postAddress===p.responseAddress))return false;
 }
 return true;
}
function callDiagnosis(s,step){
 const j=s.jobs?.d1;if(![4,5].includes(j?.revision))return diagnosis(variant(j?.variant),step);
 const condition=j.work.initial?.['ward'+step.slice(4)]?.condition||'unassessed';
 return{type:condition,connected:condition==='unassessed'?null:condition!=='disconnected',indicator:condition==='working'||condition==='noResponse'?'on':'off',response:condition==='working'?'Пост: «'+step.slice(4)+', вызов принят».':'Ответ поста не поступил.'};
}
function serviceOptions(room,cause,v){const e=callEquipment(room),other=callEquipment(room==='ward407'?'ward408':'ward407');return rotate([
 {equipmentId:e.id,connector:e.connector,postAddress:e.postAddress},
 {equipmentId:other.id,connector:e.connector,postAddress:e.postAddress},
 {equipmentId:e.id,connector:cause==='noResponse'?e.connector:'КС-3',postAddress:cause==='noResponse'?other.postAddress:e.postAddress}
 ],v).map((x,i)=>({id:['service-a','service-b','service-c'][i],...x,label:'Запись №'+room.slice(4)+'-'+String(i+1).padStart(2,'0')}));}
// Keep each record's identity and fields together. Change presentation only
// after assigning the record numbers for this issued order.
function orderServiceRecords(records, orderId, room){
 const match=typeof orderId==='string'&&/^d1:([1-9]\d*)$/.exec(orderId);
 const sequence=match&&match[0]===orderId?Number(match[1]):NaN;
 if(!Number.isSafeInteger(sequence)||!callRooms.includes(room)||!Array.isArray(records)||records.length!==3)return [];
 const dense=Array.from(records);
 if(dense.some(record=>typeof record?.id!=='string'||!record.id)||new Set(dense.map(record=>record.id)).size!==dense.length)return [];
 dense.sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0);
 return rotate(dense,(sequence-1)%3+(room==='ward408'?1:0));
}
function serviceRecords(job, room, cause, v){
 const records=serviceOptions(room,cause,v);
 return job.revision===5?orderServiceRecords(records,job.work.order,room):records;
}
const escortNotice='Техник уже в палате и на связи с постом. Запишите свои наблюдения: технику нужно ваше подтверждение для обслуживания.';
function serviceReady(s){const j=s.jobs?.d1;if(![4,5].includes(j?.revision))return false;const w=j.work;if(!w.authorized||!validRecord('d1',j))return false;return callRooms.every(room=>{const step='bell'+room.slice(4),d=w.diagnostics[step],initial=w.initial[room],e=s.world?.callEquipment?.[room];if(!j.done?.[step]||!d.inspected||!d.tested||d.selected[0]!==initial.condition||!e||e.condition!=='working')return false;if(initial.condition==='working')return e.revision===initial.revision;const p=w.services[room];return p.performed&&p.tested&&p.confirmed&&p.serviceRevision===e.revision&&e.verified&&p.responseAddress===callEquipment(room).postAddress;});}
function inspectionData(v){
 const kit=['Перевязочный','Диагностический','Осмотровой'][v],lot=['Б-17','В-24','А-09'][v],target=[1,3,0][v];
 const otherKit=['Диагностический','Осмотровой','Перевязочный'][v],otherLot=['Б-71','В-42','А-90'][v];
 const values=[{kit,lot:otherLot,seal:'целая'},{kit,lot,seal:'повреждена'},{kit:otherKit,lot,seal:'целая'},{kit,lot,seal:'целая'}];
 const ordered=[];let j=0;for(let i=0;i<4;i++)ordered.push(i===target?values[3]:values[j++]);
 return{request:{kit,lot},items:ordered.map((details,i)=>({id:'pack-'+i,name:'Контейнер '+(i+1),details}))};
}
function packingData(v,r=2,w={}){
 const size=['М','Л','С'][v],other=['Л','С','М'][v];
 const measures={М:['150 × 215 см','70 × 70 см'],Л:['180 × 220 см','70 × 70 см'],С:['120 × 200 см','50 × 70 см']};
 const items=[['Простыня',size,'чистая упаковка'],['Наволочка',size,'чистая упаковка'],['Простыня',other,'чистая упаковка'],['Наволочка',size,'повреждена упаковка'],['Простыня',size,'загрязнена'],['Наволочка',other,'чистая упаковка']].map(([type,size,condition],i)=>({id:'linen-'+i,name:type,type,size,condition,measure:measures[size][type==='Простыня'?0:1]}));
 const special=r>=3&&v===1;if(special){const reserve=items.find(x=>x.id==='linen-1');reserve.size='М';reserve.measure='70 × 70 см';reserve.unavailable=!w.reserveGranted;reserve.availabilityNote=w.reserveGranted?'Замена разрешена Кларой по физическому размеру.':'Резерв поста: требуется разрешение Клары.';}
 return{request:{destination:'406',size,components:['Простыня','Наволочка'],markingNote:'Буква на упаковке — учётная маркировка парного комплекта. Физический размер указан отдельно.',...(special?{missingComponent:'Наволочка с маркировкой Л',neededMeasure:'70 × 70 см'}:{})},items:rotate(items,v*2),...(r>=3?{shortageNoted:!!w.shortageNoted,reserveGranted:!!w.reserveGranted}:{}),...(special&&w.reserveGranted?{authorizedSubstitution:{itemId:'linen-1',mark:'М',measure:'70 × 70 см'}}:{})};
}
function compareData(v){
 const a={time:['09:15','10:25','11:40'][v],ward:['406','407','408'][v],signature:'Клара',lot:['Б-17','В-24','А-09'][v]},b={...a};
 if(v===0)b.signature='';if(v===1)b.time='10:35';if(v===2){b.ward='406';b.signature='';}
 const fieldNames={time:'Время',ward:'Палата',signature:'Подпись',lot:'Комплект'};
 return{documents:[a,b].map((values,i)=>({title:i?'Копия в журнале':'Лист процедурной',fields:Object.entries(values).map(([id,value])=>({id,label:fieldNames[id],value}))}))};
}
const caseChoiceIds={room:['matches','differs','unknown'],time:['error','matchesActual','unknown'],author:['clara','other','unknown']};
function caseConclusions(raw){
 if(!raw||typeof raw!=='object'||Array.isArray(raw))return{};
 return Object.fromEntries(Object.entries(caseChoiceIds).filter(([field,choices])=>Object.hasOwn(raw,field)&&choices.includes(raw[field])).map(([field])=>[field,raw[field]]));
}
function caseAnswer(w){return w.sourcesRead===true&&w.conclusions?.room==='differs'&&w.conclusions?.time==='matchesActual'&&w.conclusions?.author==='unknown';}
function caseData(){
 const document=(number,title,fields)=>({id:'source-'+number,number:String(number),caseId:'46',title,fields:fields.map(([id,label,value])=>({id,label,value}))});
 return{caseId:'46',documents:[
  document(1,'Направление',[['ward','Палата','406'],['plan','План','09:15'],['lot','Комплект','Б-17'],['status','Отметка','Назначено']]),
  document(2,'Лист процедуры',[['ward','Палата','406'],['fact','Факт','09:25'],['lot','Комплект','Б-17'],['signature','Подпись','Неразборчива']]),
  document(3,'Копия в журнале',[['ward','Палата','407'],['fact','Факт','09:25'],['lot','Комплект','Б-17'],['signature','Подпись','Клара']])
 ],issues:[
  {id:'room',title:'Номер палаты в копии',sources:['source-1','source-2','source-3'],choices:[{id:'matches',label:'Совпадает с источниками'},{id:'differs',label:'Есть расхождение'},{id:'unknown',label:'Недостаточно данных'}]},
  {id:'time',title:'Время в копии',sources:['source-1','source-2','source-3'],choices:[{id:'error',label:'Не совпадает со временем проведения'},{id:'matchesActual',label:'Совпадает со временем проведения'},{id:'unknown',label:'Время проведения не установлено'}]},
  {id:'author',title:'Имя исполнителя в копии',sources:['source-2','source-3'],choices:[{id:'clara',label:'Подпись Клары подтверждена'},{id:'other',label:'Установлен другой исполнитель'},{id:'unknown',label:'Имя в копии не подтверждено оригиналом'}]}
 ]};
}
function diagnosis(v,step){
 const type=['working','disconnected','noResponse'][(v+(step==='bell408'?1:0))%3];
 return{type,connected:type!=='disconnected',indicator:type==='disconnected'?'off':'on',response:type==='working'?'Пост: «'+step.slice(4)+', вызов принят».':'Ответ поста не поступил.'};
}
function timelineData(v,r=2,w={}){
 const times=[['08:05','08:20','08:35','08:50'],['09:10','09:25','09:40','09:55'],['10:15','10:30','10:45','11:00']][v];
 const rooms=['407','408','406','Пост'],notes=['Проверка сигнала','Осмотр палаты','Передача белья','Журнал возвращён на пост'];
 const cards=times.map((time,i)=>{const id='entry-'+String.fromCharCode(97+i),unreadable=r>=3&&i===1,read=unreadable&&!!w.reverseRead?.includes(id);return{id,time:unreadable?null:time,room:rooms[i],note:notes[i],...(r>=3?{timeState:unreadable?'unreadable':'readable',reverseAvailable:unreadable,reverseRead:read,reverseText:read?'После проверки сигнала палаты 407; до передачи белья палаты 406.':null}:{})};});return{cards:rotate([cards[2],cards[0],cards[3],cards[1]],v)};
}
function details(v,mode,r=2){
 const base=[{time:'08:00',route:'Палаты 404–406',mark:'Круг'},{time:'07:40',route:'Палаты 404–408',mark:'Полоса'},{time:'09:10',route:'Палаты 405–408',mark:'Круг'}][v];
 const result={...base};if(mode==='trip'){if(r===3){if(v===1)result.mark='Крест';if(v===2){result.time='03:00';result.route='Палаты 404–406';result.mark='Крест';}}else{if(v===0)result.time='03:00';if(v===1)result.mark='Крест';if(v===2)result.route='Палаты 404–406';}}return result;
}
function restoreObservation(value){if(!value||typeof value!=='object'||Array.isArray(value))return null;const result={};for(const key of ['time','route','mark']){if(typeof value[key]!=='string'||value[key].length>80)return null;result[key]=value[key];}return result;}
function captureObservation(s){const j=s.jobs?.d3;if(!j?.active||j.revision!==3||!j.work?.baselineCaptured||j.work.observed||s.mode!=='trip'||s.room!=='A'||s.trip<=j.startTrip)return null;return{...clone(j.work),observed:details(variant(j.variant),'trip',3),observedTrip:s.trip};}
function observationAnswer(w){if(!w.baselineCaptured||!w.baseline||!w.observed)return false;const expected=Object.keys(labels).filter(k=>w.baseline[k]!==w.observed[k]);return w.noChanges?expected.length===0:w.marked.length>0&&same(w.marked,expected);}
const fields=values=>Object.entries(values).map(([id,value])=>({id,label:labels[id],value}));
function observation(s){const j=s.jobs?.d3;if(j?.active&&j.revision===4&&j.work.subjectId==='signA'){const snapshot=s.mode==='trip'?j.work.observed:j.work.baseline||j.work.baselinePreview;return clone(snapshot||d3Snapshot('signA',variant(j.variant),s.mode));}if(j?.active&&[2,3].includes(j.revision)){if(j.revision===3)return clone(s.mode==='trip'?(j.work.observed||details(variant(j.variant),'trip',3)):(j.work.baseline||details(variant(j.variant),'patient',3)));return details(variant(j.variant),s.mode);}return{time:s.mode==='trip'?'03:00':'08:00',route:'Палаты 404–408',mark:'—'};}
const d3Subjects = Object.freeze({
 signA: {room:'A', label:'Табличка коридора A', actionOp:'inspect', actionLabel:'Прочитать табличку', fields:['time','route','mark']},
 bed406: {room:'ward406', label:'Край простыни в палате 406', actionOp:'lift', actionLabel:'Поднять свободный край', fields:['hem','stitch']},
 call407: {room:'ward407', label:'Кнопка вызова палаты 407', actionOp:'call', actionLabel:'Проверить вызов', fields:['indicator','reply']}
});
const d3Labels={...labels,hem:'Внутренний подгиб',stitch:'Шов',indicator:'Индикатор',reply:'Ответ поста'};
const d3Replies=[
 {id:'ward407',label:'407, вызов принят'},
 {id:'ward408',label:'408, вызов принят'},
 {id:'none',label:'Ответа не было'}
];

function d3Available(s,id) {
 const openB=s.flags?.unlockB===true;
 const openC=openB&&s.flags?.unlockC===true;
 if(id==='signA')return {available:true,reason:'Доступна без других поручений.'};
 if(id==='bed406'){
  const linen=s.world?.linen406;
  if(!openB)return {available:false,reason:'Сначала откройте проход в секцию B.'};
  const pending=s.jobs?.k2;
  if(pending?.active&&pending.work?.preparationStarted&&!pending.done?.deliver)return {available:false,reason:'Сначала завершите начатую смену белья.'};
  if(!linen?.prepared||!linen.reviewed)return {available:false,reason:'Нужна подготовленная и принятая Кларой кровать 406.'};
  return {available:true,reason:'Можно осмотреть внутренний подгиб, не перестилая кровать.'};
 }
 const call=s.world?.callEquipment?.ward407;
 if(!openC)return {available:false,reason:'Сначала откройте проход в секцию C.'};
 if(call?.condition!=='working'||call.verified!==true)return {available:false,reason:'Нужен исправный и подтверждённый вызов палаты 407.'};
 return {available:true,reason:'Проверьте индикатор и ответ поста.'};
}
function d3Provenance(s,id) {
 if(id==='signA')return {room:'A',order:null,revision:null};
 if(id==='bed406'){
  const linen=s.world?.linen406;
  return linen?.prepared&&linen.reviewed?{room:'ward406',order:linen.order,revision:linen.revision}:null;
 }
 const equipment=s.world?.callEquipment?.ward407;
 return equipment?.condition==='working'&&equipment.verified===true
  ?{room:'ward407',order:s.world?.calls?.ward407?.order||null,revision:equipment.revision}
  :null;
}
function d3ValidProvenance(p,id) {
 const subject=d3Subjects[id];
 if(!subject||!p||typeof p!=='object'||p.room!==subject.room)return false;
 if(id==='signA')return p.order===null&&p.revision===null;
 if(!Number.isSafeInteger(p.revision)||p.revision<0)return false;
 if(id==='bed406')return typeof p.order==='string'&&/^k2:[1-9]\d*$/.test(p.order)&&[3,4,5].includes(p.revision);
 return p.order===null||typeof p.order==='string'&&/^d1:[1-9]\d*$/.test(p.order);
}
function d3Snapshot(id,v,mode) {
 if(id==='signA')return details(v,mode,3);
 if(id==='bed406'){
  const first={hem:'Ровный',stitch:'Целый'};
  if(mode==='patient'||v===0)return first;
  return {...first,hem:'Смят у края',stitch:v===1?'Целый':'Видна разошедшаяся строчка'};
 }
 const reply=mode==='patient'?d3Replies[0]:d3Replies[v];
 return {indicator:'Горит',reply:reply.label};
}
function d3RestoreSnapshot(value,id) {
 if(!value||typeof value!=='object'||Array.isArray(value)||!d3Subjects[id])return null;
 const entries=d3Subjects[id].fields.map(field=>[field,value[field]]);
 if(entries.some(([,text])=>typeof text!=='string'||text.length>100))return null;
 return Object.fromEntries(entries);
}
function d3RestoreWork(raw) {
 const subjectId=Object.hasOwn(d3Subjects,raw.subjectId)?raw.subjectId:null;
 const provenance=d3ValidProvenance(raw.provenance,subjectId)
  ?{room:raw.provenance.room,order:raw.provenance.order,revision:raw.provenance.revision}
  :null;
 return {
  subjectId,provenance,
  baselinePreview:d3RestoreSnapshot(raw.baselinePreview,subjectId),
  baselineCaptured:raw.baselineCaptured===true,
  baseline:d3RestoreSnapshot(raw.baseline,subjectId),
  observed:d3RestoreSnapshot(raw.observed,subjectId),
  observedTrip:Number.isSafeInteger(raw.observedTrip)&&raw.observedTrip>=0?raw.observedTrip:null,
  marked:safeArray(raw.marked,d3Subjects[subjectId]?.fields||[]),
  noChanges:raw.noChanges===true,
  replySelected:d3Replies.some(option=>option.id===raw.replySelected)?raw.replySelected:null
 };
}
function d3Delta(w) {
 return w.baseline&&w.observed?d3Subjects[w.subjectId].fields.filter(field=>w.baseline[field]!==w.observed[field]):[];
}
function d3Answer(w) {
 if(!w.baselineCaptured||!w.observed)return false;
 if(w.subjectId==='call407')return d3Replies.find(option=>option.id===w.replySelected)?.label===w.observed.reply;
 const changed=d3Delta(w);
 return w.noChanges?changed.length===0:w.marked.length>0&&same(w.marked,changed);
}
function d3Fields(snapshot) {
 return Object.entries(snapshot||{}).map(([id,value])=>({id,label:d3Labels[id],value}));
}
function d3ValidRecord(job) {
 const w=job.work;
 const patient = w.subjectId ? d3Snapshot(w.subjectId,job.variant,'patient') : null;
 const trip = w.subjectId ? d3Snapshot(w.subjectId,job.variant,'trip') : null;
 const sameValue = (a,b) => canonical(a)===canonical(b);
 if(w.baselinePreview&&(!w.provenance||!sameValue(w.baselinePreview,patient)))return false;
 if(!w.baselinePreview&&w.provenance)return false;
 if(w.baselineCaptured!==!!w.baseline||w.baseline&&!sameValue(w.baseline,w.baselinePreview))return false;
 if(w.observed&&(!w.baselineCaptured||!sameValue(w.observed,trip)||w.observedTrip===null||w.observedTrip<=job.startTrip))return false;
 if(!w.observed&&(w.observedTrip!==null||w.noChanges||w.marked.length||w.replySelected!==null))return false;
 if(w.noChanges&&w.marked.length||w.subjectId==='call407'&&(w.noChanges||w.marked.length)||w.subjectId!=='call407'&&w.replySelected!==null)return false;
 return !job.done.difference||d3Answer(w);
}
function d3Route(s,j) {
 const w=j.work;
 if(j.done?.difference)return {room:'doctor',mode:'patient',action:'claim:d3',text:'Передайте врачу карточку двух наблюдений.'};
 if(!w.subjectId)return {room:'doctor',mode:'patient',action:'job:baseline',text:'Выберите у врача предмет наблюдения.'};
 const subject=d3Subjects[w.subjectId];
 if(!w.baselineCaptured&&!w.baselinePreview&&!d3Available(s,w.subjectId).available)return {room:'doctor',mode:'patient',action:'job:baseline',text:'Предмет пока недоступен. Выберите у врача другой предмет или вернитесь позже.'};
 if(!w.baselineCaptured)return {room:subject.room,mode:'patient',action:'job:baseline',text:'Осмотрите выбранный предмет и запишите исходное наблюдение.'};
 if(s.mode==='trip'&&s.trip<=j.startTrip)return {room:subject.room,mode:'patient',text:'Для повторного наблюдения выйдите из Трипа, затем войдите снова.'};
 return {room:subject.room,mode:'trip',action:'job:difference',text:'Повторите то же действие с выбранным предметом и запишите результат.'};
}
function d3Board(s,step,w,base) {
 if(step==='baseline'&&s.mode==='patient'&&s.room==='doctor'&&!w.baselineCaptured){
  return {...base,kind:'subjectChoice',title:'Выбрать предмет наблюдения',
   instruction:'Дважды выполните одно и то же наблюдение. Табличка доступна без других поручений.',
   options:Object.entries(d3Subjects).map(([id,subject])=>({id,label:subject.label,room:subject.room,...d3Available(s,id)})),selected:w.subjectId};
 }
 const subject=d3Subjects[w.subjectId];
 if(!subject||s.room!==subject.room)return null;
 const publicSubject={...base,subjectId:w.subjectId,actionOp:subject.actionOp,actionLabel:subject.actionLabel,subjectLabel:subject.label};
 if(step==='baseline'&&s.mode==='patient'&&!w.baselineCaptured)return {
  ...publicSubject,kind:'subjectBaseline',title:'Первичное наблюдение · '+subject.label,
  instruction:'Выполните действие с предметом и сохраните то, что удалось наблюдать.',
  details:d3Fields(w.baselinePreview),recorded:false
 };
 if(step!=='difference'||s.mode!=='trip'||!w.baselineCaptured||s.trip<=s.jobs.d3.startTrip||s.jobs.d3.done?.difference)return null;
 const isCall=w.subjectId==='call407';
 return {...publicSubject,kind:'subjectDifference',title:'Повторное наблюдение · '+subject.label,
  instruction:isCall?'Повторите вызов. Укажите ответ поста по тексту, включая отсутствие ответа.':
   'Повторите то же действие. Отметьте отличия строк или явно подтвердите совпадение.',
  baseline:d3Fields(w.baseline),current:d3Fields(w.observed),observationCaptured:!!w.observed,
  marked:w.marked,noChanges:w.noChanges,allowNoChanges:!isCall,
  replies:isCall?d3Replies.map(option=>({...option})):[],replySelected:w.replySelected
 };
}

function board(s,actionId){
 const step=typeof actionId==='string'&&actionId.startsWith('job:')?actionId.slice(4):'',jobId=owner[step],job=s.jobs?.[jobId];if(!job?.active||!supportsRevision(jobId,job.revision))return null;
 const v=variant(job.variant),w=restoreWork(jobId,job.work,v,job.revision),base={jobId,actionId,revision:job.revision,brief:brief(jobId,job.revision)};
 if(step==='tag'){const d=inspectionData(v);return{...base,kind:'inspection',title:'Приёмка контейнера',instruction:'Сверьте заявку с маркировкой и состоянием пломбы. Подтвердите пригодный комплект.',request:d.request,items:d.items.map(x=>({id:x.id,name:x.name,inspected:w.inspected.includes(x.id),details:w.inspected.includes(x.id)?x.details:null})),inspected:w.inspected,selected:w.selected};}
 if(step==='linen')return{...base,kind:'packing',title:'Комплект для палаты 406',instruction:'Соберите чистый комплект с указанной маркировкой. Непригодные упаковки оставьте на полке.',...packingData(v,job.revision,w),selected:w.selected};
 if(step==='linenReserve'&&job.revision>=3&&v===1)return{...base,kind:'clarification',title:'Уточнение комплекта для 406',instruction:'Наволочка нужной маркировки отсутствует в доступной выдаче. Сопоставьте физический размер и запросите разрешение на замену.',request:{neededType:'Наволочка',neededMeasure:'70 × 70 см'},options:[{id:'reserve-same-size',measure:'70 × 70 см',label:'Наволочка М · резерв поста'},{id:'reserve-small',measure:'50 × 70 см',label:'Наволочка С · резерв поста'}],selected:w.selectedReserve,shortageNoted:w.shortageNoted,reserveGranted:w.reserveGranted};
 if(step==='deliver'){const parcel=s.cargo.includes('linen'),d=packingData(v,job.revision,w),kit=d.items.filter(x=>w.selected.includes(x.id)&&x.condition==='чистая упаковка').map(x=>({id:x.type==='Простыня'?'sheet':'pillowcase',type:x.type,measure:x.measure})),parcelDetails=parcel?{components:d.request.components.slice(),size:d.request.size,items:(job.revision>=3?kit:d.items.filter(x=>x.size===d.request.size&&x.condition==='чистая упаковка').map(x=>({type:x.type,measure:x.measure})))}:null;
 if(job.revision>=3)return{...base,kind:'bedmaking',title:'Подготовить кровать 406',instruction:job.revision===5?'Подготовьте кровать с принесённым бельём.':'Выберите вещь из принесённого комплекта и положите на соответствующую часть кровати. Завершённая подготовка останется в палате.',request:{destination:'406'},parcel,items:parcel?kit:[],selectedPiece:w.selectedPiece,placed:w.placed,...(job.revision>=4?{preparationStarted:w.preparationStarted}:{}),...(job.revision===5?{draftScene:w.draftScene}:{}),targets:[{id:'sheetZone',label:'Матрас · постелить простыню'},{id:'pillowZone',label:'Подушка · сменить наволочку'}],...(parcelDetails?{parcelDetails}:{})};
 return{...base,kind:'delivery',title:'Передача комплекта',instruction:'Передайте принесённый комплект на отмеченную кровать. Квитанция останется для сдачи поручения.',request:{destination:'406'},parcel,...(parcelDetails?{parcelDetails}:{})};}
 if(step==='copies'){if(job.revision===3)return{...base,kind:'caseCompare',title:'Сверка медицинских записей · дело №46',instruction:'Сравните документы одной процедуры. Источники показаны рядом; нечитаемые сведения остаются неизвестными.',...caseData(),sourcesRead:w.sourcesRead,conclusions:{...w.conclusions}};return{...base,kind:'compare',title:'Сверка записей',instruction:'Отметьте только поля, в которых записи расходятся. Не дописывайте неизвестные сведения.',...compareData(v),marked:w.marked};}
 if(step==='bell407'||step==='bell408'){const d=callDiagnosis(s,step),p=w.diagnostics[step];return{...base,kind:'diagnostic',title:'Проверка вызова '+step.slice(4),instruction:'Осмотрите подключение, проверьте вызов и запишите то, что удалось наблюдать.',...(job.revision===5?{escort:escortNotice}:{}),room:step.slice(4),inspected:p.inspected,tested:p.tested,connector:p.inspected?{connected:d.connected,text:d.connected===null?'Состояние подключения не подтверждено. Нужен осмотр персонала.':d.connected?'Разъём установлен, провод цел.':'Разъём отсоединён от кнопки.'}:null,indicator:p.tested?d.indicator:'idle',response:p.tested?d.response:null,reports:[...(job.revision>=4?[{id:'unassessed',label:'Состояние требует обследования персоналом'}]:[]),{id:'working',label:'Сигнал и ответ получены'},{id:'disconnected',label:'Нет подключения кнопки'},{id:'noResponse',label:'Сигнал есть, ответа поста нет'}],selected:p.selected};}
 if(jobId==='d1'&&job.revision===4&&step==='callReview')return{...base,kind:'callReview',title:'Разрешение на обслуживание вызовов',instruction:'Сверьте оба первичных акта. Разрешение привязано к этой заявке и конкретным узлам; награда выдаётся после контрольных вызовов.',authorized:w.authorized,reports:callRooms.map(room=>{const d=callDiagnosis(s,'bell'+room.slice(4));return{room,label:room.slice(4),report:d.type,connected:d.connected,indicator:d.indicator,response:d.response,needsService:d.type!=='working'};})};
 if(jobId==='d1'&&job.revision>=4&&/^callService40[78]$/.test(step)){const room='ward'+step.slice(-3),p=w.services[room],cause=w.initial[room].condition,equipment=callEquipment(room);return{...base,kind:'callService',title:'Обслуживание вызова '+room.slice(4),instruction:job.revision===5?'Техник сверяется с постом на месте. Прочитайте шильдик и выберите запись, совпадающую с оборудованием, штатным соединением и адресом.':cause==='noResponse'?'На посту сверяют регистрацию адреса: светящийся индикатор ещё не подтверждает ответ нужной палаты.':'Персонал сверяет узел и штатное соединение по разрешению врача. Не выбирайте детали по одному похожему признаку.',room,label:room.slice(4),cause,equipment,...(job.revision===5?{escort:'Техник рядом и ждёт выбранную запись. Обслуживание он выполнит сам.'}:{}),inspected:p.inspected,evidence:p.inspected?{equipmentId:equipment.id,connector:equipment.connector,postAddress:equipment.postAddress,observedRegistration:cause==='noResponse'?'Адрес палаты не закреплён в журнале поста':cause==='unassessed'?'Нужна проверка штатного узла персоналом':'Штатное соединение отсоединено',text:'Разрешение '+w.order+' · палата '+room.slice(4)}:null,options:p.inspected?serviceRecords({...job,work:w},room,cause,v):[],selected:p.selected,performed:p.performed};}
 if(jobId==='d1'&&job.revision>=4&&/^callRetest40[78]$/.test(step)){const room='ward'+step.slice(-3),p=w.services[room];return{...base,kind:'callRetest',title:'Контрольный вызов '+room.slice(4),instruction:p.tested?'Сверьте адрес в полученном ответе поста и подтвердите контрольный вызов.':'Проверьте вызов после обслуживания. Подтвердите результат только после ответа поста с адресом этой палаты.',room,label:room.slice(4),...(job.revision===5?{escort:'Техник закончил обслуживание. Ответ поста проверяете вы.'}:{}),tested:p.tested,indicator:p.tested?'on':'idle',response:p.tested?(p.responseAddress?'Пост: «'+room.slice(4)+', вызов принят».':'Ответ нужной палаты не поступил.'):null,responseAddress:p.responseAddress,confirmed:p.confirmed};}
 if(step==='log')return{...base,kind:'timeline',title:'Журнал обхода',...(job.revision===4?{timelineMap:true}:{}),instruction:job.revision>=3?'Восстановите порядок по читаемому времени и записи на обороте. Неразборчивое время не дописывайте.':'Восстановите хронологию по времени записей. Поля исполнителя не дописывайте.',...timelineData(v,job.revision,w),order:w.order};
 if(jobId==='d3'&&job.revision===4)return d3Board(s,step,w,base);
 if(step==='baseline')return{...base,kind:'baseline',title:'Первичное наблюдение',instruction:'Осмотрите табличку коридора и сохраните её показания в карточке.',details:fields(w.baseline||details(v,'patient',job.revision)),recorded:w.baselineCaptured};
 if(step==='difference')return{...base,kind:'difference',title:'Повторное наблюдение',instruction:job.revision===3?'Сопоставьте сохранённую карточку с табличкой. Отметьте все наблюдаемые отличия или явно подтвердите, что их нет.':'Сопоставьте сохранённую карточку с табличкой перед вами. Отметьте наблюдаемое расхождение.',baseline:fields(w.baseline||details(v,'patient',job.revision)),current:fields(w.observed||details(v,'trip',job.revision)),marked:w.marked,...(job.revision===3?{allowNoChanges:true,noChanges:w.noChanges,observationCaptured:!!w.observed}:{})};
 return null;
}
function same(a,b){return a.length===b.length&&a.every(x=>b.includes(x));}
function operate(s,actionId,op,value){
 const b=board(s,actionId);if(!b)return{ok:false,message:'Рабочий лист недоступен.'};const job=s.jobs[b.jobId],w=clone(restoreWork(b.jobId,job.work,job.variant,job.revision)),step=actionId.slice(4),v=variant(job.variant);
 const fail=message=>({ok:false,message}),ok=(message,complete=null)=>({ok:true,message,work:w,complete});
 const toggle=(key,id,allowed,max=Infinity)=>{if(!allowed.includes(id))return false;w[key]=w[key].includes(id)?w[key].filter(x=>x!==id):max===1?[id]:w[key].concat(id).slice(0,max);return true;};
 if(b.kind==='inspection'){
  const d=inspectionData(v),allowed=d.items.map(x=>x.id);
  if(op==='inspect'){if(!allowed.includes(value))return fail('Такого контейнера на лотке нет.');if(!w.inspected.includes(value))w.inspected.push(value);return ok('Маркировка и пломба осмотрены.');}
  if(op==='select'){if(!toggle('selected',value,allowed,1))return fail('Выберите контейнер с лотка.');return ok('Выбор в листе приёмки сохранён.');}
  if(op==='submit'){const item=d.items.find(x=>x.id===w.selected[0]);if(!item||!w.inspected.includes(item.id))return fail('Осмотрите выбранный контейнер перед подтверждением.');const problems=[];if(item.details.kit!==d.request.kit)problems.push('название на осмотренной упаковке отличается от заявки');if(item.details.lot!==d.request.lot)problems.push('партия на осмотренной упаковке отличается от заявки');if(item.details.seal!=='целая')problems.push('на осмотренной упаковке повреждена пломба');if(problems.length)return fail('Комплект не соответствует заявке: '+problems.join('; ')+'.');return ok('Комплект проверен. Бирка приложена к листу приёмки.','tag');}
 }
 if(b.kind==='packing'){
  const d=packingData(v,job.revision,w),allowed=d.items.filter(x=>!x.unavailable).map(x=>x.id);
  if(op==='noteShortage'){if(job.revision<3||v!==1||w.reserveGranted)return fail('Для этого комплекта уточнение не требуется.');w.shortageNoted=true;return ok('Недостача записана. Уточните допустимую замену у Клары, прежде чем брать резерв поста.');}
  if(op==='select'){if(!toggle('selected',value,allowed))return fail('Вещь недоступна: резерв поста нельзя брать без разрешения.');return ok('Состав комплекта сохранён.');}
  if(op==='submit'){const selected=d.items.filter(x=>w.selected.includes(x.id)),types=selected.map(x=>x.type),problems=[];if(selected.length!==2)problems.push('сейчас выбрано вещей: '+selected.length+' из 2');else if(new Set(types).size!==d.request.components.length||!same(types,d.request.components))problems.push('в комплекте нужны два разных предмета');if(selected.some(x=>x.unavailable))problems.push('резерв поста ещё не разрешён');if(selected.some(x=>x.size!==d.request.size&&x.id!==d.authorizedSubstitution?.itemId))problems.push('на выбранных упаковках есть другая маркировка без разрешённой замены');if(selected.some(x=>x.condition!=='чистая упаковка'))problems.push('среди выбранного есть загрязнённая или повреждённая упаковка');if(problems.length)return fail('Нужны простыня и наволочка указанной маркировки в чистых целых упаковках: '+problems.join('; ')+'.');return ok('Комплект упакован и помечен для палаты 406.','linen');}
 }
 if(b.kind==='clarification'){
  if(!w.shortageNoted||w.reserveGranted)return fail('Сначала зафиксируйте недостачу в бельевой.');
  if(op==='select'){if(!b.options.some(x=>x.id===value))return fail('Выберите один из описанных резервных комплектов.');w.selectedReserve=[value];return ok('Вариант замены выбран для согласования.');}
  if(op==='submit'){const choice=b.options.find(x=>x.id===w.selectedReserve[0]);if(!choice||choice.measure!==b.request.neededMeasure)return fail('Размер замены не совпадает с заявкой. Нужна наволочка '+b.request.neededMeasure+'.');w.reserveGranted=true;return ok('Клара: разрешаю наволочку М из резерва поста — физический размер совпадает. Заберите её в бельевой.','linenReserve');}
 }
 if(b.kind==='bedmaking'){
  if(!b.parcel)return fail('Комплект должен оставаться при вас до завершения подготовки.');
  const draft=w.draftScene;
  if(job.revision>=4&&op==='startBedPreparation'){
   if(job.revision===5&&w.preparationStarted)return fail('Подготовка уже началась.');
   w.preparationStarted=true;
   const message=draft?.required?'Сквозняк приподнял край. Выберите, как его удержать.':'Подготовка начата. Выберите принесённую вещь и её место на кровати.';
   return {...ok(message),effect:{kind:'startBedPreparation'}};
  }
  if(job.revision>=4&&!w.preparationStarted)return fail('Сначала начните подготовку кровати. Новая заявка сама не снимает прежнее бельё.');
  if(op==='chooseMethod'){
   if(!draft?.required||draft.method||!['window','assistance'].includes(value))return fail('Этот способ сейчас недоступен.');
   w.draftScene=bedDraft({required:true,method:value});
   return ok(value==='window'?'Окно прикрыто. Край больше не поднимается.':'Клара придерживает край, пока вы расправляете ткань.');
  }
  if(draft?.required&&!draft.method)return fail('Сначала прикройте окно или попросите Клару придержать край.');
  const placePiece=piece=>{
   w.placed.push(piece);
   w.selectedPiece=null;
   if(w.placed.length<2)return ok(piece==='sheet'?'Простыня расправлена. Наденьте наволочку.':'Наволочка на подушке. Осталась простыня.');
   return ok(job.revision>=4?'Обе вещи размещены. Квитанция для Клары заполнена.':'Кровать 406 подготовлена: чистые простыня и наволочка на своих местах. Квитанция для Клары заполнена.','deliver');
  };
  if(op==='selectPiece'){
   if(!b.items.some(x=>x.id===value)||w.placed.includes(value))return fail('Эта вещь недоступна или уже использована.');
   w.selectedPiece=value;
   return ok(draft?.required&&value==='sheet'?'Проведите ползунок до конца, чтобы расправить простыню.':'Выбрано: '+b.items.find(x=>x.id===value).type+'. Укажите место на кровати.');
  }
  if(op==='spreadSheet'){
   if(!draft?.required||draft.spread||w.selectedPiece!=='sheet'||!b.items.some(item=>item.id==='sheet'))return fail('Сначала выберите простыню из принесённого комплекта.');
   w.draftScene=bedDraft({...draft,spread:true});
   return placePiece('sheet');
  }
  if(op==='place'){
   const required={sheet:'sheetZone',pillowcase:'pillowZone'};
   if(!w.selectedPiece)return fail('Сначала выберите вещь из комплекта.');
   if(required[w.selectedPiece]!==value)return fail('Это место не соответствует выбранной вещи. Простыня нужна на матрасе, наволочка — на подушке.');
   if(draft?.required&&w.selectedPiece==='sheet')return fail('Расправьте простыню ползунком, чтобы закрепить край.');
   if(job.revision===5)return placePiece(w.selectedPiece);
   // Issued legacy orders keep their original placement action and receipt.
   w.placed.push(w.selectedPiece);w.selectedPiece=null;
   return w.placed.length===2?ok(job.revision===4?'Обе вещи размещены. Квитанция для Клары заполнена.':'Кровать 406 подготовлена: чистые простыня и наволочка на своих местах. Квитанция для Клары заполнена.','deliver'):ok('Вещь размещена. Подготовьте оставшуюся часть кровати.');
  }
 }
 if(b.kind==='delivery'&&(op==='deliver'||op==='submit'))return b.parcel?ok('Комплект передан. Получена квитанция для Клары.','deliver'):fail('Принесите упакованный комплект из бельевой.');
 if(b.kind==='caseCompare'){
  if(op==='readSources'){w.sourcesRead=true;return ok('Три исходных документа дела открыты. Их копии доступны в материалах поручения.');}
  if(!w.sourcesRead)return fail('Сначала откройте исходные документы дела.');
  if(job.done?.copies)return fail('Лист сверки уже подтверждён.');
  if(op==='conclude'){
   if(!value||typeof value!=='object'||Array.isArray(value)||Object.keys(value).sort().join(',')!=='choice,field'||typeof value.field!=='string'||typeof value.choice!=='string'||!Object.hasOwn(caseChoiceIds,value.field)||!caseChoiceIds[value.field].includes(value.choice))return fail('Выберите допустимый вывод для указанного поля дела.');
   w.conclusions[value.field]=value.choice;return ok('Вывод выбран и сохранён в черновике. Проверьте весь акт, когда будете готовы.');
  }
  if(op==='submit'){
   const missing=b.issues.filter(issue=>!Object.hasOwn(w.conclusions,issue.id));
   if(missing.length)return fail('Выберите вывод: '+missing.map(issue=>issue.title.toLowerCase()).join(', ')+'. Остальные выбранные выводы сохранены.');
   if(!caseAnswer(w)){
    if(w.conclusions.room!=='differs')return fail('Номер палаты: сопоставьте направление, оригинал и копию одного дела. Два исходных документа важны для проверки записи в журнале. Выбранные выводы не сброшены.');
    if(w.conclusions.time!=='matchesActual')return fail('Время: сопоставьте фактическое время в оригинале и копии. Направление содержит план — это другое поле, оно не заменяет время проведения. Выбранные выводы не сброшены.');
    return fail('Исполнитель: разборчивое имя в копии не делает подпись в оригинале читаемой. Имя в копии не подтверждено оригиналом; это не означает, что Клара не могла выполнить процедуру. Выбранные выводы не сброшены.');
   }
   return ok('Лист сверки обоснован: палата расходится, время проведения перенесено верно, имя в копии не подтверждено оригиналом.','copies');
  }
 }
 if(b.kind==='compare'){
  const d=compareData(v),allowed=d.documents[0].fields.map(x=>x.id);
  if(op==='mark'){if(!toggle('marked',value,allowed))return fail('Такого поля в записях нет.');return ok('Отметки сверки сохранены.');}
  if(op==='submit'){const needed=d.documents[0].fields.filter((x,i)=>x.value!==d.documents[1].fields[i].value).map(x=>x.id);if(same(w.marked,needed))return ok('Подтверждённые расхождения отмечены. Лист сверки готов.','copies');return fail(w.marked.some(x=>!needed.includes(x))?'Среди отметок есть совпадающие поля. Снимите лишние отметки и снова сравните записи.':'Отмечены не все расхождения. Сверьте каждую строку в обеих записях.');}
 }
 if(b.kind==='diagnostic'){
  const p=w.diagnostics[step],d=callDiagnosis(s,step);
  if(op==='inspect'){if(value!==undefined&&value!==null&&value!=='connector')return fail('Осмотрите разъём кнопки.');p.inspected=true;return ok(d.connected===null?'Подключение не подтверждено. Зафиксируйте наблюдение для персонала.':d.connected?'Разъём установлен. Можно проверить сигнал.':'Разъём отсоединён. Проверьте реакцию кнопки.');}
  if(op==='test'){if(!p.inspected)return fail('Сначала осмотрите подключение кнопки.');p.tested=true;return ok('Проверка выполнена. Сверьте индикатор и ответ поста.');}
  if(op==='select'){const allowed=b.reports.map(x=>x.id);if(!allowed.includes(value))return fail('Выберите вывод для акта.');p.selected=[value];return ok('Предварительный вывод сохранён.');}
  if(op==='submit'||op==='report'){const selected=op==='report'?value:p.selected[0];if(!p.inspected||!p.tested)return fail('Для акта нужны осмотр подключения и проверка вызова.');if(selected!==d.type)return fail('Вывод не соответствует наблюдению. '+(d.type==='unassessed'?'Подключение не подтверждено: нужен осмотр персонала, а не догадка об исправности.':d.type==='disconnected'?'Разъём отсоединён: отсутствие ответа ещё не подтверждает исправность подключения.':d.type==='noResponse'?'Индикатор загорелся, но ответ поста не получен. Не приравнивайте сигнал к ответу.':'Пост ответил и назвал палату. Учитывайте полученный ответ в акте.'));p.selected=[selected];if(job.revision===5&&d.type!=='working'){const room='ward'+b.room;w.services[room].authorization={order:w.order,room,revision:w.initial[room].revision};}return ok('Акт проверки '+b.room+' заполнен.',step);}
 }
 if(b.kind==='callReview'){
  if(op!=='authorize'||w.authorized||!callRooms.every(room=>{const key='bell'+room.slice(4),d=w.diagnostics[key],e=s.world?.callEquipment?.[room];return job.done?.[key]&&d.inspected&&d.tested&&d.selected[0]===w.initial[room].condition&&e?.revision===w.initial[room].revision&&e.condition===w.initial[room].condition;}))return fail('Для разрешения нужны два подтверждённых первичных акта этой заявки.');
  w.authorized=true;for(const room of callRooms)if(w.initial[room].condition!=='working')w.services[room].authorization={order:w.order,room,revision:w.initial[room].revision};return {...ok('Врач сверил первичные акты. Обслуживание разрешено только для указанных узлов; затем нужны контрольные вызовы.'),effect:{kind:'callServiceAuthorized'}};
 }
 if(b.kind==='callService'){
  const room=b.room,p=w.services[room],e=s.world?.callEquipment?.[room],a=p.authorization;
  if(!w.authorized||!a||a.order!==w.order||a.room!==room||a.revision!==w.initial[room].revision||e?.revision!==a.revision||e.condition!==w.initial[room].condition||p.performed)return fail('Разрешение не относится к текущему состоянию этого узла.');
  if(op==='inspectEvidence'){p.inspected=true;return ok('Шильдик узла и запись персонала прочитаны. Сверьте все поля разрешения.');}
  if(!p.inspected)return fail('Сначала прочитайте шильдик и запись персонала.');
  const options=serviceRecords({...job,work:w},room,b.cause,v);
  if(op==='select'){if(!options.some(x=>x.id===value))return fail('Выберите действие из листа персонала.');p.selected=[value];return ok('Вариант указан для согласованного обслуживания.');}
  if(op==='submit'){const choice=options.find(x=>x.id===p.selected[0]),needed=callEquipment(room);if(!choice||choice.equipmentId!==needed.id||choice.connector!==needed.connector||choice.postAddress!==needed.postAddress)return fail('Поля выбранного действия не совпадают с узлом, соединением и адресом палаты.');p.performed=true;p.serviceRevision=e.revision+1;return {...ok(job.revision===5?'Техник закончил обслуживание. Проверьте ответ поста этой кнопкой.':'Персонал выполнил согласованное обслуживание. Исправность ещё не подтверждена: вернитесь в палату для контрольного вызова.'),effect:{kind:'callService',room}};}
 }
 if(b.kind==='callRetest'){
  const room=b.room,p=w.services[room],e=s.world?.callEquipment?.[room];if(!p.performed||p.serviceRevision!==e?.revision||e.condition!=='working'||p.confirmed)return fail('Состояние узла изменилось или обслуживание не подтверждено.');
  if(op==='test'){p.tested=true;p.responseAddress=callEquipment(room).postAddress;return {...ok('Пост ответил: палата '+room.slice(4)+', вызов принят. Сверьте адрес и подтвердите контроль.'),effect:{kind:'callRetestObserved',room}};}
  if(op==='confirm'){if(!p.tested||p.responseAddress!==callEquipment(room).postAddress)return fail('Нужен ответ поста именно этой палаты после обслуживания.');p.confirmed=true;return {...ok('Контрольный вызов '+room.slice(4)+' подтверждён. Результат остаётся в состоянии оборудования.'),effect:{kind:'callRetestConfirmed',room}};}
 }
 if(b.kind==='timeline'){
  if(op==='readReverse'&&job.revision>=3){const card=b.cards.find(x=>x.id===value);if(!card?.reverseAvailable)return fail('У этого листка нет сохранившейся записи на обороте.');if(!w.reverseRead.includes(value))w.reverseRead.push(value);return ok('Запись на обороте прочитана. Порядок событий можно подтвердить, не выдумывая время.');}
  const allowed=b.cards.map(x=>x.id);
  if(op==='place'){if(!allowed.includes(value))return fail('Такой записи нет.');if(!w.order.includes(value))w.order.push(value);return ok('Запись помещена в журнал.');}
  if(op==='remove'){if(!allowed.includes(value))return fail('Такой записи нет.');w.order=w.order.filter(x=>x!==value);return ok('Запись возвращена на стол.');}
  if(op==='move'){const i=w.order.indexOf(value?.id),delta=value?.direction==='up'?-1:value?.direction==='down'?1:0;if(i<0||!delta||i+delta<0||i+delta>=w.order.length)return fail('Перемещение записи недоступно.');[w.order[i],w.order[i+delta]]=[w.order[i+delta],w.order[i]];return ok('Порядок записей изменён.');}
  if(op==='submit'){if(job.revision>=3){if(w.order.length!==b.cards.length)return fail('Верните в журнал все четыре исходных листка.');if(!w.reverseRead.includes('entry-b'))return fail('Порядок листка 408 ещё не подтверждён источником. Прочитайте его оборот.');if(w.order.every((id,i)=>id==='entry-'+String.fromCharCode(97+i)))return ok('Последовательность подтверждена. Время записи 408 не установлено и не было придумано. Лист готов для врача.','log');return fail('В прочитанной записи осмотр 408 следует после проверки 407 и до передачи белья 406. Сверьте этот участок и время приёма журнала на посту.');}const expected=b.cards.slice().sort((a,b)=>a.time.localeCompare(b.time)).map(x=>x.id);if(w.order.length!==expected.length)return fail('В журнале '+w.order.length+' из '+expected.length+' записей. Сначала верните все листки со стола.');if(w.order.every((x,i)=>x===expected[i]))return ok('Порядок обхода восстановлен. Лист журнала готов.','log');const cards=w.order.map(id=>b.cards.find(x=>x.id===id)),later=cards.findIndex((card,i)=>i>0&&cards[i-1].time>card.time);return fail('Нарушена хронология: запись '+cards[later].time+' стоит после более поздней '+cards[later-1].time+'. Исправьте порядок листков.');}
 }

 if(b.kind==='subjectChoice'){
  if(op!=='chooseSubject')return fail('Выберите предмет для двух наблюдений.');
  const option=b.options.find(option=>option.id===value);
  if(!option?.available)return fail(option?.reason||'Такого предмета нет.');
  const reset=d3RestoreWork({subjectId:value});
  Object.assign(w,reset);
  return ok('Выбран предмет: '+option.label+'. Сначала осмотрите его в Пациенте.');
 }
 if(b.kind==='subjectBaseline'){
  if(op===b.actionOp){
   if(w.baselinePreview)return ok('Первое наблюдение уже прочитано. Сохраните его в карточке.');
   const availability=d3Available(s,b.subjectId);
   if(!availability.available)return fail(availability.reason);
   const provenance=d3Provenance(s,b.subjectId);
   if(!provenance)return fail('Предмет сейчас недоступен для наблюдения.');
   w.provenance=provenance;
   w.baselinePreview=d3Snapshot(b.subjectId,v,'patient');
   return ok('Первое наблюдение прочитано. Сохраните его в карточке.');
  }
  if(op==='record'){
   if(!w.baselinePreview||!w.provenance)return fail('Сначала осмотрите выбранный предмет.');
   w.baselineCaptured=true;
   w.baseline=clone(w.baselinePreview);
   return ok('Первое наблюдение сохранено. Повторите действие после следующего входа в Трип.','baseline');
  }
 }
 if(b.kind==='subjectDifference'){
  if(op===b.actionOp){
   if(w.observed)return ok('Повторное наблюдение уже прочитано и сохранено.');
   w.observed=d3Snapshot(b.subjectId,v,'trip');
   w.observedTrip=s.trip;
   return ok('Повторное наблюдение сохранено. Сверьте его с первой карточкой.');
  }
  if(!w.observed)return fail('Сначала повторите действие с выбранным предметом.');
  if(op==='selectReply'&&b.subjectId==='call407'){
   if(!d3Replies.some(option=>option.id===value))return fail('Выберите доступный ответ поста.');
   w.replySelected=value;
   return ok('Ответ указан. Проверьте его по записи вызова.');
  }
  if(op==='noChanges'&&b.allowNoChanges){
   w.noChanges=!w.noChanges;
   w.marked=[];
   return ok(w.noChanges?'Выбрано совпадение двух наблюдений.':'Вывод снят; записи сохранены.');
  }
  if(op==='mark'&&b.allowNoChanges){
   if(!toggle('marked',value,d3Subjects[b.subjectId].fields))return fail('Такого поля в карточке нет.');
   w.noChanges=false;
   return ok('Наблюдение отмечено.');
  }
  if(op==='submit'){
   if(b.subjectId==='call407'&&!w.replySelected)return fail('Укажите ответ поста или выберите «Ответа не было».');
   if(b.allowNoChanges&&!w.noChanges&&!w.marked.length)return fail('Отметьте отличия или явно подтвердите совпадение.');
   if(!d3Answer(w))return fail('Вывод не совпадает с записями. Сверьте карточки; исходные данные сохранены.');
   return ok(d3Delta(w).length?'Отличия записаны. Передайте карточку врачу.':'Совпадение подтверждено. Передайте карточку врачу.','difference');
  }
 }
 if(b.kind==='baseline'&&op==='record'){if(w.baselineCaptured)return fail('Первичная карточка уже заполнена.');w.baselineCaptured=true;if(job.revision===3)w.baseline=details(v,'patient',3);return ok('Показания таблички записаны в карточку.','baseline');}
 if(b.kind==='difference'){
  if(job.revision===3){if(!w.baselineCaptured||!w.observed||w.observedTrip<=job.startTrip)return fail('Сначала сохраните карточку в Пациенте и осмотрите табличку в новом входе в Трип.');if(op==='noChanges'){w.noChanges=!w.noChanges;w.marked=[];return ok(w.noChanges?'Выбран вывод: различий не обнаружено. Сверьте записи перед подтверждением.':'Вывод снят; карточка остаётся черновиком.');}if(op==='mark')w.noChanges=false;if(op==='submit'){if(!w.noChanges&&!w.marked.length)return fail('Пустой черновик не содержит вывода. Отметьте отличия или явно подтвердите, что их нет.');return observationAnswer(w)?ok(w.noChanges?'Совпадение записей подтверждено. Отсутствие различий зафиксировано для врача.':'Все наблюдаемые отличия записаны. Верните карточку врачу.','difference'):fail('Вывод не совпадает с двумя наблюдаемыми записями. Сверьте каждую строку; карточка и исходное наблюдение сохранены.');}}
  if(op==='mark'){if(!toggle('marked',value,['time','route','mark']))return fail('Такого поля в карточке нет.');return ok('Наблюдение отмечено.');}
  if(op==='submit'){const a=details(v,'patient'),b=details(v,'trip'),expected=Object.keys(a).filter(k=>a[k]!==b[k]);if(same(w.marked,expected))return ok('Наблюдаемое расхождение записано. Верните карточку врачу.','difference');return fail(w.marked.some(k=>!expected.includes(k))?'В карточку включены неизменившиеся показания. Сравните записи по строкам, не дописывая причины.':'Сравнение ещё не закончено: не все изменившиеся показания отмечены. Причины изменений записывать не нужно.');}
 }
 return fail('Это действие не относится к текущему рабочему листу.');
}
function description(s,cargo){
 const key={tag:'k1',linen:'k2',delivery:'k2',copies:'k3',bell407:'d1',bell408:'d1',log:'d2',baseline:'d3',difference:'d3'}[cargo],j=s.jobs?.[key];if(!supportsRevision(key,j?.revision))return null;
 const v=variant(j.variant);
 if(cargo==='tag'){const r=inspectionData(v).request;return 'Проверен '+r.kit.toLowerCase()+' комплект, партия '+r.lot+'. Пломба целая. Передайте лист приёмки Кларе.';}
 if(cargo==='linen'){const placed=j.revision>=3?j.work?.placed||[]:[];return 'Чистый комплект '+packingData(v).request.size+' для палаты 406.'+(placed.length?' Уже использовано: '+placed.map(x=>x==='sheet'?'простыня':'наволочка').join(', ')+'. Оставшаяся вещь ещё в комплекте.':' Простыня и наволочка при себе.');}
 if(cargo==='delivery')return (j.revision>=3?'Кровать 406 подготовлена: простыня и наволочка на своих местах.':'Комплект передан в палату 406.')+' Квитанцию необходимо вернуть Кларе.';
 if(cargo==='copies'){if(j.revision===3)return j.done?.copies?'Дело №46: подтверждено расхождение палаты 406/407; время проведения 09:25 перенесено верно. Имя в копии не подтверждено оригиналом: подпись в листе процедуры неразборчива. Неизвестное имя не дописывалось.':null;const d=compareData(v),names=d.documents[0].fields.filter((x,i)=>x.value!==d.documents[1].fields[i].value).map(x=>x.label.toLowerCase());return 'Подтверждены расхождения: '+names.join(', ')+'. Неподтверждённые данные не добавлялись.';}
 if(cargo==='bell407'||cargo==='bell408'){const d=callDiagnosis(s,cargo);return 'Палата '+cargo.slice(4)+'. '+(d.connected===null?'Подключение не подтверждено. ':d.connected?'Разъём установлен. ':'Разъём отсоединён. ')+(d.indicator==='on'?'Индикатор загорелся. ':'Индикатор не загорелся. ')+d.response;}
 if(cargo==='log')return j.revision>=3?'Порядок подтверждён временем и записью на обороте. Время осмотра 408 не установлено и не дописывалось.':'Записи расположены по указанному времени; неизвестные сведения об исполнителе не добавлялись.';
 if(j.revision===4&&(cargo==='baseline'||cargo==='difference')){
  const w=j.work,format=values=>d3Fields(values).map(row=>row.label+': '+row.value).join('; ');
  if(cargo==='baseline')return w.baseline?'Первое наблюдение: '+d3Subjects[w.subjectId].label+'. '+format(w.baseline)+'.':null;
  if(!w.observed)return null;
  const changed=d3Delta(w);
  return changed.length?'Изменились показания: '+changed.map(key=>d3Labels[key]+': '+w.baseline[key]+' → '+w.observed[key]).join('; ')+'. Причина не установлена.':
   'Различий не обнаружено. Оба наблюдения сохранены; причина совпадения не устанавливалась.';
 }
 const a=j.revision===3&&j.work.baseline||details(v,'patient');if(cargo==='baseline')return 'Записано в коридоре A: '+Object.keys(a).map(k=>labels[k]+': '+a[k]).join('; ')+'.';
 if(cargo==='difference'){const b=j.revision===3&&j.work.observed||details(v,'trip'),changed=Object.keys(a).filter(k=>a[k]!==b[k]);if(j.revision===3&&!changed.length)return 'В карточке подтверждено: различий не обнаружено. Исходное и повторное наблюдения сохранены; причина совпадения не устанавливалась.';return 'В карточке: '+changed.map(k=>labels[k]+': '+a[k]+' → '+b[k]).join('; ')+'. Причина расхождения не установлена.';}
 return null;
}
function kitResult(s){const j=s.jobs?.k2;if(!j?.active||!supportsRevision('k2',j.revision)||!j.done?.linen)return null;const d=packingData(variant(j.variant),j.revision,j.work),items=d.items.filter(x=>j.revision>=3?j.work.selected.includes(x.id):x.size===d.request.size&&x.condition==='чистая упаковка').map(x=>({type:x.type,measure:x.measure}));return{mark:d.request.size,items};}
function callResult(s,step){const j=s.jobs?.d1;if(!j||!supportsRevision('d1',j.revision)||!['bell407','bell408'].includes(step)||!j.work?.diagnostics?.[step]?.tested)return null;const d=callDiagnosis(s,step);return{connected:d.connected,indicator:d.indicator,responseCode:d.type==='working'?'acknowledged':'none',report:j.done?.[step]?d.type:null};}
function localCallRoute(s, job){
 const plan=[];
 for(const room of callRooms){
  const number=room.slice(4),step='bell'+number;
  const service=job.work.services[room];
  if(!job.done[step]){
   plan.push({room,mode:'patient',action:'job:'+step,text:'Осмотрите подключение, сделайте пробный вызов и заполните акт палаты '+number+'.',phase:'diagnosis'});
  }else if(job.work.initial[room].condition!=='working'){
   if(!service.performed)plan.push({room,mode:'patient',action:'job:callService'+number,text:'Техник ждёт у кнопки '+number+'. Сверьте маркировку и выберите запись обслуживания.',phase:'service'});
   else if(!service.confirmed)plan.push({room,mode:'patient',action:'job:callRetest'+number,text:service.tested?'Сверьте адрес '+number+' и подтвердите ответ.':'Сделайте контрольный вызов после обслуживания в '+number+'.',phase:'retest'});
  }
 }
 const local=plan.find(stop=>stop.room===s.room);
 const ordered=Object.freeze((local?[local,...plan.filter(stop=>stop!==local)]:plan).map(stop=>Object.freeze(stop)));
 if(ordered.length)return {...ordered[0],plan:ordered};
 return {room:'doctor',mode:'patient',action:'claim:d1',text:'Передайте врачу результаты проверки обеих палат.',plan:ordered};
}
function route(s,id){
 const j=s.jobs?.[id];if(!j?.active)return null;
 if(id==='d3'&&j.revision===4)return d3Route(s,j);
 if(id==='d3'&&j.revision===3){if(j.done?.difference)return{room:'doctor',mode:'patient',action:'claim:d3',text:'Передайте врачу заполненную карточку наблюдения.'};if(!j.work.baselineCaptured)return{room:'A',mode:'patient',action:'job:baseline',text:'Сначала запишите фактические показания таблички коридора A в исходную карточку.'};if(s.mode==='trip'&&s.trip<=j.startTrip)return{room:'A',mode:'patient',text:'Для повторного наблюдения выйдите из Трипа, затем войдите снова.'};return{room:'A',mode:'trip',action:'job:difference',text:'Сравните сохранённую карточку с табличкой. Отметьте все отличия или явно зафиксируйте их отсутствие.'};}
 if(id==='d1'&&j.revision===5)return localCallRoute(s,j);
 if(id==='d1'&&j.revision===4){
  for(const room of callRooms)if(!j.done?.['bell'+room.slice(4)])return{room,mode:'patient',action:'job:bell'+room.slice(4),text:'Осмотрите подключение, проверьте вызов и заполните первичный акт '+room.slice(4)+'.'};
  if(!j.work.authorized)return{room:'doctor',mode:'patient',action:'job:callReview',text:'Передайте врачу первичные акты для разрешения на обслуживание. Это ещё не сдача поручения.'};
  const services=[],retests=[];
  for(const room of callRooms){if(j.work.initial[room].condition==='working')continue;const p=j.work.services[room];if(!p.performed)services.push({room:j.work.initial[room].condition==='noResponse'?'nurse':'technical',mode:'patient',action:'job:callService'+room.slice(4),text:'Сверьте разрешённое действие персонала с узлом и адресом палаты '+room.slice(4)+'.',phase:'service'});else if(!p.confirmed)retests.push({room,mode:'patient',action:'job:callRetest'+room.slice(4),text:p.tested?'Сверьте адрес '+room.slice(4)+' в ответе поста и подтвердите контрольный вызов.':'После обслуживания нужен контрольный ответ поста из палаты '+room.slice(4)+'.',phase:'retest'});}
  // Guide service visits together, while preserving an available local retest.
  // Only already actionable stops are listed; each service adds its own retest.
  const local=retests.find(stop=>stop.room===s.room),plan=Object.freeze((local?[local,...services,...retests.filter(stop=>stop!==local)]:[...services,...retests]).map(stop=>Object.freeze(stop)));
  if(plan.length)return{...plan[0],plan};
  return{room:'doctor',mode:'patient',action:'claim:d1',text:'Оба результата подтверждены. Передайте врачу итоговые акты и получите прежнюю награду один раз.',plan};
 }
 if(id!=='k2'||j.revision<3)return null;if(j.done?.deliver)return{room:'nurse',mode:'patient',action:'claim:k2',text:'Передайте Кларе квитанцию подготовки кровати 406.'};if(j.done?.linen)return{room:'ward406',mode:'patient',action:'job:deliver',text:j.revision>=4&&!j.work.preparationStarted?'Начните подготовку кровати 406, затем разместите принесённые вещи.':'Разложите принесённые простыню и наволочку на кровати 406.'};if(j.variant===1&&j.work?.shortageNoted&&!j.work?.reserveGranted)return{room:'nurse',mode:'patient',action:'job:linenReserve',text:'Уточните у Клары замену отсутствующей наволочки по физическому размеру.'};return{room:'linen',mode:'patient',action:'job:linen',text:j.variant===1&&j.work?.reserveGranted?'Разрешённая замена записана. Соберите комплект в бельевой.':'Соберите чистые вещи по заявке; недостающую вещь сначала зафиксируйте.'};
}
return Object.freeze({ids,owner,brief,supportsRevision,validRecord,serviceReady,callEquipment,orderServiceRecords,make,restore,board,operate,observation,captureObservation,description,callResult,kitResult,route});
});
