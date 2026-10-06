const tg = window.Telegram.WebApp;
tg.expand();

// Ініціалізація даних гравця з Telegram
if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
    document.getElementById('player-name').innerText = tg.initDataUnsafe.user.first_name;
}

let pills = 0;
let madness = 20;
let energy = 80;

function tapCharacter() {
    if (energy >= 5) {
        energy -= 5;
        madness += 2;
        pills += 1;

        if (madness > 100) madness = 100;

        updateUI();
    } else {
        alert("Нестача енергії! Потрібно відпочити.");
    }
}

function updateUI() {
    document.getElementById('pills').innerText = pills;
    document.getElementById('madness-bar').style.width = madness + '%';
    document.getElementById('energy-bar').style.width = energy + '%';
}