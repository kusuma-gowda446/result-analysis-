document.addEventListener('DOMContentLoaded', () => {
    // Auto dismiss flash alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // Close button click handler
    document.querySelectorAll('.alert-close').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.closest('.alert').remove();
        });
    });
});

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}
