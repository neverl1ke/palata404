// Sleeve material uses one affine transform per arm. Silhouette data is used
// solely as a matte: it never displaces a vertex or a textile coordinate.
(function(){
'use strict';
function projection(t){const scale=1/(1-(1-1/1.24)*t),shift=.34+.26*t-(.5+(.34-.5)*scale);return{scale,shift,angle:8*Math.PI/180*(t*t*t*(t*(t*6-15)+10))};}
function create(canvas,mode){
  const W=1672,H=941,LIMIT=320,MASK_H=1024,TOP=550;
  const gl=canvas.getContext('webgl',{alpha:true,antialias:false,premultipliedAlpha:false,preserveDrawingBuffer:false});
  if(!gl)return null;
  function compile(kind,source){
    const shader=gl.createShader(kind);gl.shaderSource(shader,source);gl.compileShader(shader);
    if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(shader));return shader;
  }
  const program=gl.createProgram();
  gl.attachShader(program,compile(gl.VERTEX_SHADER,`
    attribute vec2 position;varying vec2 pixel;
    void main(){pixel=position;gl_Position=vec4(position.x/836.0-1.0,1.0-position.y/470.5,0.0,1.0);}`));
  gl.attachShader(program,compile(gl.FRAGMENT_SHADER,`
    precision highp float;
    uniform sampler2D original;uniform sampler2D matte;
    uniform vec2 projection;uniform vec2 turn;uniform float side;uniform float restVisibility;uniform float cuffPivotY;uniform float attachmentEnd;
    varying vec2 pixel;
    vec2 decode(float y){
      vec4 value=texture2D(matte,vec2(.5,(y+.5)/1024.0))*255.0;
      return vec2(value.r*256.0+value.g,value.b*256.0+value.a)/64.0;
    }
    vec2 bounds(float y){
      float row=clamp(y,520.0,940.0),low=floor(row);
      return mix(decode(low),decode(min(low+1.0,940.0)),fract(row));
    }
    float region(vec2 p,vec2 edge){
      if(p.y<520.0||p.y>940.0)return 0.0;
      float value=1.0-smoothstep(edge.y-1.0,edge.y+1.0,p.x);
      if(edge.x>1.0)value*=smoothstep(edge.x-1.0,edge.x+1.0,p.x);
      return value;
    }
    vec2 uv(vec2 p){return vec2(mix(p.x,1672.0-p.x,side)/1672.0,p.y/941.0);}
    void main(){
      float x=mix(pixel.x,1672.0-pixel.x,side);
      vec2 rest=(vec2(x,pixel.y)-vec2(836.0,470.5+projection.y*941.0))/projection.x+vec2(836.0,470.5);
      vec2 d=rest-vec2(140.0,cuffPivotY);
      // Exact inverse of uniform scale + rotation, shared by every texel.
      vec2 moved=vec2(turn.x*d.x+turn.y*d.y,-turn.y*d.x+turn.x*d.y)+vec2(140.0,cuffPivotY);
      vec2 oldEdge=bounds(rest.y),newEdge=bounds(moved.y);
      vec2 eraseEdge=vec2(max(0.0,oldEdge.x-26.0),oldEdge.y+26.0);
      float oldRegion=region(rest,eraseEdge),newRegion=region(moved,newEdge);
      float cover=max(oldRegion,newRegion);
      if(cover<.0001)discard;
      vec3 cloth=texture2D(original,uv(moved)).rgb;
      // Keep even the warm, shaded edge pixels of the original fabric. A
      // chroma key here would punch holes into dark folds near the outline.
      float newCover=newRegion;
      float clearX=max(rest.x,oldEdge.y+40.0);
      if(rest.x<(oldEdge.x+oldEdge.y)*.5&&oldEdge.x>40.0)clearX=min(rest.x,oldEdge.x-40.0);
      vec3 sourceWall=texture2D(original,uv(vec2(clearX,rest.y))).rgb;
      vec3 existing=texture2D(original,uv(rest)).rgb;
      vec3 wall=mix(existing,sourceWall,oldRegion);
      if(side<.5){
        // Retain the attached rear cloth of the left cuff where the rotating
        // forearm uncovers a narrow triangle underneath the fixed cuff.
        float attachment=oldRegion*(1.0-smoothstep(560.0,attachmentEnd,rest.y));
        wall=mix(wall,existing,attachment*(1.0-newCover));
      }
      vec3 result=mix(wall,cloth,newCover);
      float join=smoothstep(550.0,566.0,rest.y);
      gl_FragColor=vec4(result,cover*join*restVisibility);
    }`));
  gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(program));
  gl.useProgram(program);
  const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
  const position=gl.getAttribLocation(program,'position');gl.enableVertexAttribArray(position);gl.vertexAttribPointer(position,2,gl.FLOAT,false,0,0);
  gl.uniform1i(gl.getUniformLocation(program,'original'),0);gl.uniform1i(gl.getUniformLocation(program,'matte'),1);
  const uniforms=Object.fromEntries(['projection','turn','side','restVisibility','cuffPivotY','attachmentEnd'].map(n=>[n,gl.getUniformLocation(program,n)]));
  const ease=t=>t*t*t*(t*(t*6-15)+10);
  function makeTexture(image,filter=gl.LINEAR){
    const texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,texture);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,filter);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,filter);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
    if(image instanceof Uint8Array)gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,MASK_H,0,gl.RGBA,gl.UNSIGNED_BYTE,image);
    else gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image);
    return texture;
  }
  function traceMattes(image){
    const c=document.createElement('canvas');c.width=W;c.height=H;
    const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(image,0,0,W,H);
    const pixels=ctx.getImageData(0,0,W,H).data,profiles=[],textures=[];
    for(let side=0;side<2;side++){
      const raw=[];
      for(let y=520;y<H;y++){
        let outer=310,inner=0,found=false;
        for(let x=0;x<310;x++){
          const index=(y*W+(side?W-1-x:x))*4,r=pixels[index],b=pixels[index+2];
          if(b>.67*r&&r<230){outer=Math.min(outer,x);inner=x;found=true;}
        }
        if(!found)throw new Error('Missing sleeve matte row '+y);
        raw.push({outer,inner});
      }
      const data=new Uint8Array(MASK_H*4),profile=[];
      for(let y=0;y<MASK_H;y++){
        const row=Math.max(0,Math.min(raw.length-1,y-520));let sum=0,outer=0,inner=0;
        for(let d=-4;d<=4;d++){
          const point=raw[Math.max(0,Math.min(raw.length-1,row+d))],weight=5-Math.abs(d);
          sum+=weight;outer+=point.outer*weight;inner+=point.inner*weight;
        }
        const lo=Math.max(0,outer/sum-6),hi=Math.min(309,inner/sum+6);
        const a=Math.round(lo*64),b=Math.round(hi*64);
        data.set([a>>8,a&255,b>>8,b&255],y*4);
        if(y>=520&&y<H)profile.push({y,outer:lo,inner:hi});
      }
      textures.push(makeTexture(data,gl.NEAREST));profiles.push(profile);
    }
    return textures;
  }
  let imageTexture,mattes,disposed=false;
  function draw(t,enabled=true){
    gl.viewport(0,0,W,H);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT);
    if(disposed||!imageTexture||!enabled)return;
    const {scale,shift,angle}=projection(t),anchorY=(TOP-H/2)*scale+H/2+shift*H;
    const visibility=ease(Math.min(1,Math.abs(angle)/(.05*Math.PI/180)));
    if(visibility<.000001)return;
    gl.uniform2f(uniforms.projection,scale,shift);gl.uniform2f(uniforms.turn,Math.cos(angle),Math.sin(angle));
    // The layer reaches exact transparency continuously at the identity pose.
    // There is no final-frame swap from the compositor to the still drawing.
    gl.uniform1f(uniforms.restVisibility,visibility);
    gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,imageTexture);
    for(let side=0;side<2;side++){
      gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,mattes[side]);gl.uniform1f(uniforms.side,side);
      gl.uniform1f(uniforms.cuffPivotY,side?540:565);
      gl.uniform1f(uniforms.attachmentEnd,580);
      const a=side?W-LIMIT:0,b=side?W:LIMIT;
      gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([a,anchorY,b,anchorY,a,H,a,H,b,anchorY,b,H]),gl.DYNAMIC_DRAW);
      gl.drawArrays(gl.TRIANGLES,0,6);
    }
  };
  const image=new Image(),geometry=new Image();
  image.src='assets/rehabilitation/pullup-'+(mode==='trip'?'trip':'patient')+'.png';
  geometry.src='assets/rehabilitation/pullup-patient.png';
  const ready=Promise.all([image.decode(),geometry.decode()]).then(()=>{
    if(disposed)return;
    mattes=traceMattes(geometry);imageTexture=makeTexture(image);
  });
  function dispose(){
    if(disposed)return;disposed=true;
    if(imageTexture)gl.deleteTexture(imageTexture);
    if(mattes)for(const texture of mattes)gl.deleteTexture(texture);
    gl.deleteBuffer(buffer);gl.deleteProgram(program);
    gl.getExtension('WEBGL_lose_context')?.loseContext();
  }
  return{ready,draw,dispose};
}
window.PalataPullupArt=Object.freeze({create,projection});
})();
