const sqlite3 = require('sqlite3').verbose();

function openDatabase() {
    return new sqlite3.Database(':memory:');
}

function run(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function onRun(err) {
            if (err) return reject(err);
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

function all(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) return reject(err);
            resolve(rows);
        });
    });
}

/**
 * Runs `fn` inside BEGIN/COMMIT, rolling back if it throws.
 * The callback executes in the same serialize queue, so no other query on this
 * connection can interleave between the statements of the transaction.
 */
function transaction(db, fn) {
    return serialize(db, async () => {
        await run(db, 'BEGIN');

        let result;
        try {
            result = await fn();
        } catch (err) {
            try {
                await run(db, 'ROLLBACK');
            } catch {
                // Rollback failure must not hide the original error.
            }
            throw err;
        }

        try {
            await run(db, 'COMMIT');
        } catch (err) {
            await run(db, 'ROLLBACK').catch(() => {});
            throw err;
        }

        return result;
    });
}

function serialize(db, fn) {
    return new Promise((resolve, reject) => {
        db.serialize(() => {
            Promise.resolve()
                .then(fn)
                .then(resolve)
                .catch(reject);
        });
    });
}

module.exports = { openDatabase, run, get, all, serialize, transaction };
