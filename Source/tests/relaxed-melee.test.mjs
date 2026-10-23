import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { armMatrices, distance, point } from '../avatar-core/math.mjs';
import { relaxedMeleeAngles } from '../avatar-core/relaxed-melee.mjs';

for (const gender of ['male', 'female']) {
    test(`${gender}: knife motion rotates at wrist without IK elbow compensation`, () => {
        const r=JSON.parse(fs.readFileSync(new URL(`../avatar-core/rigs/${gender}_rig.json`,import.meta.url)));
        const arm={...r.arms.right,projection:r.anatomyProjection.melee.right,
            grip:r.poseArt.melee.right.grip || r.handCorrections.melee.right.grip};
        const samples=[];
        for(let i=0;i<=240;i++) {
            const phase=i/240*Math.PI*2;
            const b=Math.sin(phase+.08*Math.sin(phase*2));
            const a=relaxedMeleeAngles(arm,r.poses.melee,b);
            const m=armMatrices(arm,arm.shoulder,a);
            samples.push({a,m,tip:point(m.hand,[arm.grip[0],arm.grip[1]+125])});
            assert.ok(Math.abs(distance(m.shoulder,m.elbow)-distance(arm.shoulder,arm.elbow)*arm.projection[0])<1e-6);
            assert.ok(Math.abs(distance(m.elbow,m.wrist)-distance(arm.elbow,arm.wrist)*arm.projection[1])<1e-6);
        }
        const span=(getter)=>Math.max(...samples.map(getter))-Math.min(...samples.map(getter));
        assert.ok(span(s=>s.m.elbow[0])<.3,'elbow must remain almost still');
        assert.ok(span(s=>s.a.hand)*180/Math.PI>3.19,'visible wrist rotation required');
        assert.ok(span(s=>s.tip[0])>5,'tip must visibly follow hand rather than remain pinned');
        for(const k of ['upper','fore','hand']) assert.ok(Math.abs(samples[0].a[k]-samples[240].a[k])<1e-12);
    });
}
