import { rad, solveArm } from './math.mjs';

/** Forward motion from the authored rest pose, never inverse-solve a fixed knife.
 * Angles are in model space, independent of CSS scale and devicePixelRatio.
 * The hand's matrix drives the weapon controller, so the grip cannot slide.
 */
export function relaxedMeleeAngles(arm, pose, breath, motion = {}) {
    const rest = solveArm(arm, arm.shoulder, pose.right,
        pose.bend.right, rad(pose.handAngles.right));
    return {
        ...rest,
        upper: rest.upper + rad((motion.upperDegrees ?? 0.035) * breath),
        fore: rest.fore + rad((motion.foreDegrees ?? 0.12) * breath),
        hand: rest.hand + rad((motion.handDegrees ?? 1.6) * breath),
    };
}
