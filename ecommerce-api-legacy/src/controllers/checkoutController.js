const { validateCheckoutBody } = require('../validators/checkoutValidator');

function createCheckoutController({ checkoutService }) {
    return {
        async checkout(req, res, next) {
            try {
                const input = validateCheckoutBody(req.body);
                const result = await checkoutService.checkout(input);
                res.status(200).json(result);
            } catch (err) {
                next(err);
            }
        }
    };
}

module.exports = { createCheckoutController };
