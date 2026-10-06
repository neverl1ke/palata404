const tg = window.Telegram.WebApp;
tg.expand();

if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
    document.getElementById('player-name').innerText = tg.initDataUnsafe.user.first_name;
}

let hp = 100;
let pills = 0;
let madness = 20;
let energy = 80;
let currentOutfit = '🩺';

function tapCharacter() {
    if (energy >= 5) {
        energy -= 5;
        madness += 2;
        pills += 1;

        if (madness > 100) madness = 100;

        updateUI();
    } else {
        alert("Нестача енергії! Скористайся ліжком, щоб поспати.");
    }
}

function restInBed() {
    if (energy < 100) {
        energy = Math.min(100, energy + 30);
        madness = Math.min(100, madness + 5);
        updateUI();
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
    closeCustomization();
}

function updateUI() {
    document.getElementById('pills').innerText = pills;
    
    document.getElementById('hp-bar').style.width = hp + '%';
    document.getElementById('hp-val').innerText = hp + '/100';

    document.getElementById('madness-bar').style.width = madness + '%';
    document.getElementById('madness-val').innerText = madness + '%';

    document.getElementById('energy-bar').style.width = energy + '%';
    document.getElementById('energy-val').innerText = energy + '/100';
}