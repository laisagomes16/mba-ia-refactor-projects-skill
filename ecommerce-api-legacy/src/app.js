const express = require('express');
const { loadConfig } = require('./config');
const { openDatabase } = require('./db/sqlite');
const { initDb } = require('./db/initDb');
const { createPasswordHasher } = require('./adapters/passwordHasher');
const { createPaymentGateway } = require('./adapters/paymentGateway');
const { createCheckoutCache } = require('./adapters/checkoutCache');
const { createUserRepository } = require('./repositories/userRepository');
const { createCourseRepository } = require('./repositories/courseRepository');
const { createEnrollmentRepository } = require('./repositories/enrollmentRepository');
const { createPaymentRepository } = require('./repositories/paymentRepository');
const { createAuditRepository } = require('./repositories/auditRepository');
const { createReportRepository } = require('./repositories/reportRepository');
const { createCheckoutService } = require('./services/checkoutService');
const { createFinancialReportService } = require('./services/financialReportService');
const { createUserService } = require('./services/userService');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createFinancialReportController } = require('./controllers/financialReportController');
const { createUserController } = require('./controllers/userController');
const { createAdminAuthMiddleware } = require('./middleware/auth');
const { errorHandler } = require('./middleware/errorHandler');
const { createRouter } = require('./routes');

async function bootstrap() {
    const config = loadConfig();
    const db = openDatabase();
    const passwordHasher = createPasswordHasher();

    await initDb(db, passwordHasher, config.seedUserPassword);

    const userRepository = createUserRepository(db);
    const courseRepository = createCourseRepository(db);
    const enrollmentRepository = createEnrollmentRepository(db);
    const paymentRepository = createPaymentRepository(db);
    const auditRepository = createAuditRepository(db);
    const reportRepository = createReportRepository(db);

    const paymentGateway = createPaymentGateway({
        paymentGatewayKey: config.paymentGatewayKey
    });
    const checkoutCache = createCheckoutCache();

    const checkoutService = createCheckoutService({
        courseRepository,
        userRepository,
        enrollmentRepository,
        paymentRepository,
        auditRepository,
        paymentGateway,
        passwordHasher,
        checkoutCache
    });
    const financialReportService = createFinancialReportService({ reportRepository });
    const userService = createUserService({
        userRepository,
        enrollmentRepository,
        paymentRepository
    });

    const checkoutController = createCheckoutController({ checkoutService });
    const financialReportController = createFinancialReportController({ financialReportService });
    const userController = createUserController({ userService });
    const requireAdmin = createAdminAuthMiddleware({ adminApiKey: config.adminApiKey });

    const app = express();
    app.use(express.json());
    app.use(
        createRouter({
            checkoutController,
            financialReportController,
            userController,
            requireAdmin
        })
    );
    app.use(errorHandler);

    app.listen(config.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

bootstrap().catch((err) => {
    console.error('Falha ao iniciar a aplicação:', err.message);
    process.exit(1);
});
