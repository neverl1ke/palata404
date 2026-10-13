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

function getInitialUsername() {
    const savedName = localStorage.getItem('palata404_nickname');
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
        localStorage.setItem('palata404_nickname', playerName);
        updatePlayerNameDisplay();
        closeSettings();
    }
}

// === Система ідентифікації та «Сусіди по блоку» (Telegram + Web) ===
function getPlayerUniqueId() {
    if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const user = tg.initDataUnsafe.user;
        return {
            type: 'telegram',
            id: user.id.toString(),
            name: user.username ? `@${user.username}` : (user.first_name || "Гравець")
        };
    }

    let webId = localStorage.getItem('palata404_web_id');
    if (!webId) {
        webId = 'WEB-' + Math.floor(100000 + Math.random() * 900000);
        localStorage.setItem('palata404_web_id', webId);
    }
    
    return {
        type: 'browser',
        id: webId,
        name: playerName
    };
}

let friendsList = loadSaveData('palata404_friends', []);
friendsList = friendsList
    .filter(friend => friend && typeof friend === 'object' && !Array.isArray(friend)
        && (typeof friend.identifier === 'string' || typeof friend.identifier === 'number'))
    .map(friend => ({
        identifier: String(friend.identifier),
        status: typeof friend.status === 'string' ? friend.status : "На зв'язку"
    }));

function openFriends() {
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
    localStorage.setItem('palata404_friends', JSON.stringify(friendsList));
    
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
    localStorage.setItem('palata404_friends', JSON.stringify(friendsList));
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

let gender = localStorage.getItem('palata404_gender') || 'male'; 
let currentHair = localStorage.getItem('palata404_hair') || '';
let currentFace = localStorage.getItem('palata404_face') || ''; 
let currentClothes = localStorage.getItem('palata404_clothes') || '';

const facesData = [
    { id: 'face_1.png', name: 'Обличчя #1 (Голений)' },
    { id: 'face_2.png', name: 'Обличчя #2 (Коротка стрижка)' },
    { id: 'face_3.png', name: 'Обличчя #3 (Середнє волосся)' },
    { id: 'face_4.png', name: 'Обличчя #4 (Довге волосся)' },
    { id: 'face_5.png', name: 'Обличчя #5 (Андеркат)' },
    { id: 'face_6.png', name: 'Обличчя #6 (Лисий суворий)' }
];

const DEFAULT_INVENTORY = [
    { name: 'Іржавий ніж', icon: '🔪', count: 1, category: 'weapon', damageBonus: 8, desc: 'Саморобний ніж з обломка медичного шпателя.' },
    { name: 'ПМ (Пістолет Макарова)', icon: '🔫', count: 1, category: 'weapon', damageBonus: 18, desc: 'Табельний пістолет охорони.' },
    { name: 'Штурмовий АКС-74У', icon: '⚡', count: 1, category: 'weapon', damageBonus: 35, desc: 'Укорочений автомат колишньої охорони.' },
    { name: 'Побитий шолом санітара', icon: '🪖', count: 1, category: 'helmet', armorBonus: 12, desc: 'Протиударний шолом персоналу.' },
    { name: 'Бронежилет БР-1', icon: '🛡️', count: 1, category: 'armor', armorBonus: 28, desc: 'Легкий армійський бронежилет.' }
];

let inventory = loadSaveData('palata404_inventory', DEFAULT_INVENTORY);
inventory = inventory
    .filter(item => item && typeof item === 'object' && !Array.isArray(item))
    .map(item => {
        const freshItem = DEFAULT_INVENTORY.find(d => d.icon === item.icon || d.name === item.name);
        const rawCount = Number(item.count);
        const count = Number.isFinite(rawCount) && rawCount >= 0 ? Math.floor(rawCount) : 1;
        return freshItem ? { ...freshItem, count } : { ...item, count };
    });

let equippedGear = loadSaveData('palata404_equipped', {
    weapon: null,
    helmet: null,
    armor: null
});
['weapon', 'helmet', 'armor'].forEach(slot => {
    if (equippedGear[slot] !== null && typeof equippedGear[slot] !== 'string') equippedGear[slot] = null;
});

let currentCategory = 'all';
let currentWardrobeTab = 'body';
let selectedItemForAction = null;

const gameFloorsData = [
    {
        id: 10,
        title: "10 Поверх — Блок Ізоляторів",
        unlocked: true,
        mapImage: "map_floor_10.png",
        nodes: [
            { id: "sec_room404", title: "🛏️ Палата 404", x: 38, y: 31, type: "room_404" },
            { id: "sec1_collector", title: "⚙️ Ординаторська", x: 38, y: 44, type: "collector" },
            { id: "sec_procedure", title: "💉 Медпункт", x: 38, y: 62, type: "procedure", bossKey: "nurse" },
            { id: "sec2_grind", title: "🧱 Завал", x: 58, y: 50, type: "grind" },
            { id: "sec3_boss", title: "👹 Черговий лікар", x: 82, y: 44, type: "boss", bossKey: "doctor", locked: true }
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

function loadSaveData(key, fallback) {
    let saved;
    try {
        saved = localStorage.getItem(key);
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
        if (typeof value === 'number' && Number.isFinite(value)) normalized[key] = value;
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
    normalized.hp = Math.min(normalized.hp, normalized.maxHp);
    normalized.energy = Math.min(normalized.energy, normalized.maxEnergy);
    normalized.madness = Math.min(normalized.madness, 100);
    return normalized;
}

function saveGameProgress() {
    localStorage.setItem('palata404_stats', JSON.stringify(stats));
    localStorage.setItem('palata404_gender', gender);
    localStorage.setItem('palata404_hair', currentHair);
    localStorage.setItem('palata404_face', currentFace);
    localStorage.setItem('palata404_clothes', currentClothes);
    localStorage.setItem('palata404_inventory', JSON.stringify(inventory));
}

function getPlayerRank(level) {
    if (level >= 20) return "Легенда Руїн";
    if (level >= 15) return "Ветеран";
    if (level >= 10) return "Шукач";
    if (level >= 5) return "Виживальник";
    return "Новачок";
}

function addExperience(amount) {
    stats.exp += amount;
    if (!stats.nextLvlExp) stats.nextLvlExp = stats.level * 100;

    while (stats.exp >= stats.nextLvlExp) {
        stats.exp -= stats.nextLvlExp;
        stats.level += 1;
        stats.nextLvlExp = stats.level * 120;
        stats.maxHp += 5;
        stats.hp = stats.maxHp;
        alert(`🎉 Вітаємо! Ви досягли ${stats.level} рівня!\nВаше звання: ${getPlayerRank(stats.level)}`);
    }
}

function setGender(selectedGender) {
    gender = selectedGender;
    saveGameProgress();
    updateCharacterLayers();
}

function setFace(faceFileName) {
    currentFace = faceFileName;
    saveGameProgress();
    updateCharacterLayers();
    renderWardrobe();
}

function updateCharacterLayers() {
    const bodyImg = document.getElementById('layer-body');
    if (bodyImg) {
        bodyImg.src = gender === 'female' ? 'base_female.png' : 'base_male.png';
    }

    const faceImg = document.getElementById('layer-face');
    const hairImg = document.getElementById('layer-hair');
    const clothesImg = document.getElementById('layer-clothes');

    if (faceImg) faceImg.classList.add('hidden');

    if (hairImg) {
        if (currentHair) {
            hairImg.src = currentHair;
            hairImg.classList.remove('hidden');
        } else {
            hairImg.classList.add('hidden');
        }
    }

    if (clothesImg) {
        if (currentClothes) {
            clothesImg.src = currentClothes;
            clothesImg.classList.remove('hidden');
        } else {
            clothesImg.classList.add('hidden');
        }
    }
}

function updateUI() {
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
    if (damageVal) damageVal.textContent = stats.damage || 10;

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

    const mapBtn = document.getElementById('nav-map-btn');
    const locName = document.getElementById('current-location-name');
    const locDesc = document.getElementById('current-location-desc');
    const locTitleLabel = document.getElementById('loc-title-label');
    const locCardBox = document.getElementById('location-card-box');

    if (stats.madness >= 100) {
        if (mapBtn) mapBtn.style.display = 'flex'; 
        if (locTitleLabel) locTitleLabel.textContent = "⚠️ СИСТЕМНИЙ ЗБІЙ";
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
                    ${floor.unlocked ? 'План евакуації знайдено' : '🔒 План відсутній'}
                </div>
            </div>
            <span>${floor.unlocked ? '🗺️ Відкрити' : '🔒'}</span>
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
        btn.innerText = node.title;
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
        alert("🛏️ Палата #404. Твоє безпечне місце.");
    } else if (node.type === 'procedure') {
        openBossDossier(node.bossKey || 'nurse');
    } else if (node.type === 'collector') {
        alert("⚙️ Автономний Збирач #1 працює!\nЗібрано луту: +15 Срібла, +1 Пігулка.");
        stats.silver += 15;
        stats.pills += 1;
        updateUI();
    } else if (node.type === 'grind') {
        if (stats.energy >= 10) {
            stats.energy -= 10;
            alert("⛏️ Ви розчистили завал у коридорі! Отримано 30 EXP та відкрито шлях до Боса!");
            addExperience(30);
            
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
    const modal = document.getElementById('bank-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeBank() {
    const modal = document.getElementById('bank-modal');
    if (modal) modal.classList.add('hidden');
}

function openInventory() {
    closeCustomization();
    closeFriends();
    closeDossier();
    renderMinecraftStash();
    const modal = document.getElementById('inventory-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeInventory() {
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

    const TOTAL_SLOTS = 20;
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
                <span class="item-icon">${escapeHTML(item.icon)}</span>
                ${item.count > 1 ? `<span class="item-count">${item.count}</span>` : ''}
                ${isEquipped ? `<span style="position: absolute; top: 2px; left: 2px; font-size: 8px; background: #e74c3c; color: #fff; padding: 1px 3px; border-radius: 3px;">EQ</span>` : ''}
            `;
            slot.onclick = () => openItemInfo(item);
        }
        container.appendChild(slot);
    }
}

function openItemInfo(item) {
    selectedItemForAction = item;
    const titleElem = document.getElementById('item-info-title');
    if (titleElem) titleElem.textContent = `${item.icon} ${item.name}`;
    
    let bodyHtml = `<p style="color: #a3927d;">${escapeHTML(item.desc || 'Немає опису предмета.')}</p>`;
    
    const isEquipped = (
        (item.category === 'weapon' && equippedGear.weapon === item.name) ||
        (item.category === 'helmet' && equippedGear.helmet === item.name) ||
        (item.category === 'armor' && equippedGear.armor === item.name)
    );

    const actionBtn = document.getElementById('item-action-btn');

    if (item.category === 'weapon') {
        bodyHtml += `<div style="color: #e74c3c; margin-top: 5px;"><strong>⚔️ Бонус до урону:</strong> +${escapeHTML(item.damageBonus || 0)}</div>`;
        if (actionBtn) actionBtn.textContent = isEquipped ? "Зняти" : "Озброїтися";
    } else if (item.category === 'armor' || item.category === 'helmet') {
        bodyHtml += `<div style="color: #3498db; margin-top: 5px;"><strong>🛡️ Бонус до броні:</strong> +${escapeHTML(item.armorBonus || 0)}</div>`;
        if (actionBtn) actionBtn.textContent = isEquipped ? "Зняти" : "Надіти спорядження";
    } else if (item.category === 'meds') {
        bodyHtml += `<div style="color: #2ecc71; margin-top: 5px;"><strong>⚡ Ефект препарату:</strong> ${escapeHTML(item.effectDesc || 'Відновлює стан')}</div>`;
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
    updateUI();
    updateEnergyTimer();

    const actionBtn = document.getElementById('item-action-btn');
    if (actionBtn) {
        actionBtn.onclick = () => {
            if (!selectedItemForAction) {
                closeItemInfo();
                return;
            }
            
            const cat = selectedItemForAction.category;

            if (cat === 'weapon') {
                if (equippedGear.weapon === selectedItemForAction.name) {
                    stats.damage -= (selectedItemForAction.damageBonus || 0);
                    equippedGear.weapon = null;
                } else {
                    if (equippedGear.weapon) {
                        const oldWp = inventory.find(i => i.name === equippedGear.weapon);
                        if (oldWp) stats.damage -= (oldWp.damageBonus || 0);
                    }
                    stats.damage += (selectedItemForAction.damageBonus || 0);
                    equippedGear.weapon = selectedItemForAction.name;
                }
            } else if (cat === 'armor' || cat === 'helmet') {
                if (equippedGear[cat] === selectedItemForAction.name) {
                    stats.armor -= (selectedItemForAction.armorBonus || 0);
                    equippedGear[cat] = null;
                } else {
                    if (equippedGear[cat]) {
                        const oldArmor = inventory.find(i => i.name === equippedGear[cat]);
                        if (oldArmor) stats.armor -= (oldArmor.armorBonus || 0);
                    }
                    stats.armor += (selectedItemForAction.armorBonus || 0);
                    equippedGear[cat] = selectedItemForAction.name;
                }
            } else if (cat === 'meds') {
                if (selectedItemForAction.count > 0) {
                    selectedItemForAction.count -= 1;
                    
                    if (selectedItemForAction.effectType === 'madness') {
                        stats.madness = Math.max(0, stats.madness - 15);
                    } else if (selectedItemForAction.effectType === 'stamina_10') {
                        stats.energy = Math.min(stats.maxEnergy, stats.energy + (stats.maxEnergy * 0.1));
                    } else if (selectedItemForAction.effectType === 'stamina_full') {
                        stats.energy = stats.maxEnergy;
                    } else if (selectedItemForAction.effectType === 'hp_10') {
                        stats.hp = Math.min(stats.maxHp, stats.hp + (stats.maxHp * 0.1));
                    } else if (selectedItemForAction.effectType === 'hp_full') {
                        stats.hp = stats.maxHp;
                    }

                    if (selectedItemForAction.count <= 0) {
                        inventory = inventory.filter(i => i !== selectedItemForAction);
                    }
                }
            }

            localStorage.setItem('palata404_equipped', JSON.stringify(equippedGear));
            updateUI();
            closeItemInfo();
            renderMinecraftStash();
        };
    }
});

function openCustomization() {
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

function setWardrobeTab(tab, btnElem) {
    currentWardrobeTab = tab;
    if (btnElem && btnElem.parentElement) {
        btnElem.parentElement.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
        btnElem.classList.add('active');
    }
    renderWardrobe();
}

function renderWardrobe() {
    const container = document.getElementById('wardrobe-container');
    if (!container) return;
    container.innerHTML = '';

    if (currentWardrobeTab === 'body') {
        container.innerHTML = `
            <div class="outfit-card ${gender === 'male' ? 'active' : ''}">
                <div>👨 Чоловіча стать</div>
                <button class="btn-outfit" onclick="setGender('male'); renderWardrobe();">Обрати</button>
            </div>
            <div class="outfit-card ${gender === 'female' ? 'active' : ''}">
                <div>👩 Жіноча стать</div>
                <button class="btn-outfit" onclick="setGender('female'); renderWardrobe();">Обрати</button>
            </div>
        `;
    } else if (currentWardrobeTab === 'face') {
        facesData.forEach(face => {
            const isActive = currentFace === face.id;
            const card = document.createElement('div');
            card.className = `outfit-card ${isActive ? 'active' : ''}`;
            card.innerHTML = `
                <div style="display:flex; align-items:center; gap:8px;">
                    <img src="${face.id}" style="width:32px; height:32px; object-fit:cover; border-radius:4px; border:1px solid #3d2d22;" alt="Face">
                    <span>${face.name}</span>
                </div>
                <button class="btn-outfit" onclick="setFace('${face.id}')">${isActive ? 'Обрано' : 'Обрати'}</button>
            `;
            container.appendChild(card);
        });
    } else {
        container.innerHTML = `<p style="font-size:12px; color:#a3927d; text-align:center; padding: 20px 0;">Розділ у розробці</p>`;
    }
}

// === Спортзал та збереження прогресу ===
const DEFAULT_GYM_EXERCISES = [
    { id: 'squats', name: 'Присідання', icon: '🦵', current: 0, target: 15, energy: 2, madness: 1, exp: 5 },
    { id: 'pushups', name: 'Віджимання', icon: '💪', current: 0, target: 12, energy: 3, madness: 2, exp: 8 },
    { id: 'plank', name: 'Планка', icon: '🧘', current: 0, target: 10, energy: 4, madness: 2, exp: 10 },
    { id: 'pullups', name: 'Підтягування', icon: '🦾', current: 0, target: 8, energy: 5, madness: 3, exp: 14 },
    { id: 'stretching', name: 'Розтяжка', icon: '🤸', current: 0, target: 10, energy: 2, madness: 1, exp: 6 },
    { id: 'shadowbox', name: 'Бій з тінню', icon: '🥊', current: 0, target: 5, energy: 6, madness: 5, exp: 20 }
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
    && Number.isFinite(gymComplex.completedRounds)
    ? Math.max(0, Math.floor(gymComplex.completedRounds))
    : 0;

function saveGymProgress() {
    localStorage.setItem('palata404_gym', JSON.stringify(gymComplex));
}

function openGym() {
    if (stats.madness >= 100) {
        showCustomToast("❌ Тренування неможливі в стані повного психозу!");
        return;
    }
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
    let ex = gymComplex.exercises.find(e => e.id === exId);
    if (!ex) {
        console.error("Вправу не знайдено:", exId);
        return;
    }
    if (ex.current >= ex.target) {
        showCustomToast("⚠️ Цю вправу вже виконано на сьогодні!");
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
        stats.damage = (stats.damage || 10) + 3;
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
                <span style="font-size: 24px; background: rgba(0,0,0,0.3); padding: 6px; border-radius: 6px; border: 1px solid #3d2d22;">${ex.icon}</span>
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
    { id: 'room_404', name: 'Палата #404', icon: '🛏️', desc: 'Твоя власна палата.' },
    { id: 'gym', name: 'Зал реабілітації', icon: '🏋️', desc: 'Спортзал для вправ.' },
    { id: 'treatment_room', name: 'Процедурний кабінет', icon: '💉', desc: 'Видача ліків.' },
    { id: 'corridor', name: 'Коридор блоку', icon: '🚪', desc: 'Вихід у коридор.' }
];

function openMedicalHub() {
    if (stats.madness >= 100) return;
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
            : `<button class="btn-outfit" style="background: ${isCurrent ? '#2c221e' : '#594333'}; border-color: ${isCurrent ? '#4a382c' : '#8c684d'}; padding: 6px 14px; font-weight: bold;" onclick="selectRoom('${room.id}')" ${isCurrent ? 'disabled style="opacity: 0.6; cursor: default;"' : ''}>${isCurrent ? 'Ви тут' : 'Перейти'}</button>`;

        item.innerHTML = `
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 24px; background: rgba(0,0,0,0.3); padding: 6px; border-radius: 6px; border: 1px solid #3d2d22;">${room.icon}</span>
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
    let room = medicalRooms.find(r => r.id === roomId);
    if (!room) return;
    currentRoom = room;
    closeMedicalHub();
    if (roomId === 'gym') openGym();
}

function buyMedicalItem(itemType, cost, currencyType) {
    if (currencyType === 'silver') {
        if (stats.silver >= cost) stats.silver -= cost; else { alert('Мало срібла!'); return; }
    } else {
        if (stats.bucks >= cost) stats.bucks -= cost; else { alert('Мало баксів!'); return; }
    }

    let newItem = null;
    if (itemType === 'madness_pills') newItem = { name: 'Таблетки «Аміназин»', icon: '💊', category: 'meds', effectType: 'madness' };
    else if (itemType === 'stamina_10') newItem = { name: 'Енергетик', icon: '🧃', category: 'meds', effectType: 'stamina_10' };
    else if (itemType === 'hp_10') newItem = { name: 'Мала аптечка', icon: '🧪', category: 'meds', effectType: 'hp_10' };
    else if (itemType === 'hp_full') newItem = { name: 'Велика армійська аптечка', icon: '🩹', category: 'meds', effectType: 'hp_full' };

    if (newItem) {
        let ex = inventory.find(i => i.name === newItem.name);
        if (ex) ex.count = (ex.count || 1) + 1;
        else inventory.push({ ...newItem, count: 1 });
    }
    updateUI();
    saveGameProgress();
}

const ENERGY_REGEN_TIME_MS = 2 * 60 * 1000;
function updateEnergyTimer() {
    let tElem = document.getElementById('energy-timer');
    if (!tElem || stats.energy >= stats.maxEnergy) return;
    let last = parseInt(localStorage.getItem('palata404_last_time') || Date.now(), 10);
    let diff = Date.now() - last;
    if (diff >= ENERGY_REGEN_TIME_MS) {
        stats.energy = Math.min(stats.maxEnergy, stats.energy + Math.floor(diff / ENERGY_REGEN_TIME_MS));
        localStorage.setItem('palata404_last_time', Date.now().toString());
        updateUI();
    }
}
setInterval(updateEnergyTimer, 1000);

function openDossier() {
    closeInventory();
    closeCustomization();
    closeSettings();
    closeFriends();
    closeGym();
    closeMedicalHub();
    closeProcedureRoom();
    document.getElementById('dossier-name').textContent = playerName;
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
        name: "Сестра Клара «Шприц»",
        hp: 120,
        damage: 12,
        expReward: 50,
        silverReward: 30,
        sprite: "nurse_sprite.png",       // <--- Додали спрайт боса
        bg: "nurse_bg.jpg",               // <--- Додали фон арени
        avatar: "nurse_avatar_battle.png", // <--- Додали аватарку
        questItem: { name: 'Ключ від блоку боса', icon: '🔑', category: 'quest', desc: 'Відкриває заблоковані двері спецблоку.' },
        dossier: {
            code: "001",
            threat: "ЗАГРОЗА: ВИСОКА",
            callsign: "«ПРОЦЕДУРНА»",
            cardImg: "nurse_dossier_card.png",
            role: "Старша медсестра",
            status: "Патологічна агресія",
            location: "Процедурний блок, 10-й поверх",
            deviations: "Після катастрофи втратила розум. Демонструє ендогенний галюцинаторно-параноїдний синдром.",
            rewardsText: "+50 EXP • +30 Срібла • Ключ від процедурної"
        }
    },
    doctor: {
        key: 'doctor',
        name: "Черговий лікар",
        hp: 250,
        damage: 25,
        expReward: 120,
        silverReward: 80,
        sprite: "doctor_sprite.png",       // (заміни на своє ім'я файла спрайта лікаря, якщо інше)
        bg: "doctor_bg.jpg",               // Можеш замінити на doctor_bg.jpg, якщо є
        avatar: "doctor_avatar_battle.jpg", // Заміни на аватарку лікаря за потреби
        questItem: { name: 'Ключ від ізолятора', icon: '🗝️', category: 'quest', desc: 'Відкриває вихід із 10 поверху.' },
        dossier: {
            code: "002",
            threat: "ЗАГРОЗА: КРИТИЧНА",
            callsign: "«НАБЛЮДАЧ»",
            cardImg: "doctor_dossier_card.png",
            role: "Старший черговий лікар",
            status: "Зв'язок втрачено / Мутація",
            location: "Кабінет спостереження, 10-й поверх",
            deviations: "Внаслідок аномальної трансформації суб'єкт набув додаткових кінцівок.",
            rewardsText: "+120 EXP • +80 Срібла • Ключ від ізолятора"
        }
    }
};

let currentBossKey = 'nurse';
let bossCurrentHp = 120;
let bossMaxHp = 120;
let bossKillsCount = {};

let isBattleActive = false;
let raidTimeRemaining = 300;
let raidTimerInterval = null;
let playerAttackCooldown = false;
let friendAttackInterval = null;

let raidMembers = [
    { id: 'player', name: 'Пацієнт #404', damage: 0, isPlayer: true, active: true },
    { id: 'friend_1', name: 'Сліпий Микола', damage: 0, active: false, called: false },
    { id: 'friend_2', name: 'Мері', damage: 0, active: false, called: false },
    { id: 'friend_3', name: 'Буйний сусіда', damage: 0, active: false, called: false }
];

function openProcedureRoomBattle() {
    if (stats.madness < 100) {
        alert("У нормальному стані процедурний кабінет зачинений.");
        return;
    }
    const killsElem = document.getElementById('dossier-kills-count');
    if (killsElem) killsElem.textContent = bossKillsCount['nurse'] || 0;
    document.getElementById('nurse-dossier-modal').classList.remove('hidden');
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
    document.getElementById('doctor-dossier-modal').classList.remove('hidden');
}

function closeDoctorDossier() {
    const modal = document.getElementById('doctor-dossier-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// === УНІВЕРСАЛЬНИЙ ЗАПУСК БОЮ ===
function startBossFight(bossKey) {
    const boss = bossesDatabase[bossKey];
    if (!boss) return;

    if (isBattleActive) {
        closeNurseDossier();
        closeDoctorDossier();
        toggleMapModal(false);
        reopenNurseBattle();
        return;
    }

    closeNurseDossier();
    closeDoctorDossier();
    closeUniversalDossier();
    toggleMapModal(false);

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
    
    updateBattleUI();
    const battleModal = document.getElementById('nurse-battle-modal');
    if (battleModal) {
        battleModal.classList.remove('hidden');
        battleModal.style.display = 'flex';
    }

    if (raidTimerInterval) clearInterval(raidTimerInterval);
    raidTimerInterval = setInterval(updateRaidTimerTick, 1000);

    if (friendAttackInterval) clearInterval(friendAttackInterval);
    friendAttackInterval = setInterval(friendsAutoAttackTick, 3500);

    updateLobbyRaidWidget();
}

// Сумісність зі старими викликами
function startNurseFight() { startBossFight('nurse'); }
function startDoctorFight() { startBossFight('doctor'); }

function closeNurseBattle() {
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
    updateBattleUI();
    const modal = document.getElementById('nurse-battle-modal');
    if (modal) {
        modal.classList.remove('hidden');
        modal.style.display = 'flex';
    }
}

function updateRaidTimerTick() {
    if (!isBattleActive) return;
    raidTimeRemaining--;
    let mins = Math.floor(raidTimeRemaining / 60);
    let secs = raidTimeRemaining % 60;
    let timeStr = `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;

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
            subTimer.style.cssText = 'position: absolute; bottom: -14px; left: 50%; transform: translateX(-50%); font-size: 9px; color: #e74c3c; font-weight: bold; white-space: nowrap; background: rgba(0,0,0,0.8); padding: 1px 4px; border-radius: 3px;';
            raidBtn.style.position = 'relative';
            raidBtn.appendChild(subTimer);
        }
        subTimer.textContent = timeStr || '05:00';
        raidBtn.onclick = reopenNurseBattle;
    } else {
        raidBtn.style.borderColor = '';
        raidBtn.style.background = '';
        if (subTimer) subTimer.remove();
        raidBtn.onclick = handleRaidButtonAction;
    }
}

function handleRaidTimeOut() {
    isBattleActive = false;
    clearInterval(raidTimerInterval);
    clearInterval(friendAttackInterval);
    closeNurseBattle();
    alert("⏱️ Час рейду вичерпано!");
    updateLobbyRaidWidget();
}

function showCustomToast(msg) {
    const toast = document.getElementById('custom-toast-notification');
    const msgElem = document.getElementById('toast-message');
    if (!toast || !msgElem) return;
    msgElem.textContent = msg;
    toast.classList.remove('hidden');
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.classList.add('hidden'), 300);
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
    document.querySelectorAll('.friend-checkbox:checked').forEach(cb => {
        let m = raidMembers.find(x => x.id === cb.value);
        if (m) { m.called = true; m.active = true; }
    });
    closeFriendInviteModal();
    if (!document.getElementById('battle-raid-panel').classList.contains('hidden')) updateRaidListUI();
    showCustomToast("📢 Друзі приєдналися до рейду!");
}

function callAllFriends() {
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
    el.style.cssText = `position: fixed; left: ${x || window.innerWidth/2}px; top: ${y || window.innerHeight/2}px; color: ${isHit ? '#e74c3c' : '#f39c12'}; font-size: 24px; font-weight: bold; z-index: 99999; pointer-events: none; transition: all 0.8s ease-out;`;
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
    if (confirm("Втекти з бою? Це коштуватиме 20 срібла.")) {
        stats.silver = Math.max(0, stats.silver - 20);
        updateUI();
        isBattleActive = false;
        clearInterval(raidTimerInterval);
        clearInterval(friendAttackInterval);
        closeNurseBattle();
        showCustomToast("💨 Ви втекли з бою (-20 🪙)");
    }
}

function performPlayerAttack(event) {
    if (playerAttackCooldown || bossCurrentHp <= 0 || !isBattleActive) return;

    let dmg = stats.damage || 10;
    bossCurrentHp = Math.max(0, bossCurrentHp - dmg);
    let p = raidMembers.find(m => m.isPlayer);
    if (p) p.damage += dmg;

    showFloatingDamage(`-${dmg}`, false, event?.clientX, event?.clientY);
    updateRaidListUI();

    if (bossCurrentHp <= 0) {
        handleVictory();
        return;
    }

    playerAttackCooldown = true;
    setTimeout(() => playerAttackCooldown = false, 4000);

    setTimeout(() => {
        if (bossCurrentHp <= 0 || !isBattleActive) return;
        triggerBossAttackAnimation();

        let activeBoss = bossesDatabase[currentBossKey];
        let counter = activeBoss ? activeBoss.damage : 15;
        stats.hp = Math.max(0, stats.hp - counter);

        showFloatingDamage(`-${counter} HP`, true);

        if (stats.hp <= 0) {
            isBattleActive = false;
            alert("💀 Бос вас здолав...");
            stats.hp = stats.maxHp;
            closeNurseBattle();
            updateUI();
            updateLobbyRaidWidget();
            return;
        }
        updateBattleUI();
    }, 500);
}

function friendsAutoAttackTick() {
    if (bossCurrentHp <= 0 || !isBattleActive) return;
    raidMembers.forEach(m => {
        if (!m.isPlayer && m.called && m.active && bossCurrentHp > 0) {
            let fDmg = Math.floor(Math.random() * 8) + 4;
            bossCurrentHp = Math.max(0, bossCurrentHp - fDmg);
            m.damage += fDmg;
            showFloatingDamage(`${m.name}: -${fDmg}`, false);
            updateRaidListUI();
            if (bossCurrentHp <= 0) handleVictory();
        }
    });
}

function handleVictory() {
    isBattleActive = false;
    clearInterval(raidTimerInterval);
    clearInterval(friendAttackInterval);
    
    bossKillsCount[currentBossKey] = (bossKillsCount[currentBossKey] || 0) + 1;
    closeNurseBattle();
    updateLobbyRaidWidget();

    let activeBoss = bossesDatabase[currentBossKey];
    let p = raidMembers.find(m => m.isPlayer);
    
    if (p && activeBoss) {
        // Нараховуємо нагороди активного боса напряму
        stats.silver += activeBoss.silverReward;
        addExperience(activeBoss.expReward);
        
        if (activeBoss.questItem && !inventory.some(i => i.name === activeBoss.questItem.name)) {
            inventory.push({ ...activeBoss.questItem, count: 1 });
        }
    }

    let sorted = [...raidMembers.filter(m => m.isPlayer || m.called)].sort((a, b) => b.damage - a.damage);
    
    const summaryElem = document.getElementById('victory-raid-summary');
    if (summaryElem && activeBoss) {
        summaryElem.innerHTML = `
            <div style="font-weight: bold; color: #f39c12; margin-bottom: 8px;">👑 MVP: ${escapeHTML(sorted[0].name)} — ${sorted[0].damage} DMG</div>
            <div style="font-size: 13px; color: #27ae60; margin-bottom: 6px;">🎁 Винагорода: +${activeBoss.expReward} EXP, +${activeBoss.silverReward} Срібла</div>
            ${sorted.map(m => `<div style="font-size: 12px;">• ${escapeHTML(m.name)}:${m.damage} DMG</div>`).join('')}
        `;
    }

    document.getElementById('nurse-victory-modal').classList.remove('hidden');
    updateUI();
    saveGameProgress();
}

function victoryContinueToMap() {
    document.getElementById('nurse-victory-modal').classList.add('hidden');
}

function victoryRestartFight() {
    document.getElementById('nurse-victory-modal').classList.add('hidden');
    startBossFight(currentBossKey);
}

function updateBattleUI() {
    document.getElementById('b-player-name').textContent = playerName;
    document.getElementById('b-player-hp').textContent = `${stats.hp}/${stats.maxHp}`;
    document.getElementById('b-player-hpbar').style.width = `${Math.max(0, (stats.hp / stats.maxHp) * 100)}%`;
    document.getElementById('b-boss-hp').textContent = `${bossCurrentHp}/${bossMaxHp}`;
    document.getElementById('b-boss-hpbar').style.width = `${Math.max(0, (bossCurrentHp / bossMaxHp) * 100)}%`;
}

function useBattleMedkit(type) {
    let name = type === 'big' ? 'Велика армійська аптечка' : 'Мала аптечка';
    let item = inventory.find(i => i.name === name || i.category === 'meds');
    if (item && item.count > 0) {
        item.count--;
        if (item.count <= 0) inventory = inventory.filter(i => i !== item);
        stats.hp = Math.min(stats.maxHp, stats.hp + (type === 'big' ? 50 : 20));
        updateBattleUI();
        updateUI();
    }
}

function handleRaidButtonAction() {
    if (isBattleActive) reopenNurseBattle();
    else alert("Зараз немає активних рейдів.");
}

function devSetMadness(val) {
    stats.madness = val;
    updateUI();
    showCustomToast(val >= 100 ? "⚠️ Режим Психозу!" : "🟢 Режим Норма!");
}
// === УНІВЕРСАЛЬНЕ ВІДКРИТТЯ ДОСЬЄ БОСА ===
function openBossDossier(bossKey) {
    try {
        const boss = bossesDatabase[bossKey];
        if (!boss) {
            console.error("Бос не знайдений у bossesDatabase:", bossKey);
            return;
        }

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

// --- ФОТОГРАФІЯ ---
// --- ФОТОГРАФІЯ ---
document.getElementById('universal-dossier-img').src = `${bossKey}_dossier_card.png`;
        setHTML('universal-dossier-role', `<strong>Посада:</strong> ${d.role || '-'}`);
        setHTML('universal-dossier-status', `<strong>Статус:</strong> ${d.status || d.diagnosis || '-'}`);
        setHTML('universal-dossier-location', `<strong>Локація:</strong> ${d.location || d.subtitle || '-'}`);
        setTxt('universal-dossier-deviations', d.deviations || d.diagnosis || "Відомості відсутні.");

        // Нагорода
        const rew = d.rewardsText || `+${boss.expReward || 0} EXP, +${boss.silverReward || 0} Срібла`;
        setHTML('universal-dossier-rewards', `🎁 <strong>Винагорода за знешкодження:</strong> ${rew}`);

        // Характеристики
        setTxt('universal-dossier-hp', `${boss.hp || 0} HP`);
        setTxt('universal-dossier-dmg', `${boss.damage || 0} DMG`);

// --- Кнопка штурму ---
    const startBtn = document.getElementById('universal-dossier-start-btn');
    if (startBtn) {
        startBtn.onclick = function() {
            closeUniversalDossier();
            
            // Викликаємо функцію штурму напряму залежно від боса
            if (typeof startBossFight === 'function') {
                startBossFight(bossKey);
            } else if (bossKey === 'nurse') {
                if (typeof startNurseFight === 'function') startNurseFight();
                else console.error("Функція для бою з медсестрою не знайдена!");
            } else if (bossKey === 'doctor') {
                if (typeof startDoctorFight === 'function') startDoctorFight();
                else console.error("Функція для бою з лікарем не знайдена!");
            } else {
                console.error("Невідомий ключ боса для бою:", bossKey);
            }
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