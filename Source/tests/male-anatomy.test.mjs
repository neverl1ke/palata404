import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {
    I,
    point,
    distance,
    solveArm,
    armMatrices,
    rad,
} from '../avatar-core/math.mjs';
import {
    correctiveMatrices,
    correctiveVertices,
} from '../avatar-core/pose-art.mjs';
const rig = JSON.parse(
    fs.readFileSync(
        new URL('../avatar-core/rigs/male_rig.json', import.meta.url),
    ),
);
for (const [pose, sides] of Object.entries(rig.poseArt))
    for (const [side, art] of Object.entries(sides)) {
        test(`${pose}/${side}: inverse binds preserve every authored UV at rest`, () => {
            const m = correctiveMatrices(art.bind, art.bind, art.bind.torso);
            for (const k of ['upper', 'fore', 'hand', 'torso'])
                m[k].forEach((v, i) => assert.ok(Math.abs(v - I[i]) < 1e-9));
            const v = correctiveVertices(art.mesh, m);
            v.forEach((p, i) =>
                assert.ok(distance(p, art.mesh.vertices[i]) < 1e-8),
            );
        });
        test(`${pose}/${side}: artwork has modular joint anchors and bounded skin weights`, () => {
            assert.deepEqual(Object.keys(art.anchors).sort(), [
                'elbow',
                'grip',
                'shoulder',
                'wrist',
            ]);
            for (const v of art.mesh.vertices) {
                assert.ok(v.every(Number.isFinite));
                for (const w of v.slice(2)) assert.ok(w >= 0 && w <= 1);
            }
            for (const t of art.mesh.triangles)
                for (const i of t)
                    assert.ok(
                        Number.isInteger(i) &&
                            i >= 0 &&
                            i < art.mesh.vertices.length,
                    );
        });
    }
test('foreshortening changes projection, not source skeleton or transverse width', () => {
    for (const side of ['right', 'left'])
        for (const p of Object.values(rig.anatomyProjection)) {
            const source = rig.arms[side],
                arm = { ...source, projection: p[side] };
            const m = armMatrices(arm, arm.shoulder, {
                upper: 0,
                fore: 0,
                hand: 0,
            });
            for (const [i, a, b] of [
                [0, 'shoulder', 'elbow'],
                [1, 'elbow', 'wrist'],
            ]) {
                assert.ok(
                    Math.abs(
                        distance(m[a], m[b]) -
                            distance(source[a], source[b]) * arm.projection[i],
                    ) < 1e-8,
                );
                const v = source[b].map((x, i) => x - source[a][i]),
                    l = Math.hypot(...v),
                    n = [-v[1] / l, v[0] / l];
                const mat = i ? m.fore : m.upper,
                    origin = point(mat, source[a]),
                    edge = point(
                        mat,
                        source[a].map((x, i) => x + n[i] * 20),
                    );
                assert.ok(Math.abs(distance(origin, edge) - 20) < 1e-8);
            }
        }
});
test('canonical male pistol is unilateral and all legacy variants resolve to it', () => {
    assert.equal(rig.posePolicy.pistol, 'one-hand-only');
    assert.deepEqual(Object.keys(rig.poses).sort(), [
        'melee',
        'pistol',
        'rifle',
    ]);
    for (const id of ['pistol-two-hand', 'pistol-supported', 'pistol-one-hand'])
        assert.equal(rig.posePolicy.legacyAliases[id], 'pistol');
    assert.ok(
        rig.poses.pistol.right[0] < 300 && rig.poses.pistol.right[1] < 400,
    );
});
