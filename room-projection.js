/* Map a registered rectangular render to a plane without changing its source art. */
(function(){
'use strict';
function rectangleToQuad(width,height,corners){
 const source=[[0,0],[width,0],[width,height],[0,height]],rows=[];
 source.forEach(([x,y],i)=>{const [u,v]=corners[i];rows.push([x,y,1,0,0,0,-u*x,-u*y,u]);rows.push([0,0,0,x,y,1,-v*x,-v*y,v]);});
 for(let col=0;col<8;col++){
  let best=col;for(let row=col+1;row<8;row++)if(Math.abs(rows[row][col])>Math.abs(rows[best][col]))best=row;
  [rows[col],rows[best]]=[rows[best],rows[col]];
  const pivot=rows[col][col];if(Math.abs(pivot)<1e-10)return null;
  for(let n=col;n<=8;n++)rows[col][n]/=pivot;
  for(let row=0;row<8;row++)if(row!==col){const factor=rows[row][col];for(let n=col;n<=8;n++)rows[row][n]-=factor*rows[col][n];}
 }
 const [a,b,c,d,e,f,g,h]=rows.map(row=>row[8]);
 return 'matrix3d('+[a,d,0,g,b,e,0,h,0,0,1,0,c,f,0,1].map(n=>Number(n.toFixed(9))).join(',')+')';
}
window.PalataRoomProjection=Object.freeze({rectangleToQuad});
})();
