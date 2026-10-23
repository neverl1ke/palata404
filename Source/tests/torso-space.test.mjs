import test from 'node:test';
import assert from 'node:assert/strict';
import {pinnedTorsoPoint} from '../avatar-core/torso-space.mjs';
test('body joins stay fixed during both extremes of chest breathing',()=>{
 for(const sign of [-1,1]) for(const x of [187,306,474,639,797]) for(const y of [295,760]) {
  const matrix=[1+sign*.0025,0,0,1+sign*.0012,-sign*474*.0025,-sign*800*.0012];
  assert.deepEqual(pinnedTorsoPoint(matrix,[x,y]),[x,y]);
 }
});
test('pinned breathing has continuous neck and waist transitions without freezing the chest',()=>{
 const m=[1.0025,0,0,1.0012,-1.185,-.96];
 for(const y of [295,365,695,760]) {
  const a=pinnedTorsoPoint(m,[600,y-.0001]),b=pinnedTorsoPoint(m,[600,y+.0001]);
  assert.ok(Math.hypot(a[0]-b[0],a[1]-b[1])<.001);
 }
 assert.ok(pinnedTorsoPoint(m,[600,470])[0]>600.3);
});
