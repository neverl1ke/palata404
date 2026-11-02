import { point, smoothstep } from './math.mjs';

// All textures that meet the torso must use its pinned breathing space.
// Applying the raw affine to arm-root vertices opens a moving partition seam.
export function pinnedTorsoPoint(matrix, p, top = 295, bottom = 760) {
    const moved = point(matrix, p);
    const weight = smoothstep((p[1] - top) / (365 - top)) *
        (1 - smoothstep((p[1] - (bottom - 65)) / 65));
    return p.map((v, i) => v + (moved[i] - v) * weight);
}
