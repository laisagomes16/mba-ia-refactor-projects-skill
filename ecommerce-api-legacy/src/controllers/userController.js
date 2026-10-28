const { AppError } = require('../errors/AppError');

function createUserController({ userService }) {
    return {
        async deleteUser(req, res, next) {
            try {
                const id = Number(req.params.id);
                if (!Number.isInteger(id) || id <= 0) {
                    throw new AppError(400, 'Bad Request');
                }

                const message = await userService.deleteUser(id);
                res.status(200).send(message);
            } catch (err) {
                next(err);
            }
        }
    };
}

module.exports = { createUserController };
