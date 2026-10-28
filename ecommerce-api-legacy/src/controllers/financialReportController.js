function createFinancialReportController({ financialReportService }) {
    return {
        async report(req, res, next) {
            try {
                const report = await financialReportService.buildReport();
                res.status(200).json(report);
            } catch (err) {
                next(err);
            }
        }
    };
}

module.exports = { createFinancialReportController };
