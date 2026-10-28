const { get, all } = require('../db/sqlite');

function createCourseRepository(db) {
    return {
        findActiveById(id) {
            return get(db, 'SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1', [id]);
        },

        listAll() {
            return all(db, 'SELECT id, title, price, active FROM courses', []);
        }
    };
}

module.exports = { createCourseRepository };
