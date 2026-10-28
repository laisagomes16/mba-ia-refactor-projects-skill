const { AppError } = require('../errors/AppError');

function createAdminAuthMiddleware({ adminApiKey }) {
    return function requireAdmin(req, res, next) {
        const headerKey = req.header('x-admin-key');
        const bearer = req.header('authorization');
        let token = headerKey;

        if (!token && bearer && bearer.toLowerCase().startsWith('bearer ')) {
            token = bearer.slice(7).trim();
        }

        if (!token || token !== adminApiKey) {
            return next(new AppError(401, 'Unauthorized'));
        }

        return next();
    };
}

module.exports = { createAdminAuthMiddleware };
