const sidebarToggle = document.getElementById("sidebarToggle");
const sidebar = document.querySelector(".sidebar");

if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", function () {
        const isOpen = sidebar.classList.toggle("open");

        sidebarToggle.textContent = isOpen ? "×" : "☰";
        sidebarToggle.setAttribute(
            "aria-label",
            isOpen ? "Fechar menu" : "Abrir menu"
        );
        sidebarToggle.setAttribute("aria-expanded", String(isOpen));
    });

    document.addEventListener("click", function (event) {
        if (
            window.innerWidth <= 768 &&
            sidebar.classList.contains("open") &&
            !sidebar.contains(event.target) &&
            !sidebarToggle.contains(event.target)
        ) {
            sidebar.classList.remove("open");
            sidebarToggle.textContent = "☰";
            sidebarToggle.setAttribute("aria-label", "Abrir menu");
            sidebarToggle.setAttribute("aria-expanded", "false");
        }
    });
}