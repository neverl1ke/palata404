/* Read-only orientation for the existing floor plan. It changes only the
   blueprint viewport's native scroll position; it never enters a room. */
(function () {
    'use strict';
    const NS = 'http://www.w3.org/2000/svg';
    const WIDTH = 1610, HEIGHT = 850;
    let control;

    const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
    function svgNode(name, attributes) {
        const node = document.createElementNS(NS, name);
        for (const [key, value] of Object.entries(attributes || {})) node.setAttribute(key, value);
        return node;
    }
    function button(label, className) {
        const node = document.createElement('button');
        node.type = 'button'; node.className = className; node.textContent = label;
        return node;
    }

    function create(modal) {
        const header = modal.querySelector('.map-clipboard-header');
        if (!header) return null;
        const root = document.createElement('div');
        root.className = 'floor-map-navigation'; root.hidden = true;
        const toggle = button('Обзор', 'floor-map-overview-toggle');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.setAttribute('aria-controls', 'floor-map-overview');
        const panel = document.createElement('section');
        panel.id = 'floor-map-overview'; panel.className = 'floor-map-overview'; panel.hidden = true;
        panel.setAttribute('aria-label', 'Обзор этажа');
        const hint = document.createElement('p');
        hint.id = 'floor-map-overview-hint'; hint.className = 'floor-map-overview-hint';
        hint.textContent = 'Перемещайте рамку по плану';
        const mini = svgNode('svg', {
            viewBox: '0 0 ' + WIDTH + ' ' + HEIGHT,
            class: 'floor-map-overview-plan', tabindex: '0', role: 'region',
            'aria-label': 'Обзор плана. Стрелки перемещают видимую область.',
            'aria-describedby': hint.id,
            'aria-keyshortcuts': 'ArrowLeft ArrowRight ArrowUp ArrowDown Home End PageUp PageDown'
        });
        // The original drawing and its authored crop are the same as the main
        // plan. No new illustration, pin layout, or separate tiny doors.
        const crop = svgNode('svg', {x: 0, y: 0, width: WIDTH, height: HEIGHT, viewBox: '70 280 1610 850'});
        const image = svgNode('image', {x: 0, y: 0, width: 2200, height: 1400, href: 'quest-plan.svg'});
        crop.append(image); mini.append(crop);
        const markers = svgNode('g', {'aria-hidden': 'true'});
        const visible = svgNode('rect', {class: 'floor-map-visible-area', x: 0, y: 0, width: WIDTH, height: HEIGHT});
        const target = svgNode('path', {class: 'floor-map-target-marker', d: 'M0 -25 25 0 0 25 -25 0Z'});
        const current = svgNode('circle', {class: 'floor-map-current-marker', r: 23});
        markers.append(visible, target, current); mini.append(markers);
        const recenter = button('Текущая комната', 'floor-map-recenter');
        panel.append(hint, mini, recenter); root.append(toggle, panel); header.append(root);

        const state = {modal, root, toggle, panel, mini, image, current, target, visible,
            recenter, viewport: null, figure: null, frame: 0, opened: false, pointer: null};
        const orient = () => modal.dispatchEvent(new Event('palata:map-orient'));
        function close(restoreFocus) {
            const wasOpen = state.opened;
            if (state.pointer !== null && mini.hasPointerCapture(state.pointer)) mini.releasePointerCapture(state.pointer);
            state.opened = false; state.pointer = null;
            panel.hidden = true; toggle.setAttribute('aria-expanded', 'false');
            if (restoreFocus && wasOpen && !root.hidden) toggle.focus({preventScroll: true});
        }
        function innerRect() {
            const view = state.viewport;
            if (!view || !view.offsetWidth || !view.offsetHeight) return null;
            const r = view.getBoundingClientRect();
            const sx = r.width / view.offsetWidth, sy = r.height / view.offsetHeight;
            return {left: r.left + view.clientLeft * sx, top: r.top + view.clientTop * sy,
                width: view.clientWidth * sx, height: view.clientHeight * sy, sx, sy};
        }
        function geometry() {
            const inner = innerRect(), figure = state.figure?.getBoundingClientRect();
            if (!inner || !figure?.width || !figure.height || !inner.width || !inner.height) return null;
            return {inner, figure};
        }
        function pinPoint(pin, figure) {
            // Door positions are authored percentages in this same plan. Read
            // those DOM coordinates so a transient layout/focus adjustment
            // during a map rebuild cannot move the orientation marker.
            const left = pin.style.left, top = pin.style.top;
            if (left.endsWith('%') && top.endsWith('%') &&
                Number.isFinite(parseFloat(left)) && Number.isFinite(parseFloat(top))) {
                return {u: clamp(parseFloat(left) / 100, 0, 1), v: clamp(parseFloat(top) / 100, 0, 1)};
            }
            const r = pin.getBoundingClientRect();
            return {u: clamp((r.left + r.width / 2 - figure.left) / figure.width, 0, 1),
                v: clamp((r.top + r.height / 2 - figure.top) / figure.height, 0, 1)};
        }
        function updateMarker(node, pin, figure) {
            node.style.display = pin ? '' : 'none';
            if (!pin) return;
            const point = pinPoint(pin, figure);
            node.setAttribute('transform', 'translate(' + point.u * WIDTH + ' ' + point.v * HEIGHT + ')');
        }
        function draw() {
            state.frame = 0;
            const g = geometry();
            const active = modal.classList.contains('active') || modal.getAttribute('aria-hidden') === 'false' ||
                getComputedStyle(modal).display !== 'none';
            const plan = modal.dataset.compactView !== 'details' &&
                !document.querySelector('#quest-location-screen')?.getClientRects().length;
            const touch = document.documentElement.dataset.touchUi === 'true';
            const canPan = state.viewport && (state.viewport.scrollWidth > state.viewport.clientWidth + 1 ||
                state.viewport.scrollHeight > state.viewport.clientHeight + 1);
            const eligible = active && plan && !!g && (touch || canPan);
            root.hidden = !eligible;
            if (!eligible) { close(false); return; }
            if (!state.opened) return;
            const {inner, figure} = g;
            const x = clamp((inner.left - figure.left) / figure.width, 0, 1);
            const y = clamp((inner.top - figure.top) / figure.height, 0, 1);
            const right = clamp((inner.left + inner.width - figure.left) / figure.width, x, 1);
            const bottom = clamp((inner.top + inner.height - figure.top) / figure.height, y, 1);
            visible.setAttribute('x', x * WIDTH); visible.setAttribute('y', y * HEIGHT);
            visible.setAttribute('width', (right - x) * WIDTH); visible.setAttribute('height', (bottom - y) * HEIGHT);
            updateMarker(current, state.figure.querySelector('.quest-map-pin.is-current'), figure);
            updateMarker(target, state.figure.querySelector('.quest-map-pin.is-target'), figure);
            recenter.disabled = !state.figure.querySelector('.quest-map-pin.is-current');
            // Measurements share iframe coordinates, so this remains correct
            // when the shell scale is cancelled by --touch-ui-scale.
            const mr = modal.getBoundingClientRect(), tr = toggle.getBoundingClientRect();
            const scale = root.getBoundingClientRect().width / root.offsetWidth || 1;
            panel.style.maxHeight = Math.max(80, (mr.bottom - tr.bottom) / scale - 12) + 'px';
        }
        const schedule = () => { if (!state.frame) state.frame = requestAnimationFrame(draw); };
        function panTo(u, v) {
            const g = geometry();
            if (!g) return;
            const {inner, figure} = g, view = state.viewport;
            const left = view.scrollLeft + (figure.left + u * figure.width - inner.left - inner.width / 2) / inner.sx;
            const top = view.scrollTop + (figure.top + v * figure.height - inner.top - inner.height / 2) / inner.sy;
            view.scrollTo({left: clamp(left, 0, view.scrollWidth - view.clientWidth),
                top: clamp(top, 0, view.scrollHeight - view.clientHeight), behavior: 'instant'});
            schedule();
        }
        function pointerPan(event) {
            const transform = mini.getScreenCTM();
            if (!transform) return;
            // SVG's own matrix accounts for the border, viewBox and shell's
            // inverse UI transform instead of treating screen pixels as plan units.
            const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(transform.inverse());
            panTo(clamp(point.x / WIDTH, 0, 1), clamp(point.y / HEIGHT, 0, 1));
        }
        toggle.addEventListener('click', event => {
            event.stopPropagation();
            if (state.opened) { close(false); return; }
            orient(); state.opened = true; panel.hidden = false;
            toggle.setAttribute('aria-expanded', 'true'); draw();
        });
        recenter.addEventListener('click', event => {
            event.stopPropagation(); orient();
            const pin = state.figure?.querySelector('.quest-map-pin.is-current'), g = geometry();
            if (!pin || !g) return;
            const point = pinPoint(pin, g.figure);
            panTo(point.u, point.v);
            // Reveal the room itself instead of leaving the overview on top
            // of the newly centred doors.
            close(true);
        });
        mini.addEventListener('pointerdown', event => {
            if (!event.isPrimary || event.button !== 0) return;
            // touch-action:none, user-select:none and pointer capture own
            // the pan without cancelling native compatibility events.
            event.stopPropagation(); orient();
            state.pointer = event.pointerId;
            mini.setPointerCapture(event.pointerId); mini.focus({preventScroll: true}); pointerPan(event);
        });
        mini.addEventListener('pointermove', event => {
            if (state.pointer !== event.pointerId) return;
            event.stopPropagation(); orient(); pointerPan(event);
        });
        const endPointer = event => {
            if (state.pointer !== event.pointerId) return;
            event.stopPropagation(); state.pointer = null;
            if (mini.hasPointerCapture(event.pointerId)) mini.releasePointerCapture(event.pointerId);
        };
        mini.addEventListener('pointerup', endPointer); mini.addEventListener('pointercancel', endPointer);
        // This is a custom drag surface, never a native scrolling/flinging
        // region. Consume only its touch gesture; buttons keep native clicks.
        const consumeMiniTouch = event => {
            if (event.cancelable) event.preventDefault();
            event.stopPropagation();
        };
        mini.addEventListener('touchstart', consumeMiniTouch, {passive: false});
        mini.addEventListener('touchmove', consumeMiniTouch, {passive: false});
        mini.addEventListener('click', event => {event.preventDefault(); event.stopPropagation();});
        mini.addEventListener('dblclick', event => {event.preventDefault(); event.stopPropagation();});
        mini.addEventListener('keydown', event => {
            const view = state.viewport;
            if (!view || !['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End','PageUp','PageDown'].includes(event.key)) return;
            event.preventDefault(); event.stopPropagation(); orient();
            let left = view.scrollLeft, top = view.scrollTop;
            if (event.key === 'ArrowLeft') left -= view.clientWidth * .3;
            if (event.key === 'ArrowRight') left += view.clientWidth * .3;
            if (event.key === 'ArrowUp') top -= view.clientHeight * .3;
            if (event.key === 'ArrowDown') top += view.clientHeight * .3;
            if (event.key === 'PageUp') top -= view.clientHeight * .9;
            if (event.key === 'PageDown') top += view.clientHeight * .9;
            if (event.key === 'Home') {left = 0; top = 0;}
            if (event.key === 'End') {left = view.scrollWidth; top = view.scrollHeight;}
            view.scrollTo({left, top, behavior: 'instant'}); schedule();
        });
        modal.addEventListener('keydown', event => {
            if (event.key === 'Escape' && state.opened) {
                event.preventDefault(); event.stopImmediatePropagation(); close(true);
            }
        }, true);
        modal.addEventListener('pointerdown', event => {
            if (state.opened && !root.contains(event.target)) close(false);
        }, true);
        new MutationObserver(schedule).observe(modal, {attributes: true, attributeFilter: ['class', 'style', 'aria-hidden', 'data-compact-view']});
        new MutationObserver(schedule).observe(document.documentElement, {attributes: true, attributeFilter: ['data-touch-ui', 'style']});
        window.addEventListener('resize', schedule, {passive: true});
        const observer = new ResizeObserver(schedule);
        state.bind = map => {
            if (state.viewport) state.viewport.removeEventListener('scroll', schedule);
            observer.disconnect();
            state.viewport = map?.querySelector('.quest-blueprint-viewport') || null;
            state.figure = state.viewport?.querySelector('.quest-blueprint') || null;
            if (state.viewport && state.figure) {
                const source = state.figure.querySelector('.quest-blueprint-image')?.getAttribute('src');
                image.setAttribute('href', source || 'quest-plan.svg');
                state.viewport.addEventListener('scroll', schedule, {passive: true});
                observer.observe(state.viewport); observer.observe(state.figure);
            }
            schedule();
        };
        return state;
    }
    function render(map) {
        const modal = document.getElementById('map-modal');
        if (!modal) return;
        if (!control || control.modal !== modal) control = create(modal);
        control?.bind(map);
    }
    window.PalataMapNavigation = Object.freeze({render});
})();
