
document.addEventListener("DOMContentLoaded", async () => {
    "use strict";

    const elements = {
        tableBody: document.getElementById("usersTableBody"),
        message: document.getElementById("usersMessage"),
        search: document.getElementById("userSearch"),
        roleFilter: document.getElementById("userRoleFilter"),
        newButton: document.getElementById("newUserButton"),

        modal: document.getElementById("userModal"),
        modalTitle: document.getElementById("userModalTitle"),
        form: document.getElementById("userForm"),
        formMessage: document.getElementById("userFormMessage"),
        saveButton: document.getElementById("saveUserButton"),
        closeButton: document.getElementById("closeUserModal"),
        cancelButton: document.getElementById("cancelUserButton"),

        name: document.getElementById("userName"),
        email: document.getElementById("userEmail"),
        password: document.getElementById("userPassword"),
        passwordHint: document.getElementById("userPasswordHint"),
        role: document.getElementById("userRole"),
        activeGroup: document.getElementById("userActiveGroup"),
        active: document.getElementById("userActive"),

        deleteModal: document.getElementById("deleteUserModal"),
        deleteName: document.getElementById("deleteUserName"),
        deleteMessage: document.getElementById("deleteUserMessage"),
        closeDeleteButton: document.getElementById("closeDeleteUserModal"),
        cancelDeleteButton: document.getElementById("cancelDeleteUserButton"),
        confirmDeleteButton: document.getElementById("confirmDeleteUserButton")
    };

    const API_URL = "/users/";
    const ROLES_URL = "/users/roles/";

    let users = [];
    let roles = [];
    let editingUserId = null;
    let deletingUserId = null;
    let loadingUsers = false;

    // ======================================================
    // AUTENTICAÇÃO E REQUISIÇÕES
    // ======================================================

    function getToken() {
        return window.WarehouseAuth?.getToken?.()
            || localStorage.getItem("access_token");
    }

    async function apiRequest(url, options = {}) {
        const token = getToken();

        if (!token) {
            throw new Error("Sessão não encontrada. Faça login novamente.");
        }

        const headers = new Headers(options.headers || {});
        headers.set("Authorization", `Bearer ${token}`);

        if (options.body && !(options.body instanceof FormData)) {
            headers.set("Content-Type", "application/json");
        }

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (response.status === 204) {
            return null;
        }

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            let message = "Não foi possível concluir a operação.";

            if (typeof data?.detail === "string") {
                message = data.detail;
            } else if (Array.isArray(data?.detail)) {
                message = data.detail
                    .map(item => item.msg || "Dados inválidos.")
                    .join(" ");
            }

            if (response.status === 401) {
                message = "Sua sessão expirou. Faça login novamente.";
            }

            if (response.status === 403) {
                message = "Seu perfil não tem permissão para esta operação.";
            }

            throw new Error(message);
        }

        return data;
    }

    async function verifyAdminAccess() {
        try {
            const user = await window.WarehouseAuth.getCurrentUser();

            const role = window.WarehouseAuth.normalizeRole(
                user?.role || ""
            );

            return role === "ADMIN";
        } catch (error) {
            console.error("Erro ao verificar permissões:", error);
            return false;
        }
    }

    // ======================================================
    // UTILITÁRIOS
    // ======================================================

    function showMessage(message) {
        elements.message.textContent = message;
    }

    function formatDate(value) {
        if (!value) {
            return "—";
        }

        const normalizedValue = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value)
            ? value
            : `${value}Z`;

        const date = new Date(normalizedValue);

        if (Number.isNaN(date.getTime())) {
            return "—";
        }

        return new Intl.DateTimeFormat("pt-BR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            timeZone: "America/Sao_Paulo"
        }).format(date);
    }

    function normalizeRole(role) {
        return window.WarehouseAuth.normalizeRole(role);
    }

    function getRoleName(user) {
        return normalizeRole(user.role?.name || "");
    }

    function setFormMessage(message, isError = true) {
        elements.formMessage.textContent = message;
        elements.formMessage.style.color = isError
            ? "#b91c1c"
            : "#166534";
    }

    function setDeleteMessage(message) {
        elements.deleteMessage.textContent = message;
    }

    function setButtonLoading(button, loading, text) {
        button.disabled = loading;
        button.textContent = loading ? "Aguarde..." : text;
    }

    function createCell(value) {
        const cell = document.createElement("td");
        cell.textContent = String(value ?? "—");
        return cell;
    }

    // ======================================================
    // TABELA E FILTROS
    // ======================================================

    function renderUsers() {
        elements.tableBody.replaceChildren();

        const search = elements.search.value.trim().toLowerCase();
        const selectedRole = elements.roleFilter.value;

        const filteredUsers = users.filter(user => {
            const matchesSearch = String(user.email || "")
                .toLowerCase()
                .includes(search);

            const matchesRole = !selectedRole
                || getRoleName(user) === selectedRole;

            return matchesSearch && matchesRole;
        });

        if (filteredUsers.length === 0) {
            showMessage("Nenhum usuário encontrado.");
            return;
        }

        showMessage("");

        filteredUsers.forEach(user => {
            const row = document.createElement("tr");

            row.appendChild(createCell(user.id));
            row.appendChild(createCell(user.name));
            row.appendChild(createCell(user.email));
            row.appendChild(createCell(getRoleName(user) || "Sem perfil"));

            const statusCell = document.createElement("td");
            const statusBadge = document.createElement("span");

            const isActive = user.is_active !== false;

            statusBadge.className = isActive
                ? "user-status active"
                : "user-status inactive";

            statusBadge.textContent = isActive
                ? "Ativo"
                : "Inativo";

            statusCell.appendChild(statusBadge);
            row.appendChild(statusCell);

            row.appendChild(createCell(formatDate(user.created_at)));

            const actionsCell = document.createElement("td");
            const actions = document.createElement("div");
            actions.className = "user-actions";

            const editButton = document.createElement("button");
            editButton.type = "button";
            editButton.className = "user-action-button";
            editButton.textContent = "Editar";
            editButton.addEventListener("click", () => {
                openEditModal(user);
            });

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className = "user-action-button delete";
            deleteButton.textContent = "Excluir";
            deleteButton.addEventListener("click", () => {
                openDeleteModal(user);
            });

            actions.append(editButton, deleteButton);
            actionsCell.appendChild(actions);
            row.appendChild(actionsCell);

            elements.tableBody.appendChild(row);
        });
    }

    async function loadUsers() {
        if (loadingUsers) {
            return;
        }

        loadingUsers = true;
        showMessage("Carregando usuários...");
        elements.tableBody.replaceChildren();

        try {
            // A API permite até 500 registros por requisição.
            // A paginação busca todos os registros disponíveis.
            const allUsers = [];
            const pageSize = 100;
            let offset = 0;

            while (true) {
                const page = await apiRequest(
                    `${API_URL}?skip=${offset}&limit=${pageSize}`
                );

                if (!Array.isArray(page)) {
                    throw new Error("Resposta inválida da API de usuários.");
                }

                allUsers.push(...page);

                if (page.length < pageSize) {
                    break;
                }

                offset += pageSize;
            }

            users = allUsers;
            renderUsers();
        } catch (error) {
            users = [];
            showMessage(error.message);
            console.error("Erro ao carregar usuários:", error);
        } finally {
            loadingUsers = false;
        }
    }

    // ======================================================
    // PERFIS
    // ======================================================

    async function loadRoles() {
        const response = await apiRequest(ROLES_URL);

        if (!Array.isArray(response)) {
            throw new Error("Não foi possível carregar os perfis.");
        }

        roles = response;
        elements.role.replaceChildren();

        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Selecione um perfil";
        elements.role.appendChild(placeholder);

        roles.forEach(role => {
            const option = document.createElement("option");
            option.value = String(role.id);
            option.textContent = normalizeRole(role.name);
            elements.role.appendChild(option);
        });
    }

    // ======================================================
    // MODAL DE CADASTRO E EDIÇÃO
    // ======================================================

    function closeUserModal() {
        elements.modal.classList.remove("open");
        elements.form.reset();
        setFormMessage("");
        editingUserId = null;
    }

    function openNewModal() {
        editingUserId = null;
        elements.form.reset();
        setFormMessage("");

        elements.modalTitle.textContent = "Novo usuário";
        elements.saveButton.textContent = "Cadastrar usuário";

        elements.password.required = true;
        elements.passwordHint.textContent =
            "A senha deve conter entre 6 e 72 caracteres.";

        elements.activeGroup.hidden = true;
        elements.active.value = "true";

        elements.modal.classList.add("open");
        elements.name.focus();
    }

    function openEditModal(user) {
        editingUserId = user.id;
        elements.form.reset();
        setFormMessage("");

        elements.modalTitle.textContent = "Editar usuário";
        elements.saveButton.textContent = "Salvar alterações";

        elements.name.value = user.name || "";
        elements.email.value = user.email || "";
        elements.role.value = user.role_id != null
            ? String(user.role_id)
            : "";

        elements.password.value = "";
        elements.password.required = false;
        elements.passwordHint.textContent =
            "Deixe em branco para manter a senha atual.";

        elements.activeGroup.hidden = false;
        elements.active.value = user.is_active === false
            ? "false"
            : "true";

        elements.modal.classList.add("open");
        elements.name.focus();
    }

    async function saveUser(event) {
        event.preventDefault();

        if (!elements.form.reportValidity()) {
            return;
        }

        const isEditing = editingUserId !== null;
        const password = elements.password.value;

        if (password && (password.length < 6 || password.length > 72)) {
            setFormMessage("A senha deve conter entre 6 e 72 caracteres.");
            return;
        }

        const payload = {
            name: elements.name.value.trim(),
            email: elements.email.value.trim(),
            role_id: Number(elements.role.value)
        };

        if (!payload.name || !payload.email || !payload.role_id) {
            setFormMessage("Preencha todos os campos obrigatórios.");
            return;
        }

        if (password) {
            payload.password = password;
        }

        if (isEditing) {
            payload.is_active = elements.active.value === "true";
        }

        const buttonText = isEditing
            ? "Salvar alterações"
            : "Cadastrar usuário";

        setButtonLoading(elements.saveButton, true, buttonText);
        setFormMessage("");

        try {
            await apiRequest(
                isEditing ? `${API_URL}${editingUserId}` : API_URL,
                {
                    method: isEditing ? "PUT" : "POST",
                    body: JSON.stringify(payload)
                }
            );

            closeUserModal();
            await loadUsers();
        } catch (error) {
            setFormMessage(error.message);
        } finally {
            setButtonLoading(elements.saveButton, false, buttonText);
        }
    }

    // ======================================================
    // MODAL DE EXCLUSÃO
    // ======================================================

    function closeDeleteModal() {
        elements.deleteModal.classList.remove("open");
        deletingUserId = null;
        setDeleteMessage("");
    }

    function openDeleteModal(user) {
        deletingUserId = user.id;
        elements.deleteName.textContent = user.name || user.email;
        setDeleteMessage("");
        elements.deleteModal.classList.add("open");
    }

    async function deleteUser() {
        if (deletingUserId === null) {
            return;
        }

        elements.confirmDeleteButton.disabled = true;
        setDeleteMessage("");

        try {
            await apiRequest(`${API_URL}${deletingUserId}`, {
                method: "DELETE"
            });

            closeDeleteModal();
            await loadUsers();
        } catch (error) {
            setDeleteMessage(error.message);
        } finally {
            elements.confirmDeleteButton.disabled = false;
        }
    }

    // ======================================================
    // EVENTOS
    // ======================================================

    elements.search.addEventListener("input", renderUsers);
    elements.roleFilter.addEventListener("change", renderUsers);

    elements.newButton.addEventListener("click", openNewModal);
    elements.closeButton.addEventListener("click", closeUserModal);
    elements.cancelButton.addEventListener("click", closeUserModal);
    elements.form.addEventListener("submit", saveUser);

    elements.closeDeleteButton.addEventListener("click", closeDeleteModal);
    elements.cancelDeleteButton.addEventListener("click", closeDeleteModal);
    elements.confirmDeleteButton.addEventListener("click", deleteUser);

    elements.modal.addEventListener("click", event => {
        if (event.target === elements.modal) {
            closeUserModal();
        }
    });

    elements.deleteModal.addEventListener("click", event => {
        if (event.target === elements.deleteModal) {
            closeDeleteModal();
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            if (elements.modal.classList.contains("open")) {
                closeUserModal();
            }

            if (elements.deleteModal.classList.contains("open")) {
                closeDeleteModal();
            }
        }
    });

    // ======================================================
    // INICIALIZAÇÃO
    // ======================================================

    elements.newButton.hidden = true;

    const isAdmin = await verifyAdminAccess();

    if (!isAdmin) {
        showMessage(
            "Acesso negado: somente administradores podem gerenciar usuários."
        );
        return;
    }

    elements.newButton.hidden = false;

    try {
        await loadRoles();
        await loadUsers();
    } catch (error) {
        showMessage(error.message);
        console.error("Erro ao inicializar usuários:", error);
    }
});
