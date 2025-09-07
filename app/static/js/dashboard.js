// Search Function
document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("studentSearch");
    const table = document.getElementById("studentsTable");
    const rows = table.tBodies[0].rows;

    searchInput.addEventListener("keyup", () => {
        const filter = searchInput.value.toLowerCase();
        for (let row of rows) {
            const name = row.cells[0].textContent.toLowerCase();
            const email = row.cells[1].textContent.toLowerCase();
            row.style.display = name.includes(filter) || email.includes(filter) ? "" : "none";
        }
    });

    // Staff Filter (admin only)
    const staffFilter = document.getElementById("staffFilter");
    if (staffFilter) {
        staffFilter.addEventListener("change", () => {
            const selected = staffFilter.value.toLowerCase();
            for (let row of rows) {
                const staffCell = row.cells[5]; // Assigned Staff column (admin)
                if (!staffCell) continue;
                const staffNames = staffCell.textContent.toLowerCase();
                row.style.display = !selected || staffNames.includes(selected) ? "" : "none";
            }
        });
    }

    // Simple column sorting
    const headers = table.querySelectorAll("th");
    headers.forEach((header, index) => {
        header.addEventListener("click", () => {
            const tbody = table.tBodies[0];
            Array.from(tbody.querySelectorAll("tr"))
                .sort((a, b) => {
                    const cellA = a.cells[index].textContent.trim().toLowerCase();
                    const cellB = b.cells[index].textContent.trim().toLowerCase();
                    return cellA.localeCompare(cellB);
                })
                .forEach(row => tbody.appendChild(row));
            
            headers.forEach(h => h.classList.remove("sort-asc", "sort-desc"));
            header.classList.add("sort-asc");
        });
    });
});
