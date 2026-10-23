/** Explicit branch-only review mode. Existing inventory/loadouts own all state.
 * Enable with index.html?avatarCore=1. Unsupported garments keep the original
 * renderer visible; we never silently discard clothing to demonstrate a weapon.
 */
import { AvatarEngine } from './engine.mjs';
const instances = new Map();
const visibility = new ResizeObserver(entries => {
    for (const {target} of entries) {
        const state = instances.get(target);
        if (state?.engine && !state.canvas.hidden)
            state.engine.pause(target.getBoundingClientRect().width === 0);
    }
});
const catalog = await fetch(new URL('./equipment-weapons.json',import.meta.url)).then(r=>{if(!r.ok)throw new Error('Weapon catalog unavailable');return r.json()});
window.avatarCoreWeaponCatalog = new Map(catalog.items.map(item=>[item.id,{...item,thumbnail:'avatar-core/'+item.thumbnail}]));
const absolute = p => new URL('../' + p, import.meta.url).href;
async function descriptor(gender) {
    const face = paperDollRenderedFace(gender), hair = selectedPaperDollItem('hair');
    const image = document.createElement('img');
    applyPaperDollCrownMask(image, gender);
    const polygon = image.style.clipPath.match(/polygon\((.*)\)/);
    const crown = polygon ? polygon[1].split(',').map(s => s.trim().split(/\s+/).map((v,i) => parseFloat(v) * [941,1672][i] / 100)) : null;
    const layers = [];
    for (const [slot,item] of [['face',face],['hair',hair],['headwear',selectedPaperDollItem('headwear')]]) {
        for (const part of item ? paperDollItemLayers(item,gender) : []) {
            const path = paperDollImageCandidates(part,gender)[0];
            if (!path) continue;
            const source = slot === 'hair' ? await coloredHairSource(absolute(path),paperDollState.appearance.hairColor,part.colorReference) : absolute(path);
            layers.push({source,slot,placement:part.placementByGender?.[gender] || part.placement || {x:0,y:0,width:941,height:1672},order:part.renderOrder ?? (slot==='face'?3:slot==='headwear'?20:5)});
        }
    }
    return {layers,crown,bodyMask:face?.bodyMaskByGender?.[gender] ? absolute(face.bodyMaskByGender[gender]) : null};
}
async function update(host) {
    let state=instances.get(host);
    if (!state) {
        const canvas=document.createElement('canvas');
        canvas.className='avatar-core-wardrobe-preview';
        Object.assign(canvas.style,{position:'absolute',inset:'0',width:'100%',height:'100%',pointerEvents:'none',zIndex:'30'});
        host.append(canvas);state={canvas,token:0};instances.set(host,state);
        visibility.observe(host);
    }
    const gender=paperDollState.selectedGender, item=selectedPaperDollItem('weapon');
    const unsupported=['upperBody','outerwear','armor','loadout','gloves','pants','footwear','back','accessory'].some(slot=>{
        const value=selectedPaperDollItem(slot);return value && paperDollItemLayers(value,gender).some(p=>paperDollImageCandidates(p,gender).length);
    });
    const key=JSON.stringify([gender,item?.id,paperDollState.appearance,unsupported]);
    if (key===state.key) {
        if (state.engine && !state.canvas.hidden)
            state.engine.pause(host.getBoundingClientRect().width === 0);
        return;
    }
    const token=++state.token;
    state.key=key;
    state.canvas.hidden=true;
    state.engine?.pause();
    delete host.dataset.avatarCoreReady;
    host.querySelectorAll('.char-layer').forEach(n=>n.style.visibility='');
    if (unsupported) {
        host.dataset.avatarCoreBlocked='Одяг потребує окремих pose-specific рукавів; збережено чинний рендер.';
        state.engine?.pause();return;
    }
    delete host.dataset.avatarCoreBlocked;
    state.enginePromise ??= AvatarEngine.create(state.canvas,{gender,background:'transparent'});
    state.engine=await state.enginePromise;
    if (token!==state.token) return;
    if (state.engine.gender!==gender) await state.engine.setGender(gender);
    const appearance=await descriptor(gender);
    if (token!==state.token) return;
    await state.engine.setAppearance(appearance);
    await state.engine.equipWeaponItem(window.avatarCoreWeaponCatalog.has(item?.id) ? item.id : null);
    if (token!==state.token) return;
    host.querySelectorAll('.char-layer').forEach(n=>n.style.visibility='hidden');
    state.canvas.hidden=false;state.engine.render();
    state.engine.pause(host.getBoundingClientRect().width === 0);
    host.dataset.avatarCoreReady='true';
    host.dataset.avatarCoreArtStatus=state.engine.selectedWeaponArtStatus || 'body';
}
function refresh() {
    for (const id of ['character-paperdoll','wardrobe-paperdoll']) {
        const host=document.getElementById(id);if(host) update(host).catch(error=>{
            const s=instances.get(host);if(s) {s.key=null;s.canvas.hidden=true;s.engine?.pause();}
            delete host.dataset.avatarCoreReady;
            host.querySelectorAll('.char-layer').forEach(n=>n.style.visibility='');
            host.dataset.avatarCoreError=error.message;console.error(error);
        });
    }
}
window.addEventListener('paper-doll-render',refresh);
window.avatarCoreGamePreview={refresh,instances};refresh();
renderWardrobeUI();
