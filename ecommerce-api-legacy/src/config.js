const MIN_SEED_PASSWORD_LENGTH = 8;

function required(name) {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Missing required environment variable: ${name}`);
    }
    return value;
}

function requiredSeedUserPassword() {
    const value = required('SEED_USER_PASSWORD');
    if (value.length < MIN_SEED_PASSWORD_LENGTH) {
        throw new Error(
            `Environment variable SEED_USER_PASSWORD must have at least ${MIN_SEED_PASSWORD_LENGTH} characters`
        );
    }
    return value;
}

function loadConfig() {
    return {
        paymentGatewayKey: required('PAYMENT_GATEWAY_KEY'),
        adminApiKey: required('ADMIN_API_KEY'),
        seedUserPassword: requiredSeedUserPassword(),
        port: Number(process.env.PORT || 3000)
    };
}

module.exports = { loadConfig, MIN_SEED_PASSWORD_LENGTH };
