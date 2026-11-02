import { point, lerp } from './math.mjs';
import { pinnedTorsoPoint } from './torso-space.mjs';
/** Continuous source-pixel skinning at shoulder, elbow and wrist. No new anatomy. */
export function skinVertices(mesh, arm, torso, rest) {
    const correction = mesh.shoulderArcBlend;
    const angle = Math.atan2(arm.upper[1], arm.upper[0]);
    const smooth = (v) => {
        const t = Math.max(0, Math.min(1, v));
        return t * t * (3 - 2 * t);
    };
    const activation = correction
        ? smooth(
              (-angle - correction.startAngle) /
                  (correction.fullAngle - correction.startAngle),
          )
        : 0;
    const pivot = activation ? point(torso, rest.shoulder) : null;
    return mesh.vertices.map(([x, y, shoulder, elbow, wrist]) => {
        const p = [x, y],
            u = point(arm.upper, p),
            f = point(arm.fore, p),
            h = point(arm.hand, p),
            t = pinnedTorsoPoint(torso, p);
        const result = [
            lerp(t[0], lerp(lerp(u[0], f[0], elbow), h[0], wrist), shoulder),
            lerp(t[1], lerp(lerp(u[1], f[1], elbow), h[1], wrist), shoulder),
        ];
        if (
            activation &&
            shoulder > 0 &&
            shoulder < 1 &&
            elbow < 1e-8 &&
            wrist < 1e-8
        ) {
            // A local shoulder arc, not a new arm pose. Linear matrix blending
            // pinched the raised deltoid into a corner. Interpolate rotation
            // only within this source shoulder region; joints remain fixed.
            const outer =
                1 -
                smooth(
                    (x - correction.fadeOuterX[0]) /
                        (correction.fadeOuterX[1] - correction.fadeOuterX[0]),
                );
            const local =
                activation *
                outer *
                (1 -
                    smooth(
                        (y - rest.shoulder[1] - correction.fadeStart) /
                            (correction.fadeEnd - correction.fadeStart),
                    ));
            const a = angle * shoulder,
                c = Math.cos(a),
                s = Math.sin(a);
            const dx = (x - rest.shoulder[0]) * lerp(torso[0], 1, shoulder);
            const dy = (y - rest.shoulder[1]) * lerp(torso[3], 1, shoulder);
            const arc = [
                pivot[0] + dx * c - dy * s,
                pivot[1] + dx * s + dy * c,
            ];
            result[0] = lerp(result[0], arc[0], local);
            result[1] = lerp(result[1], arc[1], local);
            if (correction.contourLift) {
                const { centre, radius, pixels } = correction.contourLift;
                const r2 =
                    ((x - centre[0]) / radius[0]) ** 2 +
                    ((y - centre[1]) / radius[1]) ** 2;
                const support = Math.max(0, 1 - r2) ** 3;
                result[1] -=
                    activation *
                    pixels *
                    support *
                    16 *
                    shoulder ** 2 *
                    (1 - shoulder) ** 2;
            }
        }
        return result;
    });
}
const plans = new WeakMap();
const alphaTables = new WeakMap();
function opaqueSampler(bitmap) {
    let table = alphaTables.get(bitmap);
    if (!table) {
        const width = bitmap.naturalWidth || bitmap.width,
            height = bitmap.naturalHeight || bitmap.height;
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const cx = canvas.getContext('2d', { willReadFrequently: true });
        cx.drawImage(bitmap, 0, 0);
        const rgba = cx.getImageData(0, 0, width, height).data,
            stride = width + 1;
        const sums = new Uint32Array((height + 1) * stride),
            visible = new Uint32Array((height + 1) * stride);
        for (let y = 0; y < height; y++) {
            let row = 0,
                live = 0;
            for (let x = 0; x < width; x++) {
                row += rgba[(y * width + x) * 4 + 3] !== 255;
                live += rgba[(y * width + x) * 4 + 3] > 0;
                visible[(y + 1) * stride + x + 1] =
                    visible[y * stride + x + 1] + live;
                sums[(y + 1) * stride + x + 1] = sums[y * stride + x + 1] + row;
            }
        }
        table = { width, height, stride, sums, visible };
        alphaTables.set(bitmap, table);
    }
    return (ps) => {
        const { width, height, stride, sums, visible } = table;
        const xs = ps.map((p) => p[0]),
            ys = ps.map((p) => p[1]);
        const raw = [
            Math.floor(Math.min(...xs)) - 3,
            Math.floor(Math.min(...ys)) - 3,
            Math.ceil(Math.max(...xs)) + 3,
            Math.ceil(Math.max(...ys)) + 3,
        ];
        const [x0, y0, x1, y1] = [
            Math.max(0, raw[0]),
            Math.max(0, raw[1]),
            Math.min(width, raw[2]),
            Math.min(height, raw[3]),
        ];
        if (x1 <= x0 || y1 <= y0) return { opaque: false, empty: true };
        const count = (t) =>
            t[y1 * stride + x1] -
            t[y0 * stride + x1] -
            t[y1 * stride + x0] +
            t[y0 * stride + x0];
        return {
            opaque:
                raw[0] >= 0 &&
                raw[1] >= 0 &&
                raw[2] <= width &&
                raw[3] <= height &&
                count(sums) === 0,
            empty: count(visible) === 0,
        };
    };
}
function plan(mesh, hand, bitmap) {
    let textures = plans.get(mesh);
    if (!textures) {
        textures = new WeakMap();
        plans.set(mesh, textures);
    }
    let cache = textures.get(bitmap);
    if (!cache) {
        cache = {};
        textures.set(bitmap, cache);
    }
    const key = hand ? 'hand' : 'full';
    if (cache[key]) return cache[key];
    const opaque = opaqueSampler(bitmap);
    const operations = [],
        triangles = hand ? mesh.handTriangles : mesh.triangles,
        [bx, by] = mesh.bounds;
    for (const tri of triangles) {
        const vs = tri.map((i) => mesh.vertices[i]);
        let bone = null;
        // A pinned torso is not affine near its upper/lower partition joins.
        // Keep these cells in the vertex path instead of the affine batch.
        if (vs.every((v) => v[2] === 0)) bone = null;
        else if (vs.every((v) => v[2] === 1 && v[4] === 1)) bone = 'hand';
        else if (vs.every((v) => v[2] === 1 && v[3] === 0 && v[4] === 0))
            bone = 'upper';
        else if (vs.every((v) => v[2] === 1 && v[3] === 1 && v[4] === 0))
            bone = 'fore';
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
        // A merged path paints translucent texels only once, unlike individual
        // triangles. Keep those cells separate: alpha compositing is ordered.
        const coverage = opaque(
            ps.map((p) => [
                center[0] + (p[0] - center[0]) * expand,
                center[1] + (p[1] - center[1]) * expand,
            ]),
        );
        if (coverage.empty) continue;
        if (bone && !coverage.opaque) bone = null;
        if (!bone) {
            const last = operations.at(-1);
            if (last && !last.bone) last.triangles.push(tri);
            else operations.push({ triangles: [tri] });
            continue;
        }
        let operation = operations.at(-1);
        if (operation?.bone !== bone) {
            operation = { bone, path: new Path2D() };
            operations.push(operation);
        }
        const path = operation.path;
        ps.forEach((p, i) => {
            const x = center[0] + (p[0] - center[0]) * expand,
                y = center[1] + (p[1] - center[1]) * expand;
            i ? path.lineTo(x, y) : path.moveTo(x, y);
        });
        path.closePath();
    }
    return (cache[key] = operations);
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
    const operations = bones
        ? plan(mesh, hand, bitmap)
        : [{ triangles: hand ? mesh.handTriangles : mesh.triangles }];
    for (const operation of operations) {
        if (operation.bone) {
            ctx.save();
            ctx.transform(...bones[operation.bone]);
            ctx.translate(bx, by);
            ctx.clip(operation.path);
            ctx.drawImage(bitmap, 0, 0);
            ctx.restore();
            continue;
        }
        const triangles = operation.triangles;
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
            // Bound antialias overlap in source UV space. Expanding a collapsed
            // destination triangle borrowed distant texels and created wedges.
            ctx.transform(
                a,
                b,
                c,
                d,
                x0 - a * u0 - c * v0,
                y0 - b * u0 - d * v0,
            );
            const edges = [
                Math.hypot(u1 - u2, v1 - v2),
                Math.hypot(u0 - u2, v0 - v2),
                Math.hypot(u0 - u1, v0 - v1),
            ];
            const perimeter = edges.reduce((a, b) => a + b),
                center = [
                    (u0 * edges[0] + u1 * edges[1] + u2 * edges[2]) / perimeter,
                    (v0 * edges[0] + v1 * edges[1] + v2 * edges[2]) / perimeter,
                ];
            const expand = 1 + 1.5 / (Math.abs(den) / perimeter);
            ctx.beginPath();
            src.forEach((p, i) => {
                const q = [
                    center[0] + (p[0] - center[0]) * expand,
                    center[1] + (p[1] - center[1]) * expand,
                ];
                i ? ctx.lineTo(...q) : ctx.moveTo(...q);
            });
            ctx.closePath();
            ctx.clip();
            ctx.drawImage(bitmap, 0, 0);
            ctx.restore();
        }
    }
}
