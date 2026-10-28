const { run } = require('../db/sqlite');

function createAuditRepository(db) {
    return {
        log(action) {
            return run(
                db,
                "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
                [action]
            );
        }
    };
}

module.exports = { createAuditRepository };
