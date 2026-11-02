import { smoothstep } from './math.mjs';

function segmentDistance(p, a, b) {
    const dx=b[0]-a[0], dy=b[1]-a[1];
    const t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)));
    return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);
}

// Correct source-space ownership on folded arms. A y-only shoulder fade also
// pins a raised hand to the chest. Select the nearest authored bone before
// applying the root fade; rest/idle meshes and source rigs remain untouched.
export function poseOwnership(mesh, anchors) {
    const {shoulder:s,elbow:e,wrist:w,grip:g}=anchors;
    const dx=e[0]-s[0],dy=e[1]-s[1],length=Math.hypot(dx,dy);
    return {...mesh,vertices:mesh.vertices.map(([x,y,root,fore,hand])=>{
        const p=[x,y];
        const upper=segmentDistance(p,s,e);
        const distal=Math.min(segmentDistance(p,e,w),segmentDistance(p,w,g));
        const along=((x-s[0])*dx+(y-s[1])*dy)/length;
        const rootWeight=smoothstep((along-8)/80);
        const distalWeight=smoothstep((upper-distal+8)/24);
        return [x,y,rootWeight+(1-rootWeight)*distalWeight,fore,hand];
    })};
}
