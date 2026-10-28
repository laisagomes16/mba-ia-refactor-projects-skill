const crypto = require('crypto');
const { promisify } = require('util');

const scrypt = promisify(crypto.scrypt);
const KEY_LENGTH = 64;

function createPasswordHasher() {
    return {
        async hash(password) {
            const salt = crypto.randomBytes(16).toString('hex');
            const derived = await scrypt(password, salt, KEY_LENGTH);
            return `scrypt$${salt}$${derived.toString('hex')}`;
        },

        async verify(password, stored) {
            if (!stored || typeof stored !== 'string') return false;

            if (!stored.startsWith('scrypt$')) {
                return stored === password;
            }

            const parts = stored.split('$');
            if (parts.length !== 3) return false;

            const [, salt, hashHex] = parts;
            const derived = await scrypt(password, salt, KEY_LENGTH);
            const actual = Buffer.from(hashHex, 'hex');
            const expected = Buffer.from(derived);

            if (actual.length !== expected.length) return false;
            return crypto.timingSafeEqual(actual, expected);
        }
    };
}

module.exports = { createPasswordHasher };
