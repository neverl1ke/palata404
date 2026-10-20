import { skinVertices, drawSkin } from './skin.mjs';
import { WeaponAttachmentController } from './weapon-controller.mjs';
import {
    I,
    rad,
    angleLerp,
    point,
    distance,
    solveArm,
    armMatrices,
    smoothstep,
} from './math.mjs';
const imageCache = new Map();
export function loadImage(url) {
    if (imageCache.has(url)) {
        const cached = imageCache.get(url);
        imageCache.delete(url);
        imageCache.set(url, cached);
        return cached;
    }
    if (!imageCache.has(url)) {
        const p = new Promise((resolve, reject) => {
            const i = new Image();
            i.onload = () => resolve(i);
            i.onerror = () => reject(new Error('PNG unavailable: ' + url));
            i.src = url;
        });
        imageCache.set(url, p);
        p.catch(() => {
            if (imageCache.get(url) === p) imageCache.delete(url);
        });
        while (imageCache.size > 96)
            imageCache.delete(imageCache.keys().next().value);
    }
    return imageCache.get(url);
}
const surface = (w, h) => {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    return c;
};
const validNumber = (v, name, min, max) => {
    if (!Number.isFinite(v) || v < min || v > max) throw new RangeError(name);
    return v;
};
export class AvatarEngine {
    static async create(canvas, options = {}) {
        const e = new AvatarEngine(canvas, options);
        await e.setGender(options.gender || 'male');
        return e;
    }
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.baseURL = options.resources
            ? new URL('https://avatar-core.invalid/')
            : new URL('./', import.meta.url);
        this.resources = options.resources || null;
        this.equipment = new Map();
        this.jsonCache = new Map();
        this.visible = new Map();
        this.pose = 'idle';
        this.time = 0;
        this.transition = null;
        this.appearance = { layers: [] };
        this.paused = true;
        this.destroyed = false;
        this.generation = 0;
        this.appearanceGeneration = 0;
        this.fps = 0;
        this.options = {
            breathing: true,
            cycleMs: 4000,
            amplitude: 1,
            weaponSwayPx: 2,
            transitionMs: 320,
            debugPivots: false,
            debugBounds: false,
            debugGrips: false,
            testSleeves: false,
            skinBatching: true,
            pistolSupport: false,
            view: 'rig',
            background: '#d3cfc6',
            ...Object.fromEntries(
                Object.entries(options).filter(
                    ([k]) => !['resources', 'gender'].includes(k),
                ),
            ),
        };
        this.onVisibility = () => {
            this.lastTimestamp = null;
            if (document.hidden) this.stopRAF();
            else if (!this.paused) this.startRAF();
        };
        document.addEventListener('visibilitychange', this.onVisibility);
        this.observer = new ResizeObserver(() => this.render());
        this.observer.observe(canvas);
    }
    async json(path) {
        if (this.resources?.json?.[path])
            return structuredClone(this.resources.json[path]);
        if (!this.jsonCache.has(path))
            this.jsonCache.set(
                path,
                fetch(new URL(path, this.baseURL))
                    .then((r) => {
                        if (!r.ok)
                            throw new Error(
                                'Configuration unavailable: ' + path,
                            );
                        return r.json();
                    })
                    .catch((e) => {
                        this.jsonCache.delete(path);
                        throw e;
                    }),
            );
        return this.jsonCache.get(path);
    }
    image(path) {
        return loadImage(
            this.resources?.images?.[path] || new URL(path, this.baseURL).href,
        );
    }
    async setGender(gender) {
        if (!['male', 'female'].includes(gender))
            throw new RangeError('Unknown gender');
        if (this.destroyed) throw new Error('Engine destroyed');
        const token = ++this.generation;
        const [rig, weapons] = await Promise.all([
            this.json('rigs/' + gender + '_rig.json'),
            this.json('weapons.json'),
        ]);
        const assets = {};
        await Promise.all(
            Object.entries(rig.segments).map(
                async ([k, v]) => (assets[k] = await this.image(v.image)),
            ),
        );
        for (const side of ['right', 'left']) {
            assets[side + 'ArmSkin'] = await this.image(
                rig.skinMeshes[side].image,
            );
            assets[side + 'HandSkin'] = await this.image(
                rig.skinMeshes[side].handImage,
            );
        }
        const original = await this.image(rig.source);
        await Promise.all(
            Object.entries(weapons).map(
                async ([k, v]) =>
                    (assets['weapon-' + k] = await this.image(v.image)),
            ),
        );
        if (token !== this.generation || this.destroyed) return false;
        const bindings = [...this.equipment.values()].filter(
            (e) => e.bitmap && (!e.genders || e.genders.includes(gender)),
        );
        this.equipment.clear();
        this.visible.clear();
        this.rig = rig;
        this.gender = gender;
        this.assets = assets;
        this.weapons = weapons;
        this.weaponController = new WeaponAttachmentController(weapons);
        this.original = original;
        this.transition = null;
        this.currentAngles = {
            right: { upper: 0, fore: 0, hand: 0 },
            left: { upper: 0, fore: 0, hand: 0 },
        };
        this.appearance = { layers: [] };
        this.appearanceGeneration++;
        this.buildMasked();
        await Promise.all(
            bindings.map((e) =>
                this.bindEquipment({
                    ...e,
                    source: e.sourceByGender?.[gender] || e.source,
                }),
            ),
        );
        if (token !== this.generation || this.destroyed) return false;
        this.render();
        return true;
    }
    setOptions(options) {
        const limits = {
            cycleMs: [500, 20000],
            amplitude: [0, 3],
            weaponSwayPx: [0, 5],
            transitionMs: [0, 2000],
        };
        for (const [k, v] of Object.entries(options)) {
            if (k in limits) validNumber(v, k, ...limits[k]);
            if (!(k in this.options))
                throw new RangeError('Unknown option ' + k);
        }
        if (
            options.view &&
            !['rig', 'original', 'compare'].includes(options.view)
        )
            throw new RangeError('Unknown view');
        for (const k of [
            'breathing',
            'debugPivots',
            'debugBounds',
            'debugGrips',
            'testSleeves',
            'pistolSupport',
            'skinBatching',
        ])
            if (k in options && typeof options[k] !== 'boolean')
                throw new TypeError(k);
        Object.assign(this.options, options);
        this.render();
    }
    setPose(pose) {
        if (!['idle', 'melee', 'pistol', 'rifle'].includes(pose))
            throw new RangeError('Unknown pose');
        if (!this.rig) return;
        this.compute();
        this.transition = {
            start: this.time,
            duration: this.options.transitionMs,
            from: structuredClone(this.currentAngles),
        };
        this.pose = pose;
        this.render();
    }
    setWeapon(weaponClass) {
        this.setPose(weaponClass === 'none' ? 'idle' : weaponClass);
    }
    async setAppearance(descriptor) {
        const token = ++this.appearanceGeneration,
            gender = this.gender;
        const layers = await Promise.all(
            (descriptor.layers || []).map(async (l) => ({
                ...l,
                bitmap: await loadImage(l.source),
            })),
        );
        const mask = descriptor.bodyMask
            ? await loadImage(descriptor.bodyMask)
            : null;
        if (
            token !== this.appearanceGeneration ||
            gender !== this.gender ||
            this.destroyed
        )
            return false;
        this.appearance = { ...descriptor, layers, mask };
        this.buildMasked();
        this.render();
        return true;
    }
    buildMasked() {
        this.bitmaps = {};
        for (const [k, seg] of Object.entries(this.rig.segments)) {
            const im = this.assets[k];
            if (!this.appearance.mask) {
                this.bitmaps[k] = im;
                continue;
            }
            const [x, y, x1, y1] = seg.bounds,
                c = surface(x1 - x, y1 - y),
                cx = c.getContext('2d');
            cx.drawImage(im, 0, 0);
            cx.globalCompositeOperation = 'destination-in';
            cx.drawImage(this.appearance.mask, -x, -y, 941, 1672);
            this.bitmaps[k] = c;
        }
        this.skins = {};
        for (const side of ['right', 'left']) {
            const mesh = this.rig.skinMeshes[side],
                [x, y, x1, y1] = mesh.bounds,
                c = surface(x1 - x, y1 - y),
                cx = c.getContext('2d');
            for (const part of ['Upper', 'Fore', 'Hand']) {
                const k = side + part;
                if (this.visible.get(k) === false) continue;
                const seg = this.rig.segments[k];
                cx.drawImage(
                    this.bitmaps[k],
                    seg.bounds[0] - x,
                    seg.bounds[1] - y,
                );
            }
            for (const e of this.skinBindings(side)) {
                const p = e.placementByGender?.[this.gender] || e.placement;
                cx.drawImage(e.bitmap, p.x - x, p.y - y, p.width, p.height);
            }
            this.skins[side] =
                !this.appearance.mask &&
                this.skinBindings(side).length === 0 &&
                ['Upper', 'Fore', 'Hand'].every(
                    (part) => this.visible.get(side + part) !== false,
                )
                    ? this.assets[side + 'ArmSkin']
                    : c;
            this.handSkins ??= {};
            const hc = surface(x1 - x, y1 - y),
                hx = hc.getContext('2d');
            hx.drawImage(this.assets[side + 'HandSkin'], 0, 0);
            for (const e of this.skinBindings(side).filter((e) =>
                e.segment.endsWith('Hand'),
            )) {
                const p = e.placementByGender?.[this.gender] || e.placement;
                hx.drawImage(e.bitmap, p.x - x, p.y - y, p.width, p.height);
            }
            this.handSkins[side] = hc;
        }
        this.restLayer = surface(941, 1672);
        const rx = this.restLayer.getContext('2d');
        for (const k of [
            'torso',
            'lower',
            'head',
            'rightUpper',
            'rightFore',
            'rightHand',
            'leftUpper',
            'leftFore',
            'leftHand',
        ]) {
            if (this.visible.get(k) === false) continue;
            rx.save();
            if (k === 'head') this.clipCrown(rx);
            const seg = this.rig.segments[k];
            rx.drawImage(this.bitmaps[k], seg.bounds[0], seg.bounds[1]);
            rx.restore();
        }
        for (const side of ['right', 'left'])
            for (const e of this.skinBindings(side)) {
                const p = e.placementByGender?.[this.gender] || e.placement;
                rx.drawImage(e.bitmap, p.x, p.y, p.width, p.height);
            }
        // Fixed feet and pelvis are cached once; head is also static and masked exactly.
        this.staticLayer = surface(941, 1672);
        const cx = this.staticLayer.getContext('2d');
        for (const k of ['lower', 'head']) {
            if (this.visible.get(k) === false) continue;
            cx.save();
            if (k === 'head') this.clipCrown(cx);
            const s = this.rig.segments[k];
            cx.drawImage(this.bitmaps[k], s.bounds[0], s.bounds[1]);
            cx.restore();
        }
    }
    async bindEquipment(binding) {
        if (
            !binding ||
            typeof binding.id !== 'string' ||
            !binding.id.trim() ||
            typeof (binding.sourceByGender?.[this.gender] || binding.source) !==
                'string' ||
            ![
                'torso',
                'head',
                'lower',
                'rightUpper',
                'rightFore',
                'rightHand',
                'leftUpper',
                'leftFore',
                'leftHand',
            ].includes(binding.segment)
        )
            throw new TypeError('Invalid equipment binding');
        const placement =
            binding.placementByGender?.[this.gender] || binding.placement;
        if (
            !placement ||
            !['x', 'y', 'width', 'height'].every((k) =>
                Number.isFinite(placement[k]),
            ) ||
            placement.width <= 0 ||
            placement.height <= 0
        )
            throw new TypeError('Invalid equipment placement');
        const generation = this.generation,
            gender = this.gender;
        const token = Symbol(binding.id);
        this.equipment.set(binding.id, { pending: token });
        let bitmap;
        try {
            bitmap = await loadImage(
                binding.sourceByGender?.[gender] || binding.source,
            );
        } catch (e) {
            if (this.equipment.get(binding.id)?.pending === token)
                this.equipment.delete(binding.id);
            throw e;
        }
        if (
            this.equipment.get(binding.id)?.pending !== token ||
            this.destroyed ||
            generation !== this.generation
        )
            return false;
        this.equipment.set(binding.id, {
            ...binding,
            bitmap,
            preparedGender: gender,
        });
        this.buildMasked();
        this.render();
        return true;
    }
    unbindEquipment(id) {
        if (this.equipment.delete(id)) {
            this.buildMasked();
            this.render();
        }
    }
    setLayerVisible(id, visible) {
        if (
            id !== 'weapon' &&
            !(id in this.rig.segments) &&
            !this.equipment.has(id)
        )
            throw new RangeError('Unknown segment');
        this.visible.set(id, !!visible);
        if (id !== 'weapon') this.buildMasked();
        this.render();
    }
    clipCrown(cx) {
        const points = this.appearance.crown;
        if (!points?.length) return;
        cx.beginPath();
        points.forEach(([x, y], i) => (i ? cx.lineTo(x, y) : cx.moveTo(x, y)));
        cx.closePath();
        cx.clip();
    }
    compute() {
        if (!this.rig) return null;
        const rig = this.rig,
            b = this.options.breathing
                ? Math.sin((this.time / this.options.cycleMs) * Math.PI * 2) *
                  this.options.amplitude
                : 0;
        const sx = 1 + rig.breathing.chestX * b,
            sy = 1 + rig.breathing.chestY * b,
            [px, py] = rig.landmarks.pelvis,
            torso = [sx, 0, 0, sy, px * (1 - sx), py * (1 - sy)];
        const shoulders = Object.fromEntries(
            ['right', 'left'].map((s) => [
                s,
                point(torso, rig.arms[s].shoulder),
            ]),
        );
        const scale = (this.canvas.getBoundingClientRect().width || 400) / 941;
        let angles = {},
            matrices = {},
            transition = this.transition,
            t = transition
                ? smoothstep(
                      transition.duration
                          ? (this.time - transition.start) / transition.duration
                          : 1,
                  )
                : 1;
        let pose = rig.poses[this.pose];
        if (this.pose === 'pistol' && this.options.pistolSupport)
            pose = {
                ...pose,
                right: [rig.landmarks.chest[0], rig.landmarks.chest[1] - 25],
                left: [
                    rig.landmarks.chest[0] + 18,
                    rig.landmarks.chest[1] - 14,
                ],
                angle: -5,
                handAngles: { right: -55, left: 45 },
                bend: { right: 1, left: -1 },
            };
        const bob =
            this.pose === 'idle' ? 0 : (b * this.options.weaponSwayPx) / scale;
        if (this.pose === 'idle')
            for (const side of ['right', 'left']) {
                const sign = side === 'right' ? 1 : -1;
                angles[side] = {
                    upper: rad(rig.breathing.idleArmDegrees * b * sign),
                    fore: rad(rig.breathing.idleArmDegrees * b * sign * 1.5),
                    hand: rad(rig.breathing.idleArmDegrees * b * sign * 1.5),
                };
            }
        else
            angles.right = solveArm(
                rig.arms.right,
                shoulders.right,
                [pose.right[0] + b * 0.7, pose.right[1] + bob],
                pose.bend.right,
                rad(pose.handAngles.right) + rad(b * 0.12),
            );
        const blend = (side, target) =>
            transition
                ? {
                      upper: angleLerp(
                          transition.from[side].upper,
                          target.upper,
                          t,
                      ),
                      fore: angleLerp(
                          transition.from[side].fore,
                          target.fore,
                          t,
                      ),
                      hand: angleLerp(
                          transition.from[side].hand || 0,
                          target.hand || 0,
                          t,
                      ),
                  }
                : target;
        angles.right = blend('right', angles.right);
        matrices.right = armMatrices(
            rig.arms.right,
            shoulders.right,
            angles.right,
        );
        let weapon = null;
        if (pose) {
            weapon = this.weaponController.attach(
                this.pose,
                rig,
                matrices.right,
                angles.right,
                pose,
            );
            const target =
                this.pose === 'rifle' ||
                (this.pose === 'pistol' && this.options.pistolSupport)
                    ? weapon.support
                    : [pose.left[0], pose.left[1] + b * 1.2];
            angles.left =
                this.pose === 'melee' ||
                (this.pose === 'pistol' && !this.options.pistolSupport)
                    ? { upper: 0, fore: 0, hand: 0 }
                    : solveArm(
                          rig.arms.left,
                          shoulders.left,
                          target,
                          pose.bend.left,
                          rad(pose.handAngles.left) + rad(b * 0.12),
                      );
        }
        angles.left = blend('left', angles.left);
        matrices.left = armMatrices(rig.arms.left, shoulders.left, angles.left);
        this.currentAngles = angles;
        if (transition && t >= 1) this.transition = null;
        const transforms = { torso, head: I, lower: I };
        for (const side of ['right', 'left'])
            for (const [part, name] of [
                ['Upper', 'upper'],
                ['Fore', 'fore'],
                ['Hand', 'hand'],
            ])
                transforms[side + part] = matrices[side][name];
        return (this.frame = {
            time: this.time,
            breath: b,
            angles,
            arms: matrices,
            transforms,
            weapon,
            transitionProgress: t,
            feetFixed: true,
            primaryError: weapon
                ? distance(weapon.primary, matrices.right.grip)
                : 0,
            supportError:
                weapon?.support &&
                (this.pose === 'rifle' ||
                    (this.pose === 'pistol' && this.options.pistolSupport))
                    ? distance(weapon.support, matrices.left.grip)
                    : 0,
        });
    }
    render() {
        if (!this.rig || this.destroyed) return;
        const f = this.compute(),
            canvas = this.canvas,
            cx = this.ctx,
            rect = canvas.getBoundingClientRect(),
            dpr = window.devicePixelRatio || 1,
            w = Math.max(1, Math.round(rect.width * dpr)),
            h = Math.max(1, Math.round(rect.height * dpr));
        if (canvas.width !== w || canvas.height !== h) {
            canvas.width = w;
            canvas.height = h;
        }
        cx.setTransform(w / 941, 0, 0, h / 1672, 0, 0);
        cx.clearRect(0, 0, 941, 1672);
        if (this.options.background !== 'transparent') {
            cx.fillStyle = this.options.background;
            cx.fillRect(0, 0, 941, 1672);
        }
        if (this.options.view === 'original') {
            cx.drawImage(this.original, 0, 0);
            return;
        }
        const drawBitmap = (im, bounds, m = I, alpha = 1) => {
            cx.save();
            cx.globalAlpha = alpha;
            cx.transform(...m);
            cx.drawImage(im, bounds[0], bounds[1]);
            cx.restore();
        };
        const drawPart = (key, m = I) => {
            if (this.visible.get(key) === false) return;
            drawBitmap(this.bitmaps[key], this.rig.segments[key].bounds, m);
            this.drawEquipment(key, m);
        };
        for (const l of this.appearance.layers.filter((l) => l.order < 0))
            this.drawAppearance(l);
        const neutral =
            this.pose === 'idle' &&
            Math.abs(f.breath) < 1e-8 &&
            !this.transition;
        if (neutral) {
            cx.drawImage(this.restLayer, 0, 0);
            for (const k of ['torso', 'lower', 'head'])
                this.drawEquipment(k, I);
        } else {
            drawPart('torso', f.transforms.torso);
            cx.drawImage(this.staticLayer, 0, 0);
            this.drawEquipment('lower', I);
            this.drawEquipment('head', I);
        }
        const meshVertices = {};
        for (const side of ['right', 'left']) {
            const mesh = this.rig.skinMeshes[side];
            meshVertices[side] = skinVertices(
                mesh,
                f.arms[side],
                f.transforms.torso,
                this.rig.arms[side],
            );
            if (!neutral)
                drawSkin(
                    cx,
                    this.skins[side],
                    mesh,
                    meshVertices[side],
                    false,
                    this.options.skinBatching
                        ? { ...f.arms[side], torso: f.transforms.torso }
                        : null,
                );
            for (const part of ['Upper', 'Fore'])
                this.drawEquipment(
                    side + part,
                    f.arms[side][part.toLowerCase()],
                );
        }
        for (const l of this.appearance.layers.filter((l) => l.order >= 0))
            this.drawAppearance(l);
        if (f.weapon && this.visible.get('weapon') !== false) {
            const def = this.weapons[this.pose];
            drawBitmap(
                this.assets['weapon-' + this.pose],
                [0, 0],
                f.weapon.matrix,
                this.transition ? f.transitionProgress : 1,
            );
        }
        for (const side of ['right', 'left']) {
            if (!neutral && this.visible.get(side + 'Hand') !== false)
                drawSkin(
                    cx,
                    this.handSkins[side],
                    this.rig.skinMeshes[side],
                    meshVertices[side],
                    true,
                    this.options.skinBatching
                        ? { ...f.arms[side], torso: f.transforms.torso }
                        : null,
                );
            this.drawEquipment(side + 'Hand', f.arms[side].hand);
        }
        if (this.options.view === 'compare') {
            cx.save();
            cx.globalAlpha = 0.35;
            cx.drawImage(this.original, 0, 0);
            cx.restore();
        }
        this.drawDebug(f);
        this.lastDraw = {
            dpr,
            scale: rect.width / 941,
            backingWidth: w,
            backingHeight: h,
        };
    }
    skinBindings(side) {
        return [...this.equipment.values()]
            .filter(
                (e) =>
                    e.bitmap &&
                    e.skinned &&
                    e.segment.startsWith(side) &&
                    (!e.genders || e.genders.includes(this.gender)) &&
                    this.visible.get(e.id) !== false &&
                    this.visible.get(e.segment) !== false,
            )
            .sort((a, b) => (a.order || 0) - (b.order || 0));
    }
    drawEquipment(segment, m) {
        const cx = this.ctx;
        for (const e of [...this.equipment.values()]
            .filter(
                (e) =>
                    e.segment === segment &&
                    e.bitmap &&
                    this.visible.get(e.id) !== false &&
                    (!e.genders || e.genders.includes(this.gender)),
            )
            .sort((a, b) => (a.order || 0) - (b.order || 0))) {
            const p = e.placementByGender?.[this.gender] || e.placement;
            if (!p) continue;
            if (e.skinned && /^(right|left)(Upper|Fore|Hand)$/.test(e.segment))
                continue;
            cx.save();
            cx.transform(...m);
            cx.drawImage(e.bitmap, p.x, p.y, p.width, p.height);
            cx.restore();
        }
    }
    drawAppearance(l) {
        const cx = this.ctx;
        cx.save();
        cx.imageSmoothingQuality = 'high';
        if (l.slot === 'face') this.clipCrown(cx);
        const p = l.placement || { x: 0, y: 0, width: 941, height: 1672 };
        if (l.contain !== false) {
            const s = Math.min(
                    p.width / l.bitmap.width,
                    p.height / l.bitmap.height,
                ),
                w = l.bitmap.width * s,
                h = l.bitmap.height * s;
            cx.drawImage(
                l.bitmap,
                p.x + (p.width - w) / 2,
                p.y + (p.height - h) / 2,
                w,
                h,
            );
        } else cx.drawImage(l.bitmap, p.x, p.y, p.width, p.height);
        cx.restore();
    }
    drawDebug(f) {
        const cx = this.ctx;
        cx.save();
        cx.lineWidth = 2;
        if (this.options.debugBounds)
            for (const [k, m] of Object.entries(f.transforms)) {
                const s = this.rig.segments[k];
                if (!s) continue;
                cx.save();
                cx.transform(...m);
                cx.strokeStyle = '#bf7d51';
                cx.strokeRect(
                    s.bounds[0],
                    s.bounds[1],
                    s.bounds[2] - s.bounds[0],
                    s.bounds[3] - s.bounds[1],
                );
                cx.restore();
            }
        if (this.options.debugPivots) {
            const l = this.rig.landmarks,
                spine = [
                    l.head,
                    l.neck,
                    point(f.transforms.torso, l.chest),
                    l.pelvis,
                ];
            cx.strokeStyle = '#27aeb8';
            cx.beginPath();
            spine.forEach((p, i) => (i ? cx.lineTo(...p) : cx.moveTo(...p)));
            cx.stroke();
            cx.font = '16px system-ui';
            spine.forEach((p, i) => {
                cx.fillStyle = '#f4cb58';
                cx.beginPath();
                cx.arc(...p, 6, 0, Math.PI * 2);
                cx.fill();
                cx.fillText(
                    ['head', 'neck', 'chest', 'pelvis'][i],
                    p[0] + 10,
                    p[1],
                );
            });
        }
        if (this.options.debugPivots)
            for (const side of ['right', 'left']) {
                const a = f.arms[side];
                cx.strokeStyle = '#1ebac8';
                cx.beginPath();
                [a.shoulder, a.elbow, a.wrist, a.grip].forEach((p, i) =>
                    i ? cx.lineTo(...p) : cx.moveTo(...p),
                );
                cx.stroke();
                for (const p of [a.shoulder, a.elbow, a.wrist]) {
                    cx.fillStyle = '#f4cb58';
                    cx.beginPath();
                    cx.arc(...p, 6, 0, Math.PI * 2);
                    cx.fill();
                }
            }
        if (this.options.debugGrips && f.weapon)
            for (const p of [f.weapon.primary, f.weapon.support].filter(
                Boolean,
            )) {
                cx.strokeStyle = '#f73683';
                cx.beginPath();
                cx.arc(...p, 8, 0, Math.PI * 2);
                cx.moveTo(p[0] - 12, p[1]);
                cx.lineTo(p[0] + 12, p[1]);
                cx.stroke();
            }
        cx.restore();
    }
    advance(ms) {
        validNumber(ms, 'step ms', 0, 1000);
        this.time += ms;
        this.render();
    }
    step(ms = 1000 / 60) {
        this.advance(ms);
    }
    pause(value = true) {
        this.paused = !!value;
        this.lastTimestamp = null;
        if (value) this.stopRAF();
        else this.startRAF();
        this.render();
    }
    startRAF() {
        if (this.raf || this.destroyed || this.paused || document.hidden)
            return;
        this.raf = requestAnimationFrame((t) => {
            this.raf = null;
            if (this.lastTimestamp != null) {
                const dt = Math.max(0, t - this.lastTimestamp);
                this.fps = dt > 0 ? 1000 / dt : 0;
                this.time += dt;
                this.render();
            }
            this.lastTimestamp = t;
            this.startRAF();
        });
    }
    stopRAF() {
        if (this.raf) cancelAnimationFrame(this.raf);
        this.raf = null;
    }
    snapshot() {
        return structuredClone({
            gender: this.gender,
            rig: this.rig.id,
            pose: this.pose,
            time: this.time,
            paused: this.paused,
            frame: this.frame,
            display: this.lastDraw,
            equipment: [...this.equipment.keys()],
            cacheEntries: imageCache.size,
        });
    }
    destroy() {
        this.destroyed = true;
        this.generation++;
        this.appearanceGeneration++;
        this.stopRAF();
        this.observer.disconnect();
        document.removeEventListener('visibilitychange', this.onVisibility);
        this.equipment.clear();
        this.assets = {};
        this.bitmaps = {};
        this.staticLayer = null;
        this.restLayer = null;
        this.skins = {};
        this.handSkins = {};
    }
}
