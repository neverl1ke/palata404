/* Room illustrations are layered vectors. Controls are the objects themselves, not overlays on a screenshot. */
(function(){
const glyphs={
 bed:'<path d="M10 65V25h12v28h90v-8h12v35h-12V65H22v15H10Z"/><rect x="25" y="39" width="83" height="16" rx="5"/><rect x="28" y="30" width="22" height="12" rx="3"/>',
 cabinet:'<rect x="22" y="6" width="86" height="75" rx="3"/><path d="M65 6v75M30 24h27M73 24h27M30 49h27M73 49h27M32 81v7M98 81v7"/><circle cx="57" cy="40" r="2"/><circle cx="73" cy="40" r="2"/>',
 document:'<path d="M32 5h57l14 15v65H32Z"/><path d="M88 5v17h15M43 33h48M43 44h48M43 55h35M43 66h42"/>',
 door:'<path d="M28 85V5h74v80M37 83V14h56v69"/><circle cx="82" cy="48" r="3"/>',
 rail:'<path d="M14 76V30q0-9 9-9h90v10H24v45M100 31v45M10 77h21M93 77h16"/>',
 mat:'<path d="M12 65 39 29h75L90 75H12Z"/><path d="m28 58 52 1M37 45h52M48 33h49"/>',
 bell:'<rect x="42" y="12" width="48" height="66" rx="8"/><circle cx="66" cy="43" r="15"/><path d="M55 67h22M66 78v10"/>',
 tray:'<path d="M13 48h107l-8 25H23Z"/><rect x="35" y="15" width="18" height="32" rx="3"/><path d="M38 9h12v6H38ZM72 20h19v28H72ZM77 13h10v7H77Z"/>',
 linen:'<path d="M20 52h95v23H20ZM24 29h85v22H24ZM32 10h72v18H32Z"/><path d="M35 17h56M30 38h65M28 64h73"/>',
 sign:'<path d="M14 15h104v53H14Z"/><path d="M23 24h86v35H23ZM39 68v13M93 68v13"/>',
 clock:'<circle cx="66" cy="43" r="35"/><path d="M66 18v27l20 11M66 10v5M99 43h-5M66 77v-5M32 43h5"/>',
 stairs:'<path d="M12 80h20V63h22V46h22V29h23V12h23M20 18l68 0M88 18l-8-8M88 18l-8 8"/>',
 sink:'<path d="M20 35h95l-12 28H32ZM62 35V16q0-13 18-8M59 63v17h25"/>',
 chair:'<path d="M35 7h61v41H35ZM28 49h74v12H28ZM35 61v22M95 61v22"/>'
};
const sets={ward404:['bed','cabinet','door'],ward405:['bed','chair','document'],collector:['cabinet','tray','clock'],gym:['rail','rail','mat'],toilet:['sink','cabinet','door'],A:['sign','door','chair'],B:['door','sign','document'],C:['door','clock','stairs'],nurse:['tray','document','cabinet'],procedure:['tray','document','bed'],technical:['cabinet','clock','door'],linen:['linen','cabinet','tray'],ward406:['bed','linen','bell'],ward407:['bed','bell','chair'],ward408:['bed','bell','document'],doctor:['document','clock','chair'],stairs:['stairs','door','sign']};
const names={bed:'Кровать',cabinet:'Шкаф',document:'Документ',door:'Дверь',rail:'Поручень',mat:'Мат',bell:'Кнопка вызова',tray:'Лоток',linen:'Бельё',sign:'Табличка',clock:'Часы',stairs:'Лестница',sink:'Умывальник',chair:'Стул'};
const art=kind=>'<svg viewBox="0 0 132 90" aria-hidden="true">'+(glyphs[kind]||glyphs.document)+'</svg>';
const kindFor=id=>id==='exercise'?'rail':id==='collect'?'cabinet':id.includes('marker')?'sign':id==='stairsPatient'||id==='exit'||id==='descend'?'stairs':id.startsWith('boss:')?'door':id.includes('bell')?'bell':id.includes('linen')||id.includes('deliver')?'linen':id==='observation'?'clock':id==='job:tag'?'tray':'document';
window.PalataQuestScenes={art,kindFor,render(host,room,mode,onInspect){host.className='quest-room-scene mode-'+mode;host.dataset.sceneRoom=room;const architecture=document.createElement('div');architecture.className='scene-architecture';architecture.innerHTML='<div class="scene-window"></div><div class="scene-light"></div><div class="scene-skirt"></div>';host.append(architecture);for(const [i,kind] of sets[room].entries()){const object=document.createElement('button');object.type='button';object.className='scene-object prop prop-'+i;object.innerHTML=art(kind)+'<span>'+names[kind]+'</span>';object.setAttribute('aria-label','Осмотреть: '+names[kind]);object.addEventListener('click',()=>{object.classList.toggle('is-inspected');object.setAttribute('aria-pressed',String(object.classList.contains('is-inspected')));onInspect(names[kind]+': осмотрено. Активные предметы задания отмечены светлой рамкой.');});host.append(object);}},decorate(button,id){const label=button.textContent;button.classList.add('scene-object','active-object');button.innerHTML=art(kindFor(id));const caption=document.createElement('span');caption.textContent=label;button.append(caption);button.setAttribute('aria-label',label);},decorateChoice(button,choice){let kind=choice==='L'||choice==='R'?'rail':choice==='M'?'mat':choice==='sign'?'sign':choice==='frame'?'door':choice==='bench'?'chair':choice==='floor'?'mat':choice==='trace'||choice==='A'||choice==='AB'?'document':'door';const label=button.textContent;button.classList.add('scene-object','choice-object');button.innerHTML=art(kind);const cap=document.createElement('span');cap.textContent=label;button.append(cap);button.setAttribute('aria-label',label);button.dataset.objectKind=kind;}};
})();
