
const sidebarToggle = document.getElementById("sidebarToggle");
const sidebar = document.querySelector(".sidebar");
const appLayout = document.querySelector(".app-layout");

if (sidebarToggle && sidebar && appLayout) {
    function updateSidebarButton(isOpen) {
        sidebarToggle.textContent = isOpen ? "×" : "☰";
        sidebarToggle.setAttribute(
            "aria-label",
            isOpen ? "Fechar menu" : "Abrir menu"
        );
        sidebarToggle.setAttribute("aria-expanded", String(isOpen));
    }

    sidebarToggle.addEventListener("click", function () {
        if (window.innerWidth <= 768) {
            const isOpen = sidebar.classList.toggle("open");
            updateSidebarButton(isOpen);
        } else {
            const isCollapsed =
                appLayout.classList.toggle("sidebar-collapsed");

            updateSidebarButton(!isCollapsed);
        }
    });

    document.addEventListener("click", function (event) {
        if (
            window.innerWidth <= 768 &&
            sidebar.classList.contains("open") &&
            !sidebar.contains(event.target) &&
            !sidebarToggle.contains(event.target)
        ) {
            sidebar.classList.remove("open");
            updateSidebarButton(false);
        }
    });

    window.addEventListener("resize", function () {
        sidebar.classList.remove("open");
        appLayout.classList.remove("sidebar-collapsed");

        updateSidebarButton(window.innerWidth > 768);
    });
}
