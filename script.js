const tg = window.Telegram.WebApp;
tg.expand();

// Налаштування імені
if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
    document.getElementById('player-name').innerText = tg.initDataUnsafe.user.first_name;
}

// Початкові значення
let hp = 100;
let pills = 0;
let madness = 20;
let energy = 80;
let currentOutfit = '🩺';

// --- ЛОГІКА ЗБЕРЕЖЕННЯ ТА ЗАВАНТАЖЕННЯ ---

function saveProgress() {
    const gameState = {
        hp: hp,
        pills: pills,
        madness: madness,
        energy: energy,
        currentOutfit: currentOutfit
    };
    
    localStorage.setItem('palata404_save', JSON.stringify(gameState));

    if (tg.CloudStorage) {
        tg.CloudStorage.setItem('palata404_save', JSON.stringify(gameState));
    }
}

function loadProgress() {
    const savedData = localStorage.getItem('palata404_save');
    
    if (savedData) {
        const gameState = JSON.parse(savedData);
        hp = gameState.hp ?? 100;
        pills = gameState.pills ?? 0;
        madness = gameState.madness ?? 20;
        energy = gameState.energy ?? 80;
        currentOutfit = gameState.currentOutfit ?? '🩺';
        
        document.getElementById('outfit-icon').innerText = currentOutfit;
    }
    
    // Обов'язково оновлюємо весь UI після завантаження!
    updateUI();
}

// --- ІГРОВІ МЕХАНІКИ ---

function tapCharacter() {
    if (energy >= 5) {
        energy -= 5;
        madness += 2;
        pills += 1;

        if (madness > 100) madness = 100;

        updateUI();
        saveProgress();
    } else {
        alert("Нестача енергії! Скористайся ліжком, щоб поспати.");
    }
}

function restInBed() {
    if (energy < 100) {
        energy = Math.min(100, energy + 30);
        madness = Math.min(100, madness + 5);
        if (madness > 100) madness = 100;
        
        updateUI();
        saveProgress();
    }
}

function openCustomization() {
    document.getElementById('custom-modal').classList.remove('hidden');
}

function closeCustomization() {
    document.getElementById('custom-modal').classList.add('hidden');
}

function setOutfit(icon, name, price) {
    if (price > pills) {
        alert("Не вистачає пігулок!");
        return;
    }
    
    if (price > 0 && currentOutfit !== icon) {
        pills -= price;
    }
    
    currentOutfit = icon;
    document.getElementById('outfit-icon').innerText = currentOutfit;
    updateUI();
    saveProgress();
    closeCustomization();
}

function updateUI() {
    // 1. Оновлюємо лічильник пігулок
    document.getElementById('pills').innerText = pills;
    
    // 2. Здоров'я
    document.getElementById('hp-bar').style.width = hp + '%';
    document.getElementById('hp-val').innerText = hp + '/100';

    // 3. Божевілля (і смужка, і відсотки)
    document.getElementById('madness-bar').style.width = madness + '%';
    document.getElementById('madness-val').innerText = madness + '%';

    // 4. Енергія (і смужка, і значення)
    document.getElementById('energy-bar').style.width = energy + '%';
    document.getElementById('energy-val').innerText = energy + '/100';
}

// Завантажуємо збережені дані при запуску
loadProgress();