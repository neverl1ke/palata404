import { relaxedMeleeAngles } from './relaxed-melee.mjs';
import { skinVertices, drawSkin } from './skin.mjs';
import { correctiveMatrices, correctiveVertices } from './pose-art.mjs';
import { WeaponAttachmentController } from './weapon-controller.mjs';
import {
    I,
    rad,
    angleLerp,
    around,
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
        // Assemble adjacent alpha partitions once at their shared pixel grid.
        // Scaling separate head/torso/lower images opens antialiased seams.
        this.compositeCanvas = surface(941,1672);
        this.compositeCtx = this.compositeCanvas.getContext('2d');
        this.weaponCanvas = surface(941,1672);
        this.weaponCtx = this.weaponCanvas.getContext('2d');
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
            weaponPreviewScale: 1,
            transitionMs: 320,
            playbackRate: 1,
            debugPivots: false,
            debugBounds: false,
            debugGrips: false,
            testSleeves: false,
            skinBatching: true,
            pistolSupport: true,
            view: 'rig',
            background: '#d3cfc6',
            diagnosticSkinHue: 0,
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
        const [rig, sharedWeapons, malePreview] = await Promise.all([
            this.json('rigs/' + gender + '_rig.json'),
            this.json('weapons.json'),
            this.json(gender + '-preview.json'),
        ]);
        const weapons = malePreview?.weapons || sharedWeapons;
        const assets = {};
        await Promise.all(
            Object.entries(rig.segments).map(
                async ([k, v]) => (assets[k] = await this.image(malePreview?.runtimeSurfaces?.[k] || v.image)),
            ),
        );
        for (const side of ['right', 'left']) {
            assets[side + 'ArmSkin'] = await this.image(
                malePreview?.runtimeSurfaces?.[side + 'ArmSkin'] || rig.skinMeshes[side].image,
            );
            assets[side + 'HandSkin'] = await this.image(
                malePreview?.runtimeSurfaces?.[side + 'HandSkin'] || rig.skinMeshes[side].handImage,
            );
        }
        await Promise.all(
            Object.entries(rig.handCorrections || {}).flatMap(([pose, hands]) =>
                Object.entries(hands).map(async ([side, part]) => {
                    assets['hand-' + pose + '-' + side] = await this.image(
                        part.image,
                    );
                    if (part.wristPatch)
                        assets['wrist-' + pose + '-' + side] = await this.image(
                            malePreview?.surfaceOverrides?.[
                                pose + '-' + side
                            ] || part.wristPatch.image,
                        );
                }),
            ),
        );
        await Promise.all(
            Object.entries(rig.poseArt || {}).flatMap(([pose, sides]) =>
                Object.entries(sides).flatMap(([side, art]) => [
                    this.image(malePreview?.poseArtSurfaces?.['art-' + pose + '-' + side] || art.image).then(
                        (i) => (assets['art-' + pose + '-' + side] = i),
                    ),
                    this.image(malePreview?.poseArtSurfaces?.['art-front-' + pose + '-' + side] || art.frontImage).then(
                        (i) => (assets['art-front-' + pose + '-' + side] = i),
                    ),
                    ...(malePreview?.poseArtCompleteSurfaces?.[pose+'-'+side]
                        ? [this.image(malePreview.poseArtCompleteSurfaces[pose+'-'+side]).then(
                            i=>assets['art-complete-'+pose+'-'+side]=i)] : []),
                ]),
            ),
        );
        await Promise.all(
            (malePreview?.contactRepairs || []).map(
                async (r, i) =>
                    (assets['contact-repair-' + i] = await this.image(r.image)),
            ),
        );
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
        this.pinnedTorsoMesh = null;
        this.pinnedTorsoMeshes = new Map();
        this.rig = rig;
        this.gender = gender;
        this.assets = assets;
        this.weapons = weapons;
        this.posePreview = malePreview;
        this.artMeshes = {};
        for (const [pose,sides] of Object.entries(rig.poseArt || {}))
            for (const [side,art] of Object.entries(sides)) {
                const extra = malePreview?.poseMeshExtensions?.[pose+'-'+side];
                this.artMeshes[pose+'-'+side] = extra
                    ? {...art.mesh,triangles:[...art.mesh.triangles,...extra]}
                    : art.mesh;
            }
        this.malePreview = gender === 'male' ? malePreview : null;
        this.chestDetailMesh = null;
        this.weaponController = new WeaponAttachmentController(weapons);
        this.original = original;
        this.transition = null;
        this.currentProjection = null;
        this.currentGrip = null;
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
            weaponPreviewScale: [0.75, 1.25],
            transitionMs: [0, 2000],
            playbackRate: [0, 3],
            diagnosticSkinHue: [0, 360],
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
    pistolSupportEnabled() {
        return !this.rig.posePolicy?.oneHandPistol && this.gender !== 'male' && this.options.pistolSupport;
    }
    setPose(pose) {
        if (this.gender === 'male')
            pose = this.rig.posePolicy?.legacyAliases?.[pose] || pose;
        if (!['idle', 'melee', 'pistol', 'rifle'].includes(pose))
            throw new RangeError('Unknown pose');
        if (!this.rig) return;
        if (this.gender === 'male' || this.rig.posePolicy?.instant) {
            // Authored endpoints are switched atomically. No legacy warped
            // intermediate arms, alpha crossfade or translucent weapon.
            this.pose = pose;
            this.transition = null;
            this.render();
            return;
        }
        this.compute();
        this.transition = {
            start: this.time,
            duration: this.options.transitionMs,
            from: structuredClone(this.currentAngles),
            projectionFrom: structuredClone(
                this.currentProjection || { right: [1, 1], left: [1, 1] },
            ),
            gripFrom: structuredClone(this.currentGrip),
            poseFrom: this.pose,
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
        this.skinsWithoutHands = {};
        this.poseSkins = {};
        this.poseHandSkins = {};
        this.bindingSkins = {};
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
            const bindingSurface = surface(x1 - x, y1 - y),
                bindingCtx = bindingSurface.getContext('2d');
            for (const e of this.skinBindings(side)) {
                const p = e.placementByGender?.[this.gender] || e.placement;
                cx.drawImage(e.bitmap, p.x - x, p.y - y, p.width, p.height);
                if (!e.poseBitmaps) bindingCtx.drawImage(
                    e.bitmap,
                    p.x - x,
                    p.y - y,
                    p.width,
                    p.height,
                );
            }
            this.bindingSkins[side] = bindingSurface;
            this.skins[side] =
                !this.appearance.mask &&
                this.skinBindings(side).length === 0 &&
                ['Upper', 'Fore', 'Hand'].every(
                    (part) => this.visible.get(side + part) !== false,
                )
                    ? this.assets[side + 'ArmSkin']
                    : c;
            // Keep the proximal wrist overlap, remove ALL old distal fingers.
            // The authored closed grip is drawn exactly once after the weapon.
            const noHand = surface(x1 - x, y1 - y),
                nx = noHand.getContext('2d');
            const arm = this.rig.arms[side];
            nx.translate(arm.wrist[0] - x, arm.wrist[1] - y);
            nx.rotate(
                Math.atan2(
                    arm.wrist[1] - arm.elbow[1],
                    arm.wrist[0] - arm.elbow[0],
                ),
            );
            const half = this.rig.wristProfiles?.[side]?.halfWidth || 30;
            nx.beginPath();
            nx.moveTo(-2000, -2000);
            nx.lineTo(-10, -2000);
            nx.lineTo(-10, -half);
            nx.bezierCurveTo(20, -half, 20, half, -10, half);
            nx.lineTo(-10, 2000);
            nx.lineTo(-2000, 2000);
            nx.closePath();
            nx.clip();
            nx.setTransform(1, 0, 0, 1, 0, 0);
            nx.drawImage(this.skins[side], 0, 0);
            this.skinsWithoutHands[side] = noHand;
            for (const [pose, hands] of Object.entries(
                this.rig.handCorrections || {},
            )) {
                const correction = hands[side];
                if (!correction) continue;
                const closed = surface(x1 - x, y1 - y),
                    cc = closed.getContext('2d');
                if (this.visible.get(side + 'Hand') !== false)
                    cc.drawImage(
                        this.assets['hand-' + pose + '-' + side],
                        correction.bounds[0] - x,
                        correction.bounds[1] - y,
                    );
                const blended = surface(x1 - x, y1 - y),
                    bc = blended.getContext('2d');
                const union = surface(x1 - x, y1 - y),
                    ux = union.getContext('2d');
                ux.fillStyle = '#fff';
                ux.fillRect(0, 0, x1 - x, arm.wrist[1] - y + 12);
                ux.drawImage(closed, 0, 0);
                bc.drawImage(noHand, 0, 0);
                bc.globalCompositeOperation = 'destination-in';
                bc.drawImage(union, 0, 0);
                bc.globalCompositeOperation = 'source-over';
                bc.drawImage(closed, 0, 0);
                if (
                    correction.wristPatch &&
                    this.visible.get(side + 'Hand') !== false
                ) {
                    // The pose-local retouch was inverse-baked into these UVs.
                    // It replaces alpha as well as color, removing old cut-outs.
                    const patch = correction.wristPatch,
                        [px, py, px1, py1] = patch.bounds;
                    const pw = px1 - px,
                        ph = py1 - py,
                        image = this.assets['wrist-' + pose + '-' + side];
                    bc.clearRect(px - x, py - y, pw, ph);
                    bc.drawImage(image, px - x, py - y);
                    const front = surface(pw, ph),
                        fx = front.getContext('2d');
                    fx.drawImage(image, 0, 0);
                    fx.globalCompositeOperation = 'destination-in';
                    const gradient = fx.createLinearGradient(
                        0,
                        arm.wrist[1] - py,
                        0,
                        arm.wrist[1] + 10 - py,
                    );
                    gradient.addColorStop(0, 'rgba(255,255,255,0)');
                    gradient.addColorStop(1, '#fff');
                    fx.fillStyle = gradient;
                    fx.fillRect(0, 0, pw, ph);
                    cc.clearRect(px - x, py - y, pw, ph);
                    cc.drawImage(front, px - x, py - y);
                    // Existing diagnostic bindings are restored once in the
                    // replaced band; this does not introduce new garment art.
                    for (const target of [bc, cc]) {
                        target.save();
                        target.beginPath();
                        target.rect(px - x, py - y, pw, ph);
                        target.clip();
                        for (const e of this.skinBindings(side)) {
                            if (target === cc && !e.segment.endsWith('Hand'))
                                continue;
                            const p =
                                e.placementByGender?.[this.gender] ||
                                e.placement;
                            target.drawImage(
                                e.bitmap,
                                p.x - x,
                                p.y - y,
                                p.width,
                                p.height,
                            );
                        }
                        target.restore();
                    }
                }
                this.poseSkins[pose + '-' + side] = blended;
                this.poseHandSkins[pose + '-' + side] = closed;
            }

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
        let bitmap, poseBitmaps;
        try {
            bitmap = await loadImage(
                binding.sourceByGender?.[gender] || binding.source,
            );
            if (binding.poseSources) {
                poseBitmaps = {};
                for (const [pose, sources] of Object.entries(binding.poseSources)) {
                    const side = binding.segment.startsWith('right') ? 'right' : 'left';
                    const art = this.rig.poseArt?.[pose]?.[side];
                    if (!art) throw new RangeError('No authored arm for equipment pose ' + pose);
                    const image = await loadImage(sources.image);
                    const frontImage = sources.frontImage ? await loadImage(sources.frontImage) : null;
                    if(frontImage && !sources.completeImage)
                        throw new RangeError('Authored equipment requires a complete image for weapon-hidden inspection');
                    const completeImage = sources.completeImage ? await loadImage(sources.completeImage) : image;
                    const [x,y,x1,y1] = art.mesh.bounds;
                    for (const im of [image,frontImage,completeImage].filter(Boolean))
                        if (im.width !== x1-x || im.height !== y1-y)
                            throw new RangeError('Equipment must use the authored arm canvas');
                    poseBitmaps[pose] = {image, frontImage, completeImage};
                }
            }
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
            poseBitmaps,
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
            phase = (this.time / this.options.cycleMs) * Math.PI * 2,
            b = this.options.breathing
                ? Math.sin(phase + 0.08 * Math.sin(2 * phase)) *
                  this.options.amplitude
                : 0;
        const projectionT = this.transition
            ? smoothstep(
                  this.transition.duration
                      ? (this.time - this.transition.start) /
                            this.transition.duration
                      : 1,
              )
            : 1;
        const projections = {};
        for (const side of ['right', 'left']) {
            const target = rig.anatomyProjection?.[this.pose]?.[side] || [1, 1];
            const from = this.transition?.projectionFrom?.[side] || target;
            projections[side] = target.map(
                (v, i) => from[i] + (v - from[i]) * projectionT,
            );
        }
        this.currentProjection = projections;
        const grips = {};
        for (const side of ['right', 'left']) {
            const target =
                rig.poseArt?.[this.pose]?.[side]?.grip || this.handCorrection(side)?.grip || rig.arms[side].grip;
            const from = this.transition?.gripFrom?.[side] || target;
            grips[side] = target.map(
                (v, i) => from[i] + (v - from[i]) * projectionT,
            );
        }
        this.currentGrip = grips;
        const arms = Object.fromEntries(
            ['right', 'left'].map((side) => [
                side,
                {
                    ...rig.arms[side],
                    projection: projections[side],
                    grip: grips[side],
                },
            ]),
        );
        const sx = 1 + rig.breathing.chestX * b,
            sy = 1 + rig.breathing.chestY * b,
            [px, py] = rig.landmarks.pelvis,
            torso = [sx, 0, 0, sy, px * (1 - sx), py * (1 - sy)];
        const shoulders = Object.fromEntries(
            ['right', 'left'].map((s) => [s, point(torso, arms[s].shoulder)]),
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
        if (
            !this.rig.posePolicy?.oneHandPistol &&
            this.gender !== 'male' &&
            this.pose === 'pistol' &&
            !this.pistolSupportEnabled()
        )
            pose = rig.pistolOneHand || pose;
        // Male lobby arms inherit only a small pose-specific fraction of
        // breathing. The torso cycle and amplitude remain unchanged; a prop
        // is never animated separately from its hand.
        const profile = this.posePreview?.breathingProfiles?.[this.pose];
        const bob = this.pose === 'idle' ? 0
            : (b * this.options.weaponSwayPx * (profile?.propSway ?? 1)) / scale;
        const gripX = b * 0.7 * (profile?.gripX ?? 1);
        const handBob = rad(b * 0.12 * (profile?.handDegrees ?? 1));
        const idleArm = profile?.idleArm ?? 1;
        if (this.pose === 'idle')
            for (const side of ['right', 'left']) {
                const sign = side === 'right' ? 1 : -1;
                angles[side] = {
                    upper: rad(rig.breathing.idleArmDegrees * b * sign * idleArm),
                    fore: rad(rig.breathing.idleArmDegrees * b * sign * idleArm * 1.5),
                    hand: rad(rig.breathing.idleArmDegrees * b * sign * idleArm * 1.5),
                };
            }
        else
            angles.right = solveArm(
                arms.right,
                shoulders.right,
                [pose.right[0] + gripX, pose.right[1] + bob],
                pose.bend.right,
                rad(pose.handAngles.right) + handBob,
            );
        // Relaxed knife motion is forward kinematics from the authored pose.
        // A pinned grip near full extension made the IK pole sweep sideways.
        if (this.pose === 'melee')
            angles.right = relaxedMeleeAngles(arms.right, pose, b * this.options.weaponSwayPx / 2);
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
                      hand:
                          this.gender === 'male'
                              ? angleLerp(
                                    transition.from[side].fore,
                                    target.fore,
                                    t,
                                ) +
                                angleLerp(
                                    Math.atan2(
                                        Math.sin(
                                            (transition.from[side].hand || 0) -
                                                transition.from[side].fore,
                                        ),
                                        Math.cos(
                                            (transition.from[side].hand || 0) -
                                                transition.from[side].fore,
                                        ),
                                    ),
                                    Math.atan2(
                                        Math.sin(
                                            (target.hand || 0) - target.fore,
                                        ),
                                        Math.cos(
                                            (target.hand || 0) - target.fore,
                                        ),
                                    ),
                                    t,
                                )
                              : angleLerp(
                                    transition.from[side].hand || 0,
                                    target.hand || 0,
                                    t,
                                ),
                  }
                : target;
        const limitWrist = (side, a) => {
            if (this.gender !== 'male' || !transition) return a;
            const arm = arms[side];
            const foreDirection =
                a.fore +
                Math.atan2(
                    arm.wrist[1] - arm.elbow[1],
                    arm.wrist[0] - arm.elbow[0],
                );
            const handRest = Math.atan2(
                arm.grip[1] - arm.wrist[1],
                arm.grip[0] - arm.wrist[0],
            );
            const delta = Math.atan2(
                Math.sin(a.hand + handRest - foreDirection),
                Math.cos(a.hand + handRest - foreDirection),
            );
            return {
                ...a,
                hand:
                    foreDirection +
                    Math.max(-rad(68), Math.min(rad(68), delta)) -
                    handRest,
            };
        };
        if (this.gender === 'male' && this.pose === 'pistol') {
            // Near-folded 2D IK amplifies a few breathing pixels into a large
            // elbow swing. Hold the calibrated upper-arm pole and let depth
            // projection of the forearm absorb that small motion instead.
            const rest = rig.arms.right,
                targetArm = {
                    ...rest,
                    grip: this.rig.handCorrections.pistol.right.grip,
                    projection: rig.anatomyProjection.pistol.right,
                };
            const neutral = solveArm(
                targetArm,
                rest.shoulder,
                pose.right,
                pose.bend.right,
                rad(pose.handAngles.right),
            );
            const hand = rad(pose.handAngles.right) + handBob;
            const elbow = point(
                armMatrices(targetArm, shoulders.right, neutral).upper,
                rest.elbow,
            );
            const dx = targetArm.grip[0] - rest.wrist[0],
                dy = targetArm.grip[1] - rest.wrist[1];
            const wrist = [
                pose.right[0] +
                    gripX -
                    Math.cos(hand) * dx +
                    Math.sin(hand) * dy,
                pose.right[1] + bob - Math.sin(hand) * dx - Math.cos(hand) * dy,
            ];
            const ratio =
                distance(elbow, wrist) / distance(rest.elbow, rest.wrist);
            const from = transition?.projectionFrom?.right?.[1] ?? ratio;
            projections.right[1] = from + (ratio - from) * projectionT;
            angles.right = {
                upper: neutral.upper,
                fore:
                    Math.atan2(wrist[1] - elbow[1], wrist[0] - elbow[0]) -
                    Math.atan2(
                        rest.wrist[1] - rest.elbow[1],
                        rest.wrist[0] - rest.elbow[0],
                    ),
                hand,
            };
        }
        angles.right = limitWrist('right', blend('right', angles.right));
        matrices.right = armMatrices(arms.right, shoulders.right, angles.right);
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
                (this.pose === 'pistol' && this.pistolSupportEnabled())
                    ? weapon.support
                    : [pose.left[0], pose.left[1] + b * 1.2];
            angles.left =
                this.pose === 'melee' ||
                (this.pose === 'pistol' && !this.pistolSupportEnabled())
                    ? { upper: 0, fore: 0, hand: 0 }
                    : solveArm(
                          arms.left,
                          shoulders.left,
                          target,
                          pose.bend.left,
                          rad(pose.handAngles.left) + handBob,
                      );
        }
        angles.left = limitWrist('left', blend('left', angles.left));
        matrices.left = armMatrices(arms.left, shoulders.left, angles.left);
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
            projection: projections,
            sourceBoneLengths: Object.fromEntries(
                ['right', 'left'].map((s) => [
                    s,
                    [
                        distance(rig.arms[s].shoulder, rig.arms[s].elbow),
                        distance(rig.arms[s].elbow, rig.arms[s].wrist),
                    ],
                ]),
            ),
            primaryError: weapon
                ? distance(weapon.primary, matrices.right.grip)
                : 0,
            supportError:
                weapon?.support &&
                (this.pose === 'rifle' ||
                    (this.pose === 'pistol' && this.pistolSupportEnabled()))
                    ? distance(weapon.support, matrices.left.grip)
                    : 0,
        });
    }
    render() {
        if (!this.rig || this.destroyed) return;
        const f = this.compute(),
            canvas = this.canvas,
            cx = this.compositeCtx,
            rect = canvas.getBoundingClientRect(),
            dpr = window.devicePixelRatio || 1,
            w = Math.max(1, Math.round(rect.width * dpr)),
            h = Math.max(1, Math.round(rect.height * dpr));
        if (canvas.width !== w || canvas.height !== h) {
            canvas.width = w;
            canvas.height = h;
        }
        cx.setTransform(1, 0, 0, 1, 0, 0);
        cx.clearRect(0, 0, 941, 1672);
        const skinFilter = this.options.diagnosticSkinHue
            ? `hue-rotate(${this.options.diagnosticSkinHue}deg)` : 'none';
        cx.filter = skinFilter;
        // Compose the subject identically on every background. Painting a
        // background first makes repeated translucent triangle clips round
        // differently; the prior renderer amplified a 9-alpha fringe by 7 RGB.
        const finishBackground = () => {
            const output=this.ctx;
            output.setTransform(1,0,0,1,0,0);
            output.globalAlpha=1;
            output.globalCompositeOperation='source-over';
            output.clearRect(0,0,w,h);
            output.filter='none';
            output.imageSmoothingEnabled=true;
            output.imageSmoothingQuality='high';
            output.drawImage(this.compositeCanvas,0,0,w,h);
            if (this.options.background === 'transparent') return;
            output.save();
            output.globalAlpha = 1;
            output.globalCompositeOperation = 'destination-over';
            output.fillStyle = this.options.background;
            output.fillRect(0,0,w,h);
            output.restore();
        };
        if (this.options.view === 'original') {
            cx.drawImage(this.original, 0, 0);
            finishBackground();
            return;
        }
        const drawBitmap = (im, bounds, m = I, alpha = 1, target = cx) => {
            target.save();
            target.globalAlpha = alpha;
            target.transform(...m);
            target.drawImage(im, bounds[0], bounds[1]);
            target.restore();
        };
        const drawPart = (key, m = I) => {
            if (this.visible.get(key) === false) return;
            if (key === 'torso' && (this.gender === 'male' || this.rig.posePolicy?.instant)) this.drawPinnedTorso(f);
            else drawBitmap(this.bitmaps[key], this.rig.segments[key].bounds, m);
            if(key==='torso' && this.gender==='male' && this.malePreview?.chestDetail && Math.abs(f.breath)>1e-8) {
                const vertices=this.chestDetailVertices(f);
                const detail=this.malePreview.chestDetail;
                // The overlay is fully within opaque chest skin. Keep the
                // original torso silhouette and its edge antialiasing intact.
                cx.save(); cx.transform(...m); cx.beginPath();
                cx.ellipse(...detail.center,detail.radius[0]-5,detail.radius[1]-5,0,0,Math.PI*2);
                cx.clip(); cx.transform(...[1/m[0],0,0,1/m[3],-m[4]/m[0],-m[5]/m[3]]);
                drawSkin(cx,this.bitmaps.torso,this.chestDetailMesh,vertices,false,null);
                cx.restore();
            }
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
            if (!neutral && (this.gender === 'male' || this.rig.poseArt))
                this.drawMaleArm(side, f, false);
            else if (!neutral)
                drawSkin(
                    cx,
                    this.handCorrection(side)
                        ? this.poseSkins[this.pose + '-' + side]
                        : this.skins[side],
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
        for (const side of ['left','right']) this.drawEquipment(side+'Hand', f.arms[side].hand);
        const item = this.weaponCtx;
        item.setTransform(1,0,0,1,0,0);
        item.globalCompositeOperation='source-over';
        item.filter='none';
        item.clearRect(0,0,941,1672);
        const hasItem = f.weapon && this.visible.get('weapon') !== false;
        cx.filter = 'none';
        if (hasItem && f.weapon && this.visible.get('weapon') !== false) {
            const def = this.weapons[this.pose];
            // Diagnostic art-size variants keep the primary grip fixed.
            // The support hand is intentionally NOT solved again: this exposes
            // whether another item needs its own support/grip calibration.
            const k = this.options.weaponPreviewScale;
            const q = def.primary.map((v, i) => v + (def.offset?.[i] || 0));
            const m = f.weapon.matrix;
            const previewMatrix = [m[0]*k,m[1]*k,m[2]*k,m[3]*k,
                m[4]+(1-k)*(m[0]*q[0]+m[2]*q[1]),
                m[5]+(1-k)*(m[1]*q[0]+m[3]*q[1])];
            drawBitmap(
                this.assets['weapon-' + this.pose],
                [0, 0],
                previewMatrix,
                this.transition ? f.transitionProgress : 1,
                item,
            );
        }
        // Paint the foreground only into existing weapon coverage. The complete
        // arm is already below; this prevents doubling its antialiased edge.
        item.globalCompositeOperation='source-atop';
        for (const side of hasItem ? ['left', 'right'] : []) {
            item.filter = skinFilter;
            if (!neutral && this.visible.get(side + 'Hand') !== false) {
                const correction = this.handCorrection(side);
                if (this.gender === 'male' || this.rig.poseArt) this.drawMaleArm(side, f, true, item);
                else if (correction)
                    drawSkin(
                        item,
                        this.poseHandSkins[this.pose + '-' + side],
                        this.rig.skinMeshes[side],
                        meshVertices[side],
                        true,
                        this.options.skinBatching
                            ? { ...f.arms[side], torso: f.transforms.torso }
                            : null,
                    );
                else
                    drawSkin(
                        item,
                        this.handSkins[side],
                        this.rig.skinMeshes[side],
                        meshVertices[side],
                        true,
                        this.options.skinBatching
                            ? { ...f.arms[side], torso: f.transforms.torso }
                            : null,
                    );
            }
            this.drawEquipment(side + 'Hand', f.arms[side].hand, item);
        }
        item.globalCompositeOperation='source-over';
        cx.filter='none';
        if(hasItem) cx.drawImage(this.weaponCanvas,0,0);
        if (this.options.view === 'compare') {
            cx.save();
            cx.globalAlpha = 0.35;
            cx.drawImage(this.original, 0, 0);
            cx.restore();
        }
        cx.filter = 'none';
        this.drawDebug(f);
        finishBackground();
        this.lastDraw = {
            dpr,
            scale: rect.width / 941,
            backingWidth: w,
            backingHeight: h,
        };
    }
    // Pin both static partition joins, including the lower torso boundary.
    // Equipment uses this same deformation, rather than a conflicting affine.
    drawPinnedTorso(frame, bitmap = this.bitmaps.torso, bounds = this.rig.segments.torso.bounds) {
        if (Math.abs(frame.breath) < 1e-8) {
            this.compositeCtx.drawImage(bitmap, bounds[0], bounds[1]);
            return;
        }
        this.pinnedTorsoMeshes ??= new Map();
        const key = bounds.join(',');
        if (!this.pinnedTorsoMeshes.has(key)) {
            const [x0,y0,x1,y1] = bounds;
            const [left,top,right,bottom] = this.rig.segments.torso.bounds;
            const xs = [...new Set([x0,left,right,x1].filter(x=>x>=x0&&x<=x1))].sort((a,b)=>a-b);
            const rows = [y0,y1,top,365,bottom-65,bottom];
            for(let y=top+8;y<365;y+=8) rows.push(y);
            for(let y=bottom-57;y<bottom;y+=8) rows.push(y);
            const ys=[...new Set(rows.filter(y=>y>=y0&&y<=y1))].sort((a,b)=>a-b);
            const vertices=ys.flatMap(y=>xs.map(x=>[x,y]));
            const triangles=[];
            for(let i=0;i<ys.length-1;i++) for(let j=0;j<xs.length-1;j++) {
                const a=i*xs.length+j,c=a+xs.length;
                triangles.push([a,a+1,c],[a+1,c+1,c]);
            }
            this.pinnedTorsoMeshes.set(key,{bounds,vertices,triangles});
        }
        const mesh=this.pinnedTorsoMeshes.get(key);
        const vertices=mesh.vertices.map(p=>{
            const moved=point(frame.transforms.torso,p);
            const top=this.rig.segments.torso.bounds[1], bottom=this.rig.segments.torso.bounds[3];
            const weight=smoothstep((p[1]-top)/(365-top)) *
                (1-smoothstep((p[1]-(bottom-65))/65));
            return p.map((v,i)=>v+(moved[i]-v)*weight);
        });
        drawSkin(this.compositeCtx,bitmap,mesh,vertices,false,null);
    }
    // Local ribcage expansion: support vanishes before shoulders, neck and
    // abdomen. It never drives the arm solver or weapon controller.
    chestDetailVertices(frame) {
        const detail = this.gender === 'male' && this.malePreview?.chestDetail;
        if (!detail) return null;
        if (!this.chestDetailMesh) {
            const bounds = this.rig.segments.torso.bounds;
            const [cx,cy]=detail.center,[rx,ry]=detail.radius;
            const [x0,y0,x1,y1]=[cx-rx,cy-ry,cx+rx,cy+ry];
            const xs=[],ys=[];
            for(let x=x0;x<x1;x+=24) xs.push(x); xs.push(x1);
            for(let y=y0;y<y1;y+=24) ys.push(y); ys.push(y1);
            const vertices=ys.flatMap(y=>xs.map(x=>[x,y]));
            const triangles=[];
            for(let y=0;y<ys.length-1;y++) for(let x=0;x<xs.length-1;x++) {
                const a=y*xs.length+x,b=a+1,c=a+xs.length,d=c+1;
                triangles.push([a,b,c],[b,d,c]);
            }
            this.chestDetailMesh={bounds,vertices,triangles};
        }
        const [cx,cy]=detail.center,[rx,ry]=detail.radius;
        return this.chestDetailMesh.vertices.map(([x,y])=>{
            const dx=x-cx,dy=y-cy;
            const support=Math.max(0,1-(dx/rx)**2-(dy/ry)**2)**2;
            return point(frame.transforms.torso,[
                x+dx*detail.horizontal*frame.breath*support,
                y+dy*detail.vertical*frame.breath*support,
            ]);
        });
    }
    drawMaleArm(side, frame, front, target = this.compositeCtx) {
        const paint = (ctx, pose, allowArt = true) => {
            const visible = ['Upper', 'Fore', 'Hand'].every(
                (p) => this.visible.get(side + p) !== false,
            );
            const art =
                allowArt && ['Upper','Fore'].every(p=>this.visible.get(side+p)!==false)
                    ? this.rig.poseArt?.[pose]?.[side] : null;
            if (art) {
                const complete=this.assets['art-complete-'+pose+'-'+side];
                const bare=!!complete && this.visible.get(side+'Hand')!==false;
                const artMesh = this.artMeshes[pose+'-'+side] || art.mesh;
                const delta = correctiveMatrices(
                    art.bind,
                    frame.arms[side],
                    frame.transforms.torso,
                );
                drawSkin(
                    ctx,
                    !front && bare ? complete : this.assets[
                        (front ? 'art-front-' : 'art-') + pose + '-' + side
                    ],
                    artMesh,
                    correctiveVertices(artMesh, delta),
                    false,
                    this.options.skinBatching ? delta : null,
                );
                if (this.skinBindings(side).length) {
                    const mesh = this.rig.skinMeshes[side];
                    drawSkin(
                        ctx,
                        this.bindingSkins[side],
                        mesh,
                        skinVertices(
                            mesh,
                            frame.arms[side],
                            frame.transforms.torso,
                            this.rig.arms[side],
                        ),
                        front,
                        this.options.skinBatching
                            ? {
                                  ...frame.arms[side],
                                  torso: frame.transforms.torso,
                              }
                            : null,
                    );
                    // Optional authored-pose garment textures share exactly
                    // the same corrective mesh and bind as their skin. Legacy
                    // rest-space sleeves remain a separate, unapproved path.
                    for (const e of this.skinBindings(side)) {
                        const native = e.poseBitmaps?.[pose];
                        const texture = front ? native?.frontImage : bare ? native?.completeImage : native?.image;
                        if (!texture) continue;
                        ctx.save(); ctx.filter = 'none';
                        drawSkin(ctx, texture, artMesh,
                            correctiveVertices(artMesh, delta), false,
                            this.options.skinBatching ? delta : null);
                        ctx.restore();
                    }
                }
                return;
            }
            const correction =
                pose === 'pistol' && side === 'left'
                    ? null
                    : this.rig.handCorrections?.[pose]?.[side];
            const texture = front
                ? correction
                    ? this.poseHandSkins[pose + '-' + side]
                    : this.handSkins[side]
                : correction
                  ? this.poseSkins[pose + '-' + side]
                  : this.skins[side];
            const mesh = this.rig.skinMeshes[side];
            drawSkin(
                ctx,
                texture,
                mesh,
                skinVertices(
                    mesh,
                    frame.arms[side],
                    frame.transforms.torso,
                    this.rig.arms[side],
                ),
                front,
                this.options.skinBatching
                    ? { ...frame.arms[side], torso: frame.transforms.torso }
                    : null,
            );
        };
        paint(target, this.pose);
        if (
            !front &&
            ['Upper', 'Fore', 'Hand'].every(
                (p) => this.visible.get(side + p) !== false,
            )
        )
            for (const [i, repair] of (
                this.malePreview?.contactRepairs || []
            ).entries()) {
                if (repair.pose !== this.pose || repair.side !== side) continue;
                const bind = this.rig.poseArt[this.pose][side].bind;
                const delta = correctiveMatrices(
                    bind,
                    frame.arms[side],
                    frame.transforms.torso,
                );
                this.compositeCtx.save();
                this.compositeCtx.transform(...delta[repair.bone]);
                this.compositeCtx.drawImage(
                    this.assets['contact-repair-' + i],
                    repair.bounds[0],
                    repair.bounds[1],
                );
                this.compositeCtx.restore();
            }
    }
    handCorrection(side) {
        if (
            this.pose === 'pistol' &&
            side === 'left' &&
            !this.pistolSupportEnabled()
        )
            return null;
        return this.rig.handCorrections?.[this.pose]?.[side] || null;
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
    drawEquipment(segment, m, target = this.compositeCtx) {
        const cx = target;
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
            cx.filter = 'none';
            if (segment === 'torso' && (this.gender === 'male' || this.rig.posePolicy?.instant)) {
                if (!e.pinnedTexture) {
                    e.pinnedTexture = surface(941,1672);
                    e.pinnedTexture.getContext('2d').drawImage(e.bitmap,p.x,p.y,p.width,p.height);
                }
                this.drawPinnedTorso(this.frame,e.pinnedTexture,[0,0,941,1672]);
                cx.restore();
                continue;
            }
            cx.transform(...m);
            cx.drawImage(e.bitmap, p.x, p.y, p.width, p.height);
            cx.restore();
        }
    }
    drawAppearance(l) {
        const cx = this.compositeCtx;
        cx.save();
        if(l.slot !== 'face') cx.filter = 'none';
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
        const cx = this.compositeCtx;
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
                this.time += dt * this.options.playbackRate;
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
        if (this.destroyed) return;
        this.destroyed = true;
        this.generation++;
        this.appearanceGeneration++;
        this.stopRAF();
        this.observer.disconnect();
        document.removeEventListener('visibilitychange', this.onVisibility);
        this.equipment.clear();
        this.assets = {};
        this.bitmaps = {};
        this.armPaintSurface = null;
        this.armBlendSurface = null;
        this.compositeCanvas.width = this.compositeCanvas.height = 1;
        this.weaponCanvas.width = this.weaponCanvas.height = 1;
        this.weaponCanvas = null;
        this.weaponCtx = null;
        this.compositeCanvas = null;
        this.compositeCtx = null;
        this.pinnedTorsoMeshes?.clear();
        this.artMeshes = {};
        this.staticLayer = null;
        this.restLayer = null;
        this.skins = {};
        this.handSkins = {};
        this.bindingSkins = {};
        this.poseSkins = {};
        this.poseHandSkins = {};
        this.skinsWithoutHands = {};
    }
}
