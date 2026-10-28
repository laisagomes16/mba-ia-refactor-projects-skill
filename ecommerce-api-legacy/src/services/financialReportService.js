function createFinancialReportService({ reportRepository }) {
    return {
        async buildReport() {
            const rows = await reportRepository.listFinancialRows();
            const byCourse = new Map();

            for (const row of rows) {
                if (!byCourse.has(row.course_id)) {
                    byCourse.set(row.course_id, {
                        course: row.course_title,
                        revenue: 0,
                        students: []
                    });
                }

                const courseData = byCourse.get(row.course_id);

                if (!row.enrollment_id) {
                    continue;
                }

                if (row.payment_status === 'PAID' && row.payment_amount != null) {
                    courseData.revenue += row.payment_amount;
                }

                courseData.students.push({
                    student: row.student_name || 'Unknown',
                    paid: row.payment_amount != null ? row.payment_amount : 0
                });
            }

            return Array.from(byCourse.values());
        }
    };
}

module.exports = { createFinancialReportService };
