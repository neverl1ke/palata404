// Cosmetic only: source PNGs and registered Paper Doll geometry stay untouched.
const HAIR_COLORS = Object.freeze([
    { id: 'original', name: 'Оригінальний', group: 'original', hex: null },
    ...[
        ['black','Чорний','#201A19'], ['dark-brown','Темно-каштановий','#402A22'],
        ['brown','Каштановий','#704632'], ['light-brown','Світло-каштановий','#996A4B'],
        ['dark-fair','Темно-русявий','#76644E'], ['fair','Русявий','#A18B6D'],
        ['light-fair','Світло-русявий','#C0AA82'], ['blond','Блонд','#D9BD85'],
        ['platinum','Платиновий блонд','#E6DDC8'], ['ginger','Рудий','#AC522D'],
        ['gray','Сивий','#A8A6A3'], ['white','Білий','#C8C3BA']
    ].map(([id,name,hex]) => Object.freeze({ id, name, hex, group: 'natural' })),
    ...[
        ['burgundy','Бордовий','#792B40'], ['red','Яскраво-червоний','#9E3137'],
        ['pink','Рожевий','#F07BAF'], ['pastel-pink','Пастельно-рожевий','#E7B2C4'],
        ['purple','Фіолетовий','#8447B5'], ['lavender','Лавандовий','#B4A0E4'],
        ['navy','Темно-синій','#283E8E'], ['blue','Електричний синій','#335BA6'],
        ['turquoise','Бірюзовий','#28736F'], ['emerald','Смарагдовий','#267C55'],
        ['lime','Кислотно-зелений','#748C28'], ['orange','Помаранчевий','#ED772D']
    ].map(([id,name,hex]) => Object.freeze({ id, name, hex, group: 'alternative' }))
]);
const hairColorCache = new Map();
const HAIR_COLOR_CACHE_LIMIT = 24;

function normalizeHairColor(id) {
    return HAIR_COLORS.some(color => color.id === id) ? id : 'original';
}

// Map the original strand lighting onto the chosen pigment. Alpha is never written.
// A histogram median makes the same color usable across differently lit source art.
function hairLuminanceMedian(pixels) {
    const histogram = new Uint32Array(256);
    let count = 0;
    const luminance = i => Math.round(.2126*pixels[i] + .7152*pixels[i+1] + .0722*pixels[i+2]);
    for (let i=0; i<pixels.length; i+=4) if (pixels[i+3] >= 192) { histogram[luminance(i)]++; count++; }
    if (!count) return null;
    let median=1, cumulative=0;
    for (; median<255; median++) { cumulative+=histogram[median]; if (cumulative>=count/2) break; }
    return median;
}

function recolorHairPixels(pixels, hex, referenceMedian = null) {
    const target = [1,3,5].map(start => parseInt(hex.slice(start,start + 2),16));
    const median = referenceMedian ?? hairLuminanceMedian(pixels);
    if (median === null) return pixels;
    const luminance = i => Math.round(.2126*pixels[i] + .7152*pixels[i+1] + .0722*pixels[i+2]);
    for (let i=0; i<pixels.length; i+=4) {
        if (!pixels[i+3]) continue;
        const shade=Math.pow(luminance(i)/median,.85);
        for (let c=0; c<3; c++) pixels[i+c] = shade<=1 ? target[c]*shade
            : target[c] + (255-target[c])*Math.min(.55,(shade-1)*.3);
    }
    return pixels;
}

const hairReferenceMedians = new Map();
function hairReferenceMedian(source) {
    if (hairReferenceMedians.has(source)) return hairReferenceMedians.get(source);
    const promise = new Promise((resolve,reject) => {
        const image = new Image();
        image.onload = () => {
            try {
                const canvas = document.createElement('canvas');
                canvas.width = image.naturalWidth; canvas.height = image.naturalHeight;
                const context = canvas.getContext('2d',{willReadFrequently:true});
                context.drawImage(image,0,0);
                resolve(hairLuminanceMedian(context.getImageData(0,0,canvas.width,canvas.height).data));
            } catch (error) { reject(error); }
        };
        image.onerror = () => reject(new Error('Не вдалося завантажити еталон відтінку волосся'));
        image.src = source;
    });
    hairReferenceMedians.set(source,promise);
    promise.catch(() => { if (hairReferenceMedians.get(source) === promise) hairReferenceMedians.delete(source); });
    while (hairReferenceMedians.size > HAIR_COLOR_CACHE_LIMIT) hairReferenceMedians.delete(hairReferenceMedians.keys().next().value);
    return promise;
}

function coloredHairSource(source, id, referenceSource = null) {
    const color=HAIR_COLORS.find(entry => entry.id===id);
    if (!color?.hex) return Promise.resolve(source);
    const key=`${source}|${id}${referenceSource ? '|'+referenceSource : ''}`;
    if (hairColorCache.has(key)) {
        const cached=hairColorCache.get(key);
        hairColorCache.delete(key); hairColorCache.set(key,cached);
        return cached;
    }
    const promise=new Promise((resolve,reject) => {
        const image=new Image();
        image.onload=async () => {
            try {
                const canvas=document.createElement('canvas');
                canvas.width=image.naturalWidth; canvas.height=image.naturalHeight;
                const context=canvas.getContext('2d',{willReadFrequently:true});
                context.drawImage(image,0,0);
                const frame=context.getImageData(0,0,canvas.width,canvas.height);
                const referenceMedian = referenceSource ? await hairReferenceMedian(referenceSource) : null;
                recolorHairPixels(frame.data,color.hex,referenceMedian);
                context.putImageData(frame,0,0);
                resolve(canvas.toDataURL('image/png'));
            } catch (error) { reject(error); }
        };
        image.onerror=() => reject(new Error('Не вдалося завантажити PNG зачіски'));
        image.src=source;
    });
    hairColorCache.set(key,promise);
    // Data URLs remain valid for currently displayed layers after LRU eviction.
    while (hairColorCache.size>HAIR_COLOR_CACHE_LIMIT) hairColorCache.delete(hairColorCache.keys().next().value);
    promise.catch(() => { if (hairColorCache.get(key)===promise) hairColorCache.delete(key); });
    return promise;
}

function setHairColor(id) {
    if (!HAIR_COLORS.some(color => color.id===id)) return false;
    paperDollState.appearance.hairColor=id;
    commitPaperDollSelection();
    return true;
}
