const { AppError } = require('../errors/AppError');

function createUserService({
    userRepository,
    enrollmentRepository,
    paymentRepository
}) {
    return {
        async deleteUser(id) {
            const user = await userRepository.findById(id);
            if (!user) {
                throw new AppError(404, 'Usuário não encontrado');
            }

            const enrollments = await enrollmentRepository.listByUserId(id);
            const enrollmentIds = enrollments.map((e) => e.id);

            try {
                await paymentRepository.deleteByEnrollmentIds(enrollmentIds);
                await enrollmentRepository.deleteByUserId(id);
                await userRepository.deleteById(id);
            } catch {
                throw new AppError(500, 'Erro DB');
            }

            return 'Usuário deletado.';
        }
    };
}

module.exports = { createUserService };
