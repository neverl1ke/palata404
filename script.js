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
    nextLvlExp: 100
};

let stats = loadSaveData('palata404_stats', DEFAULT_STATS);

// Перемикач статі
let gender = localStorage.getItem('palata404_gender') || 'male'; 
let currentHair = localStorage.getItem('palata404_hair') || '';
let currentFace = localStorage.getItem('palata404_face') || '';
let currentClothes = localStorage.getItem('palata404_clothes') || '';

let inventory = loadSaveData('palata404_inventory', [
    { name: 'ПМ', icon: '🔫', count: 1, category: 'weapon' },
    { name: 'Тактичний шолом', icon: '🪖', count: 1, category: 'helmet' },
    { name: 'Бронежилет БР-1', icon: '🛡️', count: 1, category: 'armor' },
    { name: 'Приціл RedDot', icon: '🧩', count: 1, category: 'mod' },
    { name: 'Аптечка', icon: '🧪', count: 3, category: 'meds' }
]);

let currentCategory = 'all';
let currentWardrobeTab = 'body';

// === Структура Даних Поверхів та Мапи ===
const gameFloorsData = [
    {
        id: 10,
        title: "10 Поверх — Блок Ізоляторів",
        unlocked: true,
        mapImage: "map_floor_10.png", // Вкажи точну назву свого PNG/JPG файлу
        nodes: [
            { id: "sec1_collector", title: "⚙️ Збирач #1", x: 40, y: 30, type: "collector" },
            { id: "sec2_grind", title: "🧱 Завал (Розчистити)", x: 58, y: 45, type: "grind" },
            { id: "sec3_boss", title: "👹 Бос Поверху", x: 82, y: 28, type: "boss", locked: true }
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
    },
    {
        id: 7,
        title: "7 Поверх — Загальна Терапія",
        unlocked: false,
        mapImage: "",
        nodes: []
    }
];

function loadSaveData(key, fallback) {
    const saved = localStorage.getItem(key);
    if (!saved) return fallback;
    try { return JSON.parse(saved); } catch (e) { return fallback; }
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
    
    const bodyImg = document.getElementById('layer-body');
    if (bodyImg) {
        bodyImg.src = gender === 'female' ? 'base_female.png' : 'base_male.png';
    }

    saveGameProgress();
}

function updateCharacterLayers() {
    setGender(gender);

    const faceImg = document.getElementById('layer-face');
    const hairImg = document.getElementById('layer-hair');
    const clothesImg = document.getElementById('layer-clothes');

    if (currentFace) {
        faceImg.src = currentFace;
        faceImg.classList.remove('hidden');
    } else {
        faceImg.classList.add('hidden');
    }

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
    document.getElementById('hp-val').textContent = `${stats.hp} / ${stats.maxHp}`;
    document.getElementById('madness-val').textContent = `${stats.madness} / 100`;
    document.getElementById('energy-val').textContent = `${stats.energy} / ${stats.maxEnergy}`;

    document.getElementById('hp-bar').style.width = `${Math.min(100, (stats.hp / stats.maxHp) * 100)}%`;
    document.getElementById('madness-bar').style.width = `${Math.min(100, stats.madness)}%`;
    document.getElementById('energy-bar').style.width = `${Math.min(100, (stats.energy / stats.maxEnergy) * 100)}%`;

    document.getElementById('silver-val').textContent = stats.silver || 0;
    document.getElementById('pills-val').textContent = stats.pills || 0;
    document.getElementById('bucks-val').textContent = stats.bucks || 0;

    document.getElementById('player-lvl').textContent = stats.level;
    document.getElementById('player-rank').textContent = getPlayerRank(stats.level);
    document.getElementById('exp-val').textContent = `${stats.exp} / ${stats.nextLvlExp} EXP`;
    
    let expPercent = (stats.exp / stats.nextLvlExp) * 100;
    document.getElementById('exp-bar').style.width = `${Math.min(100, expPercent)}%`;

    updateCharacterLayers();
    updatePlayerNameDisplay();
    saveGameProgress();
}

function tapCharacter() {
    if (stats.energy >= 5) {
        stats.energy -= 5;
        stats.silver = (stats.silver || 0) + Math.floor(Math.random() * 5) + 2;
        
        const madnessGain = Math.floor(Math.random() * 4) + 3;
        stats.madness = Math.min(100, stats.madness + madnessGain);

        addExperience(Math.floor(Math.random() * 10) + 15);
    } else {
        alert("Занадто мало витривалості! Потрібно відпочити.");
    }
    updateUI();
}

function restInBed() {
    stats.energy = Math.min(stats.maxEnergy, stats.energy + 35);
    stats.madness = Math.max(0, stats.madness - 15);
    updateUI();
}

// === ЛОГІКА МОДАЛЬНОГО ВІКНА МАРШРУТІВ ТА КАРТИ ===
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
    if (node.type === 'collector') {
        alert("⚙️ Автономний Збирач #1 працює!\nЗібрано луту: +15 Срібла, +1 Пігулка.");
        stats.silver += 15;
        stats.pills += 1;
        updateUI();
    } else if (node.type === 'grind') {
        if (stats.energy >= 10) {
            stats.energy -= 10;
            alert("⛏️ Ви розчистили частину завалу! Отримано 30 EXP та знайдено Ключ від Блоку Боса!");
            addExperience(30);
            
            // Розблоковуємо Боса
            const bossNode = floor.nodes.find(n => n.type === 'boss');
            if (bossNode) bossNode.locked = false;
            
            openFloorMap(floor.id); // Перемальовуємо карти
            updateUI();
        } else {
            alert("Недостатньо витривалості для розчищення завалу!");
        }
    } else if (node.type === 'boss') {
        alert("⚔️ Бій з Босом 10-го Поверху!\nЦей функціонал розробляється для рейдового режиму.");
    }
}

function openSettings() {
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
            slot.innerHTML = `
                <span class="item-icon">${item.icon}</span>
                ${item.count > 1 ? `<span class="item-count">${item.count}</span>` : ''}
            `;
            slot.onclick = () => alert(`Предмет: ${item.name}`);
        }
        container.appendChild(slot);
    }
}

function openCustomization() {
    closeInventory();
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
    } else {
        container.innerHTML = `<p style="font-size:12px; color:#aaa; text-align:center; padding: 20px 0;">Розділ [${currentWardrobeTab.toUpperCase()}] буде заповнений при додаванні нових PNG-елементів!</p>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateUI();
});