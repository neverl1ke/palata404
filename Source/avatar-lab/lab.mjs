import { AvatarEngine } from '../avatar-core/engine.mjs';
const $ = (id) => document.getElementById(id),
    catalog = window.avatarCatalog;
const engine = await AvatarEngine.create($('avatar'), {
    gender: 'male',
    resources: window.AVATAR_CORE_EMBED || null,
});
window.avatarLab = { engine };
let appearanceToken = 0,
    genderToken = 0;
function options(id, rows, value) {
    $(id).replaceChildren(
        ...rows.map((r) => {
            const o = document.createElement('option');
            o.value = r.id;
            o.textContent = r.name;
            return o;
        }),
    );
    $(id).value = rows.some((r) => r.id === value) ? value : rows[0]?.id;
}
function previousFrame() {
    const path = '../review/avatar-foundation-cleanup/Gallery/before-' + engine.gender + '-' + engine.pose + '-True.png';
    $('previous-arms').src =
        window.AVATAR_CORE_EMBED?.catalogImages?.[path] || path;
}
function populate() {
    $('transition').disabled = engine.gender === 'male' || !!engine.rig.posePolicy?.instant;
    $('transition-value').textContent =
        (engine.gender === 'male' || engine.rig.posePolicy?.instant) ? 'миттєво' : engine.options.transitionMs;
    previousFrame();
    options(
        'face',
        [
            { id: 'source', name: 'Оригінальний PNG' },
            { id: 'native', name: 'Базове обличчя як у грі' },
            ...catalog.faces(engine.gender),
        ],
        'source',
    );
    options('hair', catalog.hairs(engine.gender), 'hair-none');
    options('color', catalog.colors, 'original');
    $('layers').replaceChildren(
        ...[...Object.keys(engine.rig.segments)].map((id) => {
            const label = document.createElement('label'),
                input = document.createElement('input');
            input.type = 'checkbox';
            input.checked = true;
            input.addEventListener('change', () =>
                engine.setLayerVisible(id, input.checked),
            );
            label.append(input, document.createTextNode(id));
            return label;
        }),
    );
    $('show-weapon').checked = engine.visible.get('weapon') !== false;
    $('weapon-preview-scale').value = String(engine.options.weaponPreviewScale);
    $('rig-name').textContent = engine.rig.id + ' · 941×1672';
    for (const b of document.querySelectorAll('[data-gender]'))
        b.setAttribute(
            'aria-pressed',
            String(b.dataset.gender === engine.gender),
        );
}
async function appearance() {
    const t = ++appearanceToken;
    try {
        const d = await catalog.describe(
            engine.gender,
            $('face').value,
            $('hair').value,
            $('color').value,
        );
        if (t !== appearanceToken) return;
        await engine.setAppearance(d);
        $('status').textContent = 'Готово · зовнішність не записується в сейв';
    } catch (e) {
        $('status').textContent = e.message;
        throw e;
    }
}
async function sleeves() {
    for (const id of ['rightUpper', 'rightFore', 'leftUpper', 'leftFore']) {
        engine.unbindEquipment('test-' + id);
        if ($('sleeves').checked) {
            const b = engine.rig.segments[id].bounds;
            await engine.bindEquipment({
                id: 'test-' + id,
                segment: id,
                skinned: true,
                genders: [engine.gender],
                source:
                    engine.resources?.images?.[
                        'assets/' + engine.gender + '/' + id + 'Sleeve.png'
                    ] ||
                    new URL(
                        '../avatar-core/assets/' +
                            engine.gender +
                            '/' +
                            id +
                            'Sleeve.png',
                        location.href,
                    ).href,
                placement: {
                    x: b[0],
                    y: b[1],
                    width: b[2] - b[0],
                    height: b[3] - b[1],
                },
                order: 1,
            });
        }
    }
}
async function gender(value) {
    const t = ++genderToken;
    appearanceToken++;
    $('status').textContent = 'Завантаження ' + value + '…';
    await engine.setGender(value);
    if (t !== genderToken) return;
    populate();
    await appearance();
    await sleeves();
    await diagnosticBinding();
}
let diagnosticToken = 0;
async function diagnosticBinding() {
    const token=++diagnosticToken;
    for(const id of [...engine.equipment.keys()])
        if(id.startsWith('diagnostic-')) engine.unbindEquipment(id);
    const kind=$('diagnostic-binding').value;
    if(kind==='none') return;
    const gender=engine.gender;
    const config=await engine.json('assets/diagnostics/config.json');
    const absolute=path=>engine.resources?.images?.[path] || new URL(path,engine.baseURL).href;
    for(const original of config[gender][kind]) {
        if(token!==diagnosticToken || engine.gender!==gender) return;
        const binding=structuredClone(original);
        binding.source=absolute(binding.source);
        if(binding.poseSources) for(const sources of Object.values(binding.poseSources)) {
            sources.image=absolute(sources.image);
            sources.frontImage=absolute(sources.frontImage);
            if(sources.completeImage) sources.completeImage=absolute(sources.completeImage);
        }
        await engine.bindEquipment(binding);
    }
}
window.avatarLab.diagnosticBinding=diagnosticBinding;
$('diagnostic-binding').addEventListener('change',()=>diagnosticBinding().catch(showError));
$('diagnostic-hue').addEventListener('change',e=>engine.setOptions({diagnosticSkinHue:+e.target.value}));
for (const b of document.querySelectorAll('[data-gender]'))
    b.addEventListener('click', () =>
        gender(b.dataset.gender).catch(showError),
    );
for (const b of document.querySelectorAll('[data-pose]'))
    b.addEventListener('click', () => {
        engine.setPose(b.dataset.pose);
        previousFrame();
        for (const other of document.querySelectorAll('[data-pose]'))
            other.setAttribute('aria-pressed', String(b === other));
    });
function showError(e) {
    $('status').textContent = 'Помилка: ' + e.message;
    console.error(e);
}
$('view').addEventListener('change', (e) =>
    engine.setOptions({ view: e.target.value }),
);
$('background').addEventListener('change', (e) =>
    engine.setOptions({ background: e.target.value }),
);
for (const [id, key] of [
    ['breathing', 'breathing'],
    ['pivots', 'debugPivots'],
    ['bounds', 'debugBounds'],
    ['grips', 'debugGrips'],
])
    $(id).addEventListener('change', (e) =>
        engine.setOptions({ [key]: e.target.checked }),
    );
for (const [id, key] of [
    ['speed', 'playbackRate'],
    ['cycle', 'cycleMs'],
    ['amplitude', 'amplitude'],
    ['sway', 'weaponSwayPx'],
    ['transition', 'transitionMs'],
])
    $(id).addEventListener('input', (e) => {
        $(id + '-value').textContent = e.target.value;
        engine.setOptions({ [key]: +e.target.value });
    });
$('pause').addEventListener('click', () => {
    engine.pause(!engine.paused);
    $('pause').textContent = engine.paused ? 'Продовжити' : 'Пауза';
});
$('step').addEventListener('click', () => {
    engine.pause();
    $('pause').textContent = 'Продовжити';
    engine.step();
});
$('reset').addEventListener('click', () => {
    engine.time = 0;
    engine.transition = null;
    engine.render();
});
$('sleeves').addEventListener('change', () => sleeves().catch(showError));
for (const id of ['face', 'hair', 'color'])
    $(id).addEventListener('change', () => appearance().catch(showError));
$('read-save').addEventListener('click', async () => {
    try {
        const s = catalog.readSave();
        if (s.error) {
            $('save-status').textContent = s.error;
            return;
        }
        await gender(s.gender);
        $('face').value = s.face;
        $('hair').value = s.hair;
        $('color').value = s.color;
        await appearance();
        window.avatarLab.saveSnapshot = s;
        $('save-status').textContent =
            'Зчитано ' +
            (s.mode === 'combat' ? 'Трип' : 'Пацієнт') +
            '. Обидва комплекти залишені без змін; суцільний одяг тут не анімується.';
    } catch (e) {
        showError(e);
    }
});
const timer = setInterval(() => {
    $('metrics').textContent =
        (engine.paused ? 'Пауза' : Math.round(engine.fps) + ' FPS') +
        ' · ' +
        (engine.lastDraw?.scale || 0).toFixed(3) +
        '× · DPR ' +
        (window.devicePixelRatio || 1);
}, 250);
window.addEventListener(
    'pagehide',
    () => {
        clearInterval(timer);
        engine.destroy();
    },
    { once: true },
);
populate();
await appearance();
engine.pause(false);
window.avatarLab.ready = true;

// Visibility is independent of pose, animation and all hand passes.
$('show-weapon').addEventListener('change', () => engine.setLayerVisible('weapon', $('show-weapon').checked));
$('weapon-preview-scale').addEventListener('change', () => engine.setOptions({weaponPreviewScale:Number($('weapon-preview-scale').value)}));
