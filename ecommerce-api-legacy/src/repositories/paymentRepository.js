const { run } = require('../db/sqlite');

function createPaymentRepository(db) {
    return {
        async create({ enrollmentId, amount, status }) {
            const result = await run(
                db,
                'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
                [enrollmentId, amount, status]
            );
            return { id: result.lastID, enrollmentId, amount, status };
        },

        deleteByEnrollmentIds(enrollmentIds) {
            if (!enrollmentIds.length) {
                return Promise.resolve({ changes: 0 });
            }
            const placeholders = enrollmentIds.map(() => '?').join(', ');
            return run(
                db,
                `DELETE FROM payments WHERE enrollment_id IN (${placeholders})`,
                enrollmentIds
            );
        }
    };
}

module.exports = { createPaymentRepository };
