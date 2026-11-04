
(function () {
    "use strict";

    const ROLE_ALIASES = {
        ADMIN: "ADMIN",
        GESTOR: "GESTOR",
        MANAGER: "GESTOR",
        OPERADOR: "OPERADOR",
        OPERATOR: "OPERADOR"
    };

    let currentUser = null;
    let userPromise = null;

    function getToken() {
        return localStorage.getItem("access_token");
    }

    function normalizeRole(role) {
        if (!role) {
            return null;
        }

        return ROLE_ALIASES[String(role).trim().toUpperCase()] || null;
    }

    function logout() {
        localStorage.removeItem("access_token");

        currentUser = null;
        userPromise = null;

        window.location.replace("/login");
    }

    async function getCurrentUser() {
        if (currentUser) {
            return currentUser;
        }

        if (userPromise) {
            return userPromise;
        }

        const token = getToken();

        if (!token) {
            return null;
        }

        userPromise = (async function () {
            const response = await fetch("/auth/me", {
                method: "GET",
                headers: {
                    Authorization: `Bearer ${token}`
                },
                cache: "no-store"
            });

            if (response.status === 401) {
                logout();
                return null;
            }

            if (!response.ok) {
                throw new Error(
                    "Não foi possível verificar o usuário autenticado."
                );
            }

            const user = await response.json();

            if (!user.is_active) {
                logout();
                return null;
            }

            user.role = normalizeRole(user.role);

            if (!user.role) {
                throw new Error(
                    "Perfil de acesso não reconhecido."
                );
            }

            currentUser = user;

            return user;
        })();

        try {
            return await userPromise;
        } finally {
            userPromise = null;
        }
    }

    async function hasRole(...allowedRoles) {
        const user = await getCurrentUser();

        if (!user) {
            return false;
        }

        return allowedRoles
            .map(normalizeRole)
            .includes(user.role);
    }

    function applyRolePermissions(user) {
        const elements = document.querySelectorAll("[data-roles]");

        elements.forEach(function (element) {
            const allowedRoles = element.dataset.roles
                .split(",")
                .map(normalizeRole)
                .filter(Boolean);

            const allowed = Boolean(
                user && allowedRoles.includes(user.role)
            );

            element.hidden = !allowed;
        });
    }

    async function initializePermissions() {
        const elements = document.querySelectorAll("[data-roles]");

        if (elements.length === 0) {
            return;
        }

        // Elementos restritos ficam ocultos até a verificação.
        elements.forEach(function (element) {
            element.hidden = true;
        });

        try {
            const user = await getCurrentUser();
            applyRolePermissions(user);
        } catch (error) {
            console.error(
                "Erro ao carregar permissões:",
                error
            );

            applyRolePermissions(null);
        }
    }

    function setupLogout() {
        document.querySelectorAll(
            ".logout-link, [data-logout]"
        ).forEach(function (element) {
            element.addEventListener("click", function (event) {
                event.preventDefault();
                logout();
            });
        });
    }

    function initialize() {
        setupLogout();
        initializePermissions();
    }

    window.WarehouseAuth = {
        getToken,
        getCurrentUser,
        hasRole,
        normalizeRole,
        applyRolePermissions,
        logout
    };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initialize);
    } else {
        initialize();
    }
})();
