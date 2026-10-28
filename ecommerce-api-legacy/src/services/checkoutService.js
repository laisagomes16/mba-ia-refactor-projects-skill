const { AppError } = require('../errors/AppError');

function createCheckoutService({
    courseRepository,
    userRepository,
    enrollmentRepository,
    paymentRepository,
    auditRepository,
    paymentGateway,
    passwordHasher,
    checkoutCache
}) {
    return {
        async checkout({ name, email, password, courseId, card }) {
            const course = await courseRepository.findActiveById(courseId);
            if (!course) {
                throw new AppError(404, 'Curso não encontrado');
            }

            let user = await userRepository.findByEmail(email);

            if (!user) {
                if (!password) {
                    throw new AppError(400, 'Bad Request');
                }
                const passHash = await passwordHasher.hash(password);
                user = await userRepository.create({
                    name,
                    email,
                    passHash
                });
            } else {
                if (!password) {
                    throw new AppError(401, 'Credenciais inválidas');
                }
                const ok = await passwordHasher.verify(password, user.pass);
                if (!ok) {
                    throw new AppError(401, 'Credenciais inválidas');
                }
            }

            const paymentResult = paymentGateway.charge({ card });
            if (paymentResult.status === 'DENIED') {
                throw new AppError(400, 'Pagamento recusado');
            }

            let enrollment;
            try {
                enrollment = await enrollmentRepository.create({
                    userId: user.id,
                    courseId
                });
            } catch {
                throw new AppError(500, 'Erro Matrícula');
            }

            try {
                await paymentRepository.create({
                    enrollmentId: enrollment.id,
                    amount: course.price,
                    status: paymentResult.status
                });
            } catch {
                throw new AppError(500, 'Erro Pagamento');
            }

            try {
                await auditRepository.log(`Checkout curso ${courseId} por ${user.id}`);
            } catch {
                throw new AppError(500, 'Erro DB');
            }

            checkoutCache.set(`last_checkout_${user.id}`, course.title);

            return { msg: 'Sucesso', enrollment_id: enrollment.id };
        }
    };
}

module.exports = { createCheckoutService };
