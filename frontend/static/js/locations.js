const token = localStorage.getItem("access_token");

const locationsTableBody = document.getElementById("locationsTableBody");
const locationSearch = document.getElementById("locationSearch");
const warehouseFilter = document.getElementById("warehouseFilter");
const locationMessage = document.getElementById("locationMessage");

const locationModal = document.getElementById("locationModal");
const locationForm = document.getElementById("locationForm");
const locationModalTitle = document.getElementById("locationModalTitle");

const newLocationBtn = document.getElementById("newLocationBtn");
const closeLocationModal = document.getElementById("closeLocationModal");
const cancelLocationBtn = document.getElementById("cancelLocationBtn");

const locationWarehouse = document.getElementById("locationWarehouse");
const locationCode = document.getElementById("locationCode");
const locationAisle = document.getElementById("locationAisle");
const locationRack = document.getElementById("locationRack");
const locationShelf = document.getElementById("locationShelf");
const locationActive = document.getElementById("locationActive");

let locations = [];
let warehouses = [];
let editingLocationId = null;

function authHeaders() {
    return {
        "Authorization": `Bearer ${token}`
    };
}

async function loadWarehouses() {
    try {
        const response = await fetch("/locations/warehouses/", {
            headers: authHeaders()
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || "Erro ao carregar armazéns.");
        }

        warehouses = await response.json();

        warehouseFilter.innerHTML =
            '<option value="">Todos os armazéns</option>';

        locationWarehouse.innerHTML =
            '<option value="">Selecione um armazém</option>';

        warehouses.forEach(warehouse => {
            warehouseFilter.innerHTML += `
                <option value="${warehouse.id}">
                    ${warehouse.name}
                </option>
            `;

            locationWarehouse.innerHTML += `
                <option value="${warehouse.id}">
                    ${warehouse.name}
                </option>
            `;
        });

    } catch (error) {
        showMessage(error.message, "error");
    }
}

async function loadLocations() {
    try {
        const response = await fetch("/locations/", {
            headers: authHeaders()
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || "Erro ao carregar posições.");
        }

        locations = await response.json();
        renderLocations();

    } catch (error) {
        locationsTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-table">
                    ${error.message}
                </td>
            </tr>
        `;
    }
}

function renderLocations() {
    const search = locationSearch.value.trim().toLowerCase();
    const selectedWarehouse = warehouseFilter.value;

    const filteredLocations = locations.filter(location => {
        const warehouse = warehouses.find(
            item => item.id === location.warehouse_id
        );

        const warehouseName = warehouse ? warehouse.name : "";

        const matchesSearch =
            location.code.toLowerCase().includes(search) ||
            (location.aisle || "").toLowerCase().includes(search) ||
            (location.rack || "").toLowerCase().includes(search) ||
            (location.shelf || "").toLowerCase().includes(search) ||
            warehouseName.toLowerCase().includes(search);

        const matchesWarehouse =
            !selectedWarehouse ||
            String(location.warehouse_id) === selectedWarehouse;

        return matchesSearch && matchesWarehouse;
    });

    if (filteredLocations.length === 0) {
        locationsTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-table">
                    Nenhuma posição encontrada.
                </td>
            </tr>
        `;
        return;
    }

    locationsTableBody.innerHTML = filteredLocations.map(location => {
        const warehouse = warehouses.find(
            item => item.id === location.warehouse_id
        );

        return `
            <tr>
                <td>${location.code}</td>
                <td>${warehouse ? warehouse.name : "-"}</td>
                <td>${location.aisle || "-"}</td>
                <td>${location.rack || "-"}</td>
                <td>${location.shelf || "-"}</td>

                <td>
                    <span class="${location.is_active ? "status-active" : "status-inactive"}">
                        ${location.is_active ? "Ativa" : "Inativa"}
                    </span>
                </td>

                <td>
                    <div class="location-actions">
                        <button
                            class="btn-edit"
                            data-id="${location.id}">
                            Editar
                        </button>

                        <button
                            class="btn-delete"
                            data-id="${location.id}">
                            Excluir
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

function openNewLocationModal() {
    editingLocationId = null;

    locationForm.reset();

    locationModalTitle.textContent = "Nova posição";
    locationWarehouse.disabled = false;
    locationActive.checked = true;

    const formMessage = document.getElementById("locationFormMessage");
    formMessage.textContent = "";
    formMessage.className = "location-message";

    locationModal.classList.add("show");
}

function openEditLocationModal(id) {
    const location = locations.find(item => item.id === id);

    if (!location) {
        showMessage("Posição não encontrada.", "error");
        return;
    }

    editingLocationId = id;

    locationModalTitle.textContent = "Editar posição";

    locationWarehouse.value = location.warehouse_id;
    locationWarehouse.disabled = true;

    locationCode.value = location.code;
    locationAisle.value = location.aisle || "";
    locationRack.value = location.rack || "";
    locationShelf.value = location.shelf || "";
    locationActive.checked = location.is_active;

    const formMessage = document.getElementById("locationFormMessage");
    formMessage.textContent = "";
    formMessage.className = "location-message";

    locationModal.classList.add("show");
}

async function deleteLocation(id) {
    const location = locations.find(item => item.id === id);

    if (!location) {
        showMessage("Posição não encontrada.", "error");
        return;
    }

    const confirmed = confirm(
        `Deseja realmente excluir a posição ${location.code}?`
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`/locations/${id}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const data = await response.json().catch(() => ({}));

            throw new Error(
                data.detail || "Não foi possível excluir a posição."
            );
        }

        showMessage(
            "Posição excluída com sucesso.",
            "success"
        );

        await loadLocations();

    } catch (error) {
        showMessage(error.message, "error");
    }
}

function closeModal() {
    locationModal.classList.remove("show");
}

locationForm.addEventListener("submit", async event => {
    event.preventDefault();

    const formMessage = document.getElementById("locationFormMessage");

    formMessage.textContent = "";
    formMessage.className = "location-message";

    if (!locationWarehouse.value) {
        formMessage.textContent = "Selecione um armazém.";
        formMessage.classList.add("error");
        return;
    }

    if (!locationCode.value.trim()) {
        formMessage.textContent = "Informe o código da posição.";
        formMessage.classList.add("error");
        return;
    }

    const location = {
    code: locationCode.value.trim(),
    aisle: locationAisle.value.trim() || null,
    rack: locationRack.value.trim() || null,
    shelf: locationShelf.value.trim() || null,
    is_active: locationActive.checked
};

if (!editingLocationId) {
    location.warehouse_id = Number(locationWarehouse.value);
}

const isEditing = editingLocationId !== null;

const url = isEditing
    ? `/locations/${editingLocationId}`
    : "/locations/";

const method = isEditing ? "PUT" : "POST";

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(location)
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(
                data.detail || "Não foi possível cadastrar a posição."
            );
        }

        closeModal();

        showMessage(
            isEditing
        ? "Posição atualizada com sucesso."
        : "Posição cadastrada com sucesso.",
    "success"
);

        await loadLocations();

    } catch (error) {
        formMessage.textContent = error.message;
        formMessage.classList.add("error");
    }
});

function showMessage(message, type) {
    locationMessage.textContent = message;
    locationMessage.className = `location-message ${type}`;
}

newLocationBtn.addEventListener("click", openNewLocationModal);

closeLocationModal.addEventListener("click", closeModal);
cancelLocationBtn.addEventListener("click", closeModal);

locationModal.addEventListener("click", event => {
    if (event.target === locationModal) {
        closeModal();
    }
});

locationSearch.addEventListener("input", renderLocations);
warehouseFilter.addEventListener("change", renderLocations);

locationsTableBody.addEventListener("click", event => {
    const editButton = event.target.closest(".btn-edit");
    const deleteButton = event.target.closest(".btn-delete");

    if (editButton) {
        const id = Number(editButton.dataset.id);
        openEditLocationModal(id);
        return;
    }

    if (deleteButton) {
        const id = Number(deleteButton.dataset.id);
        deleteLocation(id);
    }
});

async function initializePage() {
    await loadWarehouses();
    await loadLocations();
}

initializePage();