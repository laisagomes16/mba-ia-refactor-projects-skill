const { AppError } = require('../errors/AppError');

function errorHandler(err, req, res, next) {
    if (res.headersSent) {
        return next(err);
    }

    if (err instanceof AppError) {
        return res.status(err.statusCode).send(err.message);
    }

    console.error('[ERROR]', err && err.message ? err.message : 'Unknown error');
    return res.status(500).send('Erro DB');
}

module.exports = { errorHandler };
