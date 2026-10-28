function createCheckoutCache() {
    const store = new Map();

    return {
        set(key, data) {
            console.log(`[LOG] Salvando no cache: ${key}`);
            store.set(key, data);
        },
        get(key) {
            return store.get(key);
        }
    };
}

module.exports = { createCheckoutCache };
