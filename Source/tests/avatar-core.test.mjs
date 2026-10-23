import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {
    I,
    point,
    distance,
    around,
    angleLerp,
    solveArm,
    armMatrices,
    rad,
} from '../avatar-core/math.mjs';
import { WeaponAttachmentController } from '../avatar-core/weapon-controller.mjs';
import { skinVertices } from '../avatar-core/skin.mjs';
const rig = (g) =>
    JSON.parse(
        fs.readFileSync(
            new URL('../avatar-core/rigs/' + g + '_rig.json', import.meta.url),
        ),
    );
const weapons = JSON.parse(
    fs.readFileSync(new URL('../avatar-core/weapons.json', import.meta.url)),
);
const near = (a, b, eps = 1e-7) =>
    assert.ok(distance(a, b) < eps, `${a} != ${b}`);
for (const g of ['male', 'female']) {
    const r = rig(g);
    test(
        g +
            ' rest skeleton retains shoulder/elbow/wrist/grip source registration',
        () => {
            for (const side of ['right', 'left']) {
                const a = r.arms[side],
                    m = armMatrices(a, a.shoulder, {
                        upper: 0,
                        fore: 0,
                        hand: 0,
                    });
                for (const k of ['shoulder', 'elbow', 'wrist', 'grip'])
                    near(m[k], a[k]);
            }
        },
    );
    test(
        g +
            ' four poses use fixed bone lengths, independent hand rotations and exact primary attachment',
        () => {
            for (const [name, p] of Object.entries(r.poses)) {
                const a = r.arms.right,
                    angles = solveArm(
                        a,
                        a.shoulder,
                        p.right,
                        p.bend.right,
                        rad(p.handAngles.right),
                    ),
                    m = armMatrices(a, a.shoulder, angles);
                assert.equal(angles.clamped, false, name);
                near(m.grip, p.right);
                assert.ok(
                    Math.abs(
                        distance(m.shoulder, m.elbow) -
                            distance(a.shoulder, a.elbow),
                    ) < 1e-8,
                );
                assert.ok(
                    Math.abs(
                        distance(m.elbow, m.wrist) - distance(a.elbow, a.wrist),
                    ) < 1e-8,
                );
                const w = new WeaponAttachmentController(weapons).attach(
                    name,
                    r,
                    m,
                    angles,
                );
                near(w.primary, m.grip);
            }
        },
    );
    test(
        g + ' support grip stays on the rifle through a full breathing cycle',
        () => {
            for (let t = 0; t <= 4000; t += 125) {
                const b = Math.sin((t / 4000) * Math.PI * 2),
                    p = r.poses.rifle,
                    a = r.arms.right,
                    s = [a.shoulder[0] + b * 0.4, a.shoulder[1] - b],
                    ang = solveArm(
                        a,
                        s,
                        [p.right[0], p.right[1] + b * 6],
                        p.bend.right,
                        rad(p.handAngles.right) + b * 0.001,
                    ),
                    m = armMatrices(a, s, ang),
                    w = new WeaponAttachmentController(weapons).attach(
                        'rifle',
                        r,
                        m,
                        ang,
                    ),
                    left = r.arms.left,
                    la = solveArm(
                        left,
                        [left.shoulder[0] - b * 0.4, left.shoulder[1] - b],
                        w.support,
                        -1,
                        rad(p.handAngles.left),
                    ),
                    lm = armMatrices(
                        left,
                        [left.shoulder[0] - b * 0.4, left.shoulder[1] - b],
                        la,
                    );
                assert.equal(la.clamped, false);
                near(lm.grip, w.support);
                near(w.primary, m.grip);
            }
        },
    );
    test(
        g +
            ' skin weights are bounded and final hand texture shares weapon attachment',
        () => {
            for (const side of ['right', 'left']) {
                const mesh = r.skinMeshes[side];
                for (const v of mesh.vertices)
                    for (const w of v.slice(2)) assert.ok(w >= 0 && w <= 1);
                const a = r.arms[side],
                    angles = { upper: 0.35, fore: -1.1, hand: -0.7 },
                    m = armMatrices(a, a.shoulder, angles),
                    p = skinVertices(
                        { vertices: [[...a.grip, 1, 1, 1]] },
                        m,
                        I,
                        a,
                    )[0];
                near(p, m.grip);
                assert.ok(mesh.triangles.length > 100);
            }
        },
    );
}
test('female and male coordinates are independently registered, not a reused rig', () => {
    const m = rig('male'),
        f = rig('female');
    for (const side of ['left', 'right'])
        for (const k of ['shoulder', 'elbow', 'wrist', 'grip'])
            assert.notDeepEqual(m.arms[side][k], f.arms[side][k]);
    assert.notDeepEqual(m.poses, f.poses);
});
test('angle interpolation follows shortest rotation and endpoint continuity', () => {
    assert.ok(Math.abs(angleLerp(rad(179), rad(-179), 0.5) - Math.PI) < 1e-8);
    const a = 0.7,
        b = -1.2;
    assert.equal(angleLerp(a, b, 0), a);
    assert.ok(Math.abs(angleLerp(a, b, 1) - b) < 1e-8);
});
test('unreachable/degenerate targets are finite and explicitly marked', () => {
    const a = rig('male').arms.right;
    for (const p of [
        [99999, 0],
        [
            a.shoulder[0] + a.grip[0] - a.wrist[0],
            a.shoulder[1] + a.grip[1] - a.wrist[1],
        ],
    ]) {
        const x = solveArm(a, a.shoulder, p, 1);
        assert.equal(x.clamped, true);
        assert.ok(Number.isFinite(x.upper) && Number.isFinite(x.fore));
    }
});
test('weapon controller supports none and rejects unknown classes', () => {
    const c = new WeaponAttachmentController(weapons);
    assert.equal(c.attach('none'), null);
    assert.throws(() => c.attach('bad', rig('male'), {}, {}), RangeError);
});
