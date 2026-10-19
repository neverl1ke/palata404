(() => {
    'use strict';
    const data=window.AVATAR_AUDIT, byId=id=>document.getElementById(id), pageSize=60;
    const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const names=new Map([...data.catalog.faces,...data.catalog.hairs,...data.catalog.colors].map(x=>[x.id,x.name]));
    names.set('base','Базове обличчя');
    let filtered=[],page=0,index=0,full=false;
    const genders=new Set(data.records.map(r=>r.gender));
    for(const option of [...byId('gender').options])if(option.value&&!genders.has(option.value))option.remove();
    for(const [id,key] of [['face','face'],['hair','hair'],['color','color']]){
        byId(id).innerHTML='<option value="">Усі</option>'+[...new Set(data.records.map(r=>r[key]||'base'))].map(v=>`<option value="${escape(v)}">${escape(names.get(v)||v)}</option>`).join('');
    }
    byId('totals').textContent=`${data.records.length} детальних знімків · ${data.full_body.length} повноростових еталонів · ${data.catalog.colors.length} кольорів. ${data.summary}`;
    function draw(){
        const start=page*pageSize,visible=filtered.slice(start,start+pageSize);
        byId('grid').innerHTML=visible.map((r,n)=>`<article><button type="button" data-open="${start+n}" aria-label="Збільшити ${escape(r.key)}"><img loading="lazy" src="${escape(r.path)}" alt="${escape(r.key)}"></button><p><span class="badge ${r.status}">${r.status}</span> ${r.gender==='male'?'Чоловік':'Жінка'}<br>${escape(names.get(r.face||'base'))}<br>${escape(names.get(r.hair))} · ${escape(names.get(r.color))}<br>${escape(r.key)}</p></article>`).join('');
        byId('matches').textContent=`Знайдено: ${filtered.length}. Технічний статус і художні зауваження показані окремо у збільшеному перегляді.`;
        byId('position').textContent=`${page+1} / ${Math.max(1,Math.ceil(filtered.length/pageSize))}`;
        byId('back').disabled=page===0;byId('next').disabled=start+pageSize>=filtered.length;
    }
    function filter(){
        page=0;filtered=data.records.filter(r=>['gender','face','hair','color','status'].every(k=>!byId(k).value||String(r[k]||'base')===byId(k).value)&&(!byId('problem').checked||r.issues.length));draw();
    }
    function image(){
        const r=filtered[index];if(!r)return;
        const body=data.full_body.find(b=>b.gender===r.gender&&b.face===r.face);
        byId('large').src=full?body.path:r.path;byId('large').style.width=`${(full?480:400)*Number(byId('zoom').value)}px`;
        const sheet='overviews/'+r.gender+'-'+(r.face||'base');
        byId('overview').href=sheet+'-all-colors.webp';byId('geometry').href=sheet+'-geometry.webp';
        byId('caption').textContent=`${r.key} · ${r.status} · технічний: ${r.technical} · reload: ${r.reload_verified?'пройдено':'ще не підтверджено'}${full?' · повноростовий еталон без зачіски':''}`;
        byId('issue-detail').textContent=r.issues.map(id=>{const issue=data.issues.find(x=>x.id===id);return issue?`${issue.id}: ${issue.description}`:id}).join(' | ')||'Зафіксованих зауважень немає. Це не замінює остаточне художнє погодження.';
    }
    byId('filters').addEventListener('change',filter);byId('filters').addEventListener('reset',()=>setTimeout(filter,0));
    byId('back').onclick=()=>{page--;draw();};byId('next').onclick=()=>{page++;draw();};
    byId('grid').onclick=e=>{const button=e.target.closest('[data-open]');if(!button)return;index=Number(button.dataset.open);full=false;image();byId('viewer').showModal();};
    byId('close').onclick=()=>byId('viewer').close();
    byId('previous-image').onclick=()=>{index=(index-1+filtered.length)%filtered.length;image();};
    byId('next-image').onclick=()=>{index=(index+1)%filtered.length;image();};
    byId('portrait').onclick=()=>{full=false;image();};byId('fullbody').onclick=()=>{full=true;image();};byId('zoom').onchange=image;
    document.addEventListener('keydown',e=>{if(!byId('viewer').open)return;if(e.key==='ArrowRight')byId('next-image').click();if(e.key==='ArrowLeft')byId('previous-image').click();});
    filter();
})();
