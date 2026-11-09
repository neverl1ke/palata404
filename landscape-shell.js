(() => {
    'use strict';
    const WIDTH = 1280, HEIGHT = 720;
    const screen = document.getElementById('landscape-screen');
    const slot = document.getElementById('canvas-slot');
    const frame = document.getElementById('game-canvas');
    const prompt = document.getElementById('rotate-prompt');
    const fullscreen = document.getElementById('fullscreen-button');
    const source = new URL('index.html', location.href);
    source.search = location.search;
    source.hash = location.hash;
    source.searchParams.set('canvas', '1');
    frame.src = source.href;
    function fit() {
        const style = getComputedStyle(screen);
        const width = screen.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
        const height = screen.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom);
        const scale = Math.max(0, Math.min(width / WIDTH, height / HEIGHT));
        slot.style.width = `${WIDTH * scale}px`;
        slot.style.height = `${HEIGHT * scale}px`;
        frame.style.transform = `scale(${scale})`;
        const rotate = matchMedia('(pointer:coarse)').matches && width < 900 && height > width;
        prompt.hidden = !rotate;
        // Keep the optional fullscreen control in the letterbox, never over gameplay.
        fullscreen.hidden = !matchMedia('(pointer:fine)').matches && !rotate && height - HEIGHT * scale < 96 && width - WIDTH * scale < 96;
        document.body.dataset.rotate = String(rotate);
        frame.inert = rotate;
        frame.setAttribute('aria-hidden', String(rotate));
    }
    new ResizeObserver(fit).observe(screen);
    addEventListener('resize', fit);
    visualViewport?.addEventListener('resize', fit);
    fullscreen.addEventListener('click', async () => {
        try {
            if (document.fullscreenElement) await document.exitFullscreen();
            else if (document.documentElement.requestFullscreen) await document.documentElement.requestFullscreen();
            else throw new Error('Fullscreen unavailable');
        } catch {
            document.getElementById('fullscreen-note').hidden = false;
        }
    });
    document.addEventListener('fullscreenchange', () => {
        const active = Boolean(document.fullscreenElement);
        fullscreen.setAttribute('aria-pressed', String(active));
        fullscreen.setAttribute('aria-label', active ? 'Вийти з повного екрана' : 'На весь екран');
        fullscreen.title = active ? 'Вийти з повного екрана' : 'На весь екран';
        fit();
    });
    fit();
})();
