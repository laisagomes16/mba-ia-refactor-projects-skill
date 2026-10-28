const { AppError } = require('../errors/AppError');

function validateCheckoutBody(body) {
    const name = body && body.usr;
    const email = body && body.eml;
    const password = body && body.pwd;
    const courseId = body && body.c_id;
    const card = body && body.card;

    if (!name || !email || !courseId || !card) {
        throw new AppError(400, 'Bad Request');
    }

    if (typeof name !== 'string' || typeof email !== 'string' || typeof card !== 'string') {
        throw new AppError(400, 'Bad Request');
    }

    if (typeof email !== 'string' || !email.includes('@')) {
        throw new AppError(400, 'Bad Request');
    }

    const parsedCourseId = Number(courseId);
    if (!Number.isInteger(parsedCourseId) || parsedCourseId <= 0) {
        throw new AppError(400, 'Bad Request');
    }

    return {
        name,
        email,
        password: password == null ? undefined : String(password),
        courseId: parsedCourseId,
        card
    };
}

module.exports = { validateCheckoutBody };
