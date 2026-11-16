/* Persistent work orders for floor 10. Public boards contain evidence, never a
 * solution key. Operations return a new work state; a rejected submission cannot
 * change the saved order, complete a step, consume cargo or pay a reward. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.PalataQuestJobModel=api;})(globalThis,function(){
'use strict';
const ids=['k1','k2','k3','d1','d2','d3'];
const owner={tag:'k1',linen:'k2',deliver:'k2',copies:'k3',bell407:'d1',bell408:'d1',log:'d2',baseline:'d3',difference:'d3'};
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
function brief(id){return typeof id==='string'&&Object.hasOwn(briefs,id)?{...briefs[id]}:null;}
function make(id,serial=0){return{revision:2,variant:variant(serial),work:restoreWork(id,{},variant(serial))};}
function restoreWork(id,raw,v){
 raw=raw&&typeof raw==='object'&&!Array.isArray(raw)?raw:{};
 const result={};
 if(id==='k1'){result.inspected=safeArray(raw.inspected,['pack-0','pack-1','pack-2','pack-3']);result.selected=safeArray(raw.selected,['pack-0','pack-1','pack-2','pack-3']).slice(0,1);}
 if(id==='k2')result.selected=safeArray(raw.selected,['linen-0','linen-1','linen-2','linen-3','linen-4','linen-5']);
 if(id==='k3')result.marked=safeArray(raw.marked,['time','ward','signature','lot']);
 if(id==='d1'){
  result.diagnostics={};for(const key of ['bell407','bell408']){const d=raw.diagnostics?.[key]||{};result.diagnostics[key]={inspected:d.inspected===true,tested:d.inspected===true&&d.tested===true,selected:safeArray(d.selected,['working','disconnected','noResponse']).slice(0,1)};}
 }
 if(id==='d2')result.order=safeArray(raw.order,['entry-a','entry-b','entry-c','entry-d']);
 if(id==='d3'){result.baselineCaptured=raw.baselineCaptured===true;result.marked=safeArray(raw.marked,['time','route','mark']);}
 return result;
}
function restore(id,raw){const v=variant(raw?.variant);return{revision:2,variant:v,work:restoreWork(id,raw?.work,v)};}
function inspectionData(v){
 const kit=['Перевязочный','Диагностический','Осмотровой'][v],lot=['Б-17','В-24','А-09'][v],target=[1,3,0][v];
 const otherKit=['Диагностический','Осмотровой','Перевязочный'][v],otherLot=['Б-71','В-42','А-90'][v];
 const values=[{kit,lot:otherLot,seal:'целая'},{kit,lot,seal:'повреждена'},{kit:otherKit,lot,seal:'целая'},{kit,lot,seal:'целая'}];
 const ordered=[];let j=0;for(let i=0;i<4;i++)ordered.push(i===target?values[3]:values[j++]);
 return{request:{kit,lot},items:ordered.map((details,i)=>({id:'pack-'+i,name:'Контейнер '+(i+1),details}))};
}
function packingData(v){
 const size=['М','Л','С'][v],other=['Л','С','М'][v];
 const measures={М:['150 × 215 см','70 × 70 см'],Л:['180 × 220 см','70 × 70 см'],С:['120 × 200 см','50 × 70 см']};
 const items=[['Простыня',size,'чистая упаковка'],['Наволочка',size,'чистая упаковка'],['Простыня',other,'чистая упаковка'],['Наволочка',size,'повреждена упаковка'],['Простыня',size,'загрязнена'],['Наволочка',other,'чистая упаковка']].map(([type,size,condition],i)=>({id:'linen-'+i,name:type,type,size,condition,measure:measures[size][type==='Простыня'?0:1]}));
 return{request:{destination:'406',size,components:['Простыня','Наволочка'],markingNote:'Буква на упаковке — учётная маркировка парного комплекта. Физический размер указан отдельно.'},items:rotate(items,v*2)};
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
 const step=typeof actionId==='string'&&actionId.startsWith('job:')?actionId.slice(4):'',jobId=owner[step],job=s.jobs?.[jobId];if(!job?.active||job.revision!==2)return null;
 const v=variant(job.variant),w=restoreWork(jobId,job.work,v),base={jobId,actionId,brief:brief(jobId)};
 if(step==='tag'){const d=inspectionData(v);return{...base,kind:'inspection',title:'Приёмка контейнера',instruction:'Сверьте заявку с маркировкой и состоянием пломбы. Подтвердите пригодный комплект.',request:d.request,items:d.items.map(x=>({id:x.id,name:x.name,inspected:w.inspected.includes(x.id),details:w.inspected.includes(x.id)?x.details:null})),inspected:w.inspected,selected:w.selected};}
 if(step==='linen')return{...base,kind:'packing',title:'Комплект для палаты 406',instruction:'Соберите чистый комплект с указанной маркировкой. Непригодные упаковки оставьте на полке.',...packingData(v),selected:w.selected};
 if(step==='deliver'){const parcel=s.cargo.includes('linen'),d=packingData(v),parcelDetails=parcel?{components:d.request.components.slice(),size:d.request.size,items:d.items.filter(x=>x.size===d.request.size&&x.condition==='чистая упаковка').map(x=>({type:x.type,measure:x.measure}))}:null;return{...base,kind:'delivery',title:'Передача комплекта',instruction:'Передайте принесённый комплект на отмеченную кровать. Квитанция останется для сдачи поручения.',request:{destination:'406'},parcel,...(parcelDetails?{parcelDetails}:{})};}
 if(step==='copies')return{...base,kind:'compare',title:'Сверка записей',instruction:'Отметьте только поля, в которых записи расходятся. Не дописывайте неизвестные сведения.',...compareData(v),marked:w.marked};
 if(step==='bell407'||step==='bell408'){const d=diagnosis(v,step),p=w.diagnostics[step];return{...base,kind:'diagnostic',title:'Проверка вызова '+step.slice(4),instruction:'Осмотрите подключение, проверьте вызов и запишите то, что удалось наблюдать.',room:step.slice(4),inspected:p.inspected,tested:p.tested,connector:p.inspected?{connected:d.connected,text:d.connected?'Разъём установлен, провод цел.':'Разъём отсоединён от кнопки.'}:null,indicator:p.tested?d.indicator:'idle',response:p.tested?d.response:null,reports:[{id:'working',label:'Сигнал и ответ получены'},{id:'disconnected',label:'Нет подключения кнопки'},{id:'noResponse',label:'Сигнал есть, ответа поста нет'}],selected:p.selected};}
 if(step==='log')return{...base,kind:'timeline',title:'Журнал обхода',instruction:'Восстановите хронологию по времени записей. Поля исполнителя не дописывайте.',...timelineData(v),order:w.order};
 if(step==='baseline')return{...base,kind:'baseline',title:'Первичное наблюдение',instruction:'Осмотрите табличку коридора и сохраните её показания в карточке.',details:fields(details(v,'patient')),recorded:w.baselineCaptured};
 if(step==='difference')return{...base,kind:'difference',title:'Повторное наблюдение',instruction:'Сопоставьте сохранённую карточку с табличкой перед вами. Отметьте наблюдаемое расхождение.',baseline:fields(details(v,'patient')),current:fields(details(v,'trip')),marked:w.marked};
 return null;
}
function same(a,b){return a.length===b.length&&a.every(x=>b.includes(x));}
function operate(s,actionId,op,value){
 const b=board(s,actionId);if(!b)return{ok:false,message:'Рабочий лист недоступен.'};const job=s.jobs[b.jobId],w=clone(restoreWork(b.jobId,job.work,job.variant)),step=actionId.slice(4),v=variant(job.variant);
 const fail=message=>({ok:false,message}),ok=(message,complete=null)=>({ok:true,message,work:w,complete});
 const toggle=(key,id,allowed,max=Infinity)=>{if(!allowed.includes(id))return false;w[key]=w[key].includes(id)?w[key].filter(x=>x!==id):max===1?[id]:w[key].concat(id).slice(0,max);return true;};
 if(b.kind==='inspection'){
  const d=inspectionData(v),allowed=d.items.map(x=>x.id);
  if(op==='inspect'){if(!allowed.includes(value))return fail('Такого контейнера на лотке нет.');if(!w.inspected.includes(value))w.inspected.push(value);return ok('Маркировка и пломба осмотрены.');}
  if(op==='select'){if(!toggle('selected',value,allowed,1))return fail('Выберите контейнер с лотка.');return ok('Выбор в листе приёмки сохранён.');}
  if(op==='submit'){const item=d.items.find(x=>x.id===w.selected[0]);if(!item||!w.inspected.includes(item.id))return fail('Осмотрите выбранный контейнер перед подтверждением.');const problems=[];if(item.details.kit!==d.request.kit)problems.push('название на осмотренной упаковке отличается от заявки');if(item.details.lot!==d.request.lot)problems.push('партия на осмотренной упаковке отличается от заявки');if(item.details.seal!=='целая')problems.push('на осмотренной упаковке повреждена пломба');if(problems.length)return fail('Комплект не соответствует заявке: '+problems.join('; ')+'.');return ok('Комплект проверен. Бирка приложена к листу приёмки.','tag');}
 }
 if(b.kind==='packing'){
  const d=packingData(v),allowed=d.items.map(x=>x.id);
  if(op==='select'){if(!toggle('selected',value,allowed))return fail('Выберите вещь с полки.');return ok('Состав комплекта сохранён.');}
  if(op==='submit'){const selected=d.items.filter(x=>w.selected.includes(x.id)),types=selected.map(x=>x.type),problems=[];if(selected.length!==2)problems.push('сейчас выбрано вещей: '+selected.length+' из 2');else if(new Set(types).size!==d.request.components.length||!same(types,d.request.components))problems.push('в комплекте нужны два разных предмета');if(selected.some(x=>x.size!==d.request.size))problems.push('на выбранных упаковках есть другая маркировка');if(selected.some(x=>x.condition!=='чистая упаковка'))problems.push('среди выбранного есть загрязнённая или повреждённая упаковка');if(problems.length)return fail('Нужны простыня и наволочка указанной маркировки в чистых целых упаковках: '+problems.join('; ')+'.');return ok('Комплект упакован и помечен для палаты 406.','linen');}
 }
 if(b.kind==='delivery'&&(op==='deliver'||op==='submit'))return b.parcel?ok('Комплект передан. Получена квитанция для Клары.','deliver'):fail('Принесите упакованный комплект из бельевой.');
 if(b.kind==='compare'){
  const d=compareData(v),allowed=d.documents[0].fields.map(x=>x.id);
  if(op==='mark'){if(!toggle('marked',value,allowed))return fail('Такого поля в записях нет.');return ok('Отметки сверки сохранены.');}
  if(op==='submit'){const needed=d.documents[0].fields.filter((x,i)=>x.value!==d.documents[1].fields[i].value).map(x=>x.id);if(same(w.marked,needed))return ok('Подтверждённые расхождения отмечены. Лист сверки готов.','copies');return fail(w.marked.some(x=>!needed.includes(x))?'Среди отметок есть совпадающие поля. Снимите лишние отметки и снова сравните записи.':'Отмечены не все расхождения. Сверьте каждую строку в обеих записях.');}
 }
 if(b.kind==='diagnostic'){
  const p=w.diagnostics[step],d=diagnosis(v,step);
  if(op==='inspect'){if(value!==undefined&&value!==null&&value!=='connector')return fail('Осмотрите разъём кнопки.');p.inspected=true;return ok(d.connected?'Разъём установлен. Можно проверить сигнал.':'Разъём отсоединён. Проверьте реакцию кнопки.');}
  if(op==='test'){if(!p.inspected)return fail('Сначала осмотрите подключение кнопки.');p.tested=true;return ok('Проверка выполнена. Сверьте индикатор и ответ поста.');}
  if(op==='select'){const allowed=b.reports.map(x=>x.id);if(!allowed.includes(value))return fail('Выберите вывод для акта.');p.selected=[value];return ok('Предварительный вывод сохранён.');}
  if(op==='submit'||op==='report'){const selected=op==='report'?value:p.selected[0];if(!p.inspected||!p.tested)return fail('Для акта нужны осмотр подключения и проверка вызова.');if(selected!==d.type)return fail('Вывод не соответствует наблюдению. '+(d.type==='disconnected'?'Разъём отсоединён: отсутствие ответа ещё не подтверждает исправность подключения.':d.type==='noResponse'?'Индикатор загорелся, но ответ поста не получен. Не приравнивайте сигнал к ответу.':'Пост ответил и назвал палату. Учитывайте полученный ответ в акте.'));p.selected=[selected];return ok('Акт проверки '+b.room+' заполнен.',step);}
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
 const key={tag:'k1',linen:'k2',delivery:'k2',copies:'k3',bell407:'d1',bell408:'d1',log:'d2',baseline:'d3',difference:'d3'}[cargo],j=s.jobs?.[key];if(j?.revision!==2)return null;
 const v=variant(j.variant);
 if(cargo==='tag'){const r=inspectionData(v).request;return 'Проверен '+r.kit.toLowerCase()+' комплект, партия '+r.lot+'. Пломба целая. Передайте лист приёмки Кларе.';}
 if(cargo==='linen')return 'Чистые простыня и наволочка, маркировка комплекта '+packingData(v).request.size+'. Комплект для палаты 406.';
 if(cargo==='delivery')return 'Комплект передан в палату 406. Квитанцию необходимо вернуть Кларе.';
 if(cargo==='copies'){const d=compareData(v),names=d.documents[0].fields.filter((x,i)=>x.value!==d.documents[1].fields[i].value).map(x=>x.label.toLowerCase());return 'Подтверждены расхождения: '+names.join(', ')+'. Неподтверждённые данные не добавлялись.';}
 if(cargo==='bell407'||cargo==='bell408'){const d=diagnosis(v,cargo);return 'Палата '+cargo.slice(4)+'. '+(d.connected?'Разъём установлен. ':'Разъём отсоединён. ')+(d.indicator==='on'?'Индикатор загорелся. ':'Индикатор не загорелся. ')+d.response;}
 if(cargo==='log')return 'Записи расположены по указанному времени; неизвестные сведения об исполнителе не добавлялись.';
 const a=details(v,'patient');if(cargo==='baseline')return 'Записано в коридоре A: '+Object.keys(a).map(k=>labels[k]+': '+a[k]).join('; ')+'.';
 if(cargo==='difference'){const b=details(v,'trip');return 'В карточке: '+Object.keys(a).filter(k=>a[k]!==b[k]).map(k=>labels[k]+': '+a[k]+' → '+b[k]).join('; ')+'. Причина расхождения не установлена.';}
 return null;
}
return Object.freeze({ids,owner,brief,make,restore,board,operate,observation,description});
});
