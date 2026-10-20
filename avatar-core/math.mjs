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
    const l1 = distance(arm.shoulder, arm.elbow),
        l2 = distance(arm.elbow, arm.wrist),
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
export function armMatrices(arm, shoulder, angles) {
    const upper = around(arm.shoulder, shoulder, angles.upper),
        elbow = point(upper, arm.elbow),
        fore = around(arm.elbow, elbow, angles.fore);
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
