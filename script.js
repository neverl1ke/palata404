const tg = window.Telegram.WebApp;
tg.expand();

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
        try {
            const gameState = JSON.parse(savedData);
            hp = gameState.hp ?? 100;
            pills = gameState.pills ?? 0;
            madness = gameState.madness ?? 20;
            energy = gameState.energy ?? 80;
            currentOutfit = gameState.currentOutfit ?? '🩺';
        } catch (e) {
            console.error("Помилка зчитування збереження:", e);
        }
    }
    
    // Безпечно встановлюємо іконку одягу
    const outfitEl = document.getElementById('outfit-icon');
    if (outfitEl) {
        outfitEl.innerText = currentOutfit;
    }

    // Оновлюємо ім'я користувача
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        const nameEl = document.getElementById('player-name');
        if (nameEl) nameEl.innerText = tg.initDataUnsafe.user.first_name;
    }
    
    // Оновлюємо інтерфейс
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
    const modal = document.getElementById('custom-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeCustomization() {
    const modal = document.getElementById('custom-modal');
    if (modal) modal.classList.add('hidden');
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
    const outfitEl = document.getElementById('outfit-icon');
    if (outfitEl) outfitEl.innerText = currentOutfit;

    updateUI();
    saveProgress();
    closeCustomization();
}

function updateUI() {
    // Безопасні перевірки на наявність елементів у DOM
    const pillsEl = document.getElementById('pills');
    if (pillsEl) pillsEl.innerText = pills;
    
    // 2. Здоров'я
    const hpBar = document.getElementById('hp-bar');
    const hpVal = document.getElementById('hp-val');
    if (hpBar) hpBar.style.width = hp + '%';
    if (hpVal) hpVal.innerText = hp + '/100';

    // 3. Божевілля
    const madnessBar = document.getElementById('madness-bar');
    const madnessVal = document.getElementById('madness-val');
    if (madnessBar) madnessBar.style.width = madness + '%';
    if (madnessVal) madnessVal.innerText = madness + '%';

    // 4. Енергія
    const energyBar = document.getElementById('energy-bar');
    const energyVal = document.getElementById('energy-val');
    if (energyBar) energyBar.style.width = energy + '%';
    if (energyVal) energyVal.innerText = energy + '/100';
}

// Запускаємо логіку ТІЛЬКИ після повного завантаження сторінки
document.addEventListener('DOMContentLoaded', () => {
    loadProgress();
});