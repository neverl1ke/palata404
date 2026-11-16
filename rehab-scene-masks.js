/* Conservative object silhouettes and window panes in approved room coordinates. */
(function(){'use strict';
const panes=[[[149,3],[198,32],[198,130],[149,108]],[[217,52],[282,86],[282,171],[217,143]],[[301,96],[336,115],[336,193],[301,178]],[[150,142],[198,162],[198,265],[150,254]],[[217,169],[282,195],[282,289],[217,277]],[[301,202],[336,214],[336,306],[301,297]],[[150,283],[198,293],[198,447],[150,456]],[[217,297],[282,309],[282,438],[217,447]],[[301,314],[336,321],[336,435],[301,438]]];
function polygon(ctx,points){ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();ctx.fill();}
function create(image,mode){
 const w=image.naturalWidth,h=image.naturalHeight,c=document.createElement('canvas');c.width=w;c.height=h;const ctx=c.getContext('2d',{willReadFrequently:true}),result=ctx.createImageData(w,h);for(let i=3;i<result.data.length;i+=4)result.data[i]=255;
 for(let channel=0;channel<3;channel++){
  ctx.clearRect(0,0,w,h);ctx.save();ctx.scale(w/1672,h/941);ctx.fillStyle='#fff';
  if(channel===0){
   // Handles only: the adjacent curtain, radiator pipe and wall stay fixed.
   for(const [x,y,ww,hh]of [[31,507,14,72],[51,505,13,72],[77,455,12,60],[95,454,10,59]]){ctx.beginPath();ctx.roundRect(x,y,ww,hh,4);ctx.fill();}
  }else if(channel===1){
   polygon(ctx,mode==='trip'?[[1511,171],[1538,172],[1550,189],[1548,216],[1540,233],[1552,255],[1563,290],[1573,325],[1571,348],[1581,374],[1587,408],[1584,445],[1581,473],[1588,510],[1586,547],[1590,577],[1585,608],[1574,635],[1561,653],[1540,655],[1523,647],[1510,629],[1500,605],[1491,577],[1495,551],[1490,521],[1486,483],[1486,452],[1491,421],[1488,395],[1485,371],[1495,335],[1499,302],[1501,278],[1510,247],[1514,224],[1503,202],[1504,185]]:[[1504,246],[1527,242],[1554,242],[1579,249],[1591,271],[1595,301],[1595,586],[1584,616],[1560,635],[1528,639],[1504,632],[1490,614],[1484,586],[1484,284],[1491,260]]);
  }else for(const pane of panes)polygon(ctx,pane);
  ctx.restore();const raw=ctx.getImageData(0,0,w,h).data;
  if(channel===2){for(let i=0;i<w*h;i++)result.data[i*4+2]=raw[i*4+3];continue;}
  // Distance feathering pins the contour. Displacement stays smaller than its
  // distance to the silhouette, so photo sampling cannot pull in background.
  const d=new Float32Array(w*h);for(let i=0;i<d.length;i++)d[i]=raw[i*4+3]>128?1000:0;
  for(let y=1;y<h;y++)for(let x=1;x<w;x++){const i=y*w+x;if(d[i])d[i]=Math.min(d[i],d[i-1]+1,d[i-w]+1,d[i-w-1]+1.414);}
  for(let y=h-2;y>=0;y--)for(let x=w-2;x>=0;x--){const i=y*w+x;if(d[i])d[i]=Math.min(d[i],d[i+1]+1,d[i+w]+1,d[i+w+1]+1.414);}
  const feather=channel===0?4:8;for(let i=0;i<d.length;i++){const value=Math.max(0,Math.min(1,(d[i]-1)/feather));result.data[i*4+channel]=Math.round(value*value*(3-2*value)*255);}
 }
 ctx.putImageData(result,0,0);return c;
}
window.PalataRehabSceneMasks=Object.freeze({create});
})();
