// Geometry is in original Paper Doll pixels. Angles are radians, never CSS units.
export const I = [1, 0, 0, 1, 0, 0];
export const rad = (d) => (d * Math.PI) / 180;
export const lerp = (a, b, t) => a + (b - a) * t;
export function angleLerp(a, b, t) {
    return a + Math.atan2(Math.sin(b - a), Math.cos(b - a)) * t;
}
export function point(m, p) {
    return [m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5]];
}
export function around(rest, target, angle) {
    const c = Math.cos(angle),
        s = Math.sin(angle);
    return [
        c,
        s,
        -s,
        c,
        target[0] - c * rest[0] + s * rest[1],
        target[1] - s * rest[0] - c * rest[1],
    ];
}
export const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
export function solveArm(arm, shoulder, target, bend, handAngle = 0) {
    const gripOffset = point(
        [
            Math.cos(handAngle),
            Math.sin(handAngle),
            -Math.sin(handAngle),
            Math.cos(handAngle),
            0,
            0,
        ],
        [arm.grip[0] - arm.wrist[0], arm.grip[1] - arm.wrist[1]],
    );
    target = [target[0] - gripOffset[0], target[1] - gripOffset[1]];
    const l1 = distance(arm.shoulder, arm.elbow) * (arm.projection?.[0] ?? 1),
        l2 = distance(arm.elbow, arm.wrist) * (arm.projection?.[1] ?? 1),
        raw = distance(shoulder, target);
    const d = Math.max(Math.abs(l1 - l2) + 1e-5, Math.min(l1 + l2 - 1e-5, raw));
    const direction = Math.atan2(
        target[1] - shoulder[1],
        target[0] - shoulder[0],
    );
    const a =
        direction +
        bend *
            Math.acos(
                Math.max(
                    -1,
                    Math.min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)),
                ),
            );
    const elbow = [
        shoulder[0] + l1 * Math.cos(a),
        shoulder[1] + l1 * Math.sin(a),
    ];
    const reach = [
        shoulder[0] + d * Math.cos(direction),
        shoulder[1] + d * Math.sin(direction),
    ];
    const fore = Math.atan2(reach[1] - elbow[1], reach[0] - elbow[0]);
    return {
        upper:
            a -
            Math.atan2(
                arm.elbow[1] - arm.shoulder[1],
                arm.elbow[0] - arm.shoulder[0],
            ),
        fore:
            fore -
            Math.atan2(
                arm.wrist[1] - arm.elbow[1],
                arm.wrist[0] - arm.elbow[0],
            ),
        hand: handAngle,
        clamped: Math.abs(raw - d) > 1e-4,
    };
}
// A 2D projection may shorten a bone on screen; transverse width and the
// source skeletal lengths remain unchanged. Identity projection is byte-compatible.
function projectedAround(rest, target, angle, axis, ratio = 1) {
    const m = around(rest, target, angle);
    if (ratio === 1) return m;
    const l = Math.hypot(...axis),
        x = axis[0] / l,
        y = axis[1] / l;
    const a = 1 + (ratio - 1) * x * x,
        b = (ratio - 1) * x * y,
        d = 1 + (ratio - 1) * y * y;
    const out = [
        m[0] * a + m[2] * b,
        m[1] * a + m[3] * b,
        m[0] * b + m[2] * d,
        m[1] * b + m[3] * d,
        0,
        0,
    ];
    out[4] = target[0] - out[0] * rest[0] - out[2] * rest[1];
    out[5] = target[1] - out[1] * rest[0] - out[3] * rest[1];
    return out;
}
export function armMatrices(arm, shoulder, angles) {
    const upper = projectedAround(
            arm.shoulder,
            shoulder,
            angles.upper,
            [arm.elbow[0] - arm.shoulder[0], arm.elbow[1] - arm.shoulder[1]],
            arm.projection?.[0],
        ),
        elbow = point(upper, arm.elbow),
        fore = projectedAround(
            arm.elbow,
            elbow,
            angles.fore,
            [arm.wrist[0] - arm.elbow[0], arm.wrist[1] - arm.elbow[1]],
            arm.projection?.[1],
        );
    const wrist = point(fore, arm.wrist),
        hand = around(arm.wrist, wrist, angles.hand ?? angles.fore);
    return {
        upper,
        fore,
        hand,
        elbow,
        wrist,
        grip: point(hand, arm.grip),
        shoulder,
    };
}
export function weaponMatrix(def, grip, angle, scale = 1) {
    const c = Math.cos(angle) * scale,
        s = Math.sin(angle) * scale;
    return [
        c,
        s,
        -s,
        c,
        grip[0] - c * def.primary[0] + s * def.primary[1],
        grip[1] - s * def.primary[0] - c * def.primary[1],
    ];
}
export function smoothstep(t) {
    t = Math.max(0, Math.min(1, t));
    return t * t * (3 - 2 * t);
}
