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
 if(['linen','sheet','pillowcase'].includes(kind)){
  const pillow=kind==='pillowcase';
  add('path',{d:pillow?'M39 38Q89 23 140 36l12 34q-48 20-107 5Z':'M22 39q57-17 123-10l17 28Q109 76 39 71Z',fill:'#eee9d9',stroke:'#8b8779','stroke-width':2});
  add('path',{d:pillow?'m39 38 6 37q57 12 107-5l-2 14q-49 19-103 5l-7-13Z':'m22 39 17 32q70 5 123-14l-2 23Q105 99 40 91L23 69Z',fill:'#c9c8b8',stroke:'#8b8779','stroke-width':2});
  add('path',{d:pillow?'M48 49q45-12 89-1m-89 12q47 11 91 0m-86 13q42 10 84-1':'M40 78q63 8 114-10M40 86q65 6 113-11M49 48q48-12 91-7',fill:'none',stroke:'#aaa997','stroke-width':2});
  add('path',{d:pillow?'M35 31q57-14 111-2l13 42-5 21q-56 18-113 0l-7-20Z':'m18 32 130-11 21 34-2 31q-64 23-132 12L17 72Z',fill:'none',stroke:'#f3eedc','stroke-width':2,opacity:.85});
  if(/stained|dirty|пятн|загряз/.test(String(condition)))for(const[x,y,r]of[[96,44,8],[111,48,5],[87,48,3]])add('ellipse',{cx:x,cy:y,rx:r,ry:r*.5,fill:'#83715a',opacity:.65});
  if(/поврежд.*упаков/.test(String(condition)))add('path',{d:'m165 45-7 7 7 5-8 9 7 7',fill:'none',stroke:'#655849','stroke-width':3});
  else if(/torn|damaged|надрыв|поврежд/.test(String(condition)))add('path',{d:'m126 59-8 9 7 2-12 12',fill:'none',stroke:'#655849','stroke-width':3});
 }else if(kind==='medicalCase'){
  add('path',{d:'m23 39 106-16 28 20-108 20Z',fill:'#b5b3a3',stroke:'#5e645b','stroke-width':2});
  add('path',{d:'M23 39v42l26 17V63m0 35 108-19V43',fill:'#858d80',stroke:'#535d50','stroke-width':2});
  add('path',{d:'M29 45 50 57l100-17M29 53l20 12 101-18M51 91l99-17',fill:'none',stroke:'#cbd0bd','stroke-width':1.5});
  add('path',{d:'m71 31 28-4 9 7-30 5Zm-20 33v16l12-2V62m64-12v17l12-3V49',fill:'#bcbda8',stroke:'#525c50','stroke-width':2});
  add('path',{d:'m61 77 4 7 48-9',fill:'none',stroke:'#786a50','stroke-width':2});
  if(/поврежд|broken|damaged/.test(String(condition)))add('path',{d:'m83 78 7-5-1 7 8-4',fill:'none',stroke:'#ded6bc','stroke-width':4});
  add('path',{d:'m111 58 26-4v15l-26 5Z',fill:'#e8dfc7',stroke:'#776a53','stroke-width':1.3});
 }else if(kind==='bell'){
  add('path',{d:'M85 0h10v29H85Z',fill:'#82765a',stroke:'#544b39','stroke-width':2});
  add('rect',{x:39,y:25,width:102,height:81,rx:6,fill:'#b0a180',stroke:'#685a40','stroke-width':3});
  add('path',{d:'M44 31h91v67H44',fill:'none',stroke:'#d3bd8c','stroke-width':1.5,opacity:.6});
  for(const[x,y]of[[49,36],[131,36],[49,96],[131,96]]){add('circle',{cx:x,cy:y,r:3,fill:'#6e5d42'});add('path',{d:'m'+(x-2)+' '+y+'h4',stroke:'#352f25','stroke-width':1});}
  add('circle',{cx:90,cy:70,r:24,fill:'#66513c',stroke:'#51422f','stroke-width':2});
  add('circle',{cx:90,cy:70,r:20,fill:'#8d4938',stroke:'#5c3028','stroke-width':2});
  add('path',{d:'M77 60q13-10 25 0',fill:'none',stroke:'#bf8264','stroke-width':2,opacity:.65});
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
function linenIllustration(kind,condition){
 const candidate=window.PalataQuestBedView?.createPiece(kind,condition);if(!candidate)return icon(kind,condition);
 candidate.addEventListener('error',()=>candidate.replaceWith(icon(kind,condition)),{once:true});return candidate;
}
function reportLabel(report){return {working:'Ответ поста получен',disconnected:'Разъём отсоединён',noResponse:'Индикатор горит; ответ поста не получен',unassessed:'Состояние требует нового осмотра'}[report]||'Результат ещё не установлен';}
function facts(rows){const dl=node('dl','workbench-facts');for(const[k,v]of rows){dl.append(node('dt','',k),node('dd','',label(v)));}return dl;}
function connectorView(connector){
 const figure=node('figure','workbench-connector-view'),s=document.createElementNS(svgNS,'svg');s.setAttribute('viewBox','0 0 240 74');s.setAttribute('aria-hidden','true');
 const add=(tag,attrs)=>{const e=document.createElementNS(svgNS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));s.append(e);};
 add('rect',{x:166,y:13,width:38,height:48,rx:4,fill:'#b8b9a4',stroke:'#5f6351','stroke-width':2});
 add('rect',{x:170,y:25,width:12,height:23,rx:2,fill:'#4b5145'});
 const end=connector.connected?172:136;
 add('path',{d:'M18 48q22-27 46-7t38-3h'+(end-126),fill:'none',stroke:'#555d4f','stroke-width':7,'stroke-linecap':'round'});
 add('rect',{x:end-26,y:27,width:26,height:23,rx:4,fill:'#8b927d',stroke:'#515b49','stroke-width':2});
 add('path',{d:'M'+end+' 34h8m-8 10h8',fill:'none',stroke:'#b8ad85','stroke-width':3});
 add('path',{d:'M174 18h7m15 37h-7',fill:'none',stroke:'#7c806d','stroke-width':2});
 const caption=node('figcaption');caption.append(node('strong','','Схема осмотра соединения'),node('span','',connector.text||('Соединение: '+(connector.connected?'подключено':'отсоединено'))));figure.append(s,caption);return figure;
}
function roomLabel(value){const name=String(value??'—');return /^\d+$/.test(name)?'Палата '+name:name;}
function bedDiagram(placed){
 const s=document.createElementNS(svgNS,'svg');s.setAttribute('viewBox','0 0 500 340');s.setAttribute('aria-hidden','true');
 const add=(tag,attrs)=>{const e=document.createElementNS(svgNS,tag);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,String(v));s.append(e);};
 add('rect',{x:79,y:18,width:342,height:295,rx:22,fill:'#858b7a',stroke:'#586250','stroke-width':5});
 add('rect',{x:93,y:33,width:314,height:263,rx:14,fill:placed.has('sheet')?'#e8e2cc':'#b9b99f',stroke:'#6e745f','stroke-width':2});
 add('path',{d:'M105 15V6m73 9V6m144 9V6m73 9V6M105 313v19m290-19v19',stroke:'#5c6554','stroke-width':6,'stroke-linecap':'round'});
 add('rect',{x:125,y:51,width:250,height:70,rx:15,fill:placed.has('pillowcase')?'#f0ead7':'#aaa993',stroke:'#7f826c','stroke-width':2});
 add('path',{d:'M141 66q111-17 218 0m-215 42q107 14 213-1',fill:'none',stroke:placed.has('pillowcase')?'#b9b49e':'#8c8f79','stroke-width':2});
 if(placed.has('sheet'))add('path',{d:'M110 148q136-14 281 0M111 258q136 12 279-1M113 156v116m276-116v116',fill:'none',stroke:'#b8b39b','stroke-width':2});
 return s;
}
function bedReference(source='assets/quest-scenes/ward406.webp'){
 const figure=node('figure','workbench-bed-reference'),s=document.createElementNS(svgNS,'svg');s.setAttribute('viewBox','140 565 970 290');s.setAttribute('role','img');s.setAttribute('aria-label','Подушка и постель палаты 406');
 const image=document.createElementNS(svgNS,'image');image.setAttribute('href',source);image.setAttribute('width','1536');image.setAttribute('height','1024');s.append(image);figure.append(s,node('figcaption','','Ориентир · койка палаты 406'));return figure;
}
function render(host,options){
 const {board,act,close}=options;if(!board||!host)return null;
 const section=node('section','quest-workbench');section.setAttribute('role','dialog');section.setAttribute('aria-modal','true');section.dataset.workKind=board.kind;section.dataset.workAction=board.actionId||'';if(board.revision===3&&['k3','d2','d3'].includes(board.jobId))section.dataset.workRevision='3';
 const titleId='quest-workbench-title';section.setAttribute('aria-labelledby',titleId);
 const toolbar=node('nav','workbench-toolbar');toolbar.setAttribute('aria-label','Управление осмотром');
 const key=board.actionId||board.jobId||board.kind;
 function button(text,op,value,focusKey,extra={}){
  const b=node('button',extra.className||'workbench-button',text);b.type='button';b.dataset.workFocus=focusKey||[op,typeof value==='object'?value?.id:value].filter(x=>x!==undefined).join(':');b.dataset.workOp=op;if(value!==undefined)b.dataset.workValue=typeof value==='object'?JSON.stringify(value):String(value);
  if(extra.pressed!==undefined)b.setAttribute('aria-pressed',String(extra.pressed));if(extra.disabled)b.disabled=true;if(extra.ariaLabel)b.setAttribute('aria-label',extra.ariaLabel);
  b.addEventListener('click',()=>{const scroller=section.querySelector('.workbench-scroll');scrollMemo={key,top:scroller?.scrollTop||0,briefOpen:section.querySelector('.workbench-brief')?.open};let result;try{result=act({op,...(value===undefined?{}:{value})});}finally{scrollMemo=null;}if(result?.message&&section.isConnected)status.textContent=result.message;});return b;
 }
 const back=node('button','workbench-back','К осмотру комнаты');back.type='button';back.dataset.workFocus='close';back.onclick=()=>{scrollMemo=null;close();};
 const caseNumber=node('span','workbench-case-number','Лист поручения · '+String(board.jobId||'').toUpperCase());if(board.kind==='caseCompare')caseNumber.append(node('span','workbench-case-scroll-hint','Лист прокручивается ↓'));toolbar.append(back,caseNumber);section.append(toolbar);
 const scroll=node('div','workbench-scroll');scroll.tabIndex=-1;
 const paper=node('div','workbench-paper document-paper');const masthead=node('div','workbench-masthead');const emblem=node('img','workbench-emblem');emblem.src='assets/ui/wardrobe/requested-header-emblem.webp';emblem.alt='Эмблема учреждения';emblem.draggable=false;
 const name=node('div','workbench-institution');name.append(node('small','','МЕДИЦИНСКАЯ ДОКУМЕНТАЦИЯ'),node('strong','','Центр интенсивного лечения'),node('span','','психических расстройств №404'));const stamp=document.createElement('document-stamp');stamp.setAttribute('type','service');stamp.setAttribute('label','В РАБОТЕ');stamp.setAttribute('rotate','-5');masthead.append(emblem,name,stamp);paper.append(masthead);
 const heading=node('h2','workbench-heading',board.title||'Поручение');heading.id=titleId;heading.tabIndex=-1;heading.dataset.workHeading='';paper.append(heading,node('p','workbench-instruction',board.instruction||'Выполните поручение по наблюдаемым признакам.'));
 if(board.brief){const brief=node('details','workbench-brief');brief.setAttribute('aria-label','Поручение');brief.open=scrollMemo?.key===key&&scrollMemo.briefOpen!==undefined?scrollMemo.briefOpen:false;const summary=node('summary','workbench-brief-summary');if(board.brief.giver)summary.append(node('strong','workbench-brief-giver','От: '+board.brief.giver));if(board.brief.purpose)summary.append(node('span','workbench-brief-purpose',board.kind==='caseCompare'?'Поручение и подтверждение':board.brief.purpose));brief.append(summary);if(board.kind==='caseCompare'&&board.brief.purpose)brief.append(node('p','workbench-case-brief-detail',board.brief.purpose));if(board.brief.deliverable)brief.append(node('small','workbench-brief-deliverable','Подтверждение: '+board.brief.deliverable));paper.append(brief);}
 const area=node('div','workbench-area');const selected=new Set(board.selected||[]),marked=new Set(board.marked||[]);
 const initialScrollCue=board.kind==='caseCompare'?'Источники и выводы ниже — прокрутите лист':board.revision===3?(board.jobId==='d2'&&board.kind==='timeline'&&!(board.order||[]).length&&!(board.cards||[]).some(card=>card.reverseRead)?'Записи ниже — прокрутите лист':board.jobId==='d3'&&board.kind==='difference'&&board.allowNoChanges===true&&!marked.size&&!board.noChanges?'Сравнение ниже — прокрутите лист':''):'';
 const footer=node('footer','workbench-footer');const status=node('p','workbench-status',options.feedback||options.message||board.feedback||initialScrollCue||'Изменения сохраняются по мере работы.');status.setAttribute('role','status');status.setAttribute('aria-live','polite');status.setAttribute('aria-atomic','true');
 function request(title,rows){const r=node('aside','workbench-request');r.append(node('h3','',title),facts(rows));return r;}
 function submit(text,disabled=false){footer.append(button(text,'submit',undefined,'submit',{className:'workbench-button workbench-submit',disabled}));}
 function pairedRecords(groups,legend){
  const comparison=node('fieldset','workbench-pairing');comparison.append(node('legend','',legend));
  const headers=node('div','workbench-pairing-head');headers.append(node('span','','Поле'),...groups.map(([title])=>node('strong','',title)));comparison.append(headers);
  const ids=[...new Set(groups.flatMap(([,fields])=>fields.map(f=>f.id)))];
  for(const id of ids){const source=groups.map(([,fields])=>fields.find(f=>f.id===id)),name=source.find(Boolean)?.label||id,chosen=marked.has(id),row=button('','mark',id,'mark:'+id,{pressed:chosen,className:'workbench-compare-row'});row.dataset.workField=id;
   const field=node('span','workbench-pair-field'),tick=node('i','workbench-pair-tick',chosen?'✓':'');tick.setAttribute('aria-hidden','true');field.append(tick,node('strong','',name),node('small','',chosen?'Отмечено':'Отметить'));row.append(field);
   for(const[index,[title]]of groups.entries()){const value=node('span','workbench-pair-value');value.append(node('small','',title),node('span','',label(source[index]?.value)));row.append(value);}comparison.append(row);
  }
  comparison.append(node('p','workbench-muted workbench-pairing-note','Нажмите на строку, чтобы отметить её. Повторное нажатие снимает отметку.'));return comparison;
 }
 function timelineEvidence(card,ordered=false){
  const evidence=node('article','workbench-evidence-slip');evidence.dataset.slipId=card.id;
  const time=node('strong','workbench-evidence-time',card.time===null?(ordered?'Время не установлено':'Время не читается'):card.time);time.dataset.timeState=card.timeState||'readable';
  evidence.append(time,node('span','workbench-evidence-room',roomLabel(card.room)),node('p','workbench-evidence-note',card.note||''));
  if(card.reverseAvailable){
   const reverse=node('section','workbench-slip-reverse');reverse.append(button(card.reverseRead?'Оборот прочитан':'Прочитать оборот','readReverse',card.id,'readReverse:'+card.id,{className:'workbench-read-reverse',disabled:!!card.reverseRead}));
   if(card.reverseRead&&typeof card.reverseText==='string'){
    const fact=node('div','workbench-reverse-fact');fact.append(node('strong','','Запись на обороте'),node('p','',card.reverseText));reverse.append(fact);
   }else reverse.append(node('p','workbench-reverse-prompt','На обороте сохранилась запись о связанных событиях.'));
   evidence.append(reverse);
  }
  return evidence;
 }

 if(board.kind==='inspection'){
  area.append(request('Требование процедурной',[['Комплект',board.request?.kit],['Партия',board.request?.lot],['Упаковка','проверить маркировку и пломбу']]));
  const tray=node('div','workbench-tray');tray.setAttribute('aria-label','Контейнеры на проверку');
  for(const item of board.items||[]){
   const card=node('article','workbench-item workbench-medical-container'+(selected.has(item.id)?' is-selected':''));card.dataset.workItem=item.id;card.append(icon('medicalCase',item.inspected?item.details?.seal:null),node('h3','',item.name||'Контейнер'),node('span','workbench-item-state',selected.has(item.id)?'Выбран для приёмки':item.inspected?'Осмотрен · не выбран':'Ещё не осмотрен'));
   if(item.inspected&&item.details){const tag=facts([['Комплект',item.details.kit],['Партия',item.details.lot]]);tag.classList.add('workbench-container-label');const seal=node('p','workbench-container-seal','Пломба: '+label(item.details.seal));seal.dataset.seal=item.details.seal;card.append(tag,seal);}else card.append(node('p','workbench-muted workbench-container-label','Осмотрите контейнер, чтобы прочитать бирку.'));
   const actions=node('div','workbench-item-actions');actions.append(button(item.inspected?'Осмотрено':'Осмотреть','inspect',item.id,'inspect:'+item.id,{disabled:!!item.inspected}),button(selected.has(item.id)?'Выбран':'Выбрать','select',item.id,'select:'+item.id,{pressed:selected.has(item.id),disabled:!item.inspected}));card.append(actions);tray.append(card);
  }area.append(tray);submit('Подтвердить проверенный комплект',!selected.size);
 }else if(board.kind==='packing'){
  const order=request('Заявка на бельё',[['Палата',board.request?.destination],['Маркировка комплекта',board.request?.size],['В комплекте',(board.request?.components||[]).join(', ')]]);if(board.request?.markingNote)order.append(node('p','workbench-marking-note',board.request.markingNote));area.append(order);
  const shelves=node('div','workbench-tray workbench-linen-shelf');shelves.setAttribute('aria-label','Бельё для комплектации');
  for(const item of board.items||[]){const card=node('article','workbench-item'+(selected.has(item.id)?' is-selected':'')+(item.unavailable?' is-unavailable':''));card.dataset.workItem=item.id;const identity=node('div','workbench-linen-identity');identity.append(node('h3','',item.name||item.type),node('span','workbench-item-state',item.unavailable?'Нет в выдаче':selected.has(item.id)?'В комплекте':'На полке'));card.append(linenIllustration(item.type==='Наволочка'?'pillowcase':'sheet',item.condition),identity,node('p','workbench-kit-mark','Маркировка комплекта: '+label(item.size)));if(item.measure)card.append(node('p','workbench-linen-measure','Размер: '+label(item.measure)));if(board.authorizedSubstitution?.itemId===item.id)card.append(node('p','workbench-reserve-authorized','Клара разрешила замену'));const condition=node('div','workbench-condition');condition.append(node('small','','Состояние'),node('span','',item.unavailable?'По описи отсутствует':label(item.condition)));card.append(condition,button(item.unavailable?'Нет в наличии':selected.has(item.id)?'Убрать из комплекта':'Добавить в комплект','select',item.id,'select:'+item.id,{pressed:selected.has(item.id),disabled:!!item.unavailable}));shelves.append(card);}
  const packed=node('aside','workbench-packing-list');packed.append(node('h3','','Собираемый комплект · '+selected.size+'/2'));
  if(!selected.size)packed.append(node('p','workbench-muted','Пока пусто. Выберите вещи по заявке.'));
  for(const id of selected){const item=(board.items||[]).find(x=>x.id===id);if(item)packed.append(node('p','workbench-picked',(item.name||item.type)+' · '+label(item.size)+(item.measure?' · '+label(item.measure):'')+' · '+label(item.condition)));}
  if(board.request?.missingComponent&&!board.reserveGranted){const shortage=node('aside','workbench-shortage');shortage.append(node('h3','','Недостача по заявке'),node('p','','Сейчас не выдано: '+String(board.request.missingComponent)+'.'),button(board.shortageNoted?'Недостача отмечена':'Зафиксировать недостачу','noteShortage',undefined,'noteShortage',{disabled:!!board.shortageNoted}));if(board.shortageNoted)shortage.append(node('p','workbench-reserve-guidance','Уточните разрешённую замену у Клары в медпункте. Выбранное бельё останется в листе.'));area.append(shortage);}
  if(board.authorizedSubstitution)area.append(request('Разрешённая замена',[['Маркировка',board.authorizedSubstitution.mark],['Размер',board.authorizedSubstitution.measure],['Основание','Выдача согласована с Кларой']]));
  area.append(packed,shelves);submit('Упаковать комплект',!selected.size||!!board.request?.missingComponent&&!board.reserveGranted);
 }else if(board.kind==='clarification'){
  area.append(request('Замена отсутствующей вещи',[['Требуется',board.request?.neededType],['Нужный размер',board.request?.neededMeasure]]));
  const reserve=node('div','workbench-reserve-options');reserve.setAttribute('aria-label','Предложенные вещи из резерва');for(const option of board.options||[]){const card=button('','select',option.id,'select:'+option.id,{pressed:selected.has(option.id),className:'workbench-reserve-option'});card.append(linenIllustration('pillowcase'),node('strong','',option.label||'Наволочка из резерва'),node('span','workbench-linen-measure','Размер: '+label(option.measure)),node('small','',selected.has(option.id)?'Выбрано для согласования':'Выбрать для согласования'));reserve.append(card);}area.append(reserve);submit('Подтвердить замену',!selected.size);
 }else if(board.kind==='bedmaking'){
  const placed=new Set(board.placed||[]),explicitStart=Object.hasOwn(board,'preparationStarted'),started=!explicitStart||!!board.preparationStarted;
  if(explicitStart){section.dataset.bedExplicitStart='true';section.dataset.bedPreparation=started?'started':'not-started';}
  const pieces=node('section','workbench-bed-pieces');pieces.append(bedReference(board.referenceImage),node('h3','','Принесённый комплект'));
  if(explicitStart&&!started)pieces.append(node('p','workbench-bed-start-note','Смена белья ещё не начата. Начните подготовку, затем разместите простыню и наволочку. До начала кровать остаётся без изменений.'));
  for(const item of board.items||[]){const done=placed.has(item.id),choice=button('','selectPiece',item.id,'piece:'+item.id,{pressed:board.selectedPiece===item.id,disabled:done||!board.parcel||!started,className:'workbench-bed-piece'});choice.append(linenIllustration(item.id==='pillowcase'?'pillowcase':'sheet'),node('strong','',item.type||item.id),node('span','',label(item.measure)),node('small','',done?'Размещено':!started?'После начала смены':board.selectedPiece===item.id?'Выбрано · укажите место':'Выбрать вещь'));pieces.append(choice);}
  const visualPlaced=explicitStart&&!started?new Set(['sheet','pillowcase']):placed;
  const art=explicitStart?window.PalataQuestBedView?.create({source:board.referenceImage,preparationStarted:started,placed:[...placed],mode:'patient',crop:true}):null;
  if(art)pieces.querySelector('.workbench-bed-reference')?.remove();
  const scheme=node('section','workbench-bed-scheme');scheme.append(node('h3','',art?'Кровать 406 · крупный план':'Схема размещения'),node('p','workbench-muted',!started?'До начала смены кровать показана без изменений.':'Выберите принесённую вещь и её место на кровати.'));
  const diagram=node('div','workbench-bed-diagram'+(art?' has-bed-art':''));diagram.append(art||bedDiagram(visualPlaced));
  for(const target of board.targets||[]){if(art&&!started)continue;const part=target.id==='pillowZone'?'pillowcase':target.id==='sheetZone'?'sheet':null,done=part&&placed.has(part),zone=button(art?(done?'Готово':part==='sheet'?'Матрас':'Подушка'):explicitStart?(done?'Размещено':part==='sheet'?'Простыня':'Наволочка'):(target.label||'Место на кровати'),'place',target.id,'zone:'+target.id,{disabled:!board.parcel||!started||!board.selectedPiece||!!done,className:'workbench-bed-target',ariaLabel:target.label||'Место на кровати'});zone.dataset.bedZone=target.id;
   if(art&&part){const style=window.PalataQuestBedView.placementStyle(part);if(style)for(const[key,value]of Object.entries(style))zone.style[key]=value;}
   if(done&&!art&&!explicitStart)zone.append(node('small','','Размещено'));diagram.append(zone);
  }
  scheme.append(diagram);if(!board.parcel)scheme.append(node('p','workbench-reserve-guidance','Принесённого комплекта нет в инвентаре.'));
  area.append(pieces,scheme);if(explicitStart&&!started)footer.append(button('Начать смену белья','startBedPreparation',undefined,'startBedPreparation',{className:'workbench-button workbench-submit',disabled:!board.parcel}));footer.append(node('strong','workbench-placement-count',!started?'Смена ещё не начата':'Размещено '+placed.size+'/2'));
 }else if(board.kind==='delivery'){
  const delivery=node('div','workbench-delivery');delivery.append(icon('parcel'),node('h3','','Место передачи · палата '+String(board.request?.destination||'406')));
  delivery.append(node('p','',board.parcel?'Проверьте номер на пакете и передайте принесённое бельё.':'Принесённого комплекта нет в инвентаре.'));
  const receipt=node('div','workbench-receipt');receipt.append(node('span','','КВИТАНЦИЯ ПЕРЕДАЧИ · ЧЕРНОВИК'));const details=board.parcel&&board.parcelDetails;if(details){receipt.append(node('p','','Комплект: '+(details.components||[]).join(', ')),node('p','','Маркировка комплекта: '+label(details.size)));for(const item of details.items||[])receipt.append(node('p','workbench-receipt-item',(item.type||'Вещь')+(item.measure?' · '+label(item.measure):'')));}else receipt.append(node('p','','Принесённый комплект не подтверждён.'));receipt.append(node('p','','Палата: '+String(board.request?.destination||'406')),node('small','','Передача ещё не подтверждена. Подписанная квитанция появится после передачи белья.'));delivery.append(receipt);area.append(delivery);footer.append(button('Передать комплект и получить квитанцию','deliver',undefined,'deliver',{className:'workbench-button workbench-submit',disabled:!board.parcel}));
 }else if(board.kind==='caseCompare'){
  const documents=node('div','workbench-case-sources'),sourceCards=new Map();
  documents.setAttribute('aria-label','Документы одной процедуры');
  for(const doc of board.documents||[]){
   const card=node('article','workbench-case-source');card.dataset.caseSource=String(doc.id);card.id='quest-case-source-'+String(doc.id).replace(/[^a-zA-Z0-9_-]/g,'');card.tabIndex=-1;
   const sourceTitle=node('h3','',doc.title||'Документ');sourceTitle.id=card.id+'-title';card.setAttribute('aria-labelledby',sourceTitle.id);
   card.append(node('small','workbench-case-source-number','ДОКУМЕНТ '+String(doc.number||'')+' · ДЕЛО №'+String(doc.caseId||board.caseId||'')),sourceTitle,facts((doc.fields||[]).map(f=>[f.label,f.value])));
   sourceCards.set(doc.id,{card,doc});documents.append(card);
  }
  const decisions=node('div','workbench-case-decisions');decisions.setAttribute('aria-label','Выводы по документам');
  for(const issue of board.issues||[]){
   const field=node('fieldset','workbench-case-decision');field.dataset.caseField=String(issue.id);field.append(node('legend','',issue.title||'Вывод'));
   const evidence=node('nav','workbench-case-evidence');evidence.setAttribute('aria-label','Источники: '+String(issue.title||'вывод'));evidence.append(node('span','','Источники:'));
   for(const id of issue.sources||[]){
    const source=sourceCards.get(id);if(!source)continue;
    const link=node('a','workbench-case-source-link',source.doc.number||id);link.href='#'+source.card.id;link.dataset.caseSourceLink=String(id);link.setAttribute('aria-label','Источник '+String(source.doc.number||id)+': '+String(source.doc.title||'Документ'));
    // Reading a source is navigation within this sheet, never a work operation.
    link.addEventListener('click',event=>{event.preventDefault();source.card.scrollIntoView({block:'start',inline:'nearest',behavior:'instant'});source.card.focus({preventScroll:true});});evidence.append(link);
   }
   field.append(evidence);
   for(const choice of issue.choices||[]){
    const control=button(choice.label,'conclude',{field:issue.id,choice:choice.id},'conclude:'+issue.id+':'+choice.id,{pressed:board.conclusions?.[issue.id]===choice.id,className:'workbench-case-choice'});control.dataset.caseChoice=String(choice.id);field.append(control);
   }
   decisions.append(field);
  }
  area.append(documents,decisions,node('p','workbench-case-read-cue','Лист прокручивается ↓ Источники открываются по номеру; повторно прикреплять их не требуется.'));
  const chosen=(board.issues||[]).filter(issue=>(issue.choices||[]).some(choice=>choice.id===board.conclusions?.[issue.id])).length;
  footer.append(node('p','workbench-case-progress','Лист сверки · '+chosen+' из '+String((board.issues||[]).length)+' выводов выбрано'));
  submit('Оформить лист сверки');
 }else if(board.kind==='compare'){
  area.append(pairedRecords((board.documents||[]).map(doc=>[doc.title||'Запись',doc.fields||[]]),'Лист сверки · отметьте расходящиеся поля'));submit('Оформить лист сверки',!marked.size);
 }else if(board.kind==='diagnostic'){
  const station=node('div','workbench-call-station');station.append(node('span','workbench-call-number','ПАЛАТА '+String(board.room||'')));const unit=node('div','workbench-bell-unit');unit.append(icon('bell',board.indicator));const trigger=button(board.tested?'Вызов проверен':'Проверить вызов','test',undefined,'test',{disabled:!!board.tested||!board.inspected,className:'workbench-call-trigger',ariaLabel:board.tested?'Вызов проверен':'Нажать кнопку вызова'});unit.append(trigger);station.append(unit);
  const indicator=node('p','workbench-indicator'+(board.indicator==='on'?' is-on':''));indicator.append(node('i','workbench-indicator-lamp'),node('span','',board.tested?(board.indicator==='on'?'Индикатор загорелся':'Индикатор не загорелся'):'Индикатор · тест не выполнялся'));
  station.append(node('p','workbench-call-hint',board.tested?'Сопоставьте индикатор и ответ поста в акте.':board.inspected?'Нажмите красную кнопку, чтобы проверить вызов.':'Сначала осмотрите подключение кнопки.'),button(board.inspected?'Соединение осмотрено':'Осмотреть соединение','inspect','connector','inspect:connector',{disabled:!!board.inspected}));
  if(board.inspected&&board.connector)station.append(connectorView(board.connector));
  const response=node('div','workbench-call-response');response.append(node('h3','','Ответ поста'),node('p','',board.tested?(board.response||'Ответ не поступил.'):'Сначала выполните проверку вызова.'));
  const form=node('fieldset','workbench-diagnostic-form'),observation=node('section','workbench-test-observation');observation.append(node('h3','','Наблюдение при проверке'),indicator,response);form.append(node('legend','','Акт проверки'),observation);for(const report of board.reports||[])form.append(button(report.label,'select',report.id,'report:'+report.id,{pressed:selected.has(report.id),disabled:!board.inspected||!board.tested,className:'workbench-mark'}));form.append(node('p','workbench-muted','Запишите вывод по соединению, индикатору и ответу поста.'));area.append(station,form);submit('Подписать акт',!selected.size||!board.inspected||!board.tested);
 }else if(board.kind==='callReview'){
  const reports=node('div','workbench-call-review');reports.append(node('p','workbench-review-guidance','Врач рассматривает подписанные наблюдения. Неполученный ответ сам по себе не доказывает неисправность провода.'));
  for(const report of board.reports||[]){const card=node('section','workbench-review-card');card.dataset.callReviewRoom=String(report.room);card.append(node('h3','',roomLabel(report.label||String(report.room).replace(/^ward/,''))),facts([['Акт',reportLabel(report.report)],['Соединение',report.connected===null||report.connected===undefined?'не установлено':report.connected?'подключено':'отсоединено'],['Индикатор',report.indicator==='on'?'загорелся':report.indicator==='off'?'не загорелся':'не проверен'],['Ответ поста',report.response||'не зафиксирован']]));card.append(node('p','workbench-review-next',report.needsService?'Требуется обслуживание по допуску, затем повторный вызов из палаты.':'Наблюдаемый ответ поста получен.'));reports.append(card);}
  area.append(reports);footer.append(button((board.reports||[]).some(report=>report.needsService)?'Получить допуск к обслуживанию':'Подтвердить проверенные наблюдения','authorize',undefined,'authorize',{className:'workbench-button workbench-submit',disabled:!!board.authorized}));
 }else if(board.kind==='callService'){
  const equipment=board.equipment||{},disconnected=board.cause==='disconnected',post=board.cause==='noResponse';
  area.append(request('Допуск · '+String(roomLabel(board.label||String(board.room).replace(/^ward/,''))),[['Оборудование',equipment.id],['Разъём',equipment.connector],['Адрес поста',equipment.postAddress]]));
  const evidence=node('section','workbench-service-evidence');evidence.append(node('h3','',post?'Регистрация вызова на посту':disconnected?'Соединение оборудования':'Проверка идентификатора системы'),node('p','',post?'Проверьте запись об адресе вызова. Не заменяйте проверку догадкой о состоянии провода.':'Сопоставьте маркировку оборудования и разъёма с выданным допуском.'),button(board.inspected?'Сведения проверены':post?'Открыть запись поста':'Осмотреть маркировку','inspectEvidence',undefined,'inspectEvidence',{disabled:!!board.inspected}));
  if(board.inspected&&board.evidence){const observed=board.evidence;evidence.append(facts([['Оборудование',observed.equipmentId],['Разъём',observed.connector],['Адрес поста',observed.postAddress],['Регистрация',observed.observedRegistration]]));if(observed.text)evidence.append(node('p','workbench-service-observation',observed.text));}
  area.append(evidence);
  if(board.inspected){const options=node('section','workbench-service-options');options.setAttribute('aria-label',post?'Варианты записи адреса':'Варианты обслуживания');for(const option of board.options||[]){const choice=button('','select',option.id,'service:'+option.id,{pressed:selected.has(option.id),className:'workbench-service-option'});choice.append(node('strong','',option.label||'Вариант обслуживания'),facts([['Оборудование',option.equipmentId],['Разъём',option.connector],['Адрес поста',option.postAddress]]));options.append(choice);}area.append(options);}
  area.append(node('p','workbench-service-warning','Обслуживание не подтверждает успешный вызов. После записи вернитесь в палату и выполните контрольный вызов.'));submit('Зафиксировать обслуживание',!board.inspected||!selected.size);
 }else if(board.kind==='callRetest'){
  const station=node('section','workbench-call-station');station.append(node('span','workbench-call-number',roomLabel(board.label||String(board.room).replace(/^ward/,''))));const unit=node('div','workbench-bell-unit');unit.append(icon('bell'),button(board.tested?'Контроль выполнен':'Контрольный вызов','test',undefined,'test',{disabled:!!board.tested,className:'workbench-call-trigger',ariaLabel:board.tested?'Контрольный вызов выполнен':'Нажать кнопку контрольного вызова'}));station.append(unit,node('p','workbench-call-hint',board.tested?'Сверьте адрес ответившего поста и подтвердите результат контроля.':'Нажмите кнопку в самой палате. Результат обслуживания ещё нужно проверить.'));
  const observation=node('section','workbench-test-observation');observation.append(node('h3','','Контроль после обслуживания'));const indicator=node('p','workbench-indicator'+(board.indicator==='on'?' is-on':''));indicator.append(node('i','workbench-indicator-lamp'),node('span','',board.tested?(board.indicator==='on'?'Индикатор загорелся':'Индикатор не загорелся'):'Индикатор · контроль не выполнялся'));const response=node('div','workbench-call-response');response.append(node('h3','','Ответ поста'),node('p','',board.tested?(board.response||'Ответ не получен.'):'Сначала выполните контрольный вызов.'));observation.append(indicator,response);if(board.responseAddress)observation.append(facts([['Адрес ответившего поста',board.responseAddress]]));area.append(station,observation);footer.append(button('Подтвердить результат контрольного вызова','confirm',undefined,'confirm',{className:'workbench-button workbench-submit',disabled:!board.tested||!!board.confirmed}));
 }else if(board.kind==='timeline'&&board.revision===3){
  const ordered=new Set(board.order||[]),cards=board.cards||[],pool=node('section','workbench-slip-pool workbench-evidence-pool');pool.append(node('h3','','Записи на столе'));
  for(const card of cards){if(ordered.has(card.id))continue;const slip=timelineEvidence(card);slip.append(button('В журнал','place',card.id,'place:'+card.id,{className:'workbench-place-slip'}));pool.append(slip);}
  if(cards.every(card=>ordered.has(card.id)))pool.append(node('p','workbench-muted','Все листки в журнале. Проверьте их порядок и записи на обороте.'));
  const journal=node('section','workbench-timeline workbench-evidence-journal');journal.append(node('h3','','Лист обхода · '+ordered.size+'/'+cards.length));const list=node('ol','workbench-timeline-list');
  for(const[index,id]of(board.order||[]).entries()){
   const card=cards.find(card=>card.id===id);if(!card)continue;const row=node('li','workbench-timeline-entry');row.dataset.orderedSlip=id;row.append(timelineEvidence(card,true));const controls=node('div','workbench-order-controls'),name=roomLabel(card.room);
   controls.append(button('↑','move',{id,direction:'up'},'move:'+id+':up',{disabled:index===0,ariaLabel:'Поднять запись: '+name}),button('↓','move',{id,direction:'down'},'move:'+id+':down',{disabled:index===(board.order||[]).length-1,ariaLabel:'Опустить запись: '+name}),button('На стол','remove',id,'remove:'+id));row.append(controls);list.append(row);
  }
  journal.append(list);if(!ordered.size)journal.append(node('p','workbench-muted','Верните листки в подтверждённом порядке. Если время не читается, используйте запись о событиях.'));
  if(cards.some(card=>card.time===null))journal.append(node('p','workbench-uncertain-time-note','Неразборчивое время не дописывается: в итоговом листе оно останется «не установлено».'));
  area.append(pool,journal);submit('Подтвердить последовательность',!cards.length||ordered.size!==cards.length||cards.some(card=>card.reverseAvailable&&!card.reverseRead));
 }else if(board.kind==='timeline'){
  const pool=node('section','workbench-slip-pool');pool.append(node('h3','','Записи на столе'));const ordered=new Set(board.order||[]);
  for(const card of board.cards||[]){if(ordered.has(card.id))continue;const slip=button('','place',card.id,'place:'+card.id,{className:'workbench-slip'});slip.append(node('strong','',card.time||'Время не указано'),node('span','',roomLabel(card.room)),node('small','',card.note||''),node('em','','Поместить в журнал'));pool.append(slip);}
  if(![...(board.cards||[])].some(x=>!ordered.has(x.id)))pool.append(node('p','workbench-muted','Все записи помещены в журнал. Порядок можно изменить.'));
  const journal=node('section','workbench-timeline');journal.append(node('h3','','Лист обхода · '+(board.order||[]).length+'/'+(board.cards||[]).length));const list=node('ol','workbench-timeline-list');
  for(const[idIndex,id]of(board.order||[]).entries()){const card=(board.cards||[]).find(x=>x.id===id);if(!card)continue;const row=node('li','workbench-timeline-entry');row.append(node('strong','',card.time||'—'),node('span','',roomLabel(card.room)+' · '+String(card.note||'')));const controls=node('div','workbench-order-controls');controls.append(button('↑','move',{id,direction:'up'},'move:'+id+':up',{disabled:idIndex===0,ariaLabel:'Поднять запись '+String(card.time)}),button('↓','move',{id,direction:'down'},'move:'+id+':down',{disabled:idIndex===(board.order||[]).length-1,ariaLabel:'Опустить запись '+String(card.time)}),button('Убрать','remove',id,'remove:'+id));row.append(controls);list.append(row);}journal.append(list);if(!(board.order||[]).length)journal.append(node('p','workbench-muted','Добавляйте записи в порядке обхода.'));area.append(pool,journal);submit('Зафиксировать порядок',!(board.order||[]).length);
 }else if(board.kind==='baseline'){
  const plate=node('div','workbench-observation-plate');plate.append(node('small','','ТАБЛИЧКА КОРИДОРА A'),facts((board.details||[]).map(f=>[f.label,f.value])));
  const card=node('article','workbench-observation-card');card.append(node('h3','','Карточка наблюдения'),node('small','workbench-draft-label',board.recorded?'Запись сохранена':'Черновик · запись ещё не сохранена'),facts((board.details||[]).map(f=>[f.label,f.value])),node('p','','Сверьте переписанные показания с табличкой, затем сохраните карточку.'));if(board.recorded)card.append(node('p','workbench-picked','Наблюдение записано.'));area.append(plate,card);footer.append(button('Записать наблюдение в карточку','record',undefined,'record',{className:'workbench-button workbench-submit',disabled:!!board.recorded}));
 }else if(board.kind==='difference'&&board.revision===3&&board.allowNoChanges===true){
  area.append(pairedRecords([['Моя карточка',board.baseline||[]],['Наблюдение на месте',board.current||[]]],'Сверьте наблюдение с карточкой'));
  const decision=node('section','workbench-observation-decision'),none=button('','noChanges',undefined,'noChanges',{pressed:!!board.noChanges,className:'workbench-no-changes'}),tick=node('i','workbench-pair-tick',board.noChanges?'✓':'');tick.setAttribute('aria-hidden','true');none.append(tick,node('span','','Изменений нет'));
  decision.append(none,node('p','workbench-observation-decision-note',board.noChanges?'Явно записано отсутствие изменений. Отметки отдельных строк сняты.':'Если все показания совпали, укажите это отдельным ответом. Выбор «Изменений нет» снимает отметки строк; отметка строки отменяет этот ответ.'));area.append(decision);
  submit('Зафиксировать наблюдение',!marked.size&&!board.noChanges);
 }else if(board.kind==='difference'){
  area.append(pairedRecords([['Моя карточка',board.baseline||[]],['Наблюдение на месте',board.current||[]]],'Что расходится с карточкой?'));submit('Записать наблюдаемое расхождение',!marked.size);
 }else{
  area.append(node('p','','Этот рабочий лист сейчас недоступен. Вернитесь к осмотру комнаты.'));
 }
 paper.append(area);scroll.append(paper);footer.append(status);section.append(scroll,footer);host.replaceChildren(section);
 if(scrollMemo?.key===key){const top=scrollMemo.top;queueMicrotask(()=>{if(section.isConnected)scroll.scrollTop=top;});}
 section.addEventListener('keydown',event=>{
  if(event.key==='Escape'){event.preventDefault();event.stopPropagation();scrollMemo=null;close();return;}
  if(event.key!=='Tab')return;
  const controls=[...section.querySelectorAll('button:not(:disabled),summary,a[href],input:not(:disabled),select:not(:disabled),[tabindex="0"]')].filter(e=>e.getClientRects().length);
  if(!controls.length){event.preventDefault();heading.focus();return;}const first=controls[0],last=controls.at(-1);
  if(event.shiftKey&&(document.activeElement===first||document.activeElement===heading)){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
 });
 return section;
}
window.PalataQuestWorkbench=Object.freeze({render,linenIllustration});
})();
