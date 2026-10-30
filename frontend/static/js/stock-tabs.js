
document.addEventListener("DOMContentLoaded", () => {
    const managementTab = document.getElementById("stockManagementTab");
    const movementsTab = document.getElementById("stockMovementsTab");

    const managementPanel = document.getElementById("stockManagementPanel");
    const movementsPanel = document.getElementById("stockMovementsPanel");

    if (!managementTab || !movementsTab ||
        !managementPanel || !movementsPanel) {
        return;
    }

    function activateTab(tab) {
        const showMovements = tab === "movements";

        managementPanel.hidden = showMovements;
        movementsPanel.hidden = !showMovements;

        managementTab.classList.toggle("active", !showMovements);
        movementsTab.classList.toggle("active", showMovements);

        managementTab.setAttribute(
            "aria-selected",
            String(!showMovements)
        );

        movementsTab.setAttribute(
            "aria-selected",
            String(showMovements)
        );
    }

    managementTab.addEventListener("click", () => {
        activateTab("management");
    });

    movementsTab.addEventListener("click", () => {
        activateTab("movements");
    });

    activateTab("management");
});
