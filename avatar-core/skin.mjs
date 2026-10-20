import { point, lerp } from './math.mjs';
/** Continuous source-pixel skinning at shoulder, elbow and wrist. No new anatomy. */
export function skinVertices(mesh, arm, torso, rest) {
    return mesh.vertices.map(([x, y, shoulder, elbow, wrist]) => {
        const p = [x, y],
            u = point(arm.upper, p),
            f = point(arm.fore, p),
            h = point(arm.hand, p),
            t = point(torso, p);
        return [
            lerp(t[0], lerp(lerp(u[0], f[0], elbow), h[0], wrist), shoulder),
            lerp(t[1], lerp(lerp(u[1], f[1], elbow), h[1], wrist), shoulder),
        ];
    });
}
const plans = new WeakMap();
function plan(mesh, hand) {
    let cache = plans.get(mesh);
    if (!cache) {
        cache = {};
        plans.set(mesh, cache);
    }
    const key = hand ? 'hand' : 'full';
    if (cache[key]) return cache[key];
    const groups = {},
        flexible = [],
        triangles = hand ? mesh.handTriangles : mesh.triangles,
        [bx, by] = mesh.bounds;
    for (const tri of triangles) {
        const vs = tri.map((i) => mesh.vertices[i]);
        let bone = null;
        if (vs.every((v) => v[2] === 0)) bone = 'torso';
        else if (vs.every((v) => v[2] === 1 && v[4] === 1)) bone = 'hand';
        else if (vs.every((v) => v[2] === 1 && v[3] === 0 && v[4] === 0))
            bone = 'upper';
        else if (vs.every((v) => v[2] === 1 && v[3] === 1 && v[4] === 0))
            bone = 'fore';
        if (!bone) {
            flexible.push(tri);
            continue;
        }
        groups[bone] ??= new Path2D();
        const path = groups[bone];
        const ps = vs.map((v) => [v[0] - bx, v[1] - by]),
            lengths = [
                Math.hypot(ps[1][0] - ps[2][0], ps[1][1] - ps[2][1]),
                Math.hypot(ps[0][0] - ps[2][0], ps[0][1] - ps[2][1]),
                Math.hypot(ps[0][0] - ps[1][0], ps[0][1] - ps[1][1]),
            ],
            sum = lengths.reduce((a, b) => a + b),
            center = [
                ps.reduce((a, p, i) => a + p[0] * lengths[i], 0) / sum,
                ps.reduce((a, p, i) => a + p[1] * lengths[i], 0) / sum,
            ],
            area = Math.abs(
                (ps[1][0] - ps[0][0]) * (ps[2][1] - ps[0][1]) -
                    (ps[2][0] - ps[0][0]) * (ps[1][1] - ps[0][1]),
            ),
            expand = 1 + 1.5 / (area / sum);
        ps.forEach((p, i) => {
            const x = center[0] + (p[0] - center[0]) * expand,
                y = center[1] + (p[1] - center[1]) * expand;
            i ? path.lineTo(x, y) : path.moveTo(x, y);
        });
        path.closePath();
    }
    return (cache[key] = { groups, flexible });
}
export function drawSkin(
    ctx,
    bitmap,
    mesh,
    vertices,
    hand = false,
    bones = null,
) {
    const [bx, by] = mesh.bounds;
    let triangles = hand ? mesh.handTriangles : mesh.triangles;
    if (bones) {
        const p = plan(mesh, hand);
        triangles = p.flexible;
        for (const [bone, path] of Object.entries(p.groups)) {
            ctx.save();
            ctx.transform(...bones[bone]);
            ctx.translate(bx, by);
            ctx.clip(path);
            ctx.drawImage(bitmap, 0, 0);
            ctx.restore();
        }
    }
    for (const tri of triangles) {
        const src = tri.map((i) => [
                mesh.vertices[i][0] - bx,
                mesh.vertices[i][1] - by,
            ]),
            dst = tri.map((i) => vertices[i]),
            [[u0, v0], [u1, v1], [u2, v2]] = src,
            [[x0, y0], [x1, y1], [x2, y2]] = dst;
        const den = (u1 - u0) * (v2 - v0) - (u2 - u0) * (v1 - v0);
        if (Math.abs(den) < 1e-7) continue;
        const a = ((x1 - x0) * (v2 - v0) - (x2 - x0) * (v1 - v0)) / den,
            c = ((x2 - x0) * (u1 - u0) - (x1 - x0) * (u2 - u0)) / den;
        const b = ((y1 - y0) * (v2 - v0) - (y2 - y0) * (v1 - v0)) / den,
            d = ((y2 - y0) * (u1 - u0) - (y1 - y0) * (u2 - u0)) / den;
        const area = (x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0);
        if (Math.abs(area) < 0.01 || area * den < 0) continue;
        ctx.save();
        const edges = [
                Math.hypot(x1 - x2, y1 - y2),
                Math.hypot(x0 - x2, y0 - y2),
                Math.hypot(x0 - x1, y0 - y1),
            ],
            perimeter = edges.reduce((a, b) => a + b),
            center = [
                (x0 * edges[0] + x1 * edges[1] + x2 * edges[2]) / perimeter,
                (y0 * edges[0] + y1 * edges[1] + y2 * edges[2]) / perimeter,
            ],
            radius = Math.abs(area) / perimeter,
            expand = Math.min(3, 1 + 1.5 / Math.max(0.1, radius));
        ctx.beginPath();
        dst.forEach((p, i) => {
            const q = [
                center[0] + (p[0] - center[0]) * expand,
                center[1] + (p[1] - center[1]) * expand,
            ];
            i ? ctx.lineTo(...q) : ctx.moveTo(...q);
        });
        ctx.closePath();
        ctx.clip();
        ctx.transform(a, b, c, d, x0 - a * u0 - c * v0, y0 - b * u0 - d * v0);
        ctx.drawImage(bitmap, 0, 0);
        ctx.restore();
    }
}
