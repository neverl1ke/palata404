// Final approved painted arms, breast-side contours and male-size rifle (2026-11-03).
// The two registered PNGs are copied byte-for-byte from the user's approved preview.
// One breathing surface keeps the chest, both grips and rifle together. The previous
// IK arm motion must not be applied to this newly authored, already posed artwork.
const WIDTH = 1200, HEIGHT = 1672;
export const approvedPose = Object.freeze({
    cycleMs: 4000,
    rifleScale: 0.428,
    primaryHand: [442, 565],
    supportHand: [742.1903106342786, 649.0776064477784],
    rifleMatrix: [0.391005702400108, 0.1740647600480872,
        -0.1740647600480872, 0.391005702400108,
        323.7543862639869, 278.1131497747002],
});
const smooth = x => {x = Math.max(0, Math.min(1, x)); return x*x*(3-2*x)};
export function breathAt(time) {
    const phase = (time % approvedPose.cycleMs) / approvedPose.cycleMs * Math.PI * 2;
    const value = Math.sin(phase + 0.08 * Math.sin(2 * phase));
    return Math.abs(value) < 1e-10 ? 0 : value;
}
export function breathingPoint([x,y], breath) {
    // Head and lower legs stay registered to the cosmetic/clothing coordinate frame.
    // All visible rifle pixels and both hands lie inside the constant-motion region.
    const weight = smooth((y-275)/65) * (1-smooth((y-760)/160));
    return [x + 0.2*breath*weight, y - 1.6*breath*weight];
}
function load(name) {
    return new Promise((resolve,reject) => {
        const image = new Image();
        image.onload = () => resolve(image);
        image.onerror = () => reject(new Error(`Approved female pose unavailable: ${name}`));
        image.src = new URL(`./female/Approved20261103/${name}`, import.meta.url).href;
    });
}
class BreathingSurface {
    constructor() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = WIDTH; this.canvas.height = HEIGHT;
        const gl = this.gl = this.canvas.getContext('webgl', {
            alpha:true, premultipliedAlpha:true, antialias:false, preserveDrawingBuffer:true,
        });
        if (!gl) throw new Error('WebGL is required for the approved breathing surface');
        const shader = (kind, source) => {
            const s=gl.createShader(kind); gl.shaderSource(s,source); gl.compileShader(s);
            if (!gl.getShaderParameter(s,gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
            return s;
        };
        const program=gl.createProgram();
        gl.attachShader(program,shader(gl.VERTEX_SHADER,`
            attribute vec2 position; attribute vec2 uv; varying vec2 textureUV;
            void main(){textureUV=uv;gl_Position=vec4(position.x/1200.0*2.0-1.0,
                1.0-position.y/1672.0*2.0,0,1);}`));
        gl.attachShader(program,shader(gl.FRAGMENT_SHADER,`
            precision highp float; uniform sampler2D image; varying vec2 textureUV;
            void main(){gl_FragColor=texture2D(image,textureUV);}`));
        gl.linkProgram(program);
        if (!gl.getProgramParameter(program,gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
        gl.useProgram(program); gl.viewport(0,0,WIDTH,HEIGHT); gl.disable(gl.BLEND);
        this.position=gl.getAttribLocation(program,'position');this.uv=gl.getAttribLocation(program,'uv');
        this.buffer=gl.createBuffer();this.textures=new WeakMap();
        this.rows=[0,275];
        for(let y=283;y<920;y+=8)this.rows.push(y);
        this.rows.push(340,760,920,HEIGHT);this.rows=[...new Set(this.rows)].sort((a,b)=>a-b);
    }
    texture(image) {
        if(this.textures.has(image))return this.textures.get(image);
        const gl=this.gl,t=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,t);
        gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL,true);
        gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
        gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);
        this.textures.set(image,t);return t;
    }
    draw(image,breath) {
        const vertices=[];
        const vertex=(x,y)=>{const p=breathingPoint([x,y],breath);vertices.push(...p,x/WIDTH,y/HEIGHT)};
        for(let i=0;i<this.rows.length-1;i++) {
            const y=this.rows[i],next=this.rows[i+1];
            vertex(0,y);vertex(WIDTH,y);vertex(WIDTH,next);
            vertex(0,y);vertex(WIDTH,next);vertex(0,next);
        }
        const gl=this.gl;gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);
        gl.bindTexture(gl.TEXTURE_2D,this.texture(image));gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);
        gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(vertices),gl.DYNAMIC_DRAW);
        gl.enableVertexAttribArray(this.position);gl.vertexAttribPointer(this.position,2,gl.FLOAT,false,16,0);
        gl.enableVertexAttribArray(this.uv);gl.vertexAttribPointer(this.uv,2,gl.FLOAT,false,16,8);
        gl.drawArrays(gl.TRIANGLES,0,vertices.length/4);return this.canvas;
    }
    dispose(){this.gl.getExtension('WEBGL_lose_context')?.loseContext()}
}
export async function createScene() {
    const [bare,armed]=await Promise.all([load('arms-no-weapon.png'),load('arms-rifle.png')]);
    for(const image of [bare,armed])if(image.width!==WIDTH||image.height!==HEIGHT)
        throw new Error('Approved female pose registration must be 1200 × 1672');
    const canvas=document.createElement('canvas');canvas.width=WIDTH;canvas.height=HEIGHT;
    const ctx=canvas.getContext('2d'),surface=new BreathingSurface();
    return {canvas,width:WIDTH,approvedPose,
        render(time,weapon=true) {
            const image=weapon?armed:bare,breath=breathAt(time);
            ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,WIDTH,HEIGHT);
            // Rest frames go straight from the approved PNG, avoiding a resampling pass.
            ctx.drawImage(breath===0?image:surface.draw(image,breath),0,0);return canvas;
        },
        dispose(){surface.dispose()},
    };
}
