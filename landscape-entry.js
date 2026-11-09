/* Keep the game document intact inside a fixed landscape viewport. */
(() => {
    const url = new URL(location.href);
    if (window.__PALATA_TEST_DIRECT__ || url.searchParams.get('canvas') === '1') return;
    url.pathname = url.pathname.replace(/[^/]*$/, 'play.html');
    location.replace(url.href);
})();
