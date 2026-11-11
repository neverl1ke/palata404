/** Authored, registered clothing poses over the unchanged approved avatar.
 * The source garments are independent 941×1672 layers. Weapon pixels and grips
 * always come from the approved renderer, never from the costume sketch.
 */
import { BreathingSurface, breathAt, approvedPose } from './approved/female-scene.mjs?v=neutral-20261105';
import { config } from './approved/config.mjs';

const WIDTH=1200, HEIGHT=1672, BODY_WIDTH=941;
const bitmapCache=new Map(), foregroundCache=new Map();
const PART_ORDER=['footwear','pants','top'];
const makeCanvas=(width=WIDTH)=>{const c=document.createElement('canvas');c.width=width;c.height=HEIGHT;return c;};
const copy=source=>{const c=makeCanvas(source.width);c.getContext('2d').drawImage(source,0,0);return c;};
function bitmap(source){
    if(!bitmapCache.has(source)){
        const task=new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>reject(new Error('Pajama artwork unavailable: '+source));image.src=source;});
        bitmapCache.set(source,task);task.catch(()=>bitmapCache.delete(source));
        while(bitmapCache.size>48)bitmapCache.delete(bitmapCache.keys().next().value);
    }
    return bitmapCache.get(source);
}
export function isPoseClothing(item){
    return Boolean(item?.poseAwareClothing===true && PART_ORDER.includes(item.poseClothingPart));
}
function sourceFor(record,gender,pose,allowIdle=true){
    if(typeof record==='string')return record;
    const selected=record?.[gender];
    if(typeof selected==='string')return selected;
    return selected?.[pose] || (allowIdle ? selected?.idle : null) || null;
}
function drawRegistered(ctx,image){ctx.drawImage(image,0,0,BODY_WIDTH,HEIGHT);}
function polygon(ctx,points){ctx.beginPath();points.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();}
async function maleWeapon(engine){
    const native=engine.scene?.engine;
    if(!native)return makeCanvas();
    let weapon=null;
    // The approved native rifle provider owns a separate, original weapon
    // surface. Capture that final draw without modifying its authored module.
    const ctx=native.compositeCtx,ordinary=ctx.drawImage;
    ctx.drawImage=function(image,...args){
        if(image instanceof HTMLCanvasElement && image!==native.compositeCanvas && image.width===1100 && image.height===HEIGHT)
            weapon=copy(image);
        return ordinary.call(this,image,...args);
    };
    try{engine.render();}finally{ctx.drawImage=ordinary;}
    return weapon || copy(native.weaponCanvas);
}
async function femaleKnife(){
    const [{resources:archived},{resources:shared},{AvatarEngine}]=await Promise.all([
        config('female'),config('male'),import('./approved/female/runtime/engine.mjs'),
    ]);
    const resources=structuredClone(archived);
    const restored=name=>new URL('./approved/female/RestoredMelee20261105/'+name,import.meta.url).href;
    const overrides={
        'assets/female/knife-edge-cleanup/melee-right-arm.png':'arm.png',
        'assets/female/knife-edge-cleanup/melee-right-complete.png':'complete.png',
        'assets/female/knife-grip-arm/melee-right-front.png':'front.png',
    };
    for(const [key,name] of Object.entries(overrides))resources.images[key]=restored(name);
    const item=resources.json['equipment-weapons.json'].items.find(item=>item.id==='gear-knife');
    resources.images[item.image]=shared.images[item.image];
    const rig=await AvatarEngine.create(makeCanvas(BODY_WIDTH),{gender:'female',resources,nativeResolution:true,transitionMs:0,background:'transparent'});
    try{rig.pause();await rig.equipWeaponItem('gear-knife');rig.time=0;rig.render();return copy(rig.weaponCanvas);}
    finally{rig.destroy();}
}
async function femaleRifle(){
    // Use the very same transparent weapon artwork and exported registration
    // as the approved baked pose. Copying its armed/unarmed RGB difference
    // would retain old skin color in antialiased edges above a new shirt.
    const {trial}=await config('male'),image=await bitmap(trial.weapon);
    const canvas=makeCanvas(),ctx=canvas.getContext('2d');
    ctx.transform(...approvedPose.rifleMatrix);ctx.drawImage(image,0,0);return canvas;
}
async function weaponForeground(engine,gender,pose){
    if(pose==='idle')return null;
    const key=gender+':'+pose;
    if(!foregroundCache.has(key)){
        const task=gender==='male'?maleWeapon(engine):pose==='rifle'?femaleRifle():femaleKnife();
        foregroundCache.set(key,task);task.catch(()=>foregroundCache.delete(key));
    }
    return foregroundCache.get(key);
}
function drawAppearance(ctx,layer,crown){
    const placement=layer.placement || {x:0,y:0,width:BODY_WIDTH,height:HEIGHT};
    const scale=Math.min(placement.width/layer.bitmap.width,placement.height/layer.bitmap.height);
    const width=layer.bitmap.width*scale,height=layer.bitmap.height*scale;
    ctx.save();
    if(layer.slot==='face'&&crown?.length){polygon(ctx,crown);ctx.clip();}
    ctx.drawImage(layer.bitmap,placement.x+(placement.width-width)/2,placement.y+(placement.height-height)/2,width,height);
    ctx.restore();
}
export class PoseClothing {
    static async create(engine,{gender,clothing},absolute){
        const pose=engine.pose;
        const parts=await Promise.all(clothing.filter(isPoseClothing).map(async item=>{
            const source=sourceFor(item.poseClothingByGender,gender,pose,item.poseClothingPart!=='top');
            if(!source)throw new Error('Pajama '+item.poseClothingPart+' has no '+gender+' '+pose+' artwork');
            const maskSource=sourceFor(item.poseClothingMaskByGender,gender,pose);
            const foregroundSource=sourceFor(item.poseClothingForegroundMaskByGender,gender,pose,false);
            return {part:item.poseClothingPart,image:await bitmap(absolute(source)),mask:maskSource?await bitmap(absolute(maskSource)):null,foregroundMask:foregroundSource?await bitmap(absolute(foregroundSource)):null};
        }));
        parts.sort((a,b)=>PART_ORDER.indexOf(a.part)-PART_ORDER.indexOf(b.part));
        const foreground=await weaponForeground(engine,gender,pose);
        return new PoseClothing(engine,gender,pose,parts,foreground);
    }
    constructor(engine,gender,pose,parts,foreground){
        this.gender=gender;this.pose=pose;this.parts=parts.map(part=>part.part);
        this.neutral=makeCanvas();this.surface=new BreathingSurface();
        this.compose(engine,parts,foreground);
    }
    compose(engine,parts,foreground){
        const ctx=this.neutral.getContext('2d'),native=engine.canvas;
        const coverage=makeCanvas(),cover=coverage.getContext('2d');
        ctx.clearRect(0,0,WIDTH,HEIGHT);ctx.drawImage(native,0,0);
        // Optional alpha removal belongs only to the equipped garment. Removing
        // that item restores the untouched approved body on the next frame.
        for(const part of parts)if(part.mask){ctx.globalCompositeOperation='destination-out';drawRegistered(ctx,part.mask);}
        ctx.globalCompositeOperation='source-over';
        for(const part of parts){drawRegistered(ctx,part.image);drawRegistered(cover,part.image);}
        const restore=makeCanvas(),r=restore.getContext('2d');
        if(foreground)r.drawImage(foreground,0,0);
        if(parts.some(part=>part.foregroundMask)){
            // An exact item-owned matte may protect the original gripping hand
            // where a sleeve/torso covers it. It contains no replacement skin.
            const mask=makeCanvas(),m=mask.getContext('2d');
            for(const part of parts)if(part.foregroundMask)drawRegistered(m,part.foregroundMask);
            const original=makeCanvas(),o=original.getContext('2d');
            o.drawImage(native,0,0);o.globalCompositeOperation='destination-in';o.drawImage(mask,0,0);
            r.drawImage(original,0,0);
        }
        // Restore only the clothing intersection; the rest of the original
        // weapon and its antialiased edge were never covered or repainted.
        r.globalCompositeOperation='destination-in';r.drawImage(coverage,0,0);r.globalCompositeOperation='source-over';
        ctx.drawImage(restore,0,0);
        const appearance=makeCanvas(),a=appearance.getContext('2d');
        for(const layer of engine.appearance.layers.filter(layer=>layer.order>=0))drawAppearance(a,layer,engine.appearance.crown);
        a.globalCompositeOperation='destination-in';a.drawImage(coverage,0,0);a.globalCompositeOperation='source-over';
        ctx.drawImage(appearance,0,0);
    }
    draw(canvas,time,options){
        const ctx=canvas.getContext('2d');
        const breath=options.breathing===false?0:breathAt(time,options);
        ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,canvas.width,canvas.height);
        ctx.drawImage(breath===0?this.neutral:this.surface.draw(this.neutral,breath),0,0);
    }
    dispose(){this.surface.dispose();}
}
