const { get, run } = require('../db/sqlite');

function createUserRepository(db) {
    return {
        findByEmail(email) {
            return get(db, 'SELECT id, name, email, pass FROM users WHERE email = ?', [email]);
        },

        findById(id) {
            return get(db, 'SELECT id, name, email, pass FROM users WHERE id = ?', [id]);
        },

        async create({ name, email, passHash }) {
            const result = await run(
                db,
                'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
                [name, email, passHash]
            );
            return { id: result.lastID, name, email };
        },

        async deleteById(id) {
            const result = await run(db, 'DELETE FROM users WHERE id = ?', [id]);
            return result.changes;
        }
    };
}

module.exports = { createUserRepository };
