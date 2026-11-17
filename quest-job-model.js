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
function brief(id,revision){if(typeof id!=='string'||!Object.hasOwn(briefs,id))return null;const result={...briefs[id]};if(id==='d1'&&(revision===undefined||revision===4)){result.purpose='Проверьте оба вызова, получите разрешение врача для обнаруженных проблем и подтвердите результат после обслуживания персоналом.';result.deliverable='Два первичных акта и подтверждённые контрольные вызовы для обслуженных узлов. Награда одна, при окончательной сдаче.';}if(id==='k2'&&(revision===undefined||revision===4))result.deliverable='Квитанция подготовки кровати 406: простыня и наволочка на своих местах.';return result;}
const callRooms=['ward407','ward408'];
const callConditions=['working','disconnected','noResponse','unassessed'];
const callEquipment=room=>({id:'CALL-'+room.slice(4),connector:'КС-2',postAddress:'ПОСТ-'+room.slice(4)});
function supportsRevision(id,r){return ids.includes(id)&&(r===2||[3,4].includes(r)&&['k2','d1'].includes(id));}
function make(id,serial=0,equipment){const r=['k2','d1'].includes(id)?4:2,work=restoreWork(id,{},variant(serial),r);if(id==='d1'&&r===4){work.order='d1:'+(serial+1);for(const room of callRooms){const source=equipment?.[room];work.initial[room]={condition:callConditions.includes(source?.condition)?source.condition:'unassessed',revision:Number.isSafeInteger(source?.revision)&&source.revision>=0?source.revision:0};}}return{revision:r,variant:variant(serial),work};}
function restoreWork(id,raw,v,r=2){
 raw=raw&&typeof raw==='object'&&!Array.isArray(raw)?raw:{};
 const result={};
 if(id==='k1'){result.inspected=safeArray(raw.inspected,['pack-0','pack-1','pack-2','pack-3']);result.selected=safeArray(raw.selected,['pack-0','pack-1','pack-2','pack-3']).slice(0,1);}
 if(id==='k2'){result.selected=safeArray(raw.selected,['linen-0','linen-1','linen-2','linen-3','linen-4','linen-5']);if(r>=3){result.shortageNoted=raw.shortageNoted===true;result.reserveGranted=result.shortageNoted&&raw.reserveGranted===true;result.selectedReserve=safeArray(raw.selectedReserve,['reserve-same-size','reserve-small']).slice(0,1);result.selectedPiece=['sheet','pillowcase'].includes(raw.selectedPiece)?raw.selectedPiece:null;result.placed=safeArray(raw.placed,['sheet','pillowcase']);if(result.placed.includes(result.selectedPiece))result.selectedPiece=null;if(r===4)result.preparationStarted=raw.preparationStarted===true;}}
 if(id==='k3')result.marked=safeArray(raw.marked,['time','ward','signature','lot']);
 if(id==='d1'){
  result.diagnostics={};for(const key of ['bell407','bell408']){const d=raw.diagnostics?.[key]||{};result.diagnostics[key]={inspected:d.inspected===true,tested:d.inspected===true&&d.tested===true,selected:safeArray(d.selected,r===4?callConditions:['working','disconnected','noResponse']).slice(0,1)};}
  if(r===4){result.order=typeof raw.order==='string'?raw.order:'d1:1';result.initial={};result.authorized=raw.authorized===true;result.services={};for(const room of callRooms){const d=raw.initial?.[room]||{},p=raw.services?.[room]||{};result.initial[room]={condition:callConditions.includes(d.condition)?d.condition:'unassessed',revision:Number.isSafeInteger(d.revision)&&d.revision>=0?d.revision:0};result.services[room]={inspected:p.inspected===true,selected:safeArray(p.selected,['service-a','service-b','service-c']).slice(0,1),performed:p.performed===true,tested:p.tested===true,confirmed:p.confirmed===true,authorization:p.authorization&&typeof p.authorization==='object'?clone(p.authorization):null,serviceRevision:Number.isSafeInteger(p.serviceRevision)&&p.serviceRevision>=0?p.serviceRevision:null,responseAddress:typeof p.responseAddress==='string'?p.responseAddress:null};}}
 }
 if(id==='d2')result.order=safeArray(raw.order,['entry-a','entry-b','entry-c','entry-d']);
 if(id==='d3'){result.baselineCaptured=raw.baselineCaptured===true;result.marked=safeArray(raw.marked,['time','route','mark']);}
 return result;
}
function restore(id,raw){const v=variant(raw?.variant),r=[3,4].includes(raw?.revision)&&supportsRevision(id,raw.revision)?raw.revision:2;return{revision:r,variant:v,work:restoreWork(id,raw?.work,v,r)};}
function canonical(value){if(value===undefined)return '"__undefined__"';return JSON.stringify(value&&typeof value==='object'&&!Array.isArray(value)?Object.fromEntries(Object.keys(value).sort().map(k=>[k,JSON.parse(canonical(value[k]))])):Array.isArray(value)?value.map(x=>JSON.parse(canonical(x))):value);}
function validRecord(id,job){
 if(job?.revision!==4)return true;if(!['k2','d1'].includes(id)||!job.work||typeof job.work!=='object'||Array.isArray(job.work)||Object.keys(job).some(k=>!['active','done','count','startTrip','revision','variant','work'].includes(k))||typeof job.active!=='boolean'||!Number.isSafeInteger(job.count)||job.count<0||!Number.isSafeInteger(job.startTrip)||job.startTrip<0||!job.done||typeof job.done!=='object'||Array.isArray(job.done)||Object.entries(job.done).some(([key,value])=>!(id==='k2'?['linen','deliver']:['bell407','bell408']).includes(key)||value!==true))return false;
 const w=job.work;if(canonical(w)!==canonical(restoreWork(id,w,variant(job.variant),4)))return false;
 if(id==='k2')return((!w.placed.length&&!w.selectedPiece)||w.preparationStarted)&&(!w.reserveGranted||w.shortageNoted);
 if(w.order!=='d1:'+(job.active?job.count+1:job.count))return false;
 for(const room of callRooms){const p=w.services[room],a=p.authorization,initial=w.initial[room];
  if(a&&(!w.authorized||Object.keys(a).sort().join(',')!=='order,revision,room'||a.order!==w.order||a.room!==room||a.revision!==initial.revision))return false;
  if(p.performed&&(!a||p.serviceRevision!==a.revision+1)||p.tested&&!p.performed||p.confirmed&&(!p.tested||p.responseAddress!==callEquipment(room).postAddress)||p.responseAddress!==null&&!callRooms.some(r=>callEquipment(r).postAddress===p.responseAddress))return false;
 }
 return true;
}
function callDiagnosis(s,step){
 const j=s.jobs?.d1;if(j?.revision!==4)return diagnosis(variant(j?.variant),step);
 const condition=j.work.initial?.['ward'+step.slice(4)]?.condition||'unassessed';
 return{type:condition,connected:condition==='unassessed'?null:condition!=='disconnected',indicator:condition==='working'||condition==='noResponse'?'on':'off',response:condition==='working'?'Пост: «'+step.slice(4)+', вызов принят».':'Ответ поста не поступил.'};
}
function serviceOptions(room,cause,v){const e=callEquipment(room),other=callEquipment(room==='ward407'?'ward408':'ward407');return rotate([
 {label:cause==='noResponse'?'Закрепить адрес палаты на посту':'Штатное обслуживание узла',equipmentId:e.id,connector:e.connector,postAddress:e.postAddress},
 {label:'Заявка на соседний узел',equipmentId:other.id,connector:e.connector,postAddress:e.postAddress},
 {label:cause==='noResponse'?'Другой адрес поста':'Разъём другого типа',equipmentId:e.id,connector:cause==='noResponse'?e.connector:'КС-3',postAddress:cause==='noResponse'?other.postAddress:e.postAddress}
 ],v).map((x,i)=>({id:['service-a','service-b','service-c'][i],...x}));}
function serviceReady(s){const j=s.jobs?.d1;if(j?.revision!==4)return false;const w=j.work;if(!w.authorized||!validRecord('d1',j))return false;return callRooms.every(room=>{const step='bell'+room.slice(4),d=w.diagnostics[step],initial=w.initial[room],e=s.world?.callEquipment?.[room];if(!j.done?.[step]||!d.inspected||!d.tested||d.selected[0]!==initial.condition||!e||e.condition!=='working')return false;if(initial.condition==='working')return e.revision===initial.revision;const p=w.services[room];return p.performed&&p.tested&&p.confirmed&&p.serviceRevision===e.revision&&e.verified&&p.responseAddress===callEquipment(room).postAddress;});}
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
function diagnosis(v,step){
 const type=['working','disconnected','noResponse'][(v+(step==='bell408'?1:0))%3];
 return{type,connected:type!=='disconnected',indicator:type==='disconnected'?'off':'on',response:type==='working'?'Пост: «'+step.slice(4)+', вызов принят».':'Ответ поста не поступил.'};
}
function timelineData(v){
 const times=[['08:05','08:20','08:35','08:50'],['09:10','09:25','09:40','09:55'],['10:15','10:30','10:45','11:00']][v];
 const rooms=['407','408','406','Пост'],notes=['Проверка сигнала','Осмотр палаты','Передача белья','Журнал возвращён на пост'];
 const cards=times.map((time,i)=>({id:'entry-'+String.fromCharCode(97+i),time,room:rooms[i],note:notes[i]}));return{cards:rotate([cards[2],cards[0],cards[3],cards[1]],v)};
}
function details(v,mode){
 const base=[{time:'08:00',route:'Палаты 404–406',mark:'Круг'},{time:'07:40',route:'Палаты 404–408',mark:'Полоса'},{time:'09:10',route:'Палаты 405–408',mark:'Круг'}][v];
 const result={...base};if(mode==='trip'){if(v===0)result.time='03:00';if(v===1)result.mark='Крест';if(v===2)result.route='Палаты 404–406';}return result;
}
const fields=values=>Object.entries(values).map(([id,value])=>({id,label:labels[id],value}));
function observation(s){const j=s.jobs?.d3;return j?.active&&j.revision===2?details(variant(j.variant),s.mode):{time:s.mode==='trip'?'03:00':'08:00',route:'Палаты 404–408',mark:'—'};}
function board(s,actionId){
 const step=typeof actionId==='string'&&actionId.startsWith('job:')?actionId.slice(4):'',jobId=owner[step],job=s.jobs?.[jobId];if(!job?.active||!supportsRevision(jobId,job.revision))return null;
 const v=variant(job.variant),w=restoreWork(jobId,job.work,v,job.revision),base={jobId,actionId,revision:job.revision,brief:brief(jobId,job.revision)};
 if(step==='tag'){const d=inspectionData(v);return{...base,kind:'inspection',title:'Приёмка контейнера',instruction:'Сверьте заявку с маркировкой и состоянием пломбы. Подтвердите пригодный комплект.',request:d.request,items:d.items.map(x=>({id:x.id,name:x.name,inspected:w.inspected.includes(x.id),details:w.inspected.includes(x.id)?x.details:null})),inspected:w.inspected,selected:w.selected};}
 if(step==='linen')return{...base,kind:'packing',title:'Комплект для палаты 406',instruction:'Соберите чистый комплект с указанной маркировкой. Непригодные упаковки оставьте на полке.',...packingData(v,job.revision,w),selected:w.selected};
 if(step==='linenReserve'&&job.revision>=3&&v===1)return{...base,kind:'clarification',title:'Уточнение комплекта для 406',instruction:'Наволочка нужной маркировки отсутствует в доступной выдаче. Сопоставьте физический размер и запросите разрешение на замену.',request:{neededType:'Наволочка',neededMeasure:'70 × 70 см'},options:[{id:'reserve-same-size',measure:'70 × 70 см',label:'Наволочка М · резерв поста'},{id:'reserve-small',measure:'50 × 70 см',label:'Наволочка С · резерв поста'}],selected:w.selectedReserve,shortageNoted:w.shortageNoted,reserveGranted:w.reserveGranted};
 if(step==='deliver'){const parcel=s.cargo.includes('linen'),d=packingData(v,job.revision,w),kit=d.items.filter(x=>w.selected.includes(x.id)&&x.condition==='чистая упаковка').map(x=>({id:x.type==='Простыня'?'sheet':'pillowcase',type:x.type,measure:x.measure})),parcelDetails=parcel?{components:d.request.components.slice(),size:d.request.size,items:(job.revision>=3?kit:d.items.filter(x=>x.size===d.request.size&&x.condition==='чистая упаковка').map(x=>({type:x.type,measure:x.measure})))}:null;
 if(job.revision>=3)return{...base,kind:'bedmaking',title:'Подготовить кровать 406',instruction:'Выберите вещь из принесённого комплекта и положите на соответствующую часть кровати. Завершённая подготовка останется в палате.',request:{destination:'406'},parcel,items:parcel?kit:[],selectedPiece:w.selectedPiece,placed:w.placed,...(job.revision===4?{preparationStarted:w.preparationStarted}:{}),targets:[{id:'sheetZone',label:'Матрас · постелить простыню'},{id:'pillowZone',label:'Подушка · сменить наволочку'}],...(parcelDetails?{parcelDetails}:{})};
 return{...base,kind:'delivery',title:'Передача комплекта',instruction:'Передайте принесённый комплект на отмеченную кровать. Квитанция останется для сдачи поручения.',request:{destination:'406'},parcel,...(parcelDetails?{parcelDetails}:{})};}
 if(step==='copies')return{...base,kind:'compare',title:'Сверка записей',instruction:'Отметьте только поля, в которых записи расходятся. Не дописывайте неизвестные сведения.',...compareData(v),marked:w.marked};
 if(step==='bell407'||step==='bell408'){const d=callDiagnosis(s,step),p=w.diagnostics[step];return{...base,kind:'diagnostic',title:'Проверка вызова '+step.slice(4),instruction:'Осмотрите подключение, проверьте вызов и запишите то, что удалось наблюдать.',room:step.slice(4),inspected:p.inspected,tested:p.tested,connector:p.inspected?{connected:d.connected,text:d.connected===null?'Состояние подключения не подтверждено. Нужен осмотр персонала.':d.connected?'Разъём установлен, провод цел.':'Разъём отсоединён от кнопки.'}:null,indicator:p.tested?d.indicator:'idle',response:p.tested?d.response:null,reports:[...(job.revision===4?[{id:'unassessed',label:'Состояние требует обследования персоналом'}]:[]),{id:'working',label:'Сигнал и ответ получены'},{id:'disconnected',label:'Нет подключения кнопки'},{id:'noResponse',label:'Сигнал есть, ответа поста нет'}],selected:p.selected};}
 if(jobId==='d1'&&job.revision===4&&step==='callReview')return{...base,kind:'callReview',title:'Разрешение на обслуживание вызовов',instruction:'Сверьте оба первичных акта. Разрешение привязано к этой заявке и конкретным узлам; награда выдаётся после контрольных вызовов.',authorized:w.authorized,reports:callRooms.map(room=>{const d=callDiagnosis(s,'bell'+room.slice(4));return{room,label:room.slice(4),report:d.type,connected:d.connected,indicator:d.indicator,response:d.response,needsService:d.type!=='working'};})};
 if(jobId==='d1'&&job.revision===4&&/^callService40[78]$/.test(step)){const room='ward'+step.slice(-3),p=w.services[room],cause=w.initial[room].condition,equipment=callEquipment(room);return{...base,kind:'callService',title:'Обслуживание вызова '+room.slice(4),instruction:cause==='noResponse'?'На посту сверяют регистрацию адреса: светящийся индикатор ещё не подтверждает ответ нужной палаты.':'Персонал сверяет узел и штатное соединение по разрешению врача. Не выбирайте детали по одному похожему признаку.',room,label:room.slice(4),cause,equipment,inspected:p.inspected,evidence:p.inspected?{equipmentId:equipment.id,connector:equipment.connector,postAddress:equipment.postAddress,observedRegistration:cause==='noResponse'?'Адрес палаты не закреплён в журнале поста':cause==='unassessed'?'Нужна проверка штатного узла персоналом':'Штатное соединение отсоединено',text:'Разрешение '+w.order+' · палата '+room.slice(4)}:null,options:p.inspected?serviceOptions(room,cause,v):[],selected:p.selected,performed:p.performed};}
 if(jobId==='d1'&&job.revision===4&&/^callRetest40[78]$/.test(step)){const room='ward'+step.slice(-3),p=w.services[room];return{...base,kind:'callRetest',title:'Контрольный вызов '+room.slice(4),instruction:p.tested?'Сверьте адрес в полученном ответе поста и подтвердите контрольный вызов.':'Проверьте вызов после обслуживания. Подтвердите результат только после ответа поста с адресом этой палаты.',room,label:room.slice(4),tested:p.tested,indicator:p.tested?'on':'idle',response:p.tested?(p.responseAddress?'Пост: «'+room.slice(4)+', вызов принят».':'Ответ нужной палаты не поступил.'):null,responseAddress:p.responseAddress,confirmed:p.confirmed};}
 if(step==='log')return{...base,kind:'timeline',title:'Журнал обхода',instruction:'Восстановите хронологию по времени записей. Поля исполнителя не дописывайте.',...timelineData(v),order:w.order};
 if(step==='baseline')return{...base,kind:'baseline',title:'Первичное наблюдение',instruction:'Осмотрите табличку коридора и сохраните её показания в карточке.',details:fields(details(v,'patient')),recorded:w.baselineCaptured};
 if(step==='difference')return{...base,kind:'difference',title:'Повторное наблюдение',instruction:'Сопоставьте сохранённую карточку с табличкой перед вами. Отметьте наблюдаемое расхождение.',baseline:fields(details(v,'patient')),current:fields(details(v,'trip')),marked:w.marked};
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
  if(job.revision===4&&op==='startBedPreparation'){w.preparationStarted=true;return {...ok('Подготовка начата. Сначала выберите принесённую вещь, затем её место на кровати.'),effect:{kind:'startBedPreparation'}};}
  if(job.revision===4&&!w.preparationStarted)return fail('Сначала начните подготовку кровати. Новая заявка сама не снимает прежнее бельё.');
  if(op==='selectPiece'){if(!b.items.some(x=>x.id===value)||w.placed.includes(value))return fail('Эта вещь недоступна или уже использована.');w.selectedPiece=value;return ok('Выбрано: '+b.items.find(x=>x.id===value).type+'. Укажите место на кровати.');}
  if(op==='place'){const required={sheet:'sheetZone',pillowcase:'pillowZone'};if(!w.selectedPiece)return fail('Сначала выберите вещь из комплекта.');if(required[w.selectedPiece]!==value)return fail('Это место не соответствует выбранной вещи. Простыня нужна на матрасе, наволочка — на подушке.');w.placed.push(w.selectedPiece);w.selectedPiece=null;return w.placed.length===2?ok(job.revision===4?'Обе вещи размещены. Квитанция для Клары заполнена.':'Кровать 406 подготовлена: чистые простыня и наволочка на своих местах. Квитанция для Клары заполнена.','deliver'):ok('Вещь размещена. Подготовьте оставшуюся часть кровати.');}
 }
 if(b.kind==='delivery'&&(op==='deliver'||op==='submit'))return b.parcel?ok('Комплект передан. Получена квитанция для Клары.','deliver'):fail('Принесите упакованный комплект из бельевой.');
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
  if(op==='submit'||op==='report'){const selected=op==='report'?value:p.selected[0];if(!p.inspected||!p.tested)return fail('Для акта нужны осмотр подключения и проверка вызова.');if(selected!==d.type)return fail('Вывод не соответствует наблюдению. '+(d.type==='unassessed'?'Подключение не подтверждено: нужен осмотр персонала, а не догадка об исправности.':d.type==='disconnected'?'Разъём отсоединён: отсутствие ответа ещё не подтверждает исправность подключения.':d.type==='noResponse'?'Индикатор загорелся, но ответ поста не получен. Не приравнивайте сигнал к ответу.':'Пост ответил и назвал палату. Учитывайте полученный ответ в акте.'));p.selected=[selected];return ok('Акт проверки '+b.room+' заполнен.',step);}
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
  if(op==='select'){if(!serviceOptions(room,b.cause,v).some(x=>x.id===value))return fail('Выберите действие из листа персонала.');p.selected=[value];return ok('Вариант указан для согласованного обслуживания.');}
  if(op==='submit'){const choice=serviceOptions(room,b.cause,v).find(x=>x.id===p.selected[0]),needed=callEquipment(room);if(!choice||choice.equipmentId!==needed.id||choice.connector!==needed.connector||choice.postAddress!==needed.postAddress)return fail('Поля выбранного действия не совпадают с узлом, соединением и адресом палаты.');p.performed=true;p.serviceRevision=e.revision+1;return {...ok('Персонал выполнил согласованное обслуживание. Исправность ещё не подтверждена: вернитесь в палату для контрольного вызова.'),effect:{kind:'callService',room}};}
 }
 if(b.kind==='callRetest'){
  const room=b.room,p=w.services[room],e=s.world?.callEquipment?.[room];if(!p.performed||p.serviceRevision!==e?.revision||e.condition!=='working'||p.confirmed)return fail('Состояние узла изменилось или обслуживание не подтверждено.');
  if(op==='test'){p.tested=true;p.responseAddress=callEquipment(room).postAddress;return {...ok('Пост ответил: палата '+room.slice(4)+', вызов принят. Сверьте адрес и подтвердите контроль.'),effect:{kind:'callRetestObserved',room}};}
  if(op==='confirm'){if(!p.tested||p.responseAddress!==callEquipment(room).postAddress)return fail('Нужен ответ поста именно этой палаты после обслуживания.');p.confirmed=true;return {...ok('Контрольный вызов '+room.slice(4)+' подтверждён. Результат остаётся в состоянии оборудования.'),effect:{kind:'callRetestConfirmed',room}};}
 }
 if(b.kind==='timeline'){
  const allowed=b.cards.map(x=>x.id);
  if(op==='place'){if(!allowed.includes(value))return fail('Такой записи нет.');if(!w.order.includes(value))w.order.push(value);return ok('Запись помещена в журнал.');}
  if(op==='remove'){if(!allowed.includes(value))return fail('Такой записи нет.');w.order=w.order.filter(x=>x!==value);return ok('Запись возвращена на стол.');}
  if(op==='move'){const i=w.order.indexOf(value?.id),delta=value?.direction==='up'?-1:value?.direction==='down'?1:0;if(i<0||!delta||i+delta<0||i+delta>=w.order.length)return fail('Перемещение записи недоступно.');[w.order[i],w.order[i+delta]]=[w.order[i+delta],w.order[i]];return ok('Порядок записей изменён.');}
  if(op==='submit'){const expected=b.cards.slice().sort((a,b)=>a.time.localeCompare(b.time)).map(x=>x.id);if(w.order.length!==expected.length)return fail('В журнале '+w.order.length+' из '+expected.length+' записей. Сначала верните все листки со стола.');if(w.order.every((x,i)=>x===expected[i]))return ok('Порядок обхода восстановлен. Лист журнала готов.','log');const cards=w.order.map(id=>b.cards.find(x=>x.id===id)),later=cards.findIndex((card,i)=>i>0&&cards[i-1].time>card.time);return fail('Нарушена хронология: запись '+cards[later].time+' стоит после более поздней '+cards[later-1].time+'. Исправьте порядок листков.');}
 }
 if(b.kind==='baseline'&&op==='record'){if(w.baselineCaptured)return fail('Первичная карточка уже заполнена.');w.baselineCaptured=true;return ok('Показания таблички записаны в карточку.','baseline');}
 if(b.kind==='difference'){
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
 if(cargo==='copies'){const d=compareData(v),names=d.documents[0].fields.filter((x,i)=>x.value!==d.documents[1].fields[i].value).map(x=>x.label.toLowerCase());return 'Подтверждены расхождения: '+names.join(', ')+'. Неподтверждённые данные не добавлялись.';}
 if(cargo==='bell407'||cargo==='bell408'){const d=callDiagnosis(s,cargo);return 'Палата '+cargo.slice(4)+'. '+(d.connected===null?'Подключение не подтверждено. ':d.connected?'Разъём установлен. ':'Разъём отсоединён. ')+(d.indicator==='on'?'Индикатор загорелся. ':'Индикатор не загорелся. ')+d.response;}
 if(cargo==='log')return 'Записи расположены по указанному времени; неизвестные сведения об исполнителе не добавлялись.';
 const a=details(v,'patient');if(cargo==='baseline')return 'Записано в коридоре A: '+Object.keys(a).map(k=>labels[k]+': '+a[k]).join('; ')+'.';
 if(cargo==='difference'){const b=details(v,'trip');return 'В карточке: '+Object.keys(a).filter(k=>a[k]!==b[k]).map(k=>labels[k]+': '+a[k]+' → '+b[k]).join('; ')+'. Причина расхождения не установлена.';}
 return null;
}
function kitResult(s){const j=s.jobs?.k2;if(!j?.active||!supportsRevision('k2',j.revision)||!j.done?.linen)return null;const d=packingData(variant(j.variant),j.revision,j.work),items=d.items.filter(x=>j.revision>=3?j.work.selected.includes(x.id):x.size===d.request.size&&x.condition==='чистая упаковка').map(x=>({type:x.type,measure:x.measure}));return{mark:d.request.size,items};}
function callResult(s,step){const j=s.jobs?.d1;if(!j||!supportsRevision('d1',j.revision)||!['bell407','bell408'].includes(step)||!j.work?.diagnostics?.[step]?.tested)return null;const d=callDiagnosis(s,step);return{connected:d.connected,indicator:d.indicator,responseCode:d.type==='working'?'acknowledged':'none',report:j.done?.[step]?d.type:null};}
function route(s,id){
 const j=s.jobs?.[id];if(!j?.active)return null;
 if(id==='d1'&&j.revision===4){
  for(const room of callRooms)if(!j.done?.['bell'+room.slice(4)])return{room,mode:'patient',action:'job:bell'+room.slice(4),text:'Осмотрите подключение, проверьте вызов и заполните первичный акт '+room.slice(4)+'.'};
  if(!j.work.authorized)return{room:'doctor',mode:'patient',action:'job:callReview',text:'Передайте врачу первичные акты для разрешения на обслуживание. Это ещё не сдача поручения.'};
  for(const room of callRooms){if(j.work.initial[room].condition==='working')continue;const p=j.work.services[room];if(!p.performed)return{room:j.work.initial[room].condition==='noResponse'?'nurse':'technical',mode:'patient',action:'job:callService'+room.slice(4),text:'Сверьте разрешённое действие персонала с узлом и адресом палаты '+room.slice(4)+'.'};if(!p.confirmed)return{room,mode:'patient',action:'job:callRetest'+room.slice(4),text:p.tested?'Сверьте адрес '+room.slice(4)+' в ответе поста и подтвердите контрольный вызов.':'После обслуживания нужен контрольный ответ поста из палаты '+room.slice(4)+'.'};}
  return{room:'doctor',mode:'patient',action:'claim:d1',text:'Оба результата подтверждены. Передайте врачу итоговые акты и получите прежнюю награду один раз.'};
 }
 if(id!=='k2'||j.revision<3)return null;if(j.done?.deliver)return{room:'nurse',mode:'patient',action:'claim:k2',text:'Передайте Кларе квитанцию подготовки кровати 406.'};if(j.done?.linen)return{room:'ward406',mode:'patient',action:'job:deliver',text:j.revision===4&&!j.work.preparationStarted?'Начните подготовку кровати 406, затем разместите принесённые вещи.':'Разложите принесённые простыню и наволочку на кровати 406.'};if(j.variant===1&&j.work?.shortageNoted&&!j.work?.reserveGranted)return{room:'nurse',mode:'patient',action:'job:linenReserve',text:'Уточните у Клары замену отсутствующей наволочки по физическому размеру.'};return{room:'linen',mode:'patient',action:'job:linen',text:j.variant===1&&j.work?.reserveGranted?'Разрешённая замена записана. Соберите комплект в бельевой.':'Соберите чистые вещи по заявке; недостающую вещь сначала зафиксируйте.'};
}
return Object.freeze({ids,owner,brief,supportsRevision,validRecord,serviceReady,callEquipment,make,restore,board,operate,observation,description,callResult,kitResult,route});
});
