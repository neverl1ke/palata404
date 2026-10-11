// === Telegram Web App та Нікнейм ===
const tg = window.Telegram?.WebApp;
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
                <strong style="color: #fff8e7;">${friend.identifier}</strong>
                <div style="font-size: 10px; color: #2ecc71;">● ${friend.status}</div>
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

let stats = loadSaveData('palata404_stats', DEFAULT_STATS);

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
    { name: 'Іржавий ніж', icon: '🔪', count: 1, category: 'weapon', damageBonus: 8, desc: 'Саморобний ніж з обломка медичного шпателя. Тихий, не привертає зайвої уваги санітарів, але ефективний у тісних коридорах.' },
    { name: 'ПМ (Пістолет Макарова)', icon: '🔫', count: 1, category: 'weapon', damageBonus: 18, desc: 'Табельний пістолет охорони. Потертий вороніний метал, у магазині залишилось кілька патронів.' },
    { name: 'Штурмовий АКС-74У', icon: '⚡', count: 1, category: 'weapon', damageBonus: 35, desc: 'Укорочений автомат колишньої охорони спецблоку. Засіб останньої надії проти агресивних мутантів.' },
    { name: 'Побитий шолом санітара', icon: '🪖', count: 1, category: 'helmet', armorBonus: 12, desc: 'Протиударний шолом персоналу психлікарні із залишками захисного скла. Гасить важкі удари по голові.' },
    { name: 'Бронежилет БР-1', icon: '🛡️', count: 1, category: 'armor', armorBonus: 28, desc: 'Легкий армійський бронежилет прихованого носіння. Рятує від кульових поранень та ножів.' }
];

let inventory = loadSaveData('palata404_inventory', DEFAULT_INVENTORY);
inventory = inventory.map(item => {
    const freshItem = DEFAULT_INVENTORY.find(d => d.icon === item.icon || d.name === item.name);
    return freshItem ? { ...freshItem, count: item.count } : item;
});

let equippedGear = loadSaveData('palata404_equipped', {
    weapon: null,
    helmet: null,
    armor: null
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
            { id: "sec_room404", title: "🛏️ Палата #404", x: 38, y: 31, type: "room_404" },
            { id: "sec1_collector", title: "⚙️ Збирач #1", x: 38, y: 44, type: "collector" },
            { id: "sec_procedure", title: "💉 Процедурний", x: 38, y: 62, type: "procedure" },
            { id: "sec2_grind", title: "🧱 Завал (Розчистити)", x: 58, y: 50, type: "grind" },
            { id: "sec3_boss", title: "👹 Бос Поверху", x: 82, y: 44, type: "boss", locked: true }
        ]
    },
    {
        id: 9,
        title: "9 Поверх — Психіатрична Терапія",
        unlocked: false,
        mapImage: "",
        nodes: []
    },
    {
        id: 8,
        title: "8 Поверх — Процедурний Блок",
        unlocked: false,
        mapImage: "",
        nodes: []
    }
];

function loadSaveData(key, fallback) {
    const saved = localStorage.getItem(key);
    if (!saved) return fallback;
    try { 
        const parsed = JSON.parse(saved);
        if (typeof fallback === 'object' && fallback !== null && !Array.isArray(fallback)) {
            return { ...fallback, ...parsed };
        }
        return parsed; 
    } catch (e) { return fallback; }
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
        if (locDesc) locDesc.textContent = "Реальність втрачено. Спокійний корпус недоступний. Час виходити в коридори...";
        if (locCardBox) locCardBox.style.borderColor = "#c0392b";
    } else {
        if (mapBtn) mapBtn.style.display = 'none'; 
        if (locTitleLabel) locTitleLabel.textContent = "Поточна локація";
        if (locName) locName.textContent = currentRoom.name || "Палата #404";
        if (locDesc) locDesc.textContent = currentRoom.desc || "Твоє безпечне місце. Лікування та процедури.";
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
                    ${floor.unlocked ? 'План евакуації знайдено' : '🔒 План відсутній (Знайдіть ключ на поверху вище)'}
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
        alert("🛏️ Палата #404. Навіть у стані психозу тут віє слабким заспокійливим.");
    } else if (node.type === 'procedure') {
        openProcedureRoomBattle();
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
        alert("⚔️ Бій з Босом 10-го Поверху у праці!\nГотуйте зброю та стимулятори.");
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
                <span class="item-icon">${item.icon}</span>
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
    
    let bodyHtml = `<p style="color: #a3927d;">${item.desc || 'Немає опису предмета.'}</p>`;
    
    const isEquipped = (
        (item.category === 'weapon' && equippedGear.weapon === item.name) ||
        (item.category === 'helmet' && equippedGear.helmet === item.name) ||
        (item.category === 'armor' && equippedGear.armor === item.name)
    );

    const actionBtn = document.getElementById('item-action-btn');

    if (item.category === 'weapon') {
        bodyHtml += `<div style="color: #e74c3c; margin-top: 5px;"><strong>⚔️ Бонус до урону:</strong> +${item.damageBonus || 0}</div>`;
        if (actionBtn) actionBtn.textContent = isEquipped ? "Зняти" : "Озброїтися";
    } else if (item.category === 'armor' || item.category === 'helmet') {
        bodyHtml += `<div style="color: #3498db; margin-top: 5px;"><strong>🛡️ Бонус до броні:</strong> +${item.armorBonus || 0}</div>`;
        if (actionBtn) actionBtn.textContent = isEquipped ? "Зняти" : "Надіти спорядження";
    } else if (item.category === 'meds') {
        bodyHtml += `<div style="color: #2ecc71; margin-top: 5px;"><strong>⚡ Ефект препарату:</strong> ${item.effectDesc || 'Відновлює стан'}</div>`;
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
                    alert(`Ви зняли: ${selectedItemForAction.name}`);
                } else {
                    if (equippedGear.weapon) {
                        const oldWp = inventory.find(i => i.name === equippedGear.weapon);
                        if (oldWp) stats.damage -= (oldWp.damageBonus || 0);
                    }
                    stats.damage += (selectedItemForAction.damageBonus || 0);
                    equippedGear.weapon = selectedItemForAction.name;
                    alert(`Ви озброїлись: ${selectedItemForAction.name}! Урон тепер: ${stats.damage}`);
                }
            } else if (cat === 'armor' || cat === 'helmet') {
                if (equippedGear[cat] === selectedItemForAction.name) {
                    stats.armor -= (selectedItemForAction.armorBonus || 0);
                    equippedGear[cat] = null;
                    alert(`Ви зняли спорядження: ${selectedItemForAction.name}`);
                } else {
                    if (equippedGear[cat]) {
                        const oldArmor = inventory.find(i => i.name === equippedGear[cat]);
                        if (oldArmor) stats.armor -= (oldArmor.armorBonus || 0);
                    }
                    stats.armor += (selectedItemForAction.armorBonus || 0);
                    equippedGear[cat] = selectedItemForAction.name;
                    alert(`Ви наділи: ${selectedItemForAction.name}! Загальна броня: ${stats.armor}`);
                }
            } else if (cat === 'meds') {
                if (selectedItemForAction.count > 0) {
                    selectedItemForAction.count -= 1;
                    
                    if (selectedItemForAction.effectType === 'madness') {
                        stats.madness = Math.max(0, stats.madness - 15);
                        stats.pillsUsed = (stats.pillsUsed || 0) + 1;
                        alert("Ви прийняли таблетки «Аміназин». Божевілля зменшилось (-15).");
                    } else if (selectedItemForAction.effectType === 'stamina_10') {
                        stats.energy = Math.min(stats.maxEnergy, stats.energy + (stats.maxEnergy * 0.1));
                        alert("Ви випили енергетик (+10% витривалості).");
                    } else if (selectedItemForAction.effectType === 'stamina_full') {
                        stats.energy = stats.maxEnergy;
                        alert("Ви використали стимулятор. Витривалість повністю відновлена!");
                    } else if (selectedItemForAction.effectType === 'hp_10') {
                        stats.hp = Math.min(stats.maxHp, stats.hp + (stats.maxHp * 0.1));
                        alert("Ви використали малу аптечку. Здоров'я частково відновлено (+10%).");
                    } else if (selectedItemForAction.effectType === 'hp_full') {
                        stats.hp = stats.maxHp;
                        alert("Ви використали велику армійську аптечку. Здоров'я повністю відновлено!");
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
        container.innerHTML = `<p style="font-size:12px; color:#a3927d; text-align:center; padding: 20px 0;">Розділ [${currentWardrobeTab.toUpperCase()}] буде заповнений пізніше!</p>`;
    }
}

// === Система комплексних тренувань у лікарні (Спортзал) ===
let gymComplex = loadSaveData('palata404_gym', {
    exercises: [
        { id: 'squats', name: 'Присідання', icon: '🦵', current: 0, target: 15, energy: 2, madness: 1, exp: 5 },
        { id: 'pushups', name: 'Віджимання', icon: '💪', current: 0, target: 12, energy: 3, madness: 2, exp: 8 },
        { id: 'plank', name: 'Планка', icon: '🧘', current: 0, target: 10, energy: 4, madness: 2, exp: 10 },
        { id: 'pullups', name: 'Підтягування', icon: '🦾', current: 0, target: 8, energy: 5, madness: 3, exp: 14 },
        { id: 'stretching', name: 'Розтяжка', icon: '🤸', current: 0, target: 10, energy: 2, madness: 1, exp: 6 },
        { id: 'shadowbox', name: 'Бій з тінню', icon: '🥊', current: 0, target: 5, energy: 6, madness: 5, exp: 20 }
    ],
    completedRounds: 0
});

function openGym() {
    if (stats.madness >= 100) {
        alert("❌ Тренування неможливі в стані повного психозу! Реальність розпливається.");
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
    if (!ex) return;

    if (ex.current >= ex.target) {
        alert(`Цю вправу (${ex.name}) вже виконано до кінця в цьому циклі!`);
        return;
    }

    if (stats.energy < ex.energy) {
        alert("Занадто мало витривалості! Вона відновлюється автоматично з часом.");
        return;
    }

    stats.energy -= ex.energy;
    stats.madness = Math.min(100, stats.madness + ex.madness);
    
    ex.current += 1;
    addExperience(ex.exp);

    checkGymComplexCompletion();
    saveGymProgress();
    updateUI();
    renderGymModal();
}

function checkGymComplexCompletion() {
    let allDone = gymComplex.exercises.every(e => e.current >= e.target);
    if (allDone) {
        gymComplex.completedRounds += 1;
        stats.gymRounds = (stats.gymRounds || 0) + 1;
        stats.damage = (stats.damage || 10) + 3;
        addExperience(100);
        alert(`🏆 ВЕЛИКИЙ БАФ! Ви повністю завершили комплекс із 6 вправ!\n⚡ Базовий урон збільшено на +3!\n🎉 Отримано 100 EXP! Комплекс оновлено.`);
        gymComplex.exercises.forEach(e => e.current = 0);
    }
}

function renderGymModal() {
    const container = document.getElementById('gym-exercises-list');
    if (!container) return;
    container.innerHTML = '';

    gymComplex.exercises.forEach(ex => {
        let isDone = ex.current >= ex.target;
        let item = document.createElement('div');
        item.style.cssText = "display: flex; justify-content: space-between; align-items: center; background: #261f1a; padding: 8px 12px; border-radius: 6px; border: 1px solid #4a382c;";
        
        item.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 20px;">${ex.icon}</span>
                <div>
                    <strong style="color: ${isDone ? '#2ecc71' : '#fff8e7'};">${ex.name} ${isDone ? '✓' : ''}</strong>
                    <div style="font-size: 11px; color: #a3927d;">Прогрес: ${ex.current} / ${ex.target} | Витрата: ⚡${ex.energy}</div>
                </div>
            </div>
            <button class="btn-outfit" onclick="doGymExercise('${ex.id}')" ${isDone ? 'disabled style="opacity: 0.4; cursor: not-allowed;"' : ''}>
                ${isDone ? 'Виконано' : 'Робити'}
            </button>
        `;
        container.appendChild(item);
    });
}

// === Система навігації по Лікувальному корпусу та Процедурному кабінету ===
let currentRoom = {
    id: 'room_404',
    name: 'Палата #404',
    desc: 'Стіни шепочуть тобі... Твоє безпечне місце.'
};

const medicalRooms = [
    { id: 'room_404', name: 'Палата #404', icon: '🛏️', desc: 'Твоя власна палата. Тут можна перевести дух.' },
    { id: 'gym', name: 'Зал реабілітації (Спортзал)', icon: '🏋️', desc: 'Місце для комплексу фізичних вправ на базовий урон.' },
    { id: 'treatment_room', name: 'Процедурний кабінет', icon: '💉', desc: 'Тут видають ліки та медикаменти.' },
    { id: 'corridor', name: 'Коридор блоку', icon: '🚪', desc: 'Вихід у загальний коридор для зв\'язку з сусідами.' }
];

function openMedicalHub() {
    if (stats.madness >= 100) {
        alert("❌ Лікувальний корпус зачинений на карантин через ваш психоз!");
        return;
    }
    closeInventory();
    closeCustomization();
    closeFriends();
    closeSettings();
    closeGym();
    closeProcedureRoom();
    renderMedicalRooms();
    const modal = document.getElementById('medical-hub-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeMedicalHub() {
    const modal = document.getElementById('medical-hub-modal');
    if (modal) modal.classList.add('hidden');
}

function openProcedureRoom() {
    closeMedicalHub();
    const modal = document.getElementById('procedure-room-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeProcedureRoom() {
    const modal = document.getElementById('procedure-room-modal');
    if (modal) modal.classList.add('hidden');
}

function renderMedicalRooms() {
    const container = document.getElementById('rooms-list-container');
    if (!container) return;
    container.innerHTML = '';

    medicalRooms.forEach(room => {
        let isCurrent = currentRoom.id === room.id;
        let item = document.createElement('div');
        item.style.cssText = `display: flex; justify-content: space-between; align-items: center; background: ${isCurrent ? '#3d2e24' : '#261f1a'}; padding: 10px 12px; border-radius: 6px; border: 1px solid ${isCurrent ? '#8c684d' : '#4a382c'};`;
        
        let actionBtnHtml = room.id === 'treatment_room' 
            ? `<button class="btn-outfit" onclick="openProcedureRoom()">Відкрити</button>`
            : `<button class="btn-outfit" onclick="selectRoom('${room.id}')" ${isCurrent ? 'style="background: #8c684d; color: white;"' : ''}>${isCurrent ? 'Ви тут' : 'Перейти'}</button>`;

        item.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 22px;">${room.icon}</span>
                <div>
                    <strong style="color: ${isCurrent ? '#f39c12' : '#fff8e7'};">${room.name} ${isCurrent ? '(Тут)' : ''}</strong>
                    <div style="font-size: 11px; color: #a3927d; margin-top: 2px;">${room.desc}</div>
                </div>
            </div>
            ${actionBtnHtml}
        `;
        container.appendChild(item);
    });
}

function selectRoom(roomId) {
    let room = medicalRooms.find(r => r.id === roomId);
    if (!room) return;

    currentRoom = room;
    const nameElem = document.getElementById('current-location-name');
    const descElem = document.getElementById('current-location-desc');
    if (nameElem) nameElem.textContent = room.name;
    if (descElem) descElem.textContent = room.desc;
    closeMedicalHub();

    if (roomId === 'gym') {
        openGym();
    } else if (roomId === 'corridor') {
        alert("🚪 Коридор зустрічає тебе холодним світлом ламп і кроками охорони вдалині.");
    } else {
        alert("🛏️ Ти у своїй палаті #404.");
    }
}

function buyMedicalItem(itemType, cost, currencyType) {
    if (currencyType === 'silver') {
        if (stats.silver >= cost) stats.silver -= cost;
        else { alert('Не вистачає срібла!'); return; }
    } else if (currencyType === 'bucks') {
        if (stats.bucks >= cost) stats.bucks -= cost;
        else { alert('Не вистачає баксів ($)!'); return; }
    }

    let newItemData = null;
    if (itemType === 'madness_pills') {
        newItemData = { name: 'Таблетки «Аміназин»', icon: '💊', category: 'meds', effectType: 'madness', effectDesc: 'Знижує божевілля на -15', desc: 'Препарат стримання психіки із запасів медпункту.' };
    } else if (itemType === 'stamina_10') {
        newItemData = { name: 'Енергетик «Психо-Кола»', icon: '⚡', category: 'meds', effectType: 'stamina_10', effectDesc: 'Відновлює 10% витривалості', desc: 'Тонізуючий газований напій.' };
    } else if (itemType === 'stamina_full') {
        newItemData = { name: 'Стимулятор «Адреналін-Фул»', icon: '💉', category: 'meds', effectType: 'stamina_full', effectDesc: 'Повне відновлення витривалості', desc: 'Армійська ін\'єкція.' };
    } else if (itemType === 'hp_10') {
        newItemData = { name: 'Мала аптечка', icon: '🧪', category: 'meds', effectType: 'hp_10', effectDesc: 'Відновлює 10% здоров\'я (HP)', desc: 'Індивідуальний пакет.' };
    } else if (itemType === 'hp_full') {
        newItemData = { name: 'Велика армійська аптечка', icon: '🩹', category: 'meds', effectType: 'hp_full', effectDesc: 'Повне відновлення здоров\'я (HP)', desc: 'Герметичний армійський контейнер.' };
    }

    if (newItemData) {
        let existingItem = inventory.find(i => i.name === newItemData.name);
        if (existingItem) {
            existingItem.count = (existingItem.count || 1) + 1;
        } else {
            inventory.push({ ...newItemData, count: 1 });
        }
        alert(`Придбано та додано до інвентаря: ${newItemData.name} (${newItemData.icon})!`);
    }

    updateUI();
    saveGameProgress();
}

const ENERGY_REGEN_TIME_MS = 2 * 60 * 1000;

function updateEnergyTimer() {
    let energyTimerElem = document.getElementById('energy-timer');
    if (!energyTimerElem) return;

    if (stats.energy >= stats.maxEnergy) {
        energyTimerElem.textContent = "ПОВНА";
        return;
    }

    let lastTimeStr = localStorage.getItem('palata404_last_time');
    if (!lastTimeStr) {
        localStorage.setItem('palata404_last_time', Date.now().toString());
        return;
    }

    let lastTime = parseInt(lastTimeStr, 10);
    let now = Date.now();
    let elapsedMs = now - lastTime;
    let timeLeftMs = ENERGY_REGEN_TIME_MS - (elapsedMs % ENERGY_REGEN_TIME_MS);
    
    if (elapsedMs >= ENERGY_REGEN_TIME_MS) {
        let added = Math.floor(elapsedMs / ENERGY_REGEN_TIME_MS);
        stats.energy = Math.min(stats.maxEnergy, stats.energy + added);
        let leftoverMs = elapsedMs % ENERGY_REGEN_TIME_MS;
        localStorage.setItem('palata404_last_time', (now - leftoverMs).toString());
        updateUI();
    }

    let totalSeconds = Math.ceil(timeLeftMs / 1000);
    let minutes = Math.floor(totalSeconds / 60);
    let seconds = totalSeconds % 60;
    
    energyTimerElem.textContent = `(+1 за ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')})`;
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

    const nameElem = document.getElementById('dossier-name');
    if (nameElem) nameElem.textContent = playerName;

    const modal = document.getElementById('dossier-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeDossier() {
    const modal = document.getElementById('dossier-modal');
    if (modal) modal.classList.add('hidden');
}

function handleLocationClick() {
    if (stats.madness >= 100) {
        alert("❌ Доступ до лікувального корпусу заблоковано! Розум охоплений психозом. Ідіть на Карту або прийміть таблетки «Аміназин».");
        toggleMapModal(true);
    } else {
        openMedicalHub();
    }
}


// ==========================================
// БОЙОВА СИСТЕМА: СЕСТРА КЛАРА (ПОВНА ТА СТАБІЛЬНА)
// ==========================================

let bossCurrentHp = 120;
let bossMaxHp = 120;
let nurseKillsCount = 0;

let isBattleActive = false;
let raidTimeRemaining = 300;
let raidTimerInterval = null;

let playerAttackCooldown = false;
let friendAttackInterval = null;

let raidMembers = [
    { id: 'player', name: 'Пацієнт #404', damage: 0, isPlayer: true, active: true },
    { id: 'friend_1', name: 'Сусід з палати #402 (Сліпий Микола)', damage: 0, active: false, called: false },
    { id: 'friend_2', name: 'Пацієнтка #410 (Мері)', damage: 0, active: false, called: false },
    { id: 'friend_3', name: 'Буйний сусіда з ізолятора', damage: 0, active: false, called: false }
];

function openProcedureRoomBattle() {
    if (stats.madness < 100) {
        alert("У нормальному стані процедурний кабінет зачинений.");
        return;
    }
    const killsElem = document.getElementById('dossier-kills-count');
    if (killsElem) killsElem.textContent = nurseKillsCount;

    const dossierModal = document.getElementById('nurse-dossier-modal');
    if (dossierModal) dossierModal.classList.remove('hidden');
}

function closeNurseDossier() {
    const dossierModal = document.getElementById('nurse-dossier-modal');
    if (dossierModal) dossierModal.classList.add('hidden');
}

function startNurseFight() {
    closeNurseDossier();
    closeProcedureRoom();
    closeMedicalHub();
    if (typeof toggleMapModal === 'function') {
        toggleMapModal(false);
    }
    
    stats.hp = stats.maxHp;
    if (typeof updateUI === 'function') updateUI();

    bossCurrentHp = bossMaxHp;
    playerAttackCooldown = false;
    isBattleActive = true;
    raidTimeRemaining = 300;

    let currentName = 'Пацієнт #404';
    if (typeof playerName !== 'undefined' && playerName) {
        currentName = playerName;
    }

    raidMembers.forEach(m => {
        m.damage = 0;
        if (m.isPlayer) {
            m.name = currentName;
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
}

function closeNurseBattle() {
    const battleModal = document.getElementById('nurse-battle-modal');
    if (battleModal) {
        battleModal.classList.add('hidden');
        battleModal.style.display = 'none';
    }
    
    const raidPanel = document.getElementById('battle-raid-panel');
    if (raidPanel) raidPanel.classList.add('hidden');

    updateLobbyRaidWidget();
}

function minimizeNurseBattle() {
    const battleModal = document.getElementById('nurse-battle-modal');
    if (battleModal) {
        battleModal.classList.add('hidden');
        battleModal.style.display = 'none';
    }
    
    const raidPanel = document.getElementById('battle-raid-panel');
    if (raidPanel) raidPanel.classList.add('hidden');

    updateLobbyRaidWidget();
}

function reopenNurseBattle() {
    if (!isBattleActive) return;
    updateBattleUI();
    const battleModal = document.getElementById('nurse-battle-modal');
    if (battleModal) {
        battleModal.classList.remove('hidden');
        battleModal.style.display = 'flex';
    }
}

function updateRaidTimerTick() {
    if (!isBattleActive) return;

    raidTimeRemaining--;
    let mins = Math.floor(raidTimeRemaining / 60);
    let secs = raidTimeRemaining % 60;
    let timeStr = `${mins < 10 ? '0' : ''}${mins}:${secs < 10 ? '0' : ''}${secs}`;

    const arenaTimerElem = document.getElementById('battle-timer-display');
    if (arenaTimerElem) arenaTimerElem.textContent = timeStr;

    updateLobbyRaidWidget(timeStr);

    if (raidTimeRemaining <= 0) {
        handleRaidTimeOut();
    }
}

function updateLobbyRaidWidget(timeStr = '') {
    const raidBtn = document.querySelector('.raid-btn, #raid-menu-btn');
    if (!raidBtn) return;

    let subTimer = document.getElementById('lobby-raid-subtimer');
    if (isBattleActive) {
        if (!subTimer) {
            subTimer = document.createElement('div');
            subTimer.id = 'lobby-raid-subtimer';
            subTimer.style.cssText = 'font-size:10px; color:#e74c3c; font-weight:bold; text-align:center; margin-top:2px;';
            raidBtn.appendChild(subTimer);
        }
        subTimer.textContent = timeStr || 'В БОЮ (Натисніть)';
        raidBtn.onclick = reopenNurseBattle;
    } else {
        if (subTimer) subTimer.remove();
    }
}

function handleRaidTimeOut() {
    isBattleActive = false;
    if (raidTimerInterval) clearInterval(raidTimerInterval);
    if (friendAttackInterval) clearInterval(friendAttackInterval);

    closeNurseBattle();
    alert("⏱️ Час рейду вичерпано!");
    updateLobbyRaidWidget();
}

function showCustomToast(message) {
    const toast = document.getElementById('custom-toast-notification');
    const msgElem = document.getElementById('toast-message');
    if (!toast || !msgElem) return;

    msgElem.textContent = message;
    toast.classList.remove('hidden');
    toast.style.opacity = '1';

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.classList.add('hidden'), 300);
    }, 2200);
}

function toggleRaidPanel() {
    const panel = document.getElementById('battle-raid-panel');
    if (panel) {
        panel.classList.toggle('hidden');
        if (!panel.classList.contains('hidden')) {
            updateRaidListUI();
        }
    }
}

function openFriendInviteModal() {
    renderFriendsCheckboxList();
    const modal = document.getElementById('friend-invite-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeFriendInviteModal() {
    const modal = document.getElementById('friend-invite-modal');
    if (modal) modal.classList.add('hidden');
}

function renderFriendsCheckboxList(filterText = '') {
    const container = document.getElementById('friends-checkbox-container');
    if (!container) return;

    let availableFriends = raidMembers.filter(m => !m.isPlayer);
    if (filterText) {
        availableFriends = availableFriends.filter(f => f.name.toLowerCase().includes(filterText.toLowerCase()));
    }

    container.innerHTML = availableFriends.map(f => `
        <label style="background: #15100c; border: 1px solid #3d2d22; padding: 10px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; font-size: 13px;">
            <span style="color: ${f.called ? '#27ae60' : '#f4e8d1'};">${f.name} ${f.called ? '(Вже покликано)' : ''}</span>
            <input type="checkbox" value="${f.id}" class="friend-checkbox" ${f.called ? 'checked' : ''} style="width: 18px; height: 18px; accent-color: #8e44ad;">
        </label>
    `).join('');
}

function filterFriendsList() {
    const input = document.getElementById('friend-search-input');
    if (input) renderFriendsCheckboxList(input.value);
}

function callSelectedFriends() {
    let checkboxes = document.querySelectorAll('.friend-checkbox:checked');
    let calledCount = 0;

    checkboxes.forEach(cb => {
        let member = raidMembers.find(m => m.id === cb.value);
        if (member && !member.called) {
            member.called = true;
            member.active = true;
            calledCount++;
        }
    });

    closeFriendInviteModal();
    const panel = document.getElementById('battle-raid-panel');
    if (panel && !panel.classList.contains('hidden')) {
        updateRaidListUI();
    }
    if (calledCount > 0) {
        showCustomToast(`📢 Успішно покликано друзів: ${calledCount}!`);
    }
}

function callAllFriends() {
    raidMembers.forEach(m => {
        if (!m.isPlayer) {
            m.called = true;
            m.active = true;
        }
    });

    closeFriendInviteModal();
    const panel = document.getElementById('battle-raid-panel');
    if (panel && !panel.classList.contains('hidden')) {
        updateRaidListUI();
    }
    showCustomToast("🔥 Усі доступні друзі приєдналися до рейду!");
}

function updateRaidListUI() {
    const container = document.getElementById('raid-members-container');
    if (!container) return;

    let activeParticipants = raidMembers.filter(m => m.isPlayer || m.called);

    container.innerHTML = activeParticipants.map(m => {
        let statusColor = m.isPlayer || m.active ? '#27ae60' : '#7f8c8d';
        let statusText = m.isPlayer ? 'Головний гравець' : 'Бере участь';
        return `
            <div style="background: #15100c; border: 1px solid #3d2d22; padding: 6px 10px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; font-size: 11px;">
                <div>
                    <div style="font-weight: bold; color: ${m.isPlayer ? '#e67e22' : '#f4e8d1'};">${m.name}</div>
                    <div style="font-size: 9px; color: ${statusColor};">${statusText}</div>
                </div>
                <div style="text-align: right; color: #e74c3c; font-weight: bold;">
                    ${m.damage} DMG
                </div>
            </div>
        `;
    }).join('');
}

function showFloatingDamage(text, isPlayerHit = false, customX = null, customY = null) {
    const container = document.getElementById('damage-floating-container');
    if (!container) return;

    const el = document.createElement('div');
    el.textContent = text;
    
    let randomX = customX !== null ? customX : (window.innerWidth / 2 + (Math.random() * 100 - 50));
    let randomY = customY !== null ? customY : (window.innerHeight / 2 - (Math.random() * 60));

    el.style.position = 'fixed';
    el.style.left = `${randomX}px`;
    el.style.top = `${randomY}px`;
    el.style.color = isPlayerHit ? '#e74c3c' : '#f39c12';
    el.style.fontSize = '24px';
    el.style.fontWeight = 'bold';
    el.style.textShadow = '0 0 4px #000, 0 0 8px #000';
    el.style.zIndex = '99999';
    el.style.pointerEvents = 'none';
    el.style.transition = 'all 0.8s ease-out';
    
    container.appendChild(el);

    setTimeout(() => {
        el.style.transform = 'translateY(-60px) scale(1.2)';
        el.style.opacity = '0';
    }, 50);

    setTimeout(() => {
        el.remove();
    }, 850);
}

// Ефектний удар Медсестри з наближенням та струсом екрана
function triggerBossAttackAnimation() {
    const bossSprite = document.getElementById('nurse-boss-sprite');
    const arenaScreen = document.getElementById('battle-arena-screen');

    if (bossSprite) {
        bossSprite.classList.remove('boss-attacking');
        void bossSprite.offsetWidth; 
        bossSprite.classList.add('boss-attacking');

        setTimeout(() => {
            if (arenaScreen) {
                arenaScreen.classList.remove('shake-effect');
                void arenaScreen.offsetWidth;
                arenaScreen.classList.add('shake-effect');
            }
        }, 200);

        setTimeout(() => {
            bossSprite.classList.remove('boss-attacking');
            if (arenaScreen) arenaScreen.classList.remove('shake-effect');
        }, 550);
    }
}

function openFleeConfirmModal() {
    let modal = document.getElementById('flee-confirm-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'flee-confirm-modal';
        modal.style.cssText = "position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.8); z-index: 50000; display: flex; align-items: center; justify-content: center;";
        modal.innerHTML = `
            <div style="background: #1c1511; border: 2px solid #e74c3c; width: 400px; padding: 25px; border-radius: 12px; color: #f4e8d1; text-align: center; font-family: sans-serif; box-shadow: 0 0 30px rgba(231,76,60,0.4);">
                <div style="font-size: 35px; margin-bottom: 10px;">⚠️</div>
                <h3 style="color: #e74c3c; margin: 0 0 10px 0;">Втеча з бою</h3>
                <p style="font-size: 13px; color: #bdaea0; margin-bottom: 20px;">Ви дійсно хочете втекти? Це коштуватиме вам штрафу у <strong>20 срібла</strong>, а рейд буде провалено.</p>
                <div style="display: flex; gap: 12px;">
                    <button class="btn-outfit" style="flex: 1; background: #e74c3c; padding: 10px; font-weight: bold; cursor: pointer; border-radius: 6px; color: #fff;" onclick="confirmFleeBattle()">Втекти (-20 🪙)</button>
                    <button class="btn-outfit" style="flex: 1; background: #7f8c8d; padding: 10px; font-weight: bold; cursor: pointer; border-radius: 6px; color: #fff;" onclick="closeFleeConfirmModal()">Залишитись</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    } else {
        modal.style.display = 'flex';
    }
}

function closeFleeConfirmModal() {
    const modal = document.getElementById('flee-confirm-modal');
    if (modal) modal.style.display = 'none';
}

function confirmFleeBattle() {
    closeFleeConfirmModal();

    stats.silver = Math.max(0, (stats.silver || 0) - 20);
    if (typeof updateUI === 'function') updateUI();

    isBattleActive = false;
    if (raidTimerInterval) clearInterval(raidTimerInterval);
    if (friendAttackInterval) clearInterval(friendAttackInterval);

    const battleModal = document.getElementById('nurse-battle-modal');
    if (battleModal) {
        battleModal.classList.add('hidden');
        battleModal.style.display = 'none';
    }
    
    const raidPanel = document.getElementById('battle-raid-panel');
    if (raidPanel) raidPanel.classList.add('hidden');

    const subTimer = document.getElementById('lobby-raid-subtimer');
    if (subTimer) subTimer.remove();

    if (typeof showCustomToast === 'function') {
        showCustomToast("💨 Ви втекли з поля бою (Штраф: -20 срібла)");
    }
}

function performPlayerAttack(event) {
    if (playerAttackCooldown || bossCurrentHp <= 0 || !isBattleActive) return;

    let dmg = stats.damage || 10;
    bossCurrentHp = Math.max(0, bossCurrentHp - dmg);

    let playerMember = raidMembers.find(m => m.isPlayer);
    if (playerMember) playerMember.damage += dmg;

    let clickX = event ? event.clientX : window.innerWidth / 2;
    let clickY = event ? event.clientY : window.innerHeight / 2;
    
    showFloatingDamage(`-${dmg}`, false, clickX, clickY);

    const panel = document.getElementById('battle-raid-panel');
    if (panel && !panel.classList.contains('hidden')) {
        updateRaidListUI();
    }

    if (bossCurrentHp <= 0) {
        handleVictory();
        return;
    }

    playerAttackCooldown = true;
    let arena = document.getElementById('battle-arena-screen');
    if (arena) arena.style.cursor = 'not-allowed';

    setTimeout(() => {
        playerAttackCooldown = false;
        if (arena && bossCurrentHp > 0) arena.style.cursor = 'pointer';
    }, 4000);

    setTimeout(() => {
        if (bossCurrentHp <= 0 || !isBattleActive) return;

        triggerBossAttackAnimation();

        let counter = 12;
        stats.hp = Math.max(0, stats.hp - counter);

        showFloatingDamage(`-${counter} HP`, true, window.innerWidth / 2, window.innerHeight / 2 - 80);

        if (stats.hp <= 0) {
            isBattleActive = false;
            alert("💀 Сестра Клара вас здолала...");
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
            let friendDmg = Math.floor(Math.random() * 8) + 4;
            bossCurrentHp = Math.max(0, bossCurrentHp - friendDmg);
            m.damage += friendDmg;
            
            showFloatingDamage(`${m.name.split(' ')[0]}: -${friendDmg}`, false, window.innerWidth / 2 + (Math.random() * 80 - 40), window.innerHeight / 2);

            const panel = document.getElementById('battle-raid-panel');
            if (panel && !panel.classList.contains('hidden')) {
                updateRaidListUI();
            }

            if (bossCurrentHp <= 0) {
                handleVictory();
            }
        }
    });
}

function handleVictory() {
    isBattleActive = false;
    if (raidTimerInterval) clearInterval(raidTimerInterval);
    if (friendAttackInterval) clearInterval(friendAttackInterval);
    
    nurseKillsCount++;
    closeNurseBattle();
    updateLobbyRaidWidget();

    let minThreshold = bossMaxHp * 0.10;
    let playerMember = raidMembers.find(m => m.isPlayer);
    let playerEarnedReward = playerMember && playerMember.damage >= minThreshold;

    if (playerEarnedReward) {
        stats.silver = (stats.silver || 0) + 30;
        addExperience(50);

        let questKey = {
            name: 'Ключ від блоку боса',
            icon: '🔑',
            category: 'quest',
            count: 1,
            desc: 'Добутий після усунення медсестри.'
        };
        if (!inventory.some(i => i.name === questKey.name)) {
            inventory.push(questKey);
        }
    }

    let activeParticipants = raidMembers.filter(m => m.isPlayer || m.called);
    let sortedRaid = [...activeParticipants].sort((a, b) => b.damage - a.damage);
    let mvp = sortedRaid[0];

    let summaryHtml = `<div style="font-weight: bold; font-size: 15px; color: #f39c12; margin-bottom: 10px; text-align: center;">👑 MVP РЕЙДУ: ${mvp.name} — ${mvp.damage} DMG</div>`;
    sortedRaid.forEach(m => {
        let gotReward = m.damage >= minThreshold;
        let badge = gotReward ? '<span style="color:#27ae60;">[Отримав нагороду]</span>' : '<span style="color:#e74c3c;">[Халтурщик]</span>';
        summaryHtml += `<div style="display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 12px;"><span>• ${m.name} (${m.damage} DMG)</span> <span>${badge}</span></div>`;
    });

    const summaryElem = document.getElementById('victory-raid-summary');
    if (summaryElem) summaryElem.innerHTML = summaryHtml;

    const victoryModal = document.getElementById('nurse-victory-modal');
    if (victoryModal) victoryModal.classList.remove('hidden');
    
    updateUI();
}

function victoryContinueToMap() {
    const modal = document.getElementById('nurse-victory-modal');
    if (modal) modal.classList.add('hidden');
}

function victoryRestartFight() {
    const modal = document.getElementById('nurse-victory-modal');
    if (modal) modal.classList.add('hidden');
    startNurseFight();
}

function updateBattleUI() {
    const playerNameElem = document.getElementById('b-player-name');
    if (playerNameElem) {
        playerNameElem.textContent = playerName;
    }

    const battleAvatarBox = document.getElementById('player-battle-avatar-box');
    const lobbyAvatar = document.querySelector('.player-avatar img, #player-avatar img');
    if (battleAvatarBox && lobbyAvatar) {
        battleAvatarBox.innerHTML = `<img src="${lobbyAvatar.src}" style="width:100%; height:100%; object-fit:cover;">`;
    }

    const pHpElem = document.getElementById('b-player-hp');
    if (pHpElem) pHpElem.textContent = `${stats.hp}/${stats.maxHp}`;
    
    let pPercent = Math.max(0, (stats.hp / stats.maxHp) * 100);
    const pHpBar = document.getElementById('b-player-hpbar');
    if (pHpBar) pHpBar.style.width = `${pPercent}%`;

    const bHpElem = document.getElementById('b-boss-hp');
    if (bHpElem) bHpElem.textContent = `${bossCurrentHp}/${bossMaxHp}`;
    
    let bPercent = Math.max(0, (bossCurrentHp / bossMaxHp) * 100);
    const bHpBar = document.getElementById('b-boss-hpbar');
    if (bHpBar) bHpBar.style.width = `${bPercent}%`;

    let smallMeds = inventory.filter(i => i.name === 'Мала аптечка' || i.category === 'meds').reduce((acc, item) => acc + (item.count || 1), 0);
    let bigMeds = inventory.filter(i => i.name === 'Велика армійська аптечка' || i.name === 'Велика аптечка').reduce((acc, item) => acc + (item.count || 1), 0);

    const countSmall = document.getElementById('medkit-count-small');
    if (countSmall) countSmall.textContent = smallMeds;

    const countBig = document.getElementById('medkit-count-big');
    if (countBig) countBig.textContent = bigMeds;
}

function useBattleMedkit(type) {
    let medName = type === 'big' ? 'Велика армійська аптечка' : 'Мала аптечка';
    let medItem = inventory.find(i => i.name === medName || (type === 'small' && i.category === 'meds'));

    if (medItem && medItem.count > 0) {
        medItem.count--;
        if (medItem.count <= 0) {
            inventory = inventory.filter(i => i !== medItem);
        }
        let healAmount = type === 'big' ? 50 : 20;
        stats.hp = Math.min(stats.maxHp, stats.hp + healAmount);
        updateBattleUI();
        updateUI();
    }
}
// === КЕРУВАННЯ КНОПКОЮ ТА ВІДЖЕТОМ РЕЙДУ У ЛОБІ ===

// Дія при натисканні на кнопку рейду у верхній панелі
function handleRaidButtonAction() {
    if (typeof isBattleActive !== 'undefined' && isBattleActive) {
        reopenNurseBattle(); // Якщо бій йде — повертаємося до нього
    } else {
        alert("Зараз немає активних рейдів. Перейдіть на карту до процедурного кабінету, щоб почати штурм.");
    }
}

// Оновлення віджета рейду та таймера під кнопкою
function updateLobbyRaidWidget(timeStr = '') {
    const raidBtn = document.getElementById('nav-raid-btn');
    if (!raidBtn) return;

    let subTimer = document.getElementById('lobby-raid-subtimer');

    if (typeof isBattleActive !== 'undefined' && isBattleActive) {
        raidBtn.style.borderColor = '#e74c3c';
        raidBtn.style.background = 'rgba(192, 57, 43, 0.3)';
        
        if (!subTimer) {
            subTimer = document.createElement('div');
            subTimer.id = 'lobby-raid-subtimer';
            subTimer.style.cssText = 'position: absolute; bottom: -14px; left: 50%; transform: translateX(-50%); font-size: 9px; color: #e74c3c; font-weight: bold; white-space: nowrap; background: rgba(0,0,0,0.8); padding: 1px 4px; border-radius: 3px; pointer-events: none;';
            raidBtn.style.position = 'relative';
            raidBtn.appendChild(subTimer);
        }
        subTimer.textContent = timeStr || '05:00';
    } else {
        raidBtn.style.borderColor = '';
        raidBtn.style.background = '';
        if (subTimer) subTimer.remove();
    }
}