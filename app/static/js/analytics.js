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
                    '#10b981', // Distinction - Green
                    '#3b82f6', // First Class - Blue
                    '#f59e0b', // Second Class - Yellow
                    '#8b5cf6', // Pass - Purple
                    '#ef4444'  // Fail - Red
                ],
                borderWidth: 2,
                borderColor: '#ffffff'
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
                    backgroundColor: '#1d4ed8',
                    borderRadius: 4
                },
                {
                    label: 'Max Possible Marks',
                    data: maxScores,
                    backgroundColor: '#e2e8f0',
                    borderRadius: 4
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
        tr.innerHTML = `
            <td><strong>#${index + 1}</strong></td>
            <td>${student.usn}</td>
            <td>${student.name}</td>
            <td><strong>${student.percentage}%</strong> (${student.total} marks)</td>
            <td><span class="badge badge-${student.grade.toLowerCase().replace(' ', '')}">${student.grade}</span></td>
        `;
        tbody.appendChild(tr);
    });
}
