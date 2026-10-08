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

// === Початкові дані / Валюта / Персонаж ===
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

// Стать та вибрані елементи одягу/кастомізації
let gender = localStorage.getItem('palata404_gender') || 'male'; // 'male' або 'female'
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

// === Управління персонажем (Paper Doll) ===
function setGender(selectedGender) {
    gender = selectedGender;
    
    // Оновлення кнопок перемикача
    document.getElementById('btn-gender-male').classList.toggle('active', gender === 'male');
    document.getElementById('btn-gender-female').classList.toggle('active', gender === 'female');
    
    // Зміна бази тіла
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

// === Оновлення Інтерфейсу ===
function updateUI() {
    document.getElementById('hp-val').textContent = `${stats.hp} / ${stats.maxHp}`;
    document.getElementById('madness-val').textContent = `${stats.madness} / 100`;
    document.getElementById('energy-val').textContent = `${stats.energy} / ${stats.maxEnergy}`;

    document.getElementById('hp-bar').style.width = `${Math.min(100, (stats.hp / stats.maxHp) * 100)}%`;
    document.getElementById('madness-bar').style.width = `${Math.min(100, stats.madness)}%`;
    document.getElementById('energy-bar').style.width = `${Math.min(100, (stats.energy / stats.maxEnergy) * 100)}%`;

    // Валюта
    document.getElementById('silver-val').textContent = stats.silver || 0;
    document.getElementById('pills-val').textContent = stats.pills || 0;
    document.getElementById('bucks-val').textContent = stats.bucks || 0;

    // Рівень
    document.getElementById('player-lvl').textContent = stats.level;
    document.getElementById('player-rank').textContent = getPlayerRank(stats.level);
    document.getElementById('exp-val').textContent = `${stats.exp} / ${stats.nextLvlExp} EXP`;
    
    let expPercent = (stats.exp / stats.nextLvlExp) * 100;
    document.getElementById('exp-bar').style.width = `${Math.min(100, expPercent)}%`;

    updateCharacterLayers();
    updatePlayerNameDisplay();
    saveGameProgress();
}

// === Дії ===
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

// === Налаштування ===
function openSettings() {
    document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettings() {
    document.getElementById('settings-modal').classList.add('hidden');
}

// === Банк ===
function openBank() {
    document.getElementById('bank-modal').classList.remove('hidden');
}

function closeBank() {
    document.getElementById('bank-modal').classList.add('hidden');
}

// === Інвентар ===
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

// === Гардероб / Кастомізація ===
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
                <div>Чоловіче тіло</div>
                <button class="btn-outfit" onclick="setGender('male'); renderWardrobe();">Обрати</button>
            </div>
            <div class="outfit-card ${gender === 'female' ? 'active' : ''}">
                <div>Жіноче тіло</div>
                <button class="btn-outfit" onclick="setGender('female'); renderWardrobe();">Обрати</button>
            </div>
        `;
    } else {
        container.innerHTML = `<p style="font-size:12px; color:#aaa; text-align:center; padding: 20px 0;">Розділ [${currentWardrobeTab.toUpperCase()}] буде заповнений при додаванні нових PNG-ассетів!</p>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateUI();
});