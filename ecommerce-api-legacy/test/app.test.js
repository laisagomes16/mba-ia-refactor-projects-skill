const test = require('node:test');
const assert = require('node:assert/strict');

const { createPasswordHasher } = require('../src/adapters/passwordHasher');
const { createPaymentGateway } = require('../src/adapters/paymentGateway');
const { createCheckoutCache } = require('../src/adapters/checkoutCache');
const { loadConfig, MIN_SEED_PASSWORD_LENGTH } = require('../src/config');
const { openDatabase, all, transaction } = require('../src/db/sqlite');
const { initDb } = require('../src/db/initDb');
const { createUserRepository } = require('../src/repositories/userRepository');
const { createEnrollmentRepository } = require('../src/repositories/enrollmentRepository');
const { createPaymentRepository } = require('../src/repositories/paymentRepository');
const { createCourseRepository } = require('../src/repositories/courseRepository');
const { createAuditRepository } = require('../src/repositories/auditRepository');
const { createReportRepository } = require('../src/repositories/reportRepository');
const { createCheckoutService } = require('../src/services/checkoutService');
const { createUserService } = require('../src/services/userService');
const { createFinancialReportService } = require('../src/services/financialReportService');
const { validateCheckoutBody } = require('../src/validators/checkoutValidator');
const { createAdminAuthMiddleware } = require('../src/middleware/auth');
const { AppError } = require('../src/errors/AppError');

const SEED_EMAIL = 'leonan@fullcycle.com.br';
const SEED_PASSWORD = 'seed-password';
const APPROVED_CARD = '4111222233334444';

async function buildContext() {
    const db = openDatabase();
    const passwordHasher = createPasswordHasher();
    await initDb(db, passwordHasher, SEED_PASSWORD);

    return {
        db,
        passwordHasher,
        userRepository: createUserRepository(db),
        enrollmentRepository: createEnrollmentRepository(db),
        paymentRepository: createPaymentRepository(db),
        courseRepository: createCourseRepository(db),
        auditRepository: createAuditRepository(db),
        reportRepository: createReportRepository(db)
    };
}

function buildCheckoutService(ctx, { paymentGateway } = {}) {
    return createCheckoutService({
        courseRepository: ctx.courseRepository,
        userRepository: ctx.userRepository,
        enrollmentRepository: ctx.enrollmentRepository,
        paymentRepository: ctx.paymentRepository,
        auditRepository: ctx.auditRepository,
        paymentGateway:
            paymentGateway || createPaymentGateway({ paymentGatewayKey: 'test-gateway-key' }),
        passwordHasher: ctx.passwordHasher,
        checkoutCache: createCheckoutCache()
    });
}

function buildUserService(ctx, overrides = {}) {
    return createUserService({
        db: ctx.db,
        userRepository: overrides.userRepository || ctx.userRepository,
        enrollmentRepository: overrides.enrollmentRepository || ctx.enrollmentRepository,
        paymentRepository: overrides.paymentRepository || ctx.paymentRepository
    });
}

function countUserOneRows(db) {
    return all(
        db,
        `SELECT
            (SELECT COUNT(*) FROM users WHERE id = 1) AS users,
            (SELECT COUNT(*) FROM enrollments WHERE user_id = 1) AS enrollments,
            (SELECT COUNT(*) FROM payments WHERE enrollment_id = 1) AS payments`
    );
}

function isAppError(statusCode) {
    return (err) => {
        assert.ok(err instanceof AppError, 'expected an AppError');
        assert.equal(err.statusCode, statusCode);
        return true;
    };
}

// FINDING-001 — secrets come only from the environment, with no insecure defaults.
test('config requires every secret from the environment', () => {
    const original = { ...process.env };
    try {
        delete process.env.PAYMENT_GATEWAY_KEY;
        delete process.env.ADMIN_API_KEY;
        delete process.env.SEED_USER_PASSWORD;

        assert.throws(() => loadConfig(), /PAYMENT_GATEWAY_KEY/);

        process.env.PAYMENT_GATEWAY_KEY = 'pk';
        assert.throws(() => loadConfig(), /ADMIN_API_KEY/);

        process.env.ADMIN_API_KEY = 'ak';
        assert.throws(() => loadConfig(), /SEED_USER_PASSWORD/);

        process.env.SEED_USER_PASSWORD = 'x'.repeat(MIN_SEED_PASSWORD_LENGTH - 1);
        assert.throws(() => loadConfig(), /at least/);

        process.env.SEED_USER_PASSWORD = 'x'.repeat(MIN_SEED_PASSWORD_LENGTH);
        const config = loadConfig();
        assert.deepEqual(Object.keys(config).sort(), [
            'adminApiKey',
            'paymentGatewayKey',
            'port',
            'seedUserPassword'
        ]);
    } finally {
        process.env = original;
    }
});

// FINDING-006 — strong hashing, no plaintext fallback.
test('passwordHasher stores scrypt hashes and never the plaintext', async () => {
    const hasher = createPasswordHasher();
    const stored = await hasher.hash('senha-forte');

    assert.match(stored, /^scrypt\$[0-9a-f]{32}\$[0-9a-f]+$/);
    assert.equal(await hasher.verify('senha-forte', stored), true);
    assert.equal(await hasher.verify('senha-errada', stored), false);
});

test('passwordHasher rejects plaintext or malformed stored values', async () => {
    const hasher = createPasswordHasher();

    assert.equal(await hasher.verify('123', '123'), false);
    assert.equal(await hasher.verify('abc', 'bcrypt$salt$hash'), false);
    assert.equal(await hasher.verify('abc', 'scrypt$only-two-parts'), false);
    assert.equal(await hasher.verify('abc', null), false);
    assert.equal(await hasher.verify('abc', 42), false);
});

test('initDb seeds the default user with a hash, not a plaintext password', async () => {
    const ctx = await buildContext();
    const rows = await all(ctx.db, 'SELECT pass FROM users WHERE id = 1');

    assert.match(rows[0].pass, /^scrypt\$/);
    assert.equal(await ctx.passwordHasher.verify(SEED_PASSWORD, rows[0].pass), true);
});

// FINDING-004 — identity check when the e-mail already exists.
test('checkout rejects an existing e-mail without password', async () => {
    const ctx = await buildContext();
    const service = buildCheckoutService(ctx);

    await assert.rejects(
        service.checkout({
            name: 'Leonan',
            email: SEED_EMAIL,
            courseId: 1,
            card: APPROVED_CARD
        }),
        isAppError(401)
    );
});

test('checkout rejects an existing e-mail with a wrong password', async () => {
    const ctx = await buildContext();
    const service = buildCheckoutService(ctx);

    await assert.rejects(
        service.checkout({
            name: 'Leonan',
            email: SEED_EMAIL,
            password: 'errada',
            courseId: 1,
            card: APPROVED_CARD
        }),
        isAppError(401)
    );

    assert.deepEqual(await all(ctx.db, 'SELECT id FROM audit_logs'), []);
});

test('checkout accepts an existing e-mail with the right password', async () => {
    const ctx = await buildContext();
    const service = buildCheckoutService(ctx);

    const result = await service.checkout({
        name: 'Leonan',
        email: SEED_EMAIL,
        password: SEED_PASSWORD,
        courseId: 2,
        card: APPROVED_CARD
    });

    assert.deepEqual(result, { msg: 'Sucesso', enrollment_id: 2 });
});

test('checkout requires a password for a new user', async () => {
    const ctx = await buildContext();
    const service = buildCheckoutService(ctx);

    await assert.rejects(
        service.checkout({ name: 'Ana', email: 'ana@test.com', courseId: 1, card: '4111' }),
        isAppError(400)
    );

    assert.deepEqual(await all(ctx.db, 'SELECT id FROM users WHERE email = ?', ['ana@test.com']), []);
});

// FINDING-010 — payment rules live in the adapter, not in the use case.
test('checkout delegates the charge to the injected payment gateway', async () => {
    const ctx = await buildContext();
    const calls = [];
    const service = buildCheckoutService(ctx, {
        paymentGateway: {
            charge(payload) {
                calls.push(payload);
                return { status: 'DENIED' };
            }
        }
    });

    await assert.rejects(
        service.checkout({
            name: 'Ana',
            email: 'ana@test.com',
            password: 'segredo',
            courseId: 1,
            card: APPROVED_CARD
        }),
        isAppError(400)
    );

    assert.deepEqual(calls, [{ card: APPROVED_CARD }]);
});

test('checkout rejects an unknown or inactive course', async () => {
    const ctx = await buildContext();
    const service = buildCheckoutService(ctx);

    await assert.rejects(
        service.checkout({
            name: 'Ana',
            email: 'ana@test.com',
            password: 'segredo',
            courseId: 99,
            card: APPROVED_CARD
        }),
        isAppError(404)
    );
});

// FINDING-011 — delete cascade runs inside a transaction.
test('deleteUser removes user, enrollments and payments', async () => {
    const ctx = await buildContext();
    const service = buildUserService(ctx);

    assert.equal(await service.deleteUser(1), 'Usuário deletado.');
    assert.deepEqual(await countUserOneRows(ctx.db), [{ users: 0, enrollments: 0, payments: 0 }]);
});

test('deleteUser rolls back every delete when a step fails', async () => {
    const ctx = await buildContext();
    const failingUserRepository = {
        ...ctx.userRepository,
        deleteById() {
            return Promise.reject(new Error('boom'));
        }
    };
    const service = buildUserService(ctx, { userRepository: failingUserRepository });

    await assert.rejects(service.deleteUser(1), isAppError(500));

    // Nothing may be lost: the rollback restores the rows already deleted.
    assert.deepEqual(await countUserOneRows(ctx.db), [{ users: 1, enrollments: 1, payments: 1 }]);
});

test('deleteUser reports a missing user instead of a fake success', async () => {
    const ctx = await buildContext();
    const service = buildUserService(ctx);

    await assert.rejects(service.deleteUser(999), isAppError(404));
});

test('transaction rolls back and rethrows the original error', async () => {
    const db = openDatabase();

    await assert.rejects(
        transaction(db, async () => {
            throw new Error('original');
        }),
        /original/
    );

    // The connection stays usable after the rollback.
    assert.deepEqual(await all(db, 'SELECT 1 AS ok'), [{ ok: 1 }]);
});

// FINDING-012 — set-based report with a single query.
test('financial report aggregates revenue from a single repository call', async () => {
    const calls = [];
    const reportRepository = {
        listFinancialRows() {
            calls.push(1);
            return Promise.resolve([
                { course_id: 1, course_title: 'Clean Architecture', enrollment_id: 1, student_name: 'Leonan', payment_amount: 997, payment_status: 'PAID' },
                { course_id: 2, course_title: 'Docker', enrollment_id: 2, student_name: 'Ana', payment_amount: 497, payment_status: 'PAID' },
                { course_id: 2, course_title: 'Docker', enrollment_id: 3, student_name: 'Bruno', payment_amount: 497, payment_status: 'DENIED' },
                { course_id: 3, course_title: 'Vazio', enrollment_id: null, student_name: null, payment_amount: null, payment_status: null }
            ]);
        }
    };

    const report = await createFinancialReportService({ reportRepository }).buildReport();

    assert.equal(calls.length, 1);
    assert.deepEqual(report, [
        {
            course: 'Clean Architecture',
            revenue: 997,
            students: [{ student: 'Leonan', paid: 997 }]
        },
        {
            course: 'Docker',
            revenue: 497,
            students: [
                { student: 'Ana', paid: 497 },
                { student: 'Bruno', paid: 497 }
            ]
        },
        { course: 'Vazio', revenue: 0, students: [] }
    ]);
});

test('financial report repository returns the seeded data in one query', async () => {
    const ctx = await buildContext();
    const report = await createFinancialReportService({
        reportRepository: ctx.reportRepository
    }).buildReport();

    assert.deepEqual(report, [
        {
            course: 'Clean Architecture',
            revenue: 997,
            students: [{ student: 'Leonan', paid: 997 }]
        },
        { course: 'Docker', revenue: 0, students: [] }
    ]);
});

// FINDING-013 — input validation.
test('checkout validator normalizes the legacy payload', () => {
    assert.deepEqual(
        validateCheckoutBody({
            usr: 'Ana',
            eml: 'ana@test.com',
            pwd: 'segredo',
            c_id: '2',
            card: '4111'
        }),
        {
            name: 'Ana',
            email: 'ana@test.com',
            password: 'segredo',
            courseId: 2,
            card: '4111'
        }
    );
});

test('checkout validator rejects invalid payloads', () => {
    const valid = { usr: 'Ana', eml: 'ana@test.com', pwd: 'x', c_id: 1, card: '4111' };
    const invalidPayloads = [
        null,
        {},
        { ...valid, usr: undefined },
        { ...valid, eml: undefined },
        { ...valid, card: undefined },
        { ...valid, eml: 'invalido' },
        { ...valid, usr: 123 },
        { ...valid, card: 4111 },
        { ...valid, c_id: 'abc' },
        { ...valid, c_id: 0 }
    ];

    for (const payload of invalidPayloads) {
        assert.throws(() => validateCheckoutBody(payload), isAppError(400));
    }
});

// FINDING-002 — admin authn/authz guard.
test('admin middleware requires the configured key', async () => {
    const requireAdmin = createAdminAuthMiddleware({ adminApiKey: 'admin-secret' });
    const run = (headers) => {
        const req = { header: (name) => headers[name.toLowerCase()] };
        return new Promise((resolve) => {
            requireAdmin(req, {}, resolve);
        });
    };

    for (const headers of [{}, { 'x-admin-key': 'wrong' }, { authorization: 'Bearer wrong' }]) {
        assert.ok(isAppError(401)(await run(headers)));
    }

    assert.equal(await run({ 'x-admin-key': 'admin-secret' }), undefined);
    assert.equal(await run({ authorization: 'Bearer admin-secret' }), undefined);
});

// FINDING-005 — no card number or gateway key in logs.
test('payment gateway and cache never log the card or the gateway key', () => {
    const written = [];
    const original = console.log;
    console.log = (...args) => written.push(args.join(' '));

    try {
        createPaymentGateway({ paymentGatewayKey: 'pk_super_secret' }).charge({
            card: APPROVED_CARD
        });
        createCheckoutCache().set('last_checkout_1', 'Clean Architecture');
    } finally {
        console.log = original;
    }

    const output = written.join('\n');
    assert.equal(output.includes(APPROVED_CARD), false);
    assert.equal(output.includes('pk_super_secret'), false);
});
