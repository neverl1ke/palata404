// Display adapter for approved male v9 and revised female arms / matched-size rifle.
const imageCache=new Map();
function image(source) {
    if(!imageCache.has(source)) {
        const promise=new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=()=>reject(new Error('Appearance PNG unavailable'));i.src=source});
        imageCache.set(source,promise);promise.catch(()=>imageCache.delete(source));
        while(imageCache.size>96) imageCache.delete(imageCache.keys().next().value);
    }
    return imageCache.get(source);
}
function canvas(width=941) {const c=document.createElement('canvas');c.width=width;c.height=1672;return c}
function crownPath(ctx,points) {
    ctx.beginPath();points.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();
}
export class ApprovedAvatar {
    static async create(output,{gender}) {const avatar=new ApprovedAvatar(output);await avatar.setGender(gender);return avatar}
    constructor(output) {
        this.canvas=output;this.time=0;this.paused=true;this.pose='idle';this.appearance={layers:[]};this.options={breathing:true,transitionMs:0,amplitude:1.25,cycleMs:3600};this.body=canvas();
    }
    async setGender(gender) {
        this.scene?.dispose();
        const module=await import(`./${gender}-scene.mjs?v=wrist-20261105`);
        this.scene=await module.createScene(canvas());this.gender=gender;this.width=this.scene.width;
        this.canvas.width=this.width;this.canvas.height=1672;this.canvas.style.width=`${this.width/941*100}%`;
        this.body.width=this.width;this.appearance={layers:[]};this.mask=null;this.pose='idle';this.render();
    }
    async setAppearance(descriptor) {
        const layers=await Promise.all(descriptor.layers.map(async l=>({...l,bitmap:await image(l.source)})));
        this.appearance={...descriptor,layers};this.mask=null;
        if(descriptor.bodyMask || descriptor.crown?.length) {
            const mask=canvas(this.width),ctx=mask.getContext('2d');
            ctx.fillStyle='white';ctx.fillRect(941,0,this.width-941,1672);
            ctx.save();ctx.beginPath();ctx.rect(0,0,941,1672);ctx.clip();
            if(descriptor.crown?.length){crownPath(ctx,descriptor.crown);ctx.fill()}else ctx.fillRect(0,0,941,1672);
            if(descriptor.bodyMask){const bitmap=await image(descriptor.bodyMask);ctx.globalCompositeOperation='destination-in';ctx.drawImage(bitmap,0,0,941,1672)}
            ctx.restore();this.mask=mask;
        }
        this.render();
    }
    async equipWeaponItem(id) {
        await this.scene.equipWeaponItem?.(id);
        this.pose=id==='gear-aks'?'rifle':id==='gear-knife'?'melee':'idle';
        this.render();
    }
    setOptions(options) {Object.assign(this.options,options);this.render()}
    render() {
        if(!this.scene)return;
        const native=this.scene.render(this.options.breathing?this.time:0,this.pose,this.options);
        const body=this.body.getContext('2d');body.setTransform(1,0,0,1,0,0);body.globalCompositeOperation='source-over';body.clearRect(0,0,this.width,1672);body.drawImage(native,0,0);
        if(this.mask){body.globalCompositeOperation='destination-in';body.drawImage(this.mask,0,0);body.globalCompositeOperation='source-over'}
        const ctx=this.canvas.getContext('2d');ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,this.width,1672);
        const draw=l=>{
            const p=l.placement||{x:0,y:0,width:941,height:1672},scale=Math.min(p.width/l.bitmap.width,p.height/l.bitmap.height),w=l.bitmap.width*scale,h=l.bitmap.height*scale;
            ctx.save();if(l.slot==='face'&&this.appearance.crown?.length){crownPath(ctx,this.appearance.crown);ctx.clip()}
            ctx.drawImage(l.bitmap,p.x+(p.width-w)/2,p.y+(p.height-h)/2,w,h);ctx.restore();
        };
        this.appearance.layers.filter(l=>l.order<0).forEach(draw);ctx.drawImage(this.body,0,0);this.appearance.layers.filter(l=>l.order>=0).forEach(draw);
    }
    advance(ms){this.time+=ms;this.render()}
    pause(value=true) {
        if(this.paused===value)return;
        this.paused=value;this.lastTime=null;
        if(value){cancelAnimationFrame(this.raf);this.raf=null;return}
        const tick=now=>{
            if(this.paused)return;
            if(this.lastTime!=null)this.time+=now-this.lastTime;
            this.lastTime=now;
            // Limit rendering work without changing the breathing cycle.
            if(this.lastDraw==null||now-this.lastDraw>=1000/30){this.lastDraw=now;this.render()}
            this.raf=requestAnimationFrame(tick);
        };
        this.raf=requestAnimationFrame(tick);
    }
    destroy(){this.pause();this.scene?.dispose()}
}
