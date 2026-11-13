/** Game adapter. Inventory and Paper Doll remain the only owners of saved state. */
import { ApprovedAvatar as AvatarEngine } from './approved/avatar.mjs?v=atomic-frame-20261105';
import { PoseClothing, isPoseClothing } from './pajamas.mjs?v=5bb53efb741d';
const instances = new Map();
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const absolute = path => new URL('../' + path, import.meta.url).href;
const isVisible = host => {
    const wardrobeOpen = !document.getElementById('custom-modal')?.classList.contains('hidden');
    return !(host.id === 'character-paperdoll' && wardrobeOpen) && host.getBoundingClientRect().width > 0 && host.getBoundingClientRect().height > 0;
};
function playback(state) {
    if (!state.engine || state.canvas.hidden) return;
    state.engine.pause(!state.live || reducedMotion.matches || !isVisible(state.host));
}
const visibility = new ResizeObserver(entries => entries.forEach(({target}) => playback(instances.get(target))));
reducedMotion.addEventListener('change', () => instances.forEach(playback));

async function descriptor(snapshot) {
    const {gender, face, faceId, hair, headwear, beard, beardColor, color, crown} = snapshot;
    const layers = [];
    for (const [slot,item] of [['face',face],['hair',hair],['beard',beard],['headwear',headwear]]) {
        for (const part of item ? paperDollItemLayers(item,gender) : []) {
            const path = paperDollImageCandidates(part,gender).find(p => !failedPaperDollImages.has(p));
            if (!path) continue;
            let placement = part.placementByGender?.[gender] || part.placement || {x:0,y:0,width:941,height:1672};
            const fit = slot === 'hair' ? femaleHairFitFor(gender,faceId,hair.id,placement) : null;
            const pigment = slot === 'beard' ? beardColor : color;
            const source = !['hair','beard'].includes(slot) || part.recolor === false ? absolute(path) : fit
                ? await fittedFemaleHairSource(path,pigment,part.colorReference,fit)
                : await coloredHairSource(path,pigment,part.colorReference);
            if (fit) placement = {x:0,y:0,width:941,height:1672};
            layers.push({source,slot,placement,order:part.renderOrder ?? (slot==='face'?1:slot==='headwear'?20:slot==='beard'?8:9)});
        }
    }
    layers.sort((a,b)=>a.order-b.order);
    return {layers,crown,bodyMask:layers.some(layer=>layer.slot==='face') && face?.bodyMaskByGender?.[gender] ? absolute(face.bodyMaskByGender[gender]) : null};
}
function snapshot() {
    const pick = slot => wardrobeSession && wardrobeHiddenSlots.has(slot) ? null : selectedPaperDollItem(slot);
    const gender=paperDollState.selectedGender;
    const image=document.createElement('img');
    applyPaperDollCrownMask(image,gender);
    const polygon=image.style.clipPath.match(/polygon\((.*)\)/);
    const crown=polygon ? polygon[1].split(',').map(p=>p.trim().split(/\s+/).map((v,i)=>parseFloat(v)*[941,1672][i]/100)) : null;
    const clothing=['upperBody','outerwear','armor','loadout','gloves','pants','footwear','back','accessory'].map(pick);
    const unsupported=clothing.some(item=>item && !isPoseClothing(item) && paperDollItemLayers(item,gender).some(p=>paperDollImageCandidates(p,gender).length));
    const weapon=pick('weapon');
    return {gender,face:paperDollRenderedFace(gender) || null,faceId:paperDollState.appearance.face,hair:selectedPaperDollItem('hair'),headwear:selectedPaperDollItem('headwear'),
        beard:selectedPaperDollItem('beard'),beardColor:paperDollState.appearance.beardColor,color:paperDollState.appearance.hairColor,crown,unsupported,clothing:clothing.filter(isPoseClothing),weapon:weapon?.avatarWeapon ? (weapon.modelId || weapon.id) : null,
        key:JSON.stringify([gender,paperDollState.activeViewMode,paperDollState.appearance,weapon?.id,clothing.map(i=>i?.id),selectedPaperDollItem('headwear')?.id])};
}
function present(state) {
    const output=state.engine.canvas;
    if (state.canvas.width!==output.width) state.canvas.width=output.width;
    if (state.canvas.height!==output.height) state.canvas.height=output.height;
    state.canvas.style.width=output.style.width;
    const ctx=state.canvas.getContext('2d');ctx.clearRect(0,0,output.width,output.height);ctx.drawImage(output,0,0);
    if(state.pajamas)state.pajamas.draw(state.canvas,state.engine.time,state.pajamaMotion);
}
function clearPoseClothing(state){
    state.pajamas?.dispose();state.pajamas=null;
    if(state.pajamaMotion&&state.engine)state.engine.options.breathing=state.pajamaMotion.breathing;
    state.pajamaMotion=null;
    delete state.host.dataset.pajamaParts;delete state.host.dataset.pajamaPose;
}
function original(state) {
    clearPoseClothing(state);
    state.live=false;
    state.canvas.hidden=true;
    state.engine?.pause();
    delete state.host.dataset.avatarCoreReady;
    delete state.host.dataset.avatarPose;
    state.host.querySelectorAll('.char-layer').forEach(n=>n.style.visibility='');
    state.host.removeAttribute('data-avatar-pending');finishPaperDollFrame(state.host);
}
async function update(state) {
    while(state.pending) {
        state.pending=false;
        const current=snapshot(), revision=state.revision;
        if (current.key===state.key && !state.dirty && (!state.canvas.hidden || current.unsupported)) {
            if(!state.canvas.hidden) {
                state.host.querySelectorAll('.char-layer').forEach(n=>n.style.visibility='hidden');
                state.host.removeAttribute('data-avatar-pending');finishPaperDollFrame(state.host);
            }
            playback(state);continue;
        }
        state.live=false;state.dirty=true;state.engine?.pause();
        clearPoseClothing(state);
        // Existing approved clothing is never dropped or warped into a different pose.
        // It keeps the original renderer until matching authored sleeves are available.
        if(current.unsupported) {
            await state.host.paperDollReady;
            if (revision!==state.revision) continue;
            original(state);state.host.classList.add('avatar-clothed-breathing');state.dirty=false;state.key=current.key;state.host.dataset.avatarCoreBlocked='clothing';continue;
        }
        delete state.host.dataset.avatarCoreBlocked;
        state.engine ??= await AvatarEngine.create(state.workCanvas,{gender:current.gender,background:'transparent'});
        state.engine.onRender=()=>{if(state.live && !state.canvas.hidden)present(state)};
        if (revision!==state.revision) continue;
        if(state.engine.gender!==current.gender) await state.engine.setGender(current.gender);
        const appearance=await descriptor(current);
        if (revision!==state.revision) continue;
        await state.engine.setAppearance(appearance);
        await state.engine.equipWeaponItem(current.weapon);
        if (revision!==state.revision) continue;
        if(current.clothing.length){
            // The approved shirt sleeves are authored for these stable poses.
            // Breathe the assembled subject together instead of deforming bare
            // arms beneath an independently stationary garment.
            state.pajamaMotion={...state.engine.options};
            state.engine.options.breathing=false;state.engine.time=0;state.engine.render();
            const clothing=await PoseClothing.create(state.engine,current,absolute);
            if(revision!==state.revision){clothing.dispose();continue;}
            state.pajamas=clothing;
            state.host.dataset.pajamaParts=clothing.parts.join(' ');
            state.host.dataset.pajamaPose=clothing.pose;
        }
        state.key=current.key;state.dirty=false;state.live=true;state.host.classList.remove('avatar-clothed-breathing');present(state);
        state.host.querySelectorAll('.char-layer').forEach(n=>n.style.visibility='hidden');
        state.canvas.hidden=false;state.host.removeAttribute('data-avatar-pending');finishPaperDollFrame(state.host);
        delete state.host.dataset.avatarCoreError;
        state.host.dataset.avatarCoreReady='true';
        state.host.dataset.avatarPose=state.engine.pose;
        playback(state);
    }
}
function run(state) {
    if (state.running) return;
    state.running = update(state).catch(async error=>{
        await state.host.paperDollReady;original(state);state.key=null;state.host.dataset.avatarCoreError=error.message;console.error(error);
    }).finally(()=>{state.running=null;if(state.pending) run(state);});
}
function refresh() {
    for(const id of ['character-paperdoll','wardrobe-paperdoll']) {
        const host=document.getElementById(id);if(!host) continue;
        let state=instances.get(host);
        if(!state) {
            const canvas=document.createElement('canvas');canvas.className='avatar-core-wardrobe-preview';canvas.hidden=true;
            canvas.setAttribute('aria-hidden','true');host.append(canvas);
            const workCanvas=document.createElement('canvas');
            state={host,canvas,workCanvas,revision:0,live:false,dirty:false};instances.set(host,state);visibility.observe(host);
        }
        if(!state.canvas.hidden) host.querySelectorAll('.char-layer').forEach(n=>n.style.visibility='hidden');
        state.revision++;state.pending=true;
        run(state);
    }
}
const modal = document.getElementById('custom-modal');
if (modal) new MutationObserver(()=>instances.forEach(playback)).observe(modal,{attributes:true,attributeFilter:['class']});
window.addEventListener('paper-doll-render',refresh);
window.addEventListener('pagehide',()=>instances.forEach(state=>state.engine?.pause()));
window.addEventListener('pageshow',()=>instances.forEach(playback));
window.avatarCoreGamePreview={refresh,instances};
refresh();
