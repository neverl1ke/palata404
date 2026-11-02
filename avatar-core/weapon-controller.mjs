import { rad, point, solveArm, weaponMatrix } from './math.mjs';
/** Shared weapon art, rig-specific calibration. No inventory/combat side effects. */
export class WeaponAttachmentController {
    constructor(definitions) {
        this.definitions = definitions;
    }
    attach(weaponClass, rig, rightArm, rightAngles, calibratedPose = null, attachmentTarget = null) {
        if (weaponClass === 'none' || weaponClass === 'idle') return null;
        const def = this.definitions[weaponClass],
            pose = calibratedPose || rig.poses[weaponClass];
        if (!def || !pose) throw new RangeError('Unknown weapon class');
        const neutral = solveArm(
                rig.arms.right,
                rig.arms.right.shoulder,
                pose.right,
                pose.bend.right,
                rad(pose.handAngles.right),
            ),
            angle =
                rad(pose.angle + def.angle) + rightAngles.hand - neutral.hand;
        const offset = def.offset || [0, 0],
            primary = def.primary.map((v, i) => v + offset[i]),
            support = def.support?.map((v, i) => v + offset[i]);
        const calibrated = { ...def, primary };
        const matrix = weaponMatrix(
            calibrated,
            attachmentTarget || rightArm.grip,
            angle,
            def.scale,
        );
        return {
            id: def.id,
            class: weaponClass,
            matrix,
            primary: point(matrix, primary),
            support: support ? point(matrix, support) : null,
            angle,
            order: def.order,
            ...(attachmentTarget ? { attachmentTarget: [...attachmentTarget] } : {}),
        };
    }
}
