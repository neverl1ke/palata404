const cache = new Map();
function resolveImages(value) {
    if (typeof value === 'string' && /^\.\/(male|female)\//.test(value)) return new URL(value,import.meta.url).href;
    if (Array.isArray(value)) return value.map(resolveImages);
    if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k,v])=>[k,resolveImages(v)]));
    return value;
}
export function config(gender) {
    if (!cache.has(gender)) cache.set(gender,Promise.all(['resources','trial'].map(async kind=>{
        const response=await fetch(new URL(`./${gender}/${kind}.json`,import.meta.url));
        if (!response.ok) throw new Error(`Approved ${gender} ${kind} unavailable`);
        return resolveImages(await response.json());
    })).then(([resources,trial])=>({resources,trial})));
    return cache.get(gender);
}
