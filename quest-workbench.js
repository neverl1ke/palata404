/* Task work surfaces. All evidence and progress come from the quest model. */
(function(){
'use strict';
let scrollMemo=null;
const svgNS='http://www.w3.org/2000/svg';
function node(tag,className,text){const e=document.createElement(tag);if(className)e.className=className;if(text!==undefined)e.textContent=String(text??'');return e;}
function label(value){
 const words={true:'да',false:'нет',intact:'целая',broken:'повреждена',sealed:'целая',damaged:'повреждена',clean:'чистая',stained:'пятна на ткани',torn:'надрыв ткани',dirty:'загрязнена',connected:'соединён',disconnected:'отсоединён'};
 return value===''?'—':(words[String(value)]??String(value??'—'));
}
function icon(kind,condition){
 const s=document.createElementNS(svgNS,'svg');s.setAttribute('viewBox','0 0 180 116');s.setAttribute('aria-hidden','true');s.classList.add('workbench-object-illustration');
 const add=(tag,attrs)=>{const e=document.createElementNS(svgNS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));s.append(e);return e;};
 if(kind==='linen'){
  add('path',{d:'M24 37 139 26 161 49 45 64Z',fill:'#eee9d9',stroke:'#8b8779','stroke-width':2});
  add('path',{d:'M24 37v36l21 18 116-14V49L45 64Z',fill:'#c7c6b5',stroke:'#8b8779','stroke-width':2});
  add('path',{d:'m45 65 116-16M45 77l116-15M45 87l116-13M54 48l86-8',fill:'none',stroke:'#aaa997','stroke-width':2});
  add('path',{d:'m20 31 120-12 26 25-1 39-120 17-25-22Z',fill:'none',stroke:'#f3eedc','stroke-width':2,opacity:.85});
  if(/stained|dirty|пятн|загряз/.test(String(condition)))for(const[x,y,r]of[[96,44,8],[111,48,5],[87,48,3]])add('ellipse',{cx:x,cy:y,rx:r,ry:r*.5,fill:'#83715a',opacity:.65});
  if(/поврежд.*упаков/.test(String(condition)))add('path',{d:'m165 45-7 7 7 5-8 9 7 7',fill:'none',stroke:'#655849','stroke-width':3});
  else if(/torn|damaged|надрыв|поврежд/.test(String(condition)))add('path',{d:'m126 59-8 9 7 2-12 12',fill:'none',stroke:'#655849','stroke-width':3});
 }else if(kind==='bell'){
  add('rect',{x:35,y:10,width:110,height:96,rx:7,fill:'#c6c0a9',stroke:'#695e48','stroke-width':3});
  add('circle',{cx:90,cy:39,r:12,fill:condition==='on'?'#b7c87c':'#665e48',stroke:'#504835','stroke-width':3});
  add('circle',{cx:90,cy:77,r:18,fill:'#8d4c3c',stroke:'#59352b','stroke-width':3});
  add('path',{d:'M90 95v13m-39-88h8m62 0h8',fill:'none',stroke:'#6f624c','stroke-width':3});
 }else{
  add('path',{d:'m22 39 112-23 28 23-113 25Z',fill:'#e7dfc7',stroke:'#7c7059','stroke-width':2});
  add('path',{d:'M22 39v38l27 23V64m0 36 113-21V39',fill:'#bdb197',stroke:'#7c7059','stroke-width':2});
  add('path',{d:'m76 28 24 25v36',fill:'none',stroke:'#9d7356','stroke-width':7});
  if(/поврежд|broken|damaged/.test(String(condition)))add('path',{d:'m91 49 15-4-7 10 11 0',fill:'none',stroke:'#d8c9aa','stroke-width':5});
  add('rect',{x:111,y:55,width:36,height:22,rx:1,fill:'#eee7d4',stroke:'#8e7b5e','stroke-width':1.5});
  add('path',{d:'m117 62 22-4m-22 11 22-4',fill:'none',stroke:'#8e7b5e','stroke-width':1.5});
 }
 return s;
}
function facts(rows){const dl=node('dl','workbench-facts');for(const[k,v]of rows){dl.append(node('dt','',k),node('dd','',label(v)));}return dl;}
function roomLabel(value){const name=String(value??'—');return /^\d+$/.test(name)?'Палата '+name:name;}
function render(host,options){
 const {board,act,close}=options;if(!board||!host)return null;
 const section=node('section','quest-workbench');section.setAttribute('role','dialog');section.setAttribute('aria-modal','true');section.dataset.workKind=board.kind;section.dataset.workAction=board.actionId||'';
 const titleId='quest-workbench-title';section.setAttribute('aria-labelledby',titleId);
 const toolbar=node('nav','workbench-toolbar');toolbar.setAttribute('aria-label','Управление осмотром');
 const key=board.actionId||board.jobId||board.kind;
 function button(text,op,value,focusKey,extra={}){
  const b=node('button',extra.className||'workbench-button',text);b.type='button';b.dataset.workFocus=focusKey||[op,typeof value==='object'?value?.id:value].filter(x=>x!==undefined).join(':');b.dataset.workOp=op;if(value!==undefined)b.dataset.workValue=typeof value==='object'?JSON.stringify(value):String(value);
  if(extra.pressed!==undefined)b.setAttribute('aria-pressed',String(extra.pressed));if(extra.disabled)b.disabled=true;if(extra.ariaLabel)b.setAttribute('aria-label',extra.ariaLabel);
  b.addEventListener('click',()=>{const scroller=section.querySelector('.workbench-scroll');scrollMemo={key,top:scroller?.scrollTop||0};let result;try{result=act({op,...(value===undefined?{}:{value})});}finally{scrollMemo=null;}if(result?.message&&section.isConnected)status.textContent=result.message;});return b;
 }
 const back=node('button','workbench-back','К осмотру комнаты');back.type='button';back.dataset.workFocus='close';back.onclick=()=>{scrollMemo=null;close();};
 const caseNumber=node('span','workbench-case-number','Лист поручения · '+String(board.jobId||'').toUpperCase());toolbar.append(back,caseNumber);section.append(toolbar);
 const scroll=node('div','workbench-scroll');scroll.tabIndex=-1;
 const paper=node('div','workbench-paper document-paper');const masthead=node('div','workbench-masthead');const emblem=node('img','workbench-emblem');emblem.src='assets/ui/wardrobe/requested-header-emblem.webp';emblem.alt='Эмблема учреждения';emblem.draggable=false;
 const name=node('div','workbench-institution');name.append(node('small','','МЕДИЦИНСКАЯ ДОКУМЕНТАЦИЯ'),node('strong','','Центр интенсивного лечения'),node('span','','психических расстройств №404'));const stamp=document.createElement('document-stamp');stamp.setAttribute('type','service');stamp.setAttribute('label','В РАБОТЕ');stamp.setAttribute('rotate','-5');masthead.append(emblem,name,stamp);paper.append(masthead);
 const heading=node('h2','workbench-heading',board.title||'Поручение');heading.id=titleId;heading.tabIndex=-1;heading.dataset.workHeading='';paper.append(heading,node('p','workbench-instruction',board.instruction||'Выполните поручение по наблюдаемым признакам.'));
 const area=node('div','workbench-area');const selected=new Set(board.selected||[]),marked=new Set(board.marked||[]);
 const footer=node('footer','workbench-footer');const status=node('p','workbench-status',options.feedback||options.message||board.feedback||'Изменения сохраняются по мере работы.');status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.setAttribute('aria-atomic','true');
 function request(title,rows){const r=node('aside','workbench-request');r.append(node('h3','',title),facts(rows));return r;}
 function submit(text,disabled=false){footer.append(button(text,'submit',undefined,'submit',{className:'workbench-button workbench-submit',disabled}));}

 if(board.kind==='inspection'){
  area.append(request('Требование процедурной',[['Комплект',board.request?.kit],['Партия',board.request?.lot],['Упаковка','проверить маркировку и пломбу']]));
  const tray=node('div','workbench-tray');tray.setAttribute('aria-label','Контейнеры на проверку');
  for(const item of board.items||[]){
   const card=node('article','workbench-item'+(selected.has(item.id)?' is-selected':''));card.dataset.workItem=item.id;card.append(icon('parcel',item.inspected?item.details?.seal:null),node('h3','',item.name||'Контейнер'));
   if(item.inspected&&item.details)card.append(facts([['Комплект',item.details.kit],['Партия',item.details.lot],['Пломба',item.details.seal]]));else card.append(node('p','workbench-muted','Маркировка и пломба ещё не осмотрены.'));
   const actions=node('div','workbench-item-actions');actions.append(button(item.inspected?'Осмотрено':'Осмотреть','inspect',item.id,'inspect:'+item.id,{disabled:!!item.inspected}),button(selected.has(item.id)?'Выбран':'Выбрать','select',item.id,'select:'+item.id,{pressed:selected.has(item.id),disabled:!item.inspected}));card.append(actions);tray.append(card);
  }area.append(tray);submit('Подтвердить проверенный комплект',!selected.size);
 }else if(board.kind==='packing'){
  area.append(request('Заявка на бельё',[['Палата',board.request?.destination],['Размер',board.request?.size],['В комплекте',(board.request?.components||[]).join(', ')]]));
  const shelves=node('div','workbench-tray workbench-linen-shelf');shelves.setAttribute('aria-label','Бельё для комплектации');
  for(const item of board.items||[]){const card=node('article','workbench-item'+(selected.has(item.id)?' is-selected':''));card.dataset.workItem=item.id;card.append(icon('linen',item.condition),node('h3','',item.name||item.type),facts([['Предмет',item.type],['Размер',item.size],['Состояние',item.condition]]),button(selected.has(item.id)?'Убрать из комплекта':'Добавить в комплект','select',item.id,'select:'+item.id,{pressed:selected.has(item.id)}));shelves.append(card);}
  const packed=node('aside','workbench-packing-list');packed.append(node('h3','','Собираемый комплект'));
  if(!selected.size)packed.append(node('p','workbench-muted','Выберите вещи по заявке.'));
  for(const id of selected){const item=(board.items||[]).find(x=>x.id===id);if(item)packed.append(node('p','workbench-picked',item.name||item.type));}
  packed.append(node('p','workbench-muted','Проверьте комплект перед упаковкой. Повреждённые и чужие вещи можно отложить.'));area.append(shelves,packed);submit('Упаковать комплект',!selected.size);
 }else if(board.kind==='delivery'){
  const delivery=node('div','workbench-delivery');delivery.append(icon('parcel'),node('h3','','Место передачи · палата '+String(board.request?.destination||'406')));
  delivery.append(node('p','',board.parcel?'Проверьте номер на пакете и передайте принесённое бельё.':'Принесённого комплекта нет в инвентаре.'));
  const receipt=node('div','workbench-receipt');receipt.append(node('span','','КВИТАНЦИЯ ПЕРЕДАЧИ'),node('p','','Комплект: __________________'),node('p','','Палата: '+String(board.request?.destination||'406')),node('small','','Заполняется после передачи белья.'));delivery.append(receipt);area.append(delivery);footer.append(button('Передать комплект и получить квитанцию','deliver',undefined,'deliver',{className:'workbench-button workbench-submit',disabled:!board.parcel}));
 }else if(board.kind==='compare'){
  const documents=node('div','workbench-documents');for(const[index,doc]of(board.documents||[]).entries()){const sheet=node('article','workbench-record');sheet.append(node('small','workbench-record-number','Экземпляр '+(index+1)),node('h3','',doc.title||'Запись'),facts((doc.fields||[]).map(f=>[f.label,f.value])));documents.append(sheet);}
  const marks=node('fieldset','workbench-marks');marks.append(node('legend','','Отметьте расходящиеся поля'));const seen=new Set();for(const doc of board.documents||[])for(const field of doc.fields||[]){if(seen.has(field.id))continue;seen.add(field.id);marks.append(button(field.label,'mark',field.id,'mark:'+field.id,{pressed:marked.has(field.id),className:'workbench-mark'}));}area.append(documents,marks);submit('Оформить лист сверки',!marked.size);
 }else if(board.kind==='diagnostic'){
  const station=node('div','workbench-call-station');station.append(node('span','workbench-call-number','ПАЛАТА '+String(board.room||'')),icon('bell',board.indicator));
  const indicator=node('p','workbench-indicator'+(board.indicator==='on'?' is-on':''));indicator.append(node('i','workbench-indicator-lamp'),node('span','',board.tested?(board.indicator==='on'?'Индикатор загорелся':'Индикатор не загорелся'):'Индикатор · тест не выполнялся'));station.append(indicator);
  station.append(button(board.inspected?'Соединение осмотрено':'Осмотреть соединение','inspect','connector','inspect:connector',{disabled:!!board.inspected}),button(board.tested?'Вызов проверен':'Проверить вызов','test',undefined,'test',{disabled:!!board.tested||!board.inspected}));
  if(board.inspected&&board.connector)station.append(node('p','workbench-connector-observation',board.connector.text||('Соединение: '+(board.connector.connected?'подключено':'отсоединено'))));
  const response=node('div','workbench-call-response');response.append(node('h3','','Ответ поста'),node('p','',board.tested?(board.response||'Ответ не поступил.'):'Сначала выполните проверку вызова.'));station.append(response);
  const form=node('fieldset','workbench-diagnostic-form');form.append(node('legend','','Акт проверки'));for(const report of board.reports||[])form.append(button(report.label,'select',report.id,'report:'+report.id,{pressed:selected.has(report.id),disabled:!board.inspected||!board.tested,className:'workbench-mark'}));form.append(node('p','workbench-muted','Запишите вывод по соединению, индикатору и ответу поста.'));area.append(station,form);submit('Подписать акт',!selected.size||!board.inspected||!board.tested);
 }else if(board.kind==='timeline'){
  const pool=node('section','workbench-slip-pool');pool.append(node('h3','','Записи на столе'));const ordered=new Set(board.order||[]);
  for(const card of board.cards||[]){if(ordered.has(card.id))continue;const slip=button('','place',card.id,'place:'+card.id,{className:'workbench-slip'});slip.append(node('strong','',card.time||'Время не указано'),node('span','',roomLabel(card.room)),node('small','',card.note||''),node('em','','Поместить в журнал'));pool.append(slip);}
  if(![...(board.cards||[])].some(x=>!ordered.has(x.id)))pool.append(node('p','workbench-muted','Все записи помещены в журнал. Порядок можно изменить.'));
  const journal=node('section','workbench-timeline');journal.append(node('h3','','Лист обхода'));const list=node('ol','workbench-timeline-list');
  for(const[idIndex,id]of(board.order||[]).entries()){const card=(board.cards||[]).find(x=>x.id===id);if(!card)continue;const row=node('li','workbench-timeline-entry');row.append(node('strong','',card.time||'—'),node('span','',roomLabel(card.room)+' · '+String(card.note||'')));const controls=node('div','workbench-order-controls');controls.append(button('↑','move',{id,direction:'up'},'move:'+id+':up',{disabled:idIndex===0,ariaLabel:'Поднять запись '+String(card.time)}),button('↓','move',{id,direction:'down'},'move:'+id+':down',{disabled:idIndex===(board.order||[]).length-1,ariaLabel:'Опустить запись '+String(card.time)}),button('Убрать','remove',id,'remove:'+id));row.append(controls);list.append(row);}journal.append(list);if(!(board.order||[]).length)journal.append(node('p','workbench-muted','Добавляйте записи в порядке обхода.'));area.append(pool,journal);submit('Зафиксировать порядок',!(board.order||[]).length);
 }else if(board.kind==='baseline'){
  const plate=node('div','workbench-observation-plate');plate.append(node('small','','ТАБЛИЧКА КОРИДОРА A'),facts((board.details||[]).map(f=>[f.label,f.value])));
  const card=node('article','workbench-observation-card');card.append(node('h3','','Карточка наблюдения'),node('p','','Зафиксируйте видимые надписи. Сравнивать их можно будет по этой карточке.'));if(board.recorded)card.append(node('p','workbench-picked','Наблюдение записано.'));area.append(plate,card);footer.append(button('Записать наблюдение в карточку','record',undefined,'record',{className:'workbench-button workbench-submit',disabled:!!board.recorded}));
 }else if(board.kind==='difference'){
  const papers=node('div','workbench-documents');for(const[title,fields]of[['Моя карточка',board.baseline||[]],['Наблюдение на месте',board.current||[]]]){const sheet=node('article','workbench-record');sheet.append(node('h3','',title),facts(fields.map(f=>[f.label,f.value])));papers.append(sheet);}
  const fields=node('fieldset','workbench-marks');fields.append(node('legend','','Что расходится с карточкой?'));for(const field of board.current||[])fields.append(button(field.label,'mark',field.id,'mark:'+field.id,{pressed:marked.has(field.id),className:'workbench-mark'}));area.append(papers,fields);submit('Записать наблюдаемое расхождение',!marked.size);
 }else{
  area.append(node('p','','Этот рабочий лист сейчас недоступен. Вернитесь к осмотру комнаты.'));
 }
 paper.append(area);scroll.append(paper);footer.append(status);section.append(scroll,footer);host.replaceChildren(section);
 if(scrollMemo?.key===key){const top=scrollMemo.top;queueMicrotask(()=>{if(section.isConnected)scroll.scrollTop=top;});}
 section.addEventListener('keydown',event=>{
  if(event.key==='Escape'){event.preventDefault();event.stopPropagation();scrollMemo=null;close();return;}
  if(event.key!=='Tab')return;
  const controls=[...section.querySelectorAll('button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),[tabindex="0"]')].filter(e=>e.getClientRects().length);
  if(!controls.length){event.preventDefault();heading.focus();return;}const first=controls[0],last=controls.at(-1);
  if(event.shiftKey&&(document.activeElement===first||document.activeElement===heading)){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
 });
 return section;
}
window.PalataQuestWorkbench=Object.freeze({render});
})();
