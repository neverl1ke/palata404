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
    document.getElementById('my-unique-id').textContent = playerInfo.type === 'telegram' 
        ? `Telegram: ${playerInfo.name} (ID: ${playerInfo.id})` 
        : `Браузер ID: ${playerInfo.id}`;

    renderFriendsList();
    document.getElementById('friends-modal').classList.remove('hidden');
}

function closeFriends() {
    document.getElementById('friends-modal').classList.add('hidden');
}

function addFriend() {
    const input = document.getElementById('friend-input');
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

    faceImg.classList.add('hidden');

    if (currentHair) {
        hairImg.src = currentHair;
        hairImg.classList.remove('hidden');
    } else {
        hairImg.classList.add('hidden');
    }

    if (currentClothes) {
        clothesImg.src = currentClothes;
        clothesImg.classList.remove('hidden');
    } else {
        clothesImg.classList.add('hidden');
    }
}

 function updateUI() {
    const hpValElem = document.getElementById('hp-val');
    if (hpValElem) hpValElem.textContent = `${stats.hp} / ${stats.maxHp}`;

    document.getElementById('madness-val').textContent = `${stats.madness} / 100`;
    document.getElementById('energy-val').textContent = `${stats.energy} / ${stats.maxEnergy}`;

    document.getElementById('madness-bar').style.width = `${Math.min(100, stats.madness)}%`;
    document.getElementById('energy-bar').style.width = `${Math.min(100, (stats.energy / stats.maxEnergy) * 100)}%`;

    document.getElementById('silver-val').textContent = stats.silver || 0;
    document.getElementById('pills-val').textContent = stats.pills || 0;
    document.getElementById('bucks-val').textContent = stats.bucks || 0;

    document.getElementById('damage-val').textContent = stats.damage || 10;
    document.getElementById('armor-val').textContent = stats.armor || 0;

    document.getElementById('player-lvl').textContent = stats.level;
    document.getElementById('player-rank').textContent = getPlayerRank(stats.level);
    document.getElementById('exp-val').textContent = `${stats.exp} / ${stats.nextLvlExp} EXP`;
    
    let expPercent = (stats.exp / stats.nextLvlExp) * 100;
    document.getElementById('exp-bar').style.width = `${Math.min(100, expPercent)}%`;

    updateCharacterLayers();
    updatePlayerNameDisplay();
    saveGameProgress();

    // === ПЕРЕМИКАННЯ СТАНІВ: НОРМА vs ПСИХОЗ (100% божевілля) ===
    const mapBtn = document.getElementById('nav-map-btn');
    if (stats.madness >= 100) {
        // ПСИХОЗ: Кнопка карти з'являється
        if (mapBtn) mapBtn.style.display = 'flex'; // або 'block', залежно від твого CSS
    } else {
        // НОРМА: Кнопка карти ПОВНІСТЮ ЗНИКАЄ
        if (mapBtn) mapBtn.style.display = 'none'; 
    }
    const locName = document.getElementById('current-location-name');
    const locDesc = document.getElementById('current-location-desc');
    const locTitleLabel = document.getElementById('loc-title-label');
    const locCardBox = document.getElementById('location-card-box');

    if (stats.madness >= 100) {
        // ПСИХОЗ: Карта з'являється, доступ до корпусу блокується
        if (mapBtn) mapBtn.style.display = 'flex'; 
        if (locTitleLabel) locTitleLabel.textContent = "⚠️ СИСТЕМНИЙ ЗБІЙ";
        if (locName) locName.textContent = "ПОМИЛКА 404: Невідомо";
        if (locDesc) locDesc.textContent = "Реальність втрачено. Спокійний корпус недоступний. Час виходити в коридори...";
        if (locCardBox) locCardBox.style.borderColor = "#c0392b";
    } else {
        // НОРМА: Карта повністю зникає, працює лікувальний корпус
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
        // Запускаємо ланцюжок: спочатку відкриваємо Досьє Медсестри
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
    document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettings() {
    document.getElementById('settings-modal').classList.add('hidden');
}

function openBank() {
    document.getElementById('bank-modal').classList.remove('hidden');
}

function closeBank() {
    document.getElementById('bank-modal').classList.add('hidden');
}

function openInventory() {
    closeCustomization();
    closeFriends();
    closeDossier();
    renderMinecraftStash();
    document.getElementById('inventory-modal').classList.remove('hidden');
}

function closeInventory() {
    document.getElementById('inventory-modal').classList.add('hidden');
}

function setCategoryFilter(category, btnElem) {
    currentCategory = category;
    btnElem.parentElement.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    if (btnElem) btnElem.classList.add('active');
    renderMinecraftStash();
}

function renderMinecraftStash() {
    const container = document.getElementById('stash-items');
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

// === Система перегляду та екіпіровки/використання предметів ===
function openItemInfo(item) {
    selectedItemForAction = item;
    document.getElementById('item-info-title').textContent = `${item.icon} ${item.name}`;
    
    let bodyHtml = `<p style="color: #a3927d;">${item.desc || 'Немає опису предмета.'}</p>`;
    
    const isEquipped = (
        (item.category === 'weapon' && equippedGear.weapon === item.name) ||
        (item.category === 'helmet' && equippedGear.helmet === item.name) ||
        (item.category === 'armor' && equippedGear.armor === item.name)
    );

    if (item.category === 'weapon') {
        bodyHtml += `<div style="color: #e74c3c; margin-top: 5px;"><strong>⚔️ Бонус до урону:</strong> +${item.damageBonus || 0}</div>`;
        document.getElementById('item-action-btn').textContent = isEquipped ? "Зняти" : "Озброїтися";
    } else if (item.category === 'armor' || item.category === 'helmet') {
        bodyHtml += `<div style="color: #3498db; margin-top: 5px;"><strong>🛡️ Бонус до броні:</strong> +${item.armorBonus || 0}</div>`;
        document.getElementById('item-action-btn').textContent = isEquipped ? "Зняти" : "Надіти спорядження";
    } else if (item.category === 'meds') {
        bodyHtml += `<div style="color: #2ecc71; margin-top: 5px;"><strong>⚡ Ефект препарату:</strong> ${item.effectDesc || 'Відновлює стан'}</div>`;
        document.getElementById('item-action-btn').textContent = "Використати";
    } else {
        document.getElementById('item-action-btn').textContent = "Закрити";
    }

    document.getElementById('item-info-body').innerHTML = bodyHtml;
    document.getElementById('item-info-modal').classList.remove('hidden');
}

function closeItemInfo() {
    document.getElementById('item-info-modal').classList.add('hidden');
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
    document.getElementById('custom-modal').classList.remove('hidden');
}

function closeCustomization() {
    document.getElementById('custom-modal').classList.add('hidden');
}

function setWardrobeTab(tab, btnElem) {
    currentWardrobeTab = tab;
    btnElem.parentElement.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    if (btnElem) btnElem.classList.add('active');
    renderWardrobe();
}

function renderWardrobe() {
    const container = document.getElementById('wardrobe-container');
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
    closeInventory();
    closeCustomization();
    closeFriends();
    closeSettings();
    closeDossier();
    closeMedicalHub();
    renderGymModal();
    document.getElementById('gym-modal').classList.remove('hidden');
}

function closeGym() {
    document.getElementById('gym-modal').classList.add('hidden');
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

function saveGymProgress() {
    localStorage.setItem('palata404_gym', JSON.stringify(gymComplex));
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
    { 
        id: 'room_404', 
        name: 'Палата #404', 
        icon: '🛏️', 
        desc: 'Твоя власна палата. Тут можна перевести дух.' 
    },
    { 
        id: 'gym', 
        name: 'Зал реабілітації (Спортзал)', 
        icon: '🏋️', 
        desc: 'Місце для комплексу фізичних вправ на базовий урон.' 
    },
    { 
        id: 'treatment_room', 
        name: 'Процедурний кабінет', 
        icon: '💉', 
        desc: 'Тут видають ліки та медикаменти.' 
    },
    { 
        id: 'corridor', 
        name: 'Коридор блоку', 
        icon: '🚪', 
        desc: 'Вихід у загальний коридор для зв\'язку з сусідами.' 
    }
];

function openMedicalHub() {
    closeInventory();
    closeCustomization();
    closeFriends();
    closeSettings();
    closeDossier();
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
        
        let actionBtnHtml = '';
        if (room.id === 'treatment_room') {
            actionBtnHtml = `<button class="btn-outfit" onclick="openProcedureRoom()">Відкрити</button>`;
        } else {
            actionBtnHtml = `<button class="btn-outfit" onclick="selectRoom('${room.id}')" ${isCurrent ? 'style="background: #8c684d; color: white;"' : ''}>
                ${isCurrent ? 'Ви тут' : 'Перейти'}
            </button>`;
        }

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
    document.getElementById('current-location-name').textContent = room.name;
    document.getElementById('current-location-desc').textContent = room.desc;
    closeMedicalHub();

    if (roomId === 'gym') {
        openGym();
    } else if (roomId === 'corridor') {
        alert("🚪 Коридор зустрічає тебе холодним світлом ламп і кроками охорони вдалині.");
    } else {
        alert("🛏️ Ти у своїй палаті #404.");
    }
}

// === Логіка купівлі препаратів (додавання в інвентар) ===
function buyMedicalItem(itemType, cost, currencyType) {
    if (currencyType === 'silver') {
        if (stats.silver >= cost) {
            stats.silver -= cost;
        } else {
            alert('Не вистачає срібла!');
            return;
        }
    } else if (currencyType === 'bucks') {
        if (stats.bucks >= cost) {
            stats.bucks -= cost;
        } else {
            alert('Не вистачає баксів ($)!');
            return;
        }
    }

    let newItemData = null;

    if (itemType === 'madness_pills') {
        newItemData = {
            name: 'Таблетки «Аміназин»',
            icon: '💊',
            category: 'meds',
            effectType: 'madness',
            effectDesc: 'Знижує божевілля на -15',
            desc: 'Препарат стримання психіки із запасів медпункту.'
        };
    } else if (itemType === 'stamina_10') {
        newItemData = {
            name: 'Енергетик «Психо-Кола»',
            icon: '⚡',
            category: 'meds',
            effectType: 'stamina_10',
            effectDesc: 'Відновлює 10% витривалості',
            desc: 'Тонізуючий газований напій сумнівної якості.'
        };
    } else if (itemType === 'stamina_full') {
        newItemData = {
            name: 'Стимулятор «Адреналін-Фул»',
            icon: '💉',
            category: 'meds',
            effectType: 'stamina_full',
            effectDesc: 'Повне відновлення витривалості',
            desc: 'Армійська ін\'єкція в шприц-тюбику.'
        };
    } else if (itemType === 'hp_10') {
        newItemData = {
            name: 'Мала аптечка',
            icon: '🧪',
            category: 'meds',
            effectType: 'hp_10',
            effectDesc: 'Відновлює 10% здоров\'я (HP)',
            desc: 'Індивідуальний пакет із антисептиком.'
        };
    } else if (itemType === 'hp_full') {
        newItemData = {
            name: 'Велика армійська аптечка',
            icon: '🩹',
            category: 'meds',
            effectType: 'hp_full',
            effectDesc: 'Повне відновлення здоров\'я (HP)',
            desc: 'Герметичний армійський контейнер медикаментів.'
        };
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

// === Фоновий таймер регенерації витривалості (1 стаміна = 2 хвилини) ===
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

// === СИСТЕМА ДОСЬЄ ПАЦІЄНТА ===
function openDossier() {
    closeInventory();
    closeCustomization();
    closeSettings();
    closeFriends();
    closeGym();
    closeMedicalHub();
    closeProcedureRoom();

    document.getElementById('dossier-name').textContent = playerName;
    document.getElementById('dossier-rank').textContent = getPlayerRank(stats.level);
    document.getElementById('dossier-lvl').textContent = stats.level;
    document.getElementById('dossier-days').textContent = stats.daysInClinic || 14;

    document.getElementById('dossier-madness-attacks').textContent = stats.madnessAttacks || 3;
    document.getElementById('dossier-enemies-killed').textContent = stats.enemiesKilled || 0;
    document.getElementById('dossier-bosses-killed').textContent = stats.bossesKilled || 0;
    document.getElementById('dossier-pills-used').textContent = stats.pillsUsed || 5;
    document.getElementById('dossier-gym-rounds').textContent = stats.gymRrounds || stats.gymRounds || 0;

    document.getElementById('dossier-modal').classList.remove('hidden');
}

function closeDossier() {
    document.getElementById('dossier-modal').classList.add('hidden');
}
// === ТЕСТОВА ФУНКЦІЯ ДЛЯ РОЗРОБКИ ===
function devSetMadness(value) {
    stats.madness = value;
    updateUI();
    if (value >= 100) {
        alert("⚠️ АКТИВОВАНО ПСИХОЗ! Розум втрачено, реальність розпалася.");
    } else {
        alert("🛡️ Стабілізація розуму. Повернення в нормальний корпус.");
    }
}

function handleLocationClick() {
    if (stats.madness >= 100) {
        alert("⚠️ Розум повністю затуманений! Палата заблокована галюцинаціями. Відкриваються аномальні коридори (Карта).");
        toggleMapModal(true);
    } else {
        openMedicalHub();
    }
}
function handleLocationClick() {
    if (stats.madness >= 100) {
        alert("❌ Доступ до лікувального корпусу заблоковано! Розум охоплений психозом. Ідіть на Карту або прийміть таблетки «Аміназин».");
        toggleMapModal(true);
    } else {
        openMedicalHub();
    }
}

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
    document.getElementById('gym-modal').classList.remove('hidden');
}

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
    document.getElementById('medical-hub-modal').classList.remove('hidden');
}
let bossCurrentHp = 120;
let bossMaxHp = 120;

// Викликається при натисканні на Процедурний кабінет на карті
function openProcedureRoomBattle() {
    if (stats.madness < 100) {
        alert("У нормальному стані процедурний кабінет працює як стандартний лазарет.");
        return;
    }
    // Відкриваємо Досьє поверх карти (карта НЕ закривається)
    const dossierModal = document.getElementById('nurse-dossier-modal');
    if (dossierModal) dossierModal.classList.remove('hidden');
}

function closeNurseDossier() {
    const dossierModal = document.getElementById('nurse-dossier-modal');
    if (dossierModal) dossierModal.classList.add('hidden');
}

// Старт бою з досьє
function startNurseFight() {
    closeNurseDossier();
    toggleMapModal(false); // Тепер закриваємо карту, оскільки починається бій
    
    bossCurrentHp = bossMaxHp;
    updateBattleUI();
    
    const battleModal = document.getElementById('nurse-battle-modal');
    if (battleModal) battleModal.classList.remove('hidden');
}

function closeNurseBattle() {
    const battleModal = document.getElementById('nurse-battle-modal');
    if (battleModal) battleModal.classList.add('hidden');
}

function updateBattleUI() {
    // Підтягуємо реальний нік гравця з головного меню/профілю
    const playerNameElem = document.getElementById('b-player-name');
    if (playerNameElem && typeof playerProfile !== 'undefined' && playerProfile.name) {
        playerNameElem.textContent = playerProfile.name;
    }

    // ХП Гравця
    document.getElementById('b-player-hp').textContent = `${stats.hp}/${stats.maxHp}`;
    let pPercent = Math.max(0, (stats.hp / stats.maxHp) * 100);
    document.getElementById('b-player-hpbar').style.width = `${pPercent}%`;

    // ХП Боса
    document.getElementById('b-boss-hp').textContent = `${bossCurrentHp}/${bossMaxHp}`;
    let bPercent = Math.max(0, (bossCurrentHp / bossMaxHp) * 100);
    document.getElementById('b-boss-hpbar').style.width = `${bPercent}%`;

    // Підрахунок аптечок в інвентарі
    let smallMeds = inventory.filter(i => i.name === 'Мала аптечка' || i.category === 'meds').reduce((acc, item) => acc + (item.count || 1), 0);
    let bigMeds = inventory.filter(i => i.name === 'Велика аптечка').reduce((acc, item) => acc + (item.count || 1), 0);

    const btnSmall = document.getElementById('medkit-btn-small');
    const countSmall = document.getElementById('medkit-count-small');
    if (countSmall) countSmall.textContent = smallMeds;
    if (btnSmall) {
        if (smallMeds <= 0) {
            btnSmall.style.opacity = '0.4';
            btnSmall.style.cursor = 'not-allowed';
        } else {
            btnSmall.style.opacity = '1';
            btnSmall.style.cursor = 'pointer';
        }
    }

    const btnBig = document.getElementById('medkit-btn-big');
    const countBig = document.getElementById('medkit-count-big');
    if (countBig) countBig.textContent = bigMeds;
    if (btnBig) {
        if (bigMeds <= 0) {
            btnBig.style.opacity = '0.4';
            btnBig.style.cursor = 'not-allowed';
        } else {
            btnBig.style.opacity = '1';
            btnBig.style.cursor = 'pointer';
        }
    }
}

let nurseKillsCount = 0; // Лічильник вбивств медсестри (Усунених загроз)

function openProcedureRoomBattle() {
    if (stats.madness < 100) {
        alert("У нормальному стані процедурний кабінет зачинений.");
        return;
    }
    // Оновлюємо лічильник Усунених загроз у досьє
    const killsElem = document.getElementById('dossier-kills-count');
    if (killsElem) killsElem.textContent = nurseKillsCount;

    const dossierModal = document.getElementById('nurse-dossier-modal');
    if (dossierModal) dossierModal.classList.remove('hidden');
}

function updateBattleUI() {
    // 1. ПІДТЯГУЄМО НІКНЕЙМ ГРАВЦЯ
    const playerNameElem = document.getElementById('b-player-name');
    if (playerNameElem && typeof playerName !== 'undefined') {
        playerNameElem.textContent = playerName; // Використовуємо глобальну змінну playerName
    }

    // 2. Підтягуємо аватарку з лоббі (якщо є)
    const battleAvatarBox = document.getElementById('player-battle-avatar-box');
    const lobbyAvatar = document.querySelector('.player-avatar img, #player-avatar img');
    if (battleAvatarBox && lobbyAvatar) {
        battleAvatarBox.innerHTML = `<img src="${lobbyAvatar.src}" style="width:100%; height:100%; object-fit:cover;">`;
    }

    // 3. ХП Гравця
    document.getElementById('b-player-hp').textContent = `${stats.hp}/${stats.maxHp}`;
    let pPercent = Math.max(0, (stats.hp / stats.maxHp) * 100);
    document.getElementById('b-player-hpbar').style.width = `${pPercent}%`;

    // 4. ХП Боса
    document.getElementById('b-boss-hp').textContent = `${bossCurrentHp}/${bossMaxHp}`;
    let bPercent = Math.max(0, (bossCurrentHp / bossMaxHp) * 100);
    document.getElementById('b-boss-hpbar').style.width = `${bPercent}%`;

    // 5. Оновлення лічильників аптечок
    let smallMeds = inventory.filter(i => i.name === 'Мала аптечка' || i.category === 'meds').reduce((acc, item) => acc + (item.count || 1), 0);
    let bigMeds = inventory.filter(i => i.name === 'Велика аптечка').reduce((acc, item) => acc + (item.count || 1), 0);

    const btnSmall = document.getElementById('medkit-btn-small');
    const countSmall = document.getElementById('medkit-count-small');
    if (countSmall) countSmall.textContent = smallMeds;
    if (btnSmall) {
        btnSmall.style.opacity = smallMeds <= 0 ? '0.4' : '1';
        btnSmall.style.cursor = smallMeds <= 0 ? 'not-allowed' : 'pointer';
    }

    const countBig = document.getElementById('medkit-count-big');
    const btnBig = document.getElementById('medkit-count-big');
    if (countBig) countBig.textContent = bigMeds;
    if (btnBig) {
        btnBig.style.opacity = bigMeds <= 0 ? '0.4' : '1';
        btnBig.style.cursor = bigMeds <= 0 ? 'not-allowed' : 'pointer';
    }
}

// Функція атаки
function performPlayerAttack() {
    let dmg = stats.damage || 10;
    bossCurrentHp = Math.max(0, bossCurrentHp - dmg);

    if (bossCurrentHp <= 0) {
        nurseKillsCount++; // Збільшуємо лічильник "Усунених загроз"
        
        // Додаємо винагороду
        stats.silver = (stats.silver || 0) + 30;
        addExperience(50);

        alert("🎉 Успішна зачистка кабінету!\nПереможено Сестру Клару.\nОтримано: +50 EXP, +30 Срібла, Ключ від блоку боса!");
        
        // Ключ в інвентар
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

        closeNurseBattle();
        updateUI();
        return;
    }

    // Контратака
    let counter = 12;
    stats.hp = Math.max(0, stats.hp - counter);

    if (stats.hp <= 0) {
        alert("💀 Сестра Клара вас здолала... Ви знепритомніли.");
        stats.hp = stats.maxHp;
        closeNurseBattle();
        updateUI();
        return;
    }

    updateBattleUI();
}

function useBattleMedkit(type) {
    let medName = type === 'big' ? 'Велика аптечка' : 'Мала аптечка';
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