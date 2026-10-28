const express = require('express');

function createRouter({
    checkoutController,
    financialReportController,
    userController,
    requireAdmin
}) {
    const router = express.Router();

    router.post('/api/checkout', (req, res, next) => checkoutController.checkout(req, res, next));
    router.get(
        '/api/admin/financial-report',
        requireAdmin,
        (req, res, next) => financialReportController.report(req, res, next)
    );
    router.delete(
        '/api/users/:id',
        requireAdmin,
        (req, res, next) => userController.deleteUser(req, res, next)
    );

    return router;
}

module.exports = { createRouter };
