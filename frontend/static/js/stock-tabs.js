
document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const managementTab = document.getElementById("stockManagementTab");
    const movementsTab = document.getElementById("stockMovementsTab");

    const managementPanel = document.getElementById("stockManagementPanel");
    const movementsPanel = document.getElementById("stockMovementsPanel");

    if (!managementTab || !movementsTab ||
        !managementPanel || !movementsPanel) {
        return;
    }

    // PERMISSÕES — SPRINT 08


    let canAccessMovements = false;

    // Oculta o relatório até confirmar o perfil.
    movementsTab.hidden = true;
    movementsPanel.hidden = true;

    // CONTROLE DAS ABAS


    function activateTab(tab) {
        const showMovements = tab === "movements";

        // Bloqueia a abertura sem permissão.
        if (showMovements && !canAccessMovements) {
            return;
        }

        managementPanel.hidden = showMovements;
        movementsPanel.hidden = !showMovements;

        managementTab.classList.toggle(
            "active",
            !showMovements
        );

        movementsTab.classList.toggle(
            "active",
            showMovements
        );

        managementTab.setAttribute(
            "aria-selected",
            String(!showMovements)
        );

        movementsTab.setAttribute(
            "aria-selected",
            String(showMovements)
        );
    }


    // EVENTOS


    managementTab.addEventListener("click", () => {
        activateTab("management");
    });

    movementsTab.addEventListener("click", () => {
        activateTab("movements");
    });


    // INICIALIZAÇÃO DAS PERMISSÕES


    async function initializePermissions() {
        activateTab("management");

        try {
            if (!window.WarehouseAuth) {
                throw new Error(
                    "Módulo de autenticação indisponível."
                );
            }

            canAccessMovements = await window.WarehouseAuth.hasRole(
                "ADMIN",
                "GESTOR"
            );

            movementsTab.hidden = !canAccessMovements;

            if (!canAccessMovements) {
                activateTab("management");
            }
        } catch (error) {
            console.error(
                "Erro ao verificar permissões do estoque:",
                error
            );

            canAccessMovements = false;
            movementsTab.hidden = true;
            activateTab("management");
        }
    }

    initializePermissions();
});
