// === Telegram Web App та Нікнейм ===
const tg = window.Telegram?.WebApp;

// Treat player-controlled and saved text as text when placing it in HTML templates.
function escapeHTML(value) {
    return String(value ?? '').replace(/[&<>"']/g, character => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    })[character]);
}
if (tg) {
    try {
        tg.ready();
        tg.expand();
    } catch (e) {
        console.log("Telegram WebApp не ініціалізовано");
    }
}

function safeStorageGet(key) {
    try {
        return window.localStorage?.getItem(key) ?? null;
    } catch (e) {
        return null;
    }
}

function safeStorageSet(key, value) {
    try {
        window.localStorage?.setItem(key, value);
        return Boolean(window.localStorage);
    } catch (e) {
        return false;
    }
}

function safeStorageRemove(key) {
    try {
        window.localStorage?.removeItem(key);
        return Boolean(window.localStorage);
    } catch (error) {
        return false;
    }
}

function getInitialUsername() {
    const savedName = safeStorageGet('palata404_nickname');
    if (savedName) return savedName;

    if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        if (user.username) return `@${user.username}`;
        if (user.first_name) return `${user.first_name}${user.last_name ? ' ' + user.last_name : ''}`;
    }

    return "Пацієнт #404";
}

let playerName = getInitialUsername();

function updatePlayerNameDisplay() {
    const nameElement = document.getElementById('player-name');
    if (nameElement) {
        nameElement.textContent = playerName;
    }
}

function changeNickname() {
    const newName = prompt("Введіть ваш новий нікнейм:", playerName);
    if (newName && newName.trim() !== "") {
        playerName = newName.trim().substring(0, 20);
        safeStorageSet('palata404_nickname', playerName);
        updatePlayerNameDisplay();
        closeSettings();
    }
}

// === Система ідентифікації та «Сусіди по блоку» (Telegram + Web) ===
function getPlayerUniqueId() {
    if (tg?.initDataUnsafe?.user?.id != null) {
        const user = tg.initDataUnsafe.user;
        return {
            type: 'telegram',
            id: user.id.toString(),
            name: user.username ? `@${user.username}` : (user.first_name || "Гравець")
        };
    }

    let webId = safeStorageGet('palata404_web_id');
    if (!webId) {
        webId = 'WEB-' + Math.floor(100000 + Math.random() * 900000);
        safeStorageSet('palata404_web_id', webId);
    }

    return {
        type: 'browser',
        id: webId,
        name: playerName
    };
}

initializeRaidArchive();
pendingBattleReward = readPendingBattleReward();
initializeStaffArchive();

let friendsList = loadSaveData('palata404_friends', []);
friendsList = friendsList
    .filter(friend => friend && typeof friend === 'object' && !Array.isArray(friend)
        && (typeof friend.identifier === 'string' || typeof friend.identifier === 'number'))
    .map(friend => ({
        identifier: String(friend.identifier),
        status: typeof friend.status === 'string' ? friend.status : "На зв'язку"
    }));

function openFriends() {
    closeOtherModals(['friends-modal']);
    closeInventory();
    closeCustomization();
    closeSettings();
    closeDossier();

    const playerInfo = getPlayerUniqueId();
    const uniqueIdElem = document.getElementById('my-unique-id');
    if (uniqueIdElem) {
        uniqueIdElem.textContent = playerInfo.type === 'telegram'
            ? `Telegram: ${playerInfo.name} (ID: ${playerInfo.id})`
            : `Браузер ID: ${playerInfo.id}`;
    }

    renderFriendsList();
    const friendsModal = document.getElementById('friends-modal');
    if (friendsModal) friendsModal.classList.remove('hidden');
}

function closeFriends() {
    const friendsModal = document.getElementById('friends-modal');
    if (friendsModal) friendsModal.classList.add('hidden');
}

function addFriend() {
    const input = document.getElementById('friend-input');
    if (!input) return;
    const val = input.value.trim();

    if (!val) {
        alert("Введіть коректний ID або юзернейм!");
        return;
    }

    const currentPlayer = getPlayerUniqueId();
    if (val === currentPlayer.id || val === currentPlayer.name) {
        alert("Ви не можете додати самого себе до пацієнтів!");
        return;
    }

    if (friendsList.some(f => f.identifier === val)) {
        alert("Цей пацієнт уже у вашому списку зв'язку!");
        return;
    }

    friendsList.push({ identifier: val, status: 'На зв\'язку' });
    safeStorageSet('palata404_friends', JSON.stringify(friendsList));

    input.value = '';
    renderFriendsList();
    alert("Пацієнта успішно додано до сусідів по блоку!");
}

function renderFriendsList() {
    const container = document.getElementById('friends-list');
    if (!container) return;
    container.innerHTML = '';

    if (friendsList.length === 0) {
        container.innerHTML = `<div style="color: #7f8c8d; text-align: center; padding: 10px;">Список сусідів порожній</div>`;
        return;
    }

    friendsList.forEach((friend, index) => {
        const item = document.createElement('div');
        item.style.cssText = "display: flex; justify-content: space-between; align-items: center; background: #261f1a; padding: 6px 10px; border-radius: 4px; border: 1px solid #4a382c;";
        item.innerHTML = `
            <div>
                <strong style="color: #fff8e7;">${escapeHTML(friend.identifier)}</strong>
                <div style="font-size: 10px; color: #2ecc71;">● ${escapeHTML(friend.status)}</div>
            </div>
            <button onclick="removeFriend(${index})" style="background: none; border: none; color: #e74c3c; cursor: pointer; font-size: 14px;" title="Видалити">✕</button>
        `;
        container.appendChild(item);
    });
}

function removeFriend(index) {
    friendsList.splice(index, 1);
    safeStorageSet('palata404_friends', JSON.stringify(friendsList));
    renderFriendsList();
}

// === Дані / Статистика / Персонаж ===
const DEFAULT_STATS = {
    silver: 150,
    pills: 5,
    bucks: 10,
    hp: 100,
    maxHp: 100,
    madness: 20,
    energy: 100,
    maxEnergy: 100,
    level: 1,
    exp: 0,
    nextLvlExp: 100,
    damage: 10,
    armor: 0,
    daysInClinic: 14,
    madnessAttacks: 3,
    enemiesKilled: 0,
    bossesKilled: 0,
    pillsUsed: 5,
    gymRounds: 0
};

let stats = normalizeStats(loadSaveData('palata404_stats', DEFAULT_STATS));
let lastKnownEnergy = stats.energy;
let lastKnownMadness = stats.madness;

let gender = safeStorageGet('palata404_gender') === 'female' ? 'female' : 'male';
let currentHair = safeStorageGet('palata404_hair') || '';
let currentFace = safeStorageGet('palata404_face') || '';
let currentClothes = safeStorageGet('palata404_clothes') || '';

const facesData = PAPER_DOLL_ITEMS.filter(item => item.slot === 'face').map(({ id, name }) => ({ id, name }));

const MEDICAL_ITEMS = Object.freeze({
    madness_pills: { name: 'Таблетки «Аміназин»', icon: 'pills', category: 'meds', effectType: 'madness', effectDesc: 'Знижує божевілля на 15', cost: 50, currency: 'silver' },
    stamina_10: { name: 'Енергетик', icon: 'drink', category: 'meds', effectType: 'stamina_10', effectDesc: 'Відновлює 10% витривалості', cost: 2, currency: 'bucks' },
    stamina_full: { name: 'Стимулятор', icon: 'lightning', category: 'meds', effectType: 'stamina_full', effectDesc: 'Повністю відновлює витривалість', cost: 10, currency: 'bucks' },
    hp_10: { name: 'Мала аптечка', icon: 'medkit', category: 'meds', effectType: 'hp_10', effectDesc: 'Відновлює 10% здоров’я', cost: 30, currency: 'silver' },
    hp_full: { name: 'Велика армійська аптечка', icon: 'surgery', category: 'meds', effectType: 'hp_full', effectDesc: 'Повністю відновлює здоров’я', cost: 150, currency: 'silver' }
});

const DEFAULT_INVENTORY = [
    { name: 'Іржавий ніж', icon: 'knife', count: 1, category: 'weapon', damageBonus: 8, desc: 'Саморобний ніж з обломка медичного шпателя.' },
    { name: 'ПМ (Пістолет Макарова)', icon: 'pistol', count: 1, category: 'weapon', damageBonus: 18, desc: 'Табельний пістолет охорони.' },
    { name: 'Штурмовий АКС-74У', icon: 'rifle', count: 1, category: 'weapon', damageBonus: 35, desc: 'Укорочений автомат колишньої охорони.' },
    { name: 'Побитий шолом санітара', icon: 'helmet', count: 1, category: 'helmet', armorBonus: 12, desc: 'Протиударний шолом персоналу.' },
    { name: 'Бронежилет БР-1', icon: 'shield', count: 1, category: 'armor', armorBonus: 28, desc: 'Легкий армійський бронежилет.' }
];

let inventory = loadSaveData('palata404_inventory', DEFAULT_INVENTORY);
inventory = normalizeInventory(inventory);

let equippedGear = loadSaveData('palata404_equipped', {
    weapon: null,
    helmet: null,
    armor: null
});
['weapon', 'helmet', 'armor'].forEach(slot => {
    const item = inventory.find(entry => entry.category === slot && entry.name === equippedGear[slot]);
    if (!item || item.count <= 0) equippedGear[slot] = null;
});

// Older saves contain aggregate combat stats. Separate permanent gains from gear once.
const equippedWeaponBonus = getEquippedItem('weapon')?.damageBonus || 0;
const equippedArmorBonus = (getEquippedItem('helmet')?.armorBonus || 0)
    + (getEquippedItem('armor')?.armorBonus || 0);
stats.baseDamage = Number.isSafeInteger(stats.baseDamage) && stats.baseDamage >= 0
    ? stats.baseDamage
    : Math.max(DEFAULT_STATS.damage + stats.gymRounds * 3, stats.damage - equippedWeaponBonus);
stats.baseArmor = Number.isSafeInteger(stats.baseArmor) && stats.baseArmor >= 0
    ? stats.baseArmor
    : Math.max(DEFAULT_STATS.armor, stats.armor - equippedArmorBonus);
recalculateEquipmentStats();

let paperDollState = loadPaperDollState({ gender, face: currentFace, hair: currentHair });
syncLegacyPaperDollSelection();

function normalizeInventory(items) {
    const result = [];
    items.forEach(item => {
        if (!item || typeof item !== 'object' || Array.isArray(item)
            || typeof item.name !== 'string' || !item.name.trim()) return;
        const rawCount = item.count === undefined ? 1 : Number(item.count);
        if (!Number.isSafeInteger(rawCount) || rawCount <= 0) return;
        const freshItem = DEFAULT_INVENTORY.find(entry => entry.name === item.name)
            || Object.values(MEDICAL_ITEMS).find(entry => entry.name === item.name);
        const normalized = { ...item, ...(freshItem || {}), count: rawCount };
        ['name', 'icon', 'desc', 'effectDesc', 'effectType', 'category'].forEach(field => {
            if (normalized[field] !== undefined && typeof normalized[field] !== 'string') delete normalized[field];
        });
        ['damageBonus', 'armorBonus'].forEach(field => {
            if (normalized[field] !== undefined) {
                const bonus = Number(normalized[field]);
                normalized[field] = Number.isSafeInteger(bonus) && bonus >= 0 ? bonus : 0;
            }
        });
        const existing = result.find(entry => entry.name === normalized.name && entry.category === normalized.category);
        if (existing) existing.count = Math.min(Number.MAX_SAFE_INTEGER, existing.count + normalized.count);
        else result.push(normalized);
    });
    return result;
}

function getEquippedItem(slot) {
    return inventory.find(item => item.category === slot && item.name === equippedGear[slot] && item.count > 0);
}

function recalculateEquipmentStats() {
    stats.damage = stats.baseDamage + (getEquippedItem('weapon')?.damageBonus || 0);
    stats.armor = stats.baseArmor + (getEquippedItem('helmet')?.armorBonus || 0)
        + (getEquippedItem('armor')?.armorBonus || 0);
}

let currentCategory = 'all';
let selectedItemForAction = null;

const gameFloorsData = [
    {
        id: 10,
        title: "10 Поверх — Блок Ізоляторів",
        unlocked: true,
        mapImage: "map_floor_10.png",
        nodes: [
            { id: "sec_room404", icon: "bed", title: "Палата 404", x: 38, y: 31, type: "room_404" },
            { id: "sec1_collector", icon: "gear", title: "Ординаторська", x: 38, y: 44, type: "collector" },
            { id: "sec_procedure", icon: "syringe", title: "Медпункт", x: 38, y: 62, type: "procedure", bossKey: "nurse" },
            { id: "sec2_grind", icon: "rubble", title: "Завал", x: 58, y: 50, type: "grind" },
            { id: "sec3_boss", icon: "boss", title: "Черговий лікар", x: 82, y: 44, type: "boss", bossKey: "doctor", locked: true }
        ]
    },
    {
        id: 9,
        title: "9 Поверх — Психіатрична Терапія",
        unlocked: false,
        mapImage: "",
        nodes: []
    }
];

let gameProgress = loadSaveData('palata404_progress', { rubbleCleared: false });
gameProgress = { rubbleCleared: gameProgress.rubbleCleared === true };
if (gameProgress.rubbleCleared) {
    const mainFloor = gameFloorsData.find(floor => floor.id === 10);
    const bossNode = mainFloor?.nodes.find(node => node.type === 'boss');
    if (bossNode) bossNode.locked = false;
}

function loadSaveData(key, fallback) {
    let saved;
    try {
        const pendingFields = { palata404_stats: 'stats', palata404_inventory: 'inventory', palata404_boss_kills: 'bossKills' };
        const field = pendingFields[key];
        const pendingState = pendingBattleReward?.state || pendingStaffReward?.state;
        saved = pendingState && field && pendingState[field] !== undefined
            ? JSON.stringify(pendingState[field]) : safeStorageGet(key);
    } catch (e) {
        return fallback;
    }
    if (!saved) return fallback;

    try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(fallback)) {
            return Array.isArray(parsed) ? parsed : fallback;
        }
        if (typeof fallback === 'object' && fallback !== null) {
            if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return fallback;
            return { ...fallback, ...parsed };
        }
        return parsed;
    } catch (e) {
        return fallback;
    }
}

function normalizeStats(savedStats) {
    const normalized = { ...DEFAULT_STATS };
    Object.keys(DEFAULT_STATS).forEach(key => {
        const value = savedStats?.[key];
        if (typeof value === 'number' && Number.isFinite(value) && Math.abs(value) <= Number.MAX_SAFE_INTEGER) normalized[key] = value;
    });

    const wholeNumberFields = [
        'silver', 'pills', 'bucks', 'hp', 'maxHp', 'madness', 'energy', 'maxEnergy',
        'level', 'exp', 'nextLvlExp', 'damage', 'armor', 'daysInClinic',
        'madnessAttacks', 'enemiesKilled', 'bossesKilled', 'pillsUsed', 'gymRounds'
    ];
    wholeNumberFields.forEach(key => {
        normalized[key] = Math.max(0, Math.floor(normalized[key]));
    });

    normalized.maxHp = Math.max(1, normalized.maxHp);
    normalized.maxEnergy = Math.max(1, normalized.maxEnergy);
    normalized.level = Math.max(1, normalized.level);
    normalized.nextLvlExp = Math.max(1, normalized.nextLvlExp);
    normalized.exp = Math.min(normalized.exp, normalized.nextLvlExp - 1);
    normalized.hp = Math.min(normalized.hp, normalized.maxHp);
    normalized.energy = Math.min(normalized.energy, normalized.maxEnergy);
    normalized.madness = Math.min(normalized.madness, 100);
    ['baseDamage', 'baseArmor'].forEach(key => {
        const value = savedStats?.[key];
        if (Number.isSafeInteger(value) && value >= 0) normalized[key] = value;
    });
    return normalized;
}

function saveGameProgress() {
    // Journal the entire reward state first. An interrupted write restores snapshots,
    // never re-runs experience gains or increments the boss counter.
    if (!prepareBattleRewardSave() || !prepareStaffRewardSave()) return false;
    const saved = [
        safeStorageSet('palata404_stats', JSON.stringify(stats)),
        safeStorageSet('palata404_gender', gender),
        safeStorageSet('palata404_hair', currentHair),
        safeStorageSet('palata404_face', currentFace),
        safeStorageSet('palata404_clothes', currentClothes),
        safeStorageSet('palata404_inventory', JSON.stringify(inventory)),
        safeStorageSet('palata404_equipped', JSON.stringify(equippedGear)),
        savePaperDollState(),
        safeStorageSet('palata404_room', currentRoom.id),
        safeStorageSet('palata404_progress', JSON.stringify(gameProgress)),
        safeStorageSet('palata404_boss_kills', JSON.stringify(bossKillsCount))
    ].every(Boolean);
    const staffSaved = saved && saveStaffArchiveState();
    return finishStaffRewardSave(finishBattleRewardSave(staffSaved));
}

function getPlayerRank(level) {
    if (level >= 20) return "Легенда Руїн";
    if (level >= 15) return "Ветеран";
    if (level >= 10) return "Шукач";
    if (level >= 5) return "Виживальник";
    return "Новачок";
}

function addExperience(amount, notify = true) {
    if (!Number.isSafeInteger(amount) || amount <= 0) return [];
    const reachedLevels = [];
    stats.exp += amount;
    if (!stats.nextLvlExp) stats.nextLvlExp = stats.level * 100;

    while (stats.exp >= stats.nextLvlExp) {
        stats.exp -= stats.nextLvlExp;
        stats.level += 1;
        stats.nextLvlExp = stats.level * 120;
        stats.maxHp += 5;
        const previousHp = stats.hp;
        stats.hp = stats.maxHp;
        recordPlayerRecovery(stats.hp - previousHp);
        reachedLevels.push(stats.level);
        if (notify) alert(`Вітаємо! Ви досягли ${stats.level} рівня!\nВаше звання: ${getPlayerRank(stats.level)}`);
    }
    return reachedLevels;
}

function setGender(selectedGender) {
    if (selectedGender !== 'male' && selectedGender !== 'female') return;
    paperDollState.selectedGender = selectedGender;
    const hair = PAPER_DOLL_ITEMS.find(item => item.id === paperDollState.appearance.hair);
    if (hair && !paperDollItemSupportsGender(hair, selectedGender)) paperDollState.appearance.hair = 'hair-none';
    commitPaperDollSelection();
}

function setFace(faceFileName) {
    if (!facesData.some(face => face.id === faceFileName)) return;
    equipPaperDollItem('face', faceFileName);
}

function updateCharacterLayers() {
    renderPaperDoll();
    renderPaperDollControls(false);
}

function updateUI() {
    if (lastKnownMadness < 100 && stats.madness >= 100) stats.madnessAttacks += 1;
    lastKnownMadness = stats.madness;
    const wasAtMaxEnergy = lastKnownEnergy >= stats.maxEnergy;
    const isAtMaxEnergy = stats.energy >= stats.maxEnergy;
    if (wasAtMaxEnergy !== isAtMaxEnergy) {
        energyLastTime = Date.now();
        safeStorageSet('palata404_last_time', energyLastTime.toString());
    }
    lastKnownEnergy = stats.energy;

    const hpValElem = document.getElementById('hp-val');
    if (hpValElem) hpValElem.textContent = `${stats.hp} / ${stats.maxHp}`;

    const madnessVal = document.getElementById('madness-val');
    if (madnessVal) madnessVal.textContent = `${stats.madness} / 100`;

    const energyVal = document.getElementById('energy-val');
    if (energyVal) energyVal.textContent = `${stats.energy} / ${stats.maxEnergy}`;

    const madnessBar = document.getElementById('madness-bar');
    if (madnessBar) madnessBar.style.width = `${Math.min(100, stats.madness)}%`;

    const energyBar = document.getElementById('energy-bar');
    if (energyBar) energyBar.style.width = `${Math.min(100, (stats.energy / stats.maxEnergy) * 100)}%`;

    const silverVal = document.getElementById('silver-val');
    if (silverVal) silverVal.textContent = stats.silver || 0;

    const pillsVal = document.getElementById('pills-val');
    if (pillsVal) pillsVal.textContent = stats.pills || 0;

    const bucksVal = document.getElementById('bucks-val');
    if (bucksVal) bucksVal.textContent = stats.bucks || 0;

    const damageVal = document.getElementById('damage-val');
    if (damageVal) damageVal.textContent = stats.damage;

    const armorVal = document.getElementById('armor-val');
    if (armorVal) armorVal.textContent = stats.armor || 0;

    const playerLvl = document.getElementById('player-lvl');
    if (playerLvl) playerLvl.textContent = stats.level;

    const playerRank = document.getElementById('player-rank');
    if (playerRank) playerRank.textContent = getPlayerRank(stats.level);

    const expVal = document.getElementById('exp-val');
    if (expVal) expVal.textContent = `${stats.exp} / ${stats.nextLvlExp} EXP`;

    let expPercent = (stats.exp / stats.nextLvlExp) * 100;
    const expBar = document.getElementById('exp-bar');
    if (expBar) expBar.style.width = `${Math.min(100, expPercent)}%`;

    updateCharacterLayers();
    updatePlayerNameDisplay();
    saveGameProgress();
    updateBattleMedkitCounts();
    const reportButton = document.getElementById('last-battle-result-btn');
    if (reportButton) reportButton.disabled = !lastBattleResult;
    if (isBattleActive) updateBattleUI();
    if (stats.madness >= 100) {
        closeGym();
        closeMedicalHub();
        closeProcedureRoom();
    }

    const mapBtn = document.getElementById('nav-map-btn');
    const locName = document.getElementById('current-location-name');
    const locDesc = document.getElementById('current-location-desc');
    const locTitleLabel = document.getElementById('loc-title-label');
    const locCardBox = document.getElementById('location-card-box');

    if (stats.madness >= 100) {
        if (mapBtn) mapBtn.style.display = 'flex';
        if (locTitleLabel) locTitleLabel.innerHTML = `${iconHTML("warning")} СИСТЕМНИЙ ЗБІЙ`;
        if (locName) locName.textContent = "ПОМИЛКА 404: Невідомо";
        if (locDesc) locDesc.textContent = "Реальність втрачено. Спокійний корпус недоступний...";
        if (locCardBox) locCardBox.style.borderColor = "#c0392b";
    } else {
        if (mapBtn) mapBtn.style.display = 'none';
        if (locTitleLabel) locTitleLabel.textContent = "Поточна локація";
        if (locName) locName.textContent = currentRoom.name || "Палата #404";
        if (locDesc) locDesc.textContent = currentRoom.desc || "Твоє безпечне місце.";
        if (locCardBox) locCardBox.style.borderColor = "#3d2d22";
    }
}

// === КАРТА ТА МАРШРУТИ ===
function toggleMapModal(show) {
    const modal = document.getElementById('map-modal');
    if (!modal) return;
    if (show) {
        closeOtherModals(['map-modal']);
        modal.classList.remove('hidden');
        showFloorsList();
    } else {
        modal.classList.add('hidden');
    }
}

function showFloorsList() {
    document.getElementById('map-floors-view').classList.remove('hidden');
    document.getElementById('map-single-floor-view').classList.add('hidden');
    document.getElementById('map-title-text').innerText = "СПИСОК ПОВЕРХІВ";

    const container = document.getElementById('floors-list-container');
    if (!container) return;
    container.innerHTML = '';

    gameFloorsData.forEach(floor => {
        const item = document.createElement('div');
        item.className = `floor-card-item ${floor.unlocked ? '' : 'locked-floor'}`;
        item.innerHTML = `
            <div>
                <strong>${floor.title}</strong>
                <div style="font-size: 11px; color: #8c7a6b; margin-top: 2px;">
                    ${floor.unlocked ? 'План евакуації знайдено' : 'План відсутній'}
                </div>
            </div>
            <span>${iconHTML(floor.unlocked ? 'map' : 'lock')} ${floor.unlocked ? 'Відкрити' : 'Зачинено'}</span>
        `;

        if (floor.unlocked) {
            item.onclick = () => openFloorMap(floor.id);
        }
        container.appendChild(item);
    });
}

function openFloorMap(floorId) {
    const floor = gameFloorsData.find(f => f.id === floorId);
    if (!floor || !floor.unlocked) return;

    document.getElementById('map-floors-view').classList.add('hidden');
    document.getElementById('map-single-floor-view').classList.remove('hidden');
    document.getElementById('map-title-text').innerText = floor.title;

    document.getElementById('blueprint-img').src = floor.mapImage;

    const nodesLayer = document.getElementById('blueprint-nodes-container');
    if (!nodesLayer) return;
    nodesLayer.innerHTML = '';

    floor.nodes.forEach(node => {
        const btn = document.createElement('button');
        btn.className = `map-node-pin ${node.type === 'boss' ? 'node-boss' : ''} ${node.locked ? 'node-locked' : ''}`;
        btn.innerHTML = `${iconHTML(node.icon)} ${escapeHTML(node.title)}`;
        btn.style.left = `${node.x}%`;
        btn.style.top = `${node.y}%`;

        btn.onclick = () => {
            if (node.locked) {
                alert("Цей сектор заблоковано! Спочатку розчистіть завал у коридорі.");
            } else {
                handleNodeClick(node, floor);
            }
        };

        nodesLayer.appendChild(btn);
    });
}

function handleNodeClick(node, floor) {
    if (node.type === 'room_404') {
        alert("Палата #404. Твоє безпечне місце.");
    } else if (node.type === 'procedure') {
        openBossDossier(node.bossKey || 'nurse');
    } else if (node.type === 'collector') {
        alert("Автономний Збирач #1 працює!\nЗібрано луту: +15 Срібла, +1 Пігулка.");
        stats.silver += 15;
        stats.pills += 1;
        updateUI();
    } else if (node.type === 'grind') {
        updateEnergyTimer();
        if (gameProgress.rubbleCleared) {
            showCustomToast("Завал уже розчищено.");
            return;
        }
        if (stats.energy >= 10) {
            stats.energy -= 10;
            alert("Ви розчистили завал у коридорі! Отримано 30 EXP та відкрито шлях до Боса!");
            addExperience(30);

            gameProgress.rubbleCleared = true;
            grantStaffQuestMilestones();
            const bossNode = floor.nodes.find(n => n.type === 'boss');
            if (bossNode) bossNode.locked = false;

            openFloorMap(floor.id);
            updateUI();
        } else {
            alert("Недостатньо витривалості для розчищення завалу!");
        }
    } else if (node.type === 'boss') {
        if (node.bossKey) {
            openBossDossier(node.bossKey);
        }
    }
}

function openSettings() {
    closeOtherModals(['settings-modal']);
    closeInventory();
    closeCustomization();
    closeFriends();
    closeDossier();
    const modal = document.getElementById('settings-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeSettings() {
    const modal = document.getElementById('settings-modal');
    if (modal) modal.classList.add('hidden');
}

function openBank() {
    closeOtherModals(['bank-modal']);
    const modal = document.getElementById('bank-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeBank() {
    const modal = document.getElementById('bank-modal');
    if (modal) modal.classList.add('hidden');
}

function openInventory() {
    closeOtherModals(['inventory-modal']);
    closeCustomization();
    closeFriends();
    closeDossier();
    renderMinecraftStash();
    const modal = document.getElementById('inventory-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeInventory() {
    closeItemInfo();
    const modal = document.getElementById('inventory-modal');
    if (modal) modal.classList.add('hidden');
}

function setCategoryFilter(category, btnElem) {
    currentCategory = category;
    if (btnElem && btnElem.parentElement) {
        btnElem.parentElement.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        btnElem.classList.add('active');
    }
    renderMinecraftStash();
}

function renderMinecraftStash() {
    const container = document.getElementById('stash-items');
    if (!container) return;
    container.innerHTML = '';

    const filteredItems = currentCategory === 'all'
        ? inventory
        : inventory.filter(item => item.category === currentCategory);

    const TOTAL_SLOTS = Math.max(20, Math.ceil(filteredItems.length / 5) * 5);
    for (let i = 0; i < TOTAL_SLOTS; i++) {
        let slot = document.createElement('div');
        slot.className = 'mc-slot';

        if (filteredItems[i]) {
            let item = filteredItems[i];

            const isEquipped = (
                (item.category === 'weapon' && equippedGear.weapon === item.name) ||
                (item.category === 'helmet' && equippedGear.helmet === item.name) ||
                (item.category === 'armor' && equippedGear.armor === item.name)
            );

            slot.innerHTML = `
                <span class="item-icon">${iconHTML(item.icon)}</span>
                ${item.count > 1 ? `<span class="item-count">${item.count}</span>` : ''}
                ${isEquipped ? `<span style="position: absolute; top: 2px; left: 2px; font-size: 8px; background: #e74c3c; color: #fff; padding: 1px 3px; border-radius: 3px;">EQ</span>` : ''}
            `;
            slot.setAttribute('role', 'button');
            slot.tabIndex = 0;
            slot.setAttribute('aria-label', item.name);
            slot.onclick = () => openItemInfo(item);
        }
        container.appendChild(slot);
    }
}

function openItemInfo(item) {
    selectedItemForAction = item;
    const titleElem = document.getElementById('item-info-title');
    if (titleElem) titleElem.innerHTML = `${iconHTML(item.icon)} ${escapeHTML(item.name)}`;

    let bodyHtml = `<p style="color: #a3927d;">${escapeHTML(item.desc || 'Немає опису предмета.')}</p>`;

    const isEquipped = (
        (item.category === 'weapon' && equippedGear.weapon === item.name) ||
        (item.category === 'helmet' && equippedGear.helmet === item.name) ||
        (item.category === 'armor' && equippedGear.armor === item.name)
    );

    const actionBtn = document.getElementById('item-action-btn');

    if (item.category === 'weapon') {
        bodyHtml += `<div style="color: #e74c3c; margin-top: 5px;"><strong>${iconHTML('swords')} Бонус до урону:</strong> +${escapeHTML(item.damageBonus || 0)}</div>`;
        if (actionBtn) actionBtn.textContent = isEquipped ? "Зняти" : "Озброїтися";
    } else if (item.category === 'armor' || item.category === 'helmet') {
        bodyHtml += `<div style="color: #3498db; margin-top: 5px;"><strong>${iconHTML('shield')} Бонус до броні:</strong> +${escapeHTML(item.armorBonus || 0)}</div>`;
        if (actionBtn) actionBtn.textContent = isEquipped ? "Зняти" : "Надіти спорядження";
    } else if (item.category === 'meds') {
        bodyHtml += `<div style="color: #2ecc71; margin-top: 5px;"><strong>${iconHTML('lightning')} Ефект препарату:</strong> ${escapeHTML(item.effectDesc || 'Відновлює стан')}</div>`;
        if (actionBtn) actionBtn.textContent = "Використати";
    } else {
        if (actionBtn) actionBtn.textContent = "Закрити";
    }

    const bodyElem = document.getElementById('item-info-body');
    if (bodyElem) bodyElem.innerHTML = bodyHtml;

    const infoModal = document.getElementById('item-info-modal');
    if (infoModal) infoModal.classList.remove('hidden');
}

function closeItemInfo() {
    const modal = document.getElementById('item-info-modal');
    if (modal) modal.classList.add('hidden');
    selectedItemForAction = null;
}

document.addEventListener('DOMContentLoaded', () => {
    updatePlayerNameDisplay();
    updateEnergyTimer();
    updateUI();
    initializeModalControls();
    autoScaleBattleArena();
    const blueprint = document.getElementById('blueprint-img');
    const updateMapAspectRatio = () => {
        if (blueprint?.naturalWidth && blueprint.naturalHeight) {
            blueprint.parentElement.style.setProperty('--map-aspect-ratio', String(blueprint.naturalWidth / blueprint.naturalHeight));
        }
    };
    blueprint?.addEventListener('load', updateMapAspectRatio);
    updateMapAspectRatio();
    if (new URLSearchParams(window.location.search).get('dev') === '1') {
        document.getElementById('developer-tools')?.classList.remove('hidden');
    }

    const actionBtn = document.getElementById('item-action-btn');
    if (actionBtn) {
        actionBtn.onclick = () => {
            if (!selectedItemForAction) {
                closeItemInfo();
                return;
            }

            const cat = selectedItemForAction.category;

            if (!inventory.includes(selectedItemForAction) || selectedItemForAction.count <= 0) {
                closeItemInfo();
                return;
            }
            if (['weapon', 'helmet', 'armor'].includes(cat)) {
                equippedGear[cat] = equippedGear[cat] === selectedItemForAction.name
                    ? null : selectedItemForAction.name;
                recalculateEquipmentStats();
            } else if (cat === 'meds') {
                consumeMedicalItem(selectedItemForAction);
            }

            safeStorageSet('palata404_equipped', JSON.stringify(equippedGear));
            updateUI();
            closeItemInfo();
            renderMinecraftStash();
        };
    }
});

function openCustomization() {
    closeOtherModals(['custom-modal']);
    closeInventory();
    closeFriends();
    closeDossier();
    renderWardrobe();
    const modal = document.getElementById('custom-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeCustomization() {
    const modal = document.getElementById('custom-modal');
    if (modal) modal.classList.add('hidden');
}

function setWardrobeTab(tab) {
    const aliases = { body: ['appearance','baseBody'], face: ['appearance','face'], hair: ['hair','hair'], clothes: ['clothes','upperBody'] };
    if (!aliases[tab]) return;
    [wardrobeCategory, wardrobeSlot] = aliases[tab];
    renderWardrobe();
}

function renderWardrobe() {
    renderWardrobeUI();
}

// === Спортзал та збереження прогресу ===
const DEFAULT_GYM_EXERCISES = [
    { id: 'squats', name: 'Присідання', icon: 'squats', current: 0, target: 15, energy: 2, madness: 1, exp: 5 },
    { id: 'pushups', name: 'Віджимання', icon: 'pushups', current: 0, target: 12, energy: 3, madness: 2, exp: 8 },
    { id: 'plank', name: 'Планка', icon: 'plank', current: 0, target: 10, energy: 4, madness: 2, exp: 10 },
    { id: 'pullups', name: 'Підтягування', icon: 'pullups', current: 0, target: 8, energy: 5, madness: 3, exp: 14 },
    { id: 'stretching', name: 'Розтяжка', icon: 'stretch', current: 0, target: 10, energy: 2, madness: 1, exp: 6 },
    { id: 'shadowbox', name: 'Бій з тінню', icon: 'boxing', current: 0, target: 5, energy: 6, madness: 5, exp: 20 }
];

let gymComplex = loadSaveData('palata404_gym', {
    exercises: DEFAULT_GYM_EXERCISES,
    completedRounds: 0
});
const savedGymExercises = Array.isArray(gymComplex.exercises) ? gymComplex.exercises : [];
gymComplex.exercises = DEFAULT_GYM_EXERCISES.map(defaultExercise => {
    const savedExercise = savedGymExercises.find(exercise => exercise && typeof exercise === 'object'
        && exercise.id === defaultExercise.id);
    const rawCurrent = savedExercise?.current;
    const current = typeof rawCurrent === 'number' && Number.isFinite(rawCurrent)
        ? Math.min(defaultExercise.target, Math.max(0, Math.floor(rawCurrent)))
        : defaultExercise.current;
    return { ...defaultExercise, current };
});
gymComplex.completedRounds = typeof gymComplex.completedRounds === 'number'
    && Number.isSafeInteger(gymComplex.completedRounds)
    ? Math.max(0, Math.floor(gymComplex.completedRounds))
    : 0;
// Older versions recorded rounds in the gym save but not in the personal dossier.
gymComplex.completedRounds = Math.max(gymComplex.completedRounds, stats.gymRounds);
stats.gymRounds = gymComplex.completedRounds;
stats.baseDamage = Math.max(stats.baseDamage, DEFAULT_STATS.damage + stats.gymRounds * 3);
recalculateEquipmentStats();

function saveGymProgress() {
    safeStorageSet('palata404_gym', JSON.stringify(gymComplex));
}

function openGym() {
    if (stats.madness >= 100) {
        showCustomToast('Ця локація недоступна у стані психозу.');
        return;
    }
    closeOtherModals(['gym-modal']);
    closeInventory();
    closeCustomization();
    closeFriends();
    closeSettings();
    closeDossier();
    closeMedicalHub();
    renderGymModal();
    const modal = document.getElementById('gym-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeGym() {
    const modal = document.getElementById('gym-modal');
    if (modal) modal.classList.add('hidden');
}

function doGymExercise(exId) {
    if (stats.madness >= 100) {
        showCustomToast('❌ Тренування неможливі в стані повного психозу!');
        closeGym();
        return;
    }
    updateEnergyTimer();
    let ex = gymComplex.exercises.find(e => e.id === exId);
    if (!ex) {
        console.error("Вправу не знайдено:", exId);
        return;
    }
    if (ex.current >= ex.target) {
        showCustomToast("⚠️ Цю вправу вже виконано в цьому комплексі!");
        return;
    }
    if (stats.energy < ex.energy) {
        showCustomToast("⚡ Недостатньо витривалості для цієї вправи!");
        return;
    }

    stats.energy -= ex.energy;
    stats.madness = Math.min(100, stats.madness + ex.madness);
    ex.current += 1;
    addExperience(ex.exp);

    let allDone = gymComplex.exercises.every(e => e.current >= e.target);
    if (allDone) {
        gymComplex.completedRounds += 1;
        stats.gymRounds = (stats.gymRounds || 0) + 1;
        stats.baseDamage += 3;
        recalculateEquipmentStats();
        addExperience(100);
        showCustomToast("🏆 ВЕЛИКИЙ БАФ! Урон збільшено на +3!");
        gymComplex.exercises.forEach(e => e.current = 0);
    }

    saveGymProgress();
    updateUI();
    renderGymModal();
}

function renderGymModal() {
    const container = document.getElementById('gym-exercises-list');
    if (!container) return;
    container.innerHTML = '';

    gymComplex.exercises.forEach(ex => {
        let isDone = ex.current >= ex.target;
        let item = document.createElement('div');
        item.style.cssText = `
            display: flex; justify-content: space-between; align-items: center;
            background: ${isDone ? 'rgba(39, 174, 96, 0.08)' : 'rgba(30, 23, 18, 0.85)'};
            padding: 10px 14px; border-radius: 8px;
            border: 1px solid ${isDone ? 'rgba(39, 174, 96, 0.4)' : '#3d2d22'};
        `;
        item.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 24px; background: rgba(0,0,0,0.3); padding: 6px; border-radius: 6px; border: 1px solid #3d2d22;">${iconHTML(ex.icon, 'large')}</span>
                <div>
                    <strong style="color: ${isDone ? '#2ecc71' : '#fff8e7'}; font-size: 14px;">${ex.name} ${isDone ? '✓' : ''}</strong>
                    <div style="font-size: 11px; color: ${isDone ? '#27ae60' : '#a3927d'}; margin-top: 2px;">Прогрес: ${ex.current} / ${ex.target}</div>
                </div>
            </div>
            <button class="btn-outfit" onclick="doGymExercise('${ex.id}')" ${isDone ? 'disabled style="background: rgba(39, 174, 96, 0.2); border-color: #27ae60; color: #2ecc71; opacity: 0.7; cursor: default;"' : 'style="background: #594333; border-color: #8c684d; padding: 6px 14px; font-weight: bold;"'}>${isDone ? 'Виконано' : 'Робити'}</button>
        `;
        container.appendChild(item);
    });
}
// === Лікувальний корпус ===
let currentRoom = { id: 'room_404', name: 'Палата #404', desc: 'Стіни шепочуть тобі...' };
const medicalRooms = [
    { id: 'room_404', name: 'Палата #404', icon: 'bed', desc: 'Твоя власна палата.' },
    { id: 'gym', name: 'Зал реабілітації', icon: 'dumbbell', desc: 'Спортзал для вправ.' },
    { id: 'treatment_room', name: 'Процедурний кабінет', icon: 'syringe', desc: 'Видача ліків.' },
    { id: 'corridor', name: 'Коридор блоку', icon: 'door', desc: 'Вихід у коридор.' }
];

const savedRoomId = safeStorageGet('palata404_room');
currentRoom = medicalRooms.find(room => room.id === savedRoomId) || medicalRooms[0];

function openMedicalHub() {
    if (stats.madness >= 100) {
        showCustomToast('Ця локація недоступна у стані психозу.');
        return;
    }
    closeOtherModals(['medical-hub-modal']);
    closeInventory();
    closeCustomization();
    closeFriends();
    closeSettings();
    closeGym();
    closeProcedureRoom();
    renderMedicalRooms();
    document.getElementById('medical-hub-modal').classList.remove('hidden');
}

function closeMedicalHub() {
    document.getElementById('medical-hub-modal').classList.add('hidden');
}

function openProcedureRoom() {
    if (stats.madness >= 100) {
        showCustomToast('Ця локація недоступна у стані психозу.');
        return;
    }
    closeOtherModals(['procedure-room-modal']);
    currentRoom = medicalRooms.find(room => room.id === 'treatment_room');
    updateUI();
    closeMedicalHub();
    document.getElementById('procedure-room-modal').classList.remove('hidden');
}

function closeProcedureRoom() {
    document.getElementById('procedure-room-modal').classList.add('hidden');
}

function renderMedicalRooms() {
    const container = document.getElementById('rooms-list-container');
    if (!container) return;
    container.innerHTML = '';

    medicalRooms.forEach(room => {
        let isCurrent = currentRoom.id === room.id;
        let item = document.createElement('div');
        item.style.cssText = `
            display: flex; justify-content: space-between; align-items: center;
            background: ${isCurrent ? 'rgba(89, 67, 51, 0.35)' : 'rgba(30, 23, 18, 0.85)'};
            padding: 10px 14px; border-radius: 8px;
            border: 1px solid ${isCurrent ? '#8c684d' : '#3d2d22'};
            transition: all 0.2s ease;
        `;
        let btnHtml = room.id === 'treatment_room'
            ? `<button class="btn-outfit" style="background: #594333; border-color: #8c684d; padding: 6px 14px; font-weight: bold;" onclick="openProcedureRoom()">Відкрити</button>`
            : `<button class="btn-outfit" style="background: ${isCurrent ? '#2c221e' : '#594333'}; border-color: ${isCurrent ? '#4a382c' : '#8c684d'}; padding: 6px 14px; font-weight: bold; ${isCurrent ? 'opacity: 0.6; cursor: default;' : ''}" onclick="selectRoom('${room.id}')" ${isCurrent ? 'disabled' : ''}>${isCurrent ? 'Ви тут' : 'Перейти'}</button>`;

        item.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 24px; background: rgba(0,0,0,0.3); padding: 6px; border-radius: 6px; border: 1px solid #3d2d22;">${iconHTML(room.icon, 'large')}</span>
                <div>
                    <strong style="color: ${isCurrent ? '#f39c12' : '#fff8e7'}; font-size: 14px;">${room.name}</strong>
                    <div style="font-size: 11px; color: #a3927d; margin-top: 2px;">${room.desc}</div>
                </div>
            </div>
            ${btnHtml}
        `;
        container.appendChild(item);
    });
}

function selectRoom(roomId) {
    if (stats.madness >= 100) return;
    let room = medicalRooms.find(r => r.id === roomId);
    if (!room) return;
    currentRoom = room;
    closeMedicalHub();
    updateUI();
    if (roomId === 'gym') openGym();
    if (roomId === 'treatment_room') openProcedureRoom();
}

function buyMedicalItem(itemType, cost, currencyType) {
    const newItem = Object.prototype.hasOwnProperty.call(MEDICAL_ITEMS, itemType) ? MEDICAL_ITEMS[itemType] : null;
    if (!newItem || (cost !== undefined && Number(cost) !== newItem.cost)
        || (currencyType !== undefined && currencyType !== newItem.currency)) {
        console.error('Некоректні параметри покупки:', itemType, cost, currencyType);
        return;
    }
    if (stats.madness >= 100) {
        showCustomToast('Процедурний кабінет недоступний у стані психозу.');
        return;
    }
    if (stats[newItem.currency] < newItem.cost) {
        alert(newItem.currency === 'silver' ? 'Мало срібла!' : 'Мало баксів!');
        return;
    }
    stats[newItem.currency] -= newItem.cost;
    const existingItem = inventory.find(item => item.name === newItem.name && item.category === 'meds');
    if (existingItem) existingItem.count += 1;
    else inventory.push({ ...newItem, count: 1 });
    updateUI();
    renderMinecraftStash();
}

function consumeMedicalItem(item) {
    if (!item || !inventory.includes(item) || item.category !== 'meds' || item.count <= 0) return false;
    const previousHp = stats.hp;
    let changed = false;
    switch (item.effectType) {
        case 'madness':
            changed = stats.madness > 0;
            stats.madness = Math.max(0, stats.madness - 15);
            if (changed) stats.pillsUsed += 1;
            break;
        case 'stamina_10':
        case 'stamina_full':
            updateEnergyTimer();
            changed = stats.energy < stats.maxEnergy;
            stats.energy = item.effectType === 'stamina_full' ? stats.maxEnergy
                : Math.min(stats.maxEnergy, stats.energy + Math.max(1, Math.ceil(stats.maxEnergy * 0.1)));
            break;
        case 'hp_10':
        case 'hp_full':
            changed = stats.hp < stats.maxHp;
            stats.hp = item.effectType === 'hp_full' ? stats.maxHp
                : Math.min(stats.maxHp, stats.hp + Math.max(1, Math.ceil(stats.maxHp * 0.1)));
            break;
        default:
            showCustomToast('Невідомий ефект препарату.');
            return false;
    }
    if (!changed) {
        showCustomToast('Ця характеристика вже повністю відновлена.');
        return false;
    }
    item.count -= 1;
    if (item.count <= 0) inventory = inventory.filter(entry => entry !== item);
    recordPlayerRecovery(stats.hp - previousHp, true);
    return true;
}

const ENERGY_REGEN_TIME_MS = 2 * 60 * 1000;
if (stats.energy >= stats.maxEnergy) {
    safeStorageSet('palata404_last_time', Date.now().toString());
}
let energyLastTime = Number(safeStorageGet('palata404_last_time'));
if (!Number.isFinite(energyLastTime) || energyLastTime <= 0 || energyLastTime > Date.now()) {
    energyLastTime = Date.now();
    safeStorageSet('palata404_last_time', energyLastTime.toString());
}

function updateEnergyTimer() {
    const timerElem = document.getElementById('energy-timer');

    const now = Date.now();
    let lastTime = energyLastTime;

    if (stats.energy >= stats.maxEnergy) {
        if (timerElem) timerElem.textContent = '';
        return;
    }

    if (lastTime > now) {
        lastTime = now;
        energyLastTime = now;
        safeStorageSet('palata404_last_time', now.toString());
    }
    const elapsed = Math.max(0, now - lastTime);
    const recovered = Math.floor(elapsed / ENERGY_REGEN_TIME_MS);
    if (recovered > 0) {
        stats.energy = Math.min(stats.maxEnergy, stats.energy + recovered);
        lastTime += recovered * ENERGY_REGEN_TIME_MS;
        if (stats.energy >= stats.maxEnergy) lastTime = now;
        energyLastTime = lastTime;
        safeStorageSet('palata404_last_time', lastTime.toString());
        updateUI();
    }

    if (stats.energy >= stats.maxEnergy) {
        if (timerElem) timerElem.textContent = '';
        return;
    }

    const remaining = Math.max(0, ENERGY_REGEN_TIME_MS - (now - lastTime));
    const minutes = Math.floor(remaining / 60000);
    const seconds = Math.floor((remaining % 60000) / 1000);
    if (timerElem) timerElem.textContent = `+1 через ${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}
setInterval(updateEnergyTimer, 1000);

function openDossier() {
    closeOtherModals(['dossier-modal']);
    closeInventory();
    closeCustomization();
    closeSettings();
    closeFriends();
    closeGym();
    closeMedicalHub();
    closeProcedureRoom();
    const fields = {
        'dossier-name': playerName, 'dossier-rank': getPlayerRank(stats.level),
        'dossier-lvl': stats.level, 'dossier-days': stats.daysInClinic,
        'dossier-madness-attacks': stats.madnessAttacks, 'dossier-enemies-killed': stats.enemiesKilled,
        'dossier-bosses-killed': stats.bossesKilled, 'dossier-pills-used': stats.pillsUsed,
        'dossier-gym-rounds': stats.gymRounds
    };
    Object.entries(fields).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    });
    document.getElementById('dossier-modal').classList.remove('hidden');
}

function closeDossier() {
    document.getElementById('dossier-modal').classList.add('hidden');
}

function handleLocationClick() {
    if (stats.madness >= 100) toggleMapModal(true);
    else openMedicalHub();
}


// ==========================================
// УНІВЕРСАЛЬНА БАЗА ДАНИХ БОСІВ (СКАЛЬОВАНА АРХІТЕКТУРА)
// ==========================================

const bossesDatabase = {
    nurse: {
        key: 'nurse',
        floorId: 10,
        name: "Сестра Клара «Шприц»",
        hp: 120,
        damage: 12,
        expReward: 50,
        silverReward: 30,
        sprite: "nurse_sprite.png",
        bg: "nurse_bg.jpg",
        avatar: "nurse_avatar_battle.png",
        staffArchive: STAFF_ARCHIVE_CASES.nurse,
        victoryReport: {
            caseCode: '404-KL', status: 'Об’єкт тимчасово стабілізовано',
            conclusion: 'Повторну аномальну активність об’єкта тимчасово припинено. Документальні підтвердження остаточної нейтралізації відсутні.'
        },
        questItem: { name: 'Ключ від блоку боса', icon: 'key', category: 'quest', desc: 'Відкриває заблоковані двері спецблоку.' },
        dossier: {
            code: "001",
            threat: "ЗАГРОЗА: ВИСОКА",
            callsign: "«ПРОЦЕДУРНА»",
            cardImg: "nurse_dossier_card.png",
            role: "Старша медсестра",
            status: "Патологічна агресія",
            location: "Процедурний блок, 10-й поверх",
            deviations: "Після катастрофи втратила розум. Демонструє ендогенний галюцинаторно-параноїдний синдром.",
            rewardsText: "+50 EXP • +30 Срібла • Ключ від блоку боса"
        }
    },
    doctor: {
        key: 'doctor',
        floorId: 10,
        name: "Черговий лікар",
        hp: 250,
        damage: 25,
        expReward: 120,
        silverReward: 80,
        sprite: "doctor_sprite.png",
        bg: "doctor_bg.jpg",
        avatar: "doctor_avatar_battle.jpg",
        staffArchive: STAFF_ARCHIVE_CASES.doctor,
        victoryReport: {
            caseCode: '404-IZ', status: 'Об’єкт тимчасово стабілізовано',
            conclusion: 'Контроль об’єкта над ізоляційним блоком тимчасово порушено. Стан запірних механізмів потребує повторної перевірки.'
        },
        questItem: { name: 'Ключ від ізолятора', icon: 'key', category: 'quest', desc: 'Відкриває вихід із 10 поверху.' },
        dossier: {
            code: "002",
            threat: "ЗАГРОЗА: КРИТИЧНА",
            callsign: "«НАБЛЮДАЧ»",
            cardImg: "doctor_dossier_card.png",
            role: "Старший черговий лікар",
            status: "Зв'язок втрачено / Аномальні прояви не підтверджено",
            location: "Кабінет спостереження, 10-й поверх",
            deviations: "Свідки суперечливо описують кількість і рухи кінцівок. Природу цих проявів не встановлено; незалежної перевірки немає.",
            rewardsText: "+120 EXP • +80 Срібла • Ключ від ізолятора"
        }
    }
};

// Saved/legacy IDs must resolve only to actual catalog entries, never Object.prototype.
function getBossDefinition(key) {
    return typeof key === 'string' && Object.hasOwn(bossesDatabase, key) ? bossesDatabase[key] : null;
}

let currentBossKey = 'nurse';
let bossCurrentHp = 120;
let bossMaxHp = 120;
let bossKillsCount = loadSaveData('palata404_boss_kills', {});
Object.keys(bossesDatabase).forEach(key => {
    const count = bossKillsCount[key];
    bossKillsCount[key] = Number.isSafeInteger(count) && count >= 0 ? count : 0;
});

let isBattleActive = false;
let raidTimeRemaining = 300;
let raidTimerInterval = null;
let playerAttackCooldown = false;
let friendAttackInterval = null;
let attackCooldownTimeout = null;
let bossCounterTimeout = null;
let attackCooldownEndsAt = 0;
let raidEndsAt = 0;
let battleGeneration = 0;
let toastFadeTimeout = null;
let toastHideTimeout = null;

let raidMembers = [
    { id: 'player', name: 'Пацієнт #404', damage: 0, isPlayer: true, active: true },
    { id: 'friend_1', name: 'Сліпий Микола', damage: 0, active: false, called: false },
    { id: 'friend_2', name: 'Мері', damage: 0, active: false, called: false },
    { id: 'friend_3', name: 'Буйний сусіда', damage: 0, active: false, called: false }
];

lastBattleResult = normalizeBattleResult(pendingBattleReward?.result || loadSaveData('palata404_last_battle_result', null));
if (!ownsBattleResult(lastBattleResult)) lastBattleResult = null;
battleResultPersisted = Boolean(lastBattleResult && !pendingBattleReward);
restoreStaffEncountersFromHistory();

function openProcedureRoomBattle() {
    if (stats.madness < 100) {
        alert("У нормальному стані процедурний кабінет зачинений.");
        return;
    }
    openBossDossier('nurse');
}
function openNurseDossier() {
    if (typeof openBossDossier === 'function') {
        openBossDossier('nurse');
    }
}
function closeNurseDossier() {
    const modal = document.getElementById('nurse-dossier-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}
function openDoctorDossier() {
    openBossDossier('doctor');
}

function closeDoctorDossier() {
    const modal = document.getElementById('doctor-dossier-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// === УНІВЕРСАЛЬНИЙ ЗАПУСК БОЮ ===
function stopBattleTimers() {
    clearInterval(raidTimerInterval);
    clearInterval(friendAttackInterval);
    clearTimeout(attackCooldownTimeout);
    clearTimeout(bossCounterTimeout);
    raidTimerInterval = null;
    friendAttackInterval = null;
    attackCooldownTimeout = null;
    bossCounterTimeout = null;
    playerAttackCooldown = false;
    attackCooldownEndsAt = 0;
    raidEndsAt = 0;
    battleGeneration += 1;
}

function startBossFight(bossKey) {
    const boss = getBossDefinition(bossKey);
    if (!boss) return;

    if (isBattleActive) {
        closeNurseDossier();
        closeDoctorDossier();
        closeUniversalDossier();
        toggleMapModal(false);
        reopenNurseBattle();
        return;
    }

    closeNurseDossier();
    closeDoctorDossier();
    closeUniversalDossier();
    toggleMapModal(false);

    closeOtherModals(['nurse-battle-modal']);
    currentBossKey = bossKey;
    bossCurrentHp = boss.hp;
    bossMaxHp = boss.hp;

    // Динамическая подгрузка картинки, фона, имени и аватарки босса
    const spriteElem = document.getElementById('nurse-boss-sprite');
    if (spriteElem) spriteElem.src = boss.sprite;

    const arenaElem = document.getElementById('battle-arena-screen');
    if (arenaElem) arenaElem.style.backgroundImage = `url('${boss.bg}')`;

    const nameElem = document.getElementById('battle-boss-name');
    if (nameElem) nameElem.textContent = boss.name;

    const avatarElem = document.getElementById('battle-boss-avatar');
    if (avatarElem) {
        avatarElem.src = boss.avatar;
        avatarElem.alt = boss.name;
    }

    stats.hp = stats.maxHp;
    updateUI();

    playerAttackCooldown = false;
    isBattleActive = true;
    raidTimeRemaining = 300;

    raidMembers.forEach(m => {
        m.damage = 0;
        if (m.isPlayer) {
            m.name = playerName;
            m.active = true;
        } else {
            m.active = false;
            m.called = false;
        }
    });
    beginBattleMetrics(bossKey);
    encounterStaffBoss(bossKey);

    updateBattleUI();
    const battleModal = document.getElementById('nurse-battle-modal');
    if (battleModal) {
        battleModal.classList.remove('hidden');
        battleModal.style.display = 'flex';
    }

    stopBattleTimers();
    raidEndsAt = Date.now() + 300 * 1000;
    updateRaidTimerTick();
    autoScaleBattleArena();
    raidTimerInterval = setInterval(updateRaidTimerTick, 1000);
    friendAttackInterval = setInterval(friendsAutoAttackTick, 3500);

    updateLobbyRaidWidget();
}

// Сумісність зі старими викликами
function startNurseFight() { startBossFight('nurse'); }
function startDoctorFight() { startBossFight('doctor'); }

function closeNurseBattle() {
    closeFriendInviteModal();
    const modal = document.getElementById('nurse-battle-modal');
    if (modal) {
        modal.classList.add('hidden');
        modal.style.display = 'none';
    }
    document.getElementById('battle-raid-panel')?.classList.add('hidden');
    updateLobbyRaidWidget();
}

function minimizeNurseBattle() { closeNurseBattle(); }

function reopenNurseBattle() {
    if (!isBattleActive) return;
    updateRaidTimerTick();
    if (!isBattleActive) return;
    closeOtherModals(['nurse-battle-modal']);
    autoScaleBattleArena();
    updateBattleUI();
    const modal = document.getElementById('nurse-battle-modal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
    }
}

function updateRaidTimerTick() {
    if (!isBattleActive) return;
    raidTimeRemaining = Math.max(0, Math.ceil((raidEndsAt - Date.now()) / 1000));
    const mins = Math.floor(raidTimeRemaining / 60);
    const secs = raidTimeRemaining % 60;
    const timeStr = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    const timerElem = document.getElementById('battle-timer-display');
    if (timerElem) timerElem.textContent = timeStr;
    updateLobbyRaidWidget(timeStr);
    if (raidTimeRemaining <= 0) handleRaidTimeOut();
}

function updateLobbyRaidWidget(timeStr = '') {
    const raidBtn = document.getElementById('nav-raid-btn');
    if (!raidBtn) return;
    let subTimer = document.getElementById('lobby-raid-subtimer');

    if (isBattleActive) {
        raidBtn.style.borderColor = '#e74c3c';
        raidBtn.style.background = 'rgba(192, 57, 43, 0.3)';
        if (!subTimer) {
            subTimer = document.createElement('div');
            subTimer.id = 'lobby-raid-subtimer';
            raidBtn.appendChild(subTimer);
        }
        subTimer.textContent = timeStr || `${String(Math.floor(raidTimeRemaining / 60)).padStart(2, '0')}:${String(raidTimeRemaining % 60).padStart(2, '0')}`;
        raidBtn.onclick = reopenNurseBattle;
    } else {
        raidBtn.style.borderColor = '';
        raidBtn.style.background = '';
        if (subTimer) subTimer.remove();
        raidBtn.onclick = handleRaidButtonAction;
    }
}

function handleRaidTimeOut() {
    if (!isBattleActive) return;
    recordUnrewardedRaid('timeout');
    isBattleActive = false;
    stopBattleTimers();
    closeNurseBattle();
    closeFriendInviteModal();
    alert("Час рейду вичерпано!");
    updateLobbyRaidWidget();
}

function showCustomToast(msg) {
    const toast = document.getElementById('custom-toast-notification');
    const msgElem = document.getElementById('toast-message');
    if (!toast || !msgElem) return;
    clearTimeout(toastFadeTimeout);
    clearTimeout(toastHideTimeout);
    const message = String(msg ?? '');
    const prefix = Object.keys(LEGACY_ICON_KEYS).find(marker => message.startsWith(marker));
    const text = prefix ? message.slice(prefix.length).trimStart() : message;
    msgElem.innerHTML = `${iconHTML(prefix || 'info')} ${escapeHTML(text)}`;
    toast.style.opacity = '1';
    toast.classList.remove('hidden');
    toastFadeTimeout = setTimeout(() => {
        toast.style.opacity = '0';
        toastHideTimeout = setTimeout(() => toast.classList.add('hidden'), 300);
    }, 2200);
}

function toggleRaidPanel() {
    const panel = document.getElementById('battle-raid-panel');
    if (panel) {
        panel.classList.toggle('hidden');
        if (!panel.classList.contains('hidden')) updateRaidListUI();
    }
}

function openFriendInviteModal() {
    if (!isBattleActive) return;
    renderFriendsCheckboxList();
    document.getElementById('friend-invite-modal').classList.remove('hidden');
}

function closeFriendInviteModal() {
    document.getElementById('friend-invite-modal').classList.add('hidden');
}

function renderFriendsCheckboxList(filterText = '') {
    const container = document.getElementById('friends-checkbox-container');
    if (!container) return;
    let list = raidMembers.filter(m => !m.isPlayer);
    if (filterText) list = list.filter(f => f.name.toLowerCase().includes(filterText.toLowerCase()));

    container.innerHTML = list.map(f => `
        <label style="background: #15100c; border: 1px solid #3d2d22; padding: 10px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; font-size: 13px;">
            <span style="color: ${f.called ? '#27ae60' : '#f4e8d1'};">${escapeHTML(f.name)}</span>
            <input type="checkbox" value="${escapeHTML(f.id)}" class="friend-checkbox" ${f.called ? 'checked' : ''} style="width: 18px; height: 18px;">
        </label>
    `).join('');
}

function filterFriendsList() {
    renderFriendsCheckboxList(document.getElementById('friend-search-input')?.value || '');
}

function callSelectedFriends() {
    if (!isBattleActive) return;
    document.querySelectorAll('.friend-checkbox:checked').forEach(cb => {
        let m = raidMembers.find(x => x.id === cb.value);
        if (m) { m.called = true; m.active = true; }
    });
    closeFriendInviteModal();
    if (!document.getElementById('battle-raid-panel').classList.contains('hidden')) updateRaidListUI();
    showCustomToast("📢 Друзі приєдналися до рейду!");
}

function callAllFriends() {
    if (!isBattleActive) return;
    raidMembers.forEach(m => { if (!m.isPlayer) { m.called = true; m.active = true; } });
    closeFriendInviteModal();
    if (!document.getElementById('battle-raid-panel').classList.contains('hidden')) updateRaidListUI();
    showCustomToast("🔥 Усі друзі приєдналися!");
}

function updateRaidListUI() {
    const container = document.getElementById('raid-members-container');
    if (!container) return;
    container.innerHTML = raidMembers.filter(m => m.isPlayer || m.called).map(m => `
        <div style="background: #15100c; border: 1px solid #3d2d22; padding: 6px 10px; border-radius: 6px; display: flex; justify-content: space-between; font-size: 11px;">
            <div><strong>${escapeHTML(m.name)}</strong></div>
            <div style="color: #e74c3c; font-weight: bold;">${m.damage} DMG</div>
        </div>
    `).join('');
}

function showFloatingDamage(text, isHit = false, x = null, y = null) {
    const container = document.getElementById('damage-floating-container');
    if (!container) return;
    const el = document.createElement('div');
    el.textContent = text;
    el.style.cssText = `position: fixed; left: ${x ?? window.innerWidth / 2}px; top: ${y ?? window.innerHeight / 2}px; color: ${isHit ? '#e74c3c' : '#f39c12'}; font-size: 24px; font-weight: bold; z-index: 99999; pointer-events: none; transition: all 0.8s ease-out;`;
    container.appendChild(el);
    setTimeout(() => { el.style.transform = 'translateY(-60px) scale(1.2)'; el.style.opacity = '0'; }, 50);
    setTimeout(() => el.remove(), 850);
}

function triggerBossAttackAnimation() {
    const sprite = document.getElementById('nurse-boss-sprite');
    if (sprite) {
        sprite.classList.remove('boss-attacking');
        void sprite.offsetWidth;
        sprite.classList.add('boss-attacking');
        setTimeout(() => sprite.classList.remove('boss-attacking'), 550);
    }
}

function openFleeConfirmModal() {
    if (!isBattleActive) return;
    if (confirm("Втекти з бою? Це коштуватиме 20 срібла.")) {
        recordUnrewardedRaid('fled');
        stats.silver = Math.max(0, stats.silver - 20);
        updateUI();
        isBattleActive = false;
        stopBattleTimers();
        closeNurseBattle();
        closeFriendInviteModal();
        showCustomToast("💨 Ви втекли з бою (-20 срібла)");
    }
}

function performPlayerAttack(event) {
    if (!isBattleActive) return;
    updateRaidTimerTick();
    if (!isBattleActive || Date.now() < attackCooldownEndsAt || bossCurrentHp <= 0) return;
    const generation = battleGeneration;
    const dmg = Math.min(bossCurrentHp, stats.damage);
    const player = raidMembers.find(member => member.isPlayer);
    const attackId = nextBattleEventId('attack');
    if (!recordBattleEvent(attackId, player, { damage: dmg, turns: 1 })) return;
    bossCurrentHp = Math.max(0, bossCurrentHp - dmg);
    showFloatingDamage(`-${dmg}`, false, event?.clientX, event?.clientY);
    updateRaidListUI();
    updateBattleUI();
    if (bossCurrentHp <= 0) {
        handleVictory();
        return;
    }
    playerAttackCooldown = true;
    attackCooldownEndsAt = Date.now() + 4000;
    clearTimeout(attackCooldownTimeout);
    attackCooldownTimeout = setTimeout(() => {
        if (generation === battleGeneration) playerAttackCooldown = false;
    }, 4000);
    bossCounterTimeout = setTimeout(() => {
        if (generation !== battleGeneration || bossCurrentHp <= 0 || !isBattleActive) return;
        updateRaidTimerTick();
        if (!isBattleActive) return;
        triggerBossAttackAnimation();
        const activeBoss = bossesDatabase[currentBossKey];
        // Armor reduces incoming damage with diminishing returns; each hit deals at least 1 HP.
        const counter = Math.max(1, Math.ceil(activeBoss.damage * 100 / (100 + stats.armor)));
        const actualDamage = Math.min(stats.hp, counter);
        if (!recordBattleEvent(`${attackId}:counter`, player, { damageTaken: actualDamage })) return;
        stats.hp = Math.max(0, stats.hp - counter);
        showFloatingDamage(`-${actualDamage} HP`, true);
        if (stats.hp <= 0) {
            recordUnrewardedRaid('defeat');
            isBattleActive = false;
            stopBattleTimers();
            closeFriendInviteModal();
            alert('Бос вас здолав...');
            stats.hp = stats.maxHp;
            closeNurseBattle();
            updateUI();
            updateLobbyRaidWidget();
            return;
        }
        updateUI();
    }, 500);
}

function friendsAutoAttackTick() {
    if (!isBattleActive || bossCurrentHp <= 0) return;
    updateRaidTimerTick();
    if (!isBattleActive) return;
    raidMembers.forEach(member => {
        if (!member.isPlayer && member.called && member.active && bossCurrentHp > 0 && isBattleActive) {
            const damage = Math.min(bossCurrentHp, Math.floor(Math.random() * 8) + 4);
            if (!recordBattleEvent(nextBattleEventId('helper-attack'), member, { damage, turns: 1 })) return;
            bossCurrentHp = Math.max(0, bossCurrentHp - damage);
            showFloatingDamage(`${member.name}: -${damage}`, false);
            if (bossCurrentHp <= 0) handleVictory();
        }
    });
    updateRaidListUI();
    updateBattleUI();
}

function handleVictory() {
    if (!isBattleActive || bossCurrentHp > 0 || !currentBattleSession || currentBattleSession.finished) return;
    if (lastBattleResult?.battleId === currentBattleSession.id) {
        isBattleActive = false;
        currentBattleSession.finished = true;
        stopBattleTimers();
        openLastBattleResult();
        return;
    }
    const activeBoss = bossesDatabase[currentBattleSession.bossKey];
    if (!activeBoss) return;
    const result = buildBattleResult(activeBoss);
    processStaffRaid(result);
    currentBattleSession.finished = true;
    isBattleActive = false;
    stopBattleTimers();
    bossKillsCount[currentBattleSession.bossKey] = (bossKillsCount[currentBattleSession.bossKey] || 0) + 1;
    stats.bossesKilled += 1;
    stats.enemiesKilled += 1;
    closeFriendInviteModal();
    closeNurseBattle();
    updateLobbyRaidWidget();

    stats.silver += result.payout.silver;
    // Keep level-up notifications after the durable reward write.
    const reachedLevels = addExperience(result.payout.exp, false);
    if (activeBoss.questItem && result.extraRewards[0]?.granted) {
        inventory.push({ ...activeBoss.questItem, count: 1 });
    }
    lastBattleResult = result;
    battleResultPersisted = false;
    pendingBattleReward = { result, state: null };
    updateUI();
    openLastBattleResult();
    reachedLevels.forEach(level => alert(`Вітаємо! Ви досягли ${level} рівня!\nВаше звання: ${getPlayerRank(level)}`));
}

function victoryContinueToMap() {
    document.getElementById('nurse-victory-modal').classList.add('hidden');
    toggleMapModal(true);
}

function victoryRestartFight() {
    document.getElementById('nurse-victory-modal').classList.add('hidden');
    startBossFight(lastBattleResult?.boss.id || currentBossKey);
}

function updateBattleMedkitCounts() {
    const medkits = [
        { type: 'small', name: 'Мала аптечка' },
        { type: 'big', name: 'Велика армійська аптечка' }
    ];
    medkits.forEach(medkit => {
        const item = inventory.find(entry => entry.name === medkit.name && entry.category === 'meds');
        const countElem = document.getElementById(`medkit-count-${medkit.type}`);
        if (countElem) countElem.textContent = String(item?.count || 0);
    });
}

function updateBattleUI() {
    document.getElementById('b-player-name').textContent = playerName;
    document.getElementById('b-player-hp').textContent = `${stats.hp}/${stats.maxHp}`;
    document.getElementById('b-player-hpbar').style.width = `${Math.max(0, (stats.hp / stats.maxHp) * 100)}%`;
    document.getElementById('b-boss-hp').textContent = `${bossCurrentHp}/${bossMaxHp}`;
    document.getElementById('b-boss-hpbar').style.width = `${Math.max(0, (bossCurrentHp / bossMaxHp) * 100)}%`;
}

function useBattleMedkit(type) {
    if (!isBattleActive || (type !== 'big' && type !== 'small')) return;
    updateRaidTimerTick();
    if (!isBattleActive) return;
    const name = type === 'big' ? MEDICAL_ITEMS.hp_full.name : MEDICAL_ITEMS.hp_10.name;
    const item = inventory.find(entry => entry.name === name && entry.category === 'meds');
    if (consumeMedicalItem(item)) updateUI();
}

function handleRaidButtonAction() {
    if (isBattleActive) reopenNurseBattle();
    else alert("Зараз немає активних рейдів.");
}

function devSetMadness(val) {
    if (new URLSearchParams(window.location.search).get('dev') !== '1') return;
    if (!Number.isFinite(val)) return;
    stats.madness = Math.max(0, Math.min(100, Math.floor(val)));
    updateUI();
    showCustomToast(val >= 100 ? "⚠️ Режим Психозу!" : "🟢 Режим Норма!");
}
// === УНІВЕРСАЛЬНЕ ВІДКРИТТЯ ДОСЬЄ БОСА ===
function openBossDossier(bossKey) {
    try {
        const boss = getBossDefinition(bossKey);
        if (!boss) {
            console.error("Бос не знайдений у bossesDatabase:", bossKey);
            return;
        }

        closeOtherModals(['universal-dossier-modal']);
        // Закриваємо модалки (за наявності функцій)
        if (typeof closeInventory === 'function') closeInventory();
        if (typeof closeCustomization === 'function') closeCustomization();
        if (typeof closeSettings === 'function') closeSettings();
        if (typeof closeFriends === 'function') closeFriends();
        if (typeof toggleMapModal === 'function') toggleMapModal(false);

        const d = boss.dossier || {};

        // Заповнюємо базові текстові елементи, якщо вони є в HTML
        const setTxt = (id, txt) => {
            const el = document.getElementById(id);
            if (el) el.textContent = txt;
        };
        const setHTML = (id, html) => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = html;
        };

        setTxt('universal-dossier-code', d.code ? `ОСОБОВА СПРАВА № ${d.code}` : `ОСОБОВА СПРАВА`);
        setTxt('universal-dossier-threat', d.threat || "ЗАГРОЗА: ВИСОКА");
        setTxt('universal-dossier-name', boss.name || "Невідомий об'єкт");
        setTxt('universal-dossier-callsign', `ПОЗИВНИЙ: ${d.callsign || '«НЕВІДОМО»'}`);

// Фотографія з каталогу босів.
const dossierImage = document.getElementById('universal-dossier-img');
        if (dossierImage) {
            dossierImage.src = d.cardImg || boss.sprite;
            dossierImage.alt = boss.name;
        }
        setHTML('universal-dossier-role', `<strong>Посада:</strong> ${escapeHTML(d.role || '-')}`);
        setHTML('universal-dossier-status', `<strong>Статус:</strong> ${escapeHTML(d.status || d.diagnosis || '-')}`);
        setHTML('universal-dossier-location', `<strong>Локація:</strong> ${escapeHTML(d.location || d.subtitle || '-')}`);
        setTxt('universal-dossier-deviations', d.deviations || d.diagnosis || "Відомості відсутні.");

        // Нагорода
        const rew = d.rewardsText || `+${boss.expReward || 0} EXP, +${boss.silverReward || 0} Срібла`;
        setHTML('universal-dossier-rewards', `${iconHTML('gift')} <strong>Винагорода за знешкодження:</strong> ${escapeHTML(rew)}`);

        // Характеристики
        setTxt('universal-dossier-hp', `${boss.hp || 0} HP`);
        setTxt('universal-dossier-dmg', `${boss.damage || 0} DMG`);
        const detailsBtn = document.getElementById('universal-dossier-details-btn');
        if (detailsBtn) detailsBtn.onclick = () => openStaffArchive(bossKey);

// --- Кнопка штурму ---
    const startBtn = document.getElementById('universal-dossier-start-btn');
    if (startBtn) {
        startBtn.onclick = function() {
            closeUniversalDossier();

            startBossFight(bossKey);
        };
    }

        // Відображаємо модальне вікно
        const modal = document.getElementById('universal-dossier-modal');
        if (modal) modal.classList.remove('hidden');

    } catch (err) {
        console.error("Помилка відкриття досьє:", err);
    }
}

function closeUniversalDossier() {
    const modal = document.getElementById('universal-dossier-modal');
    if (modal) modal.classList.add('hidden');
}

const MODAL_IDS = [
    'settings-modal', 'bank-modal', 'inventory-modal', 'item-info-modal', 'custom-modal',
    'friends-modal', 'map-modal', 'gym-modal', 'medical-hub-modal', 'procedure-room-modal',
    'dossier-modal', 'universal-dossier-modal', 'nurse-battle-modal', 'friend-invite-modal',
    'nurse-victory-modal', 'battle-detail-modal', 'raid-archive-modal', 'raid-archive-confirm', 'staff-archive-modal'
];

function closeOtherModals(keepIds = []) {
    MODAL_IDS.forEach(id => {
        if (keepIds.includes(id)) return;
        const modal = document.getElementById(id);
        if (modal) {
            modal.classList.add('hidden');
            if (id === 'nurse-battle-modal') modal.style.display = 'none';
        }
    });
    if (!keepIds.includes('item-info-modal')) selectedItemForAction = null;
}

function initializeModalControls() {
    const modals = MODAL_IDS.map(id => document.getElementById(id)).filter(Boolean);
    const triggers = new Map();
    const openOrder = [];
    let previouslyOpen = [];
    const focusable = modal => Array.from(modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )).filter(element => !element.disabled && element.getClientRects().length > 0);
    const topModal = () => openOrder.at(-1);
    const closeModal = modal => {
        if (modal.id === 'nurse-battle-modal') closeNurseBattle();
        else if (modal.id === 'item-info-modal') closeItemInfo();
        else if (modal.id === 'inventory-modal') closeInventory();
        else if (modal.id === 'battle-detail-modal') closeDetailedBattleReport();
        else if (modal.id === 'raid-archive-confirm') cancelRaidArchiveClear();
        else modal.classList.add('hidden');
    };
    const sync = () => {
        const opened = modals.filter(modal => !modal.classList.contains('hidden'));
        const closed = previouslyOpen.filter(modal => !opened.includes(modal));
        for (const modal of closed) {
            const index = openOrder.indexOf(modal);
            if (index >= 0) openOrder.splice(index, 1);
        }
        const added = opened.filter(modal => !previouslyOpen.includes(modal));
        added.forEach(modal => {
            triggers.set(modal, document.activeElement);
            openOrder.push(modal);
            modal.tabIndex = -1;
        });
        document.body.classList.toggle('modal-open', opened.length > 0);
        const top = topModal();
        document.querySelectorAll('.hud-folder-tab[data-nav-modal]').forEach(button => {
            button.setAttribute('aria-pressed', String(button.dataset.navModal.split(' ').includes(top?.id)));
        });
        if (top && (added.length > 0 || (closed.length > 0 && !top.contains(document.activeElement)))) {
            (focusable(top)[0] || top).focus({ preventScroll: true });
        } else if (!top && closed.length > 0) {
            const trigger = triggers.get(closed.at(-1));
            if (trigger?.isConnected && !trigger.closest('.hidden')) trigger.focus({ preventScroll: true });
        }
        previouslyOpen = opened;
    };
    const observer = new MutationObserver(sync);
    modals.forEach(modal => {
        observer.observe(modal, { attributes: true, attributeFilter: ['class'] });
        modal.addEventListener('click', event => {
            if (event.target === modal && modal === topModal()) closeModal(modal);
        });
    });
    document.addEventListener('keydown', event => {
        const target = event.target;
        if ((event.key === 'Enter' || event.key === ' ') && target.matches('[role="button"]')
            && !target.matches('button, input, a')) {
            event.preventDefault();
            target.click();
            return;
        }
        const top = topModal();
        if (!top) return;
        if (event.key === 'Escape') {
            event.preventDefault();
            closeModal(top);
        } else if (event.key === 'Tab') {
            const elements = focusable(top);
            const first = elements[0];
            const last = elements.at(-1);
            if (!first) {
                event.preventDefault();
                top.focus();
            } else if (event.shiftKey && (document.activeElement === first || !top.contains(document.activeElement))) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && (document.activeElement === last || !top.contains(document.activeElement))) {
                event.preventDefault();
                first.focus();
            }
        }
    });
    sync();
}

function autoScaleBattleArena() {
    const wrapper = document.getElementById('battle-arena-scale');
    if (!wrapper) return;
    const width = window.visualViewport?.width || window.innerWidth;
    const height = window.visualViewport?.height || window.innerHeight;
    const portrait = height > width;
    const scale = portrait ? Math.min(width / 675, height / 1200) : Math.min(width / 1200, height / 675);
    wrapper.style.transform = `scale(${scale})${portrait ? ' rotate(90deg)' : ''}`;
}
window.addEventListener('resize', autoScaleBattleArena);
window.visualViewport?.addEventListener('resize', autoScaleBattleArena);
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        updateEnergyTimer();
        updateRaidTimerTick();
        autoScaleBattleArena();
    }
});
