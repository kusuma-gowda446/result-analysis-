document.addEventListener('DOMContentLoaded', () => {
    fetch('/analytics/api/stats')
        .then(response => response.json())
        .then(data => {
            renderGradeChart(data.grade_counts);
            renderSubjectChart(data.subject_stats);
            renderTopPerformersTable(data.top_performers);
        })
        .catch(err => console.error('Error loading analytics:', err));
});

function renderGradeChart(gradeCounts) {
    const ctx = document.getElementById('gradeChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(gradeCounts),
            datasets: [{
                data: Object.values(gradeCounts),
                backgroundColor: [
                    '#10b981', // Distinction - Emerald
                    '#2563eb', // First Class - Royal Blue
                    '#f59e0b', // Second Class - Amber
                    '#8b5cf6', // Pass - Purple
                    '#ef4444'  // Fail - Crimson
                ],
                borderWidth: 2,
                borderColor: 'transparent'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function renderSubjectChart(subjectStats) {
    const ctx = document.getElementById('subjectChart');
    if (!ctx) return;

    const labels = subjectStats.map(s => s.name);
    const avgScores = subjectStats.map(s => s.avg_score);
    const maxScores = subjectStats.map(s => s.max_marks);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Class Average',
                    data: avgScores,
                    backgroundColor: '#2563eb',
                    borderRadius: 6
                },
                {
                    label: 'Max Possible Marks',
                    data: maxScores,
                    backgroundColor: 'rgba(148, 163, 184, 0.25)',
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            },
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
}

function renderTopPerformersTable(topPerformers) {
    const tbody = document.getElementById('topPerformersBody');
    if (!tbody) return;

    tbody.innerHTML = '';
    topPerformers.forEach((student, index) => {
        const tr = document.createElement('tr');
        let badgeClass = 'badge-emerald';
        if (student.grade === 'Fail') badgeClass = 'badge-crimson';
        else if (student.grade === 'Second Class' || student.grade === 'Pass') badgeClass = 'badge-amber';

        tr.innerHTML = `
            <td class="ps-4"><strong>#${index + 1}</strong></td>
            <td><span class="badge badge-amber font-monospace">${student.usn}</span></td>
            <td class="fw-bold text-body">${student.name}</td>
            <td class="text-center font-monospace"><strong>${student.percentage}%</strong> (${student.total} marks)</td>
            <td class="text-center pe-4"><span class="badge ${badgeClass} px-3 py-1 rounded-pill fs-8">${student.grade}</span></td>
        `;
        tbody.appendChild(tr);
    });
}
