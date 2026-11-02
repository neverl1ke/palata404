/** Game adapter. Inventory and Paper Doll remain the only owners of saved state. */
import { AvatarEngine } from './engine.mjs';
const instances = new Map();
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const absolute = path => new URL('../' + path, import.meta.url).href;
const isVisible = host => {
    const wardrobeOpen = !document.getElementById('custom-modal')?.classList.contains('hidden');
    return !(host.id === 'character-paperdoll' && wardrobeOpen) && host.getBoundingClientRect().width > 0 && host.getBoundingClientRect().height > 0;
};
function playback(state) {
    if (!state.engine || state.canvas.hidden) return;
    state.engine.pause(reducedMotion.matches || !isVisible(state.host));
}
const visibility = new ResizeObserver(entries => entries.forEach(({target}) => playback(instances.get(target))));
reducedMotion.addEventListener('change', () => instances.forEach(playback));

async function descriptor(snapshot) {
    const {gender, face, hair, headwear, color, crown} = snapshot;
    const layers = [];
    for (const [slot,item] of [['face',face],['hair',hair],['headwear',headwear]]) {
        for (const part of item ? paperDollItemLayers(item,gender) : []) {
            const path = paperDollImageCandidates(part,gender).find(p => !failedPaperDollImages.has(p));
            if (!path) continue;
            let placement = part.placementByGender?.[gender] || part.placement || {x:0,y:0,width:941,height:1672};
            const fit = slot === 'hair' ? femaleHairFitFor(gender,face?.id,hair.id,placement) : null;
            const source = slot !== 'hair' ? absolute(path) : fit
                ? await fittedFemaleHairSource(path,color,part.colorReference,fit)
                : await coloredHairSource(path,color,part.colorReference);
            if (fit) placement = {x:0,y:0,width:941,height:1672};
            layers.push({source,slot,placement,order:part.renderOrder ?? (slot==='face'?1:slot==='headwear'?20:9)});
        }
    }
    layers.sort((a,b)=>a.order-b.order);
    return {layers,crown,bodyMask:face?.bodyMaskByGender?.[gender] ? absolute(face.bodyMaskByGender[gender]) : null};
}
function snapshot() {
    const gender=paperDollState.selectedGender;
    const image=document.createElement('img');
    applyPaperDollCrownMask(image,gender);
    const polygon=image.style.clipPath.match(/polygon\((.*)\)/);
    const crown=polygon ? polygon[1].split(',').map(p=>p.trim().split(/\s+/).map((v,i)=>parseFloat(v)*[941,1672][i]/100)) : null;
    const clothing=['upperBody','outerwear','armor','loadout','gloves','pants','footwear','back','accessory'].map(selectedPaperDollItem);
    const unsupported=clothing.some(item=>item && paperDollItemLayers(item,gender).some(p=>paperDollImageCandidates(p,gender).length));
    const weapon=selectedPaperDollItem('weapon');
    return {gender,face:paperDollRenderedFace(gender),hair:selectedPaperDollItem('hair'),headwear:selectedPaperDollItem('headwear'),
        color:paperDollState.appearance.hairColor,crown,unsupported,weapon:weapon?.avatarWeapon ? weapon.id : null,
        key:JSON.stringify([gender,paperDollState.activeViewMode,paperDollState.appearance,weapon?.id,clothing.map(i=>i?.id),selectedPaperDollItem('headwear')?.id])};
}
function original(state) {
    state.canvas.hidden=true;
    state.engine?.pause();
    delete state.host.dataset.avatarCoreReady;
    delete state.host.dataset.avatarPose;
    state.host.querySelectorAll('.char-layer').forEach(n=>n.style.visibility='');
}
async function update(state) {
    while(state.pending) {
        state.pending=false;
        const current=snapshot(), revision=state.revision;
        if (current.key===state.key) { playback(state);continue; }
        original(state);
        // Existing approved clothing is never dropped or warped into a different pose.
        // It keeps the original renderer until matching authored sleeves are available.
        state.host.classList.toggle('avatar-clothed-breathing',current.unsupported);
        if(current.unsupported) {
            state.key=current.key;state.host.dataset.avatarCoreBlocked='clothing';continue;
        }
        delete state.host.dataset.avatarCoreBlocked;
        state.engine ??= await AvatarEngine.create(state.canvas,{gender:current.gender,background:'transparent'});
        if (revision!==state.revision) continue;
        if(state.engine.gender!==current.gender) await state.engine.setGender(current.gender);
        const appearance=await descriptor(current);
        if (revision!==state.revision) continue;
        await state.engine.setAppearance(appearance);
        await state.engine.equipWeaponItem(current.weapon);
        if (revision!==state.revision) continue;
        state.key=current.key;
        state.host.querySelectorAll('.char-layer').forEach(n=>n.style.visibility='hidden');
        state.canvas.hidden=false;
        delete state.host.dataset.avatarCoreError;
        state.host.dataset.avatarCoreReady='true';
        state.host.dataset.avatarPose=state.engine.pose;
        playback(state);
    }
}
function run(state) {
    if (state.running) return;
    state.running = update(state).catch(error=>{
        original(state);state.key=null;state.host.dataset.avatarCoreError=error.message;console.error(error);
    }).finally(()=>{state.running=null;if(state.pending) run(state);});
}
function refresh() {
    for(const id of ['character-paperdoll','wardrobe-paperdoll']) {
        const host=document.getElementById(id);if(!host) continue;
        let state=instances.get(host);
        if(!state) {
            const canvas=document.createElement('canvas');canvas.className='avatar-core-wardrobe-preview';canvas.hidden=true;
            canvas.setAttribute('aria-hidden','true');host.append(canvas);
            state={host,canvas,revision:0};instances.set(host,state);visibility.observe(host);
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
