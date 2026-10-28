function required(name) {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Missing required environment variable: ${name}`);
    }
    return value;
}

function loadConfig() {
    return {
        dbUser: required('DB_USER'),
        dbPass: required('DB_PASS'),
        paymentGatewayKey: required('PAYMENT_GATEWAY_KEY'),
        smtpUser: process.env.SMTP_USER || '',
        adminApiKey: required('ADMIN_API_KEY'),
        port: Number(process.env.PORT || 3000),
        seedUserPassword: process.env.SEED_USER_PASSWORD || '123'
    };
}

module.exports = { loadConfig };
