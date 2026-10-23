import { I, point } from './math.mjs';

// Pose-space corrective art. UV coordinates stay in the authored pose; every
// attachment has an inverse bind matrix, so it follows the existing skeleton.
function inverse(m) {
    const d = m[0] * m[3] - m[1] * m[2];
    return [
        m[3] / d,
        -m[1] / d,
        -m[2] / d,
        m[0] / d,
        (m[2] * m[5] - m[3] * m[4]) / d,
        (m[1] * m[4] - m[0] * m[5]) / d,
    ];
}
function multiply(a, b) {
    return [
        a[0] * b[0] + a[2] * b[1],
        a[1] * b[0] + a[3] * b[1],
        a[0] * b[2] + a[2] * b[3],
        a[1] * b[2] + a[3] * b[3],
        a[0] * b[4] + a[2] * b[5] + a[4],
        a[1] * b[4] + a[3] * b[5] + a[5],
    ];
}
export function correctiveMatrices(bind, arm, torso = I) {
    return Object.fromEntries(
        ['upper', 'fore', 'hand', 'torso'].map((k) => [
            k,
            multiply(k === 'torso' ? torso : arm[k], inverse(bind[k])),
        ]),
    );
}
export function correctiveVertices(mesh, matrices) {
    return mesh.vertices.map(([x, y, s, e, w]) => {
        const p = [x, y],
            t = point(matrices.torso, p),
            u = point(matrices.upper, p),
            f = point(matrices.fore, p),
            h = point(matrices.hand, p);
        return [0, 1].map(
            (i) =>
                t[i] * (1 - s) +
                s * ((u[i] * (1 - e) + f[i] * e) * (1 - w) + h[i] * w),
        );
    });
}
