const CARD_APPROVED_PREFIX = '4';

function createPaymentGateway({ paymentGatewayKey }) {
    return {
        charge({ card }) {
            // Key is required for adapter construction; never log card or key.
            if (!paymentGatewayKey) {
                return { status: 'DENIED' };
            }

            const status = String(card).startsWith(CARD_APPROVED_PREFIX) ? 'PAID' : 'DENIED';
            return { status };
        }
    };
}

module.exports = { createPaymentGateway, CARD_APPROVED_PREFIX };
