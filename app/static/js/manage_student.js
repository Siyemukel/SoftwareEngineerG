document.addEventListener('DOMContentLoaded', function () {

    // -------------------- Delete Modal Handling --------------------
    const confirmDeleteModal = document.getElementById('confirmDeleteModal');
    if (confirmDeleteModal) {
        confirmDeleteModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const studentId = button.getAttribute('data-student-id');
            const confirmBtn = confirmDeleteModal.querySelector('#confirmDeleteBtn');
            confirmBtn.href = `/delete_student/${studentId}`;
        });
    }

    // -------------------- Table Row Hover Effect --------------------
    const tableRows = document.querySelectorAll('.students-table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', () => row.style.backgroundColor = '#f1f3f5');
        row.addEventListener('mouseleave', () => row.style.backgroundColor = '');
    });

    // -------------------- Smooth Scroll for Buttons (Optional) --------------------
    const actionButtons = document.querySelectorAll('.action-buttons a');
    actionButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            btn.style.transition = 'all 0.2s ease';
            btn.style.transform = 'scale(0.97)';
            setTimeout(() => btn.style.transform = 'scale(1)', 200);
        });
    });

});
