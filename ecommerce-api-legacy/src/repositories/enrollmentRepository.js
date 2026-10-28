const { run, all } = require('../db/sqlite');

function createEnrollmentRepository(db) {
    return {
        async create({ userId, courseId }) {
            const result = await run(
                db,
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                [userId, courseId]
            );
            return { id: result.lastID, userId, courseId };
        },

        deleteByUserId(userId) {
            return run(db, 'DELETE FROM enrollments WHERE user_id = ?', [userId]);
        },

        listByUserId(userId) {
            return all(db, 'SELECT id, user_id, course_id FROM enrollments WHERE user_id = ?', [userId]);
        }
    };
}

module.exports = { createEnrollmentRepository };
