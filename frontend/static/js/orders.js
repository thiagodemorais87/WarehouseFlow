const token = localStorage.getItem("access_token");

const ordersTableBody = document.getElementById("ordersTableBody");
const ordersMessage = document.getElementById("ordersMessage");

const orderSearch = document.getElementById("orderSearch");
const orderTypeFilter = document.getElementById("orderTypeFilter");
const orderStatusFilter = document.getElementById("orderStatusFilter");

const newOrderButton = document.getElementById("newOrderButton");

const orderModal = document.getElementById("orderModal");
const closeOrderModal = document.getElementById("closeOrderModal");
const cancelOrderButton = document.getElementById("cancelOrderButton");

const orderForm = document.getElementById("orderForm");
const orderType = document.getElementById("orderType");
const orderItems = document.getElementById("orderItems");
const addOrderItemButton = document.getElementById("addOrderItemButton");
const orderFormMessage = document.getElementById("orderFormMessage");


// ======================================================
// DETALHES DO PEDIDO
// ======================================================

const orderDetailsModal =
    document.getElementById("orderDetailsModal");

const orderDetailsTitle =
    document.getElementById("orderDetailsTitle");

const detailOrderType =
    document.getElementById("detailOrderType");

const detailOrderStatus =
    document.getElementById("detailOrderStatus");

const detailOrderDate =
    document.getElementById("detailOrderDate");

const detailOrderItems =
    document.getElementById("detailOrderItems");

const orderDetailsMessage =
    document.getElementById("orderDetailsMessage");

const closeOrderDetailsModal =
    document.getElementById("closeOrderDetailsModal");

const closeOrderDetailsButton =
    document.getElementById("closeOrderDetailsButton");

const addDetailOrderItemButton =
    document.getElementById("addDetailOrderItemButton");


// ======================================================
// ADICIONAR ITEM A PEDIDO EXISTENTE
// ======================================================

const addOrderItemModal =
    document.getElementById("addOrderItemModal");

const closeAddOrderItemModal =
    document.getElementById("closeAddOrderItemModal");

const cancelAddOrderItemButton =
    document.getElementById("cancelAddOrderItemButton");

const addOrderItemForm =
    document.getElementById("addOrderItemForm");

const detailProductSelect =
    document.getElementById("detailProductSelect");

const detailProductQuantity =
    document.getElementById("detailProductQuantity");

const addOrderItemMessage =
    document.getElementById("addOrderItemMessage");


// ======================================================
// EDITAR ITEM
// ======================================================

const editOrderItemModal =
    document.getElementById("editOrderItemModal");

const closeEditOrderItemModal =
    document.getElementById("closeEditOrderItemModal");

const cancelEditOrderItemButton =
    document.getElementById("cancelEditOrderItemButton");

const editOrderItemForm =
    document.getElementById("editOrderItemForm");

const editOrderItemProduct =
    document.getElementById("editOrderItemProduct");

const editOrderItemQuantity =
    document.getElementById("editOrderItemQuantity");

const editOrderItemMessage =
    document.getElementById("editOrderItemMessage");


// ======================================================
// STATUS DO PEDIDO
// ======================================================

const orderStatusModal =
    document.getElementById("orderStatusModal");

const orderStatusTitle =
    document.getElementById("orderStatusTitle");

const orderStatusForm =
    document.getElementById("orderStatusForm");

const newOrderStatus =
    document.getElementById("newOrderStatus");

const orderStatusMessage =
    document.getElementById("orderStatusMessage");

const closeOrderStatusModal =
    document.getElementById("closeOrderStatusModal");

const cancelOrderStatusButton =
    document.getElementById("cancelOrderStatusButton");


// ======================================================
// ESTADO
// ======================================================

let selectedOrderId = null;
let selectedOrderItemId = null;

let productsData = [];
let ordersData = [];


if (!token) {
    window.location.href = "/login";
}


// ======================================================
// UTILITÁRIOS
// ======================================================

async function getErrorMessage(response, fallback) {
    try {
        const error = await response.json();

        if (typeof error.detail === "string") {
            return error.detail;
        }

        if (Array.isArray(error.detail)) {
            return error.detail
                .map(item => item.msg || "Erro de validação.")
                .join(" ");
        }

        return fallback;
    } catch {
        return fallback;
    }
}


function handleUnauthorized(response) {
    if (response.status !== 401) {
        return false;
    }

    localStorage.removeItem("access_token");
    window.location.href = "/login";

    return true;
}


// ======================================================
// PEDIDOS
// ======================================================

async function loadOrders() {
    ordersMessage.style.display = "block";
    ordersMessage.textContent = "Carregando pedidos...";

    try {
        const response = await fetch("/orders/", {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (handleUnauthorized(response)) {
            return;
        }

        if (!response.ok) {
            throw new Error(
                await getErrorMessage(
                    response,
                    "Não foi possível carregar os pedidos."
                )
            );
        }

        ordersData = await response.json();

        applyFilters();

    } catch (error) {
        ordersTableBody.innerHTML = "";

        ordersMessage.style.display = "block";
        ordersMessage.textContent = error.message;
    }
}


function renderOrders(orders) {
    ordersTableBody.innerHTML = "";

    if (!orders.length) {
        ordersMessage.style.display = "block";
        ordersMessage.textContent = "Nenhum pedido encontrado.";
        return;
    }

    ordersMessage.style.display = "none";

    orders.forEach(order => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td data-label="Pedido">
                #${order.id}
            </td>

            <td data-label="Tipo">
                ${formatOrderType(order.type)}
            </td>

            <td data-label="Itens">
                ${order.items?.length || 0}
            </td>

            <td data-label="Status">
                <span class="order-status ${getStatusClass(order.status)}">
                    ${formatOrderStatus(order.status)}
                </span>
            </td>

            <td data-label="Data">
                ${formatDate(order.created_at)}
            </td>

            <td data-label="Ações">
                <div class="order-actions">

                    <button
                        type="button"
                        class="order-detail-button"
                        data-id="${order.id}"
                    >
                        Detalhes
                    </button>

                    <button
                        type="button"
                        class="order-status-button"
                        data-id="${order.id}"
                    >
                        Status
                    </button>

                </div>
            </td>
        `;

        ordersTableBody.appendChild(row);
    });
}


function applyFilters() {
    const search = orderSearch.value
        .trim()
        .toLowerCase()
        .replace("#", "");

    const type = orderTypeFilter.value;
    const status = orderStatusFilter.value;

    const filteredOrders = ordersData.filter(order => {
        const matchesSearch =
            !search ||
            String(order.id).includes(search);

        const matchesType =
            !type ||
            order.type === type;

        const matchesStatus =
            !status ||
            order.status === status;

        return matchesSearch && matchesType && matchesStatus;
    });

    renderOrders(filteredOrders);
}


// ======================================================
// FORMATAÇÃO
// ======================================================

function formatOrderType(type) {
    const types = {
        INBOUND: "Recebimento",
        OUTBOUND: "Expedição"
    };

    return types[type] || type;
}


function formatOrderStatus(status) {
    const statuses = {
        PENDING: "Pendente",
        PROCESSING: "Em processamento",
        COMPLETED: "Concluído",
        CANCELLED: "Cancelado"
    };

    return statuses[status] || status;
}


function getStatusClass(status) {
    const classes = {
        PENDING: "status-pending",
        PROCESSING: "status-processing",
        COMPLETED: "status-completed",
        CANCELLED: "status-cancelled"
    };

    return classes[status] || "";
}


function formatDate(date) {
    if (!date) {
        return "—";
    }

    const dateWithTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(date)
        ? date
        : `${date}Z`;

    return new Date(dateWithTimezone).toLocaleString("pt-BR", {
        timeZone: "America/Recife",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
    });
}


// ======================================================
// PRODUTOS
// ======================================================

async function loadProducts() {
    const response = await fetch("/products/", {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (handleUnauthorized(response)) {
        throw new Error("Sessão expirada.");
    }

    if (!response.ok) {
        throw new Error(
            await getErrorMessage(
                response,
                "Não foi possível carregar os produtos."
            )
        );
    }

    productsData = await response.json();
}


function getProduct(productId) {
    return productsData.find(
        product => Number(product.id) === Number(productId)
    );
}


// ======================================================
// CRIAÇÃO DO PEDIDO
// ======================================================

function addOrderItem() {
    const item = document.createElement("div");

    item.className = "order-item-row";

    const options = productsData
        .map(product => `
            <option value="${product.id}">
                ${product.sku} - ${product.name}
            </option>
        `)
        .join("");

    item.innerHTML = `
        <div class="form-group">
            <label>Produto *</label>

            <select class="order-item-product" required>
                <option value="">Selecione um produto</option>
                ${options}
            </select>
        </div>

        <div class="form-group quantity-group">
            <label>Quantidade *</label>

            <input
                type="number"
                class="order-item-quantity"
                min="1"
                step="1"
                value="1"
                required
            >
        </div>

        <button
            type="button"
            class="remove-order-item"
            aria-label="Remover item"
        >
            Remover
        </button>
    `;

    orderItems.appendChild(item);
}


async function openOrderModal() {
    orderForm.reset();
    orderItems.innerHTML = "";

    orderFormMessage.textContent = "";
    orderFormMessage.className = "form-message";

    try {
        if (!productsData.length) {
            await loadProducts();
        }

        if (!productsData.length) {
            throw new Error(
                "Nenhum produto cadastrado. Cadastre um produto antes de criar um pedido."
            );
        }

        addOrderItem();

        orderModal.classList.add("open");

    } catch (error) {
        alert(error.message);
    }
}


function closeOrderForm() {
    orderModal.classList.remove("open");

    orderForm.reset();
    orderItems.innerHTML = "";

    orderFormMessage.textContent = "";
    orderFormMessage.className = "form-message";
}


newOrderButton.addEventListener("click", openOrderModal);

closeOrderModal.addEventListener("click", closeOrderForm);
cancelOrderButton.addEventListener("click", closeOrderForm);

addOrderItemButton.addEventListener("click", addOrderItem);


orderModal.addEventListener("click", function (event) {
    if (event.target === orderModal) {
        closeOrderForm();
    }
});


orderItems.addEventListener("click", function (event) {
    const removeButton =
        event.target.closest(".remove-order-item");

    if (!removeButton) {
        return;
    }

    const rows =
        orderItems.querySelectorAll(".order-item-row");

    if (rows.length === 1) {
        orderFormMessage.textContent =
            "O pedido deve possuir pelo menos um item.";

        orderFormMessage.className =
            "form-message error";

        return;
    }

    removeButton
        .closest(".order-item-row")
        .remove();
});


orderForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    orderFormMessage.textContent = "";
    orderFormMessage.className = "form-message";

    const type = orderType.value;

    const rows = [
        ...orderItems.querySelectorAll(".order-item-row")
    ];

    if (!type) {
        orderFormMessage.textContent =
            "Selecione o tipo do pedido.";

        orderFormMessage.className =
            "form-message error";

        return;
    }

    if (!rows.length) {
        orderFormMessage.textContent =
            "Adicione pelo menos um item ao pedido.";

        orderFormMessage.className =
            "form-message error";

        return;
    }

    const items = [];

    for (const row of rows) {
        const productId = Number(
            row.querySelector(".order-item-product").value
        );

        const quantity = Number(
            row.querySelector(".order-item-quantity").value
        );

        if (!productId) {
            orderFormMessage.textContent =
                "Selecione o produto de todos os itens.";

            orderFormMessage.className =
                "form-message error";

            return;
        }

        if (!Number.isInteger(quantity) || quantity <= 0) {
            orderFormMessage.textContent =
                "As quantidades devem ser números inteiros maiores que zero.";

            orderFormMessage.className =
                "form-message error";

            return;
        }

        items.push({
            product_id: productId,
            quantity: quantity
        });
    }

    try {
        const response = await fetch("/orders/", {
            method: "POST",

            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },

            body: JSON.stringify({
                type: type,
                status: "PENDING",
                items: items
            })
        });

        if (handleUnauthorized(response)) {
            return;
        }

        if (!response.ok) {
            throw new Error(
                await getErrorMessage(
                    response,
                    "Não foi possível criar o pedido."
                )
            );
        }

        closeOrderForm();

        await loadOrders();

    } catch (error) {
        orderFormMessage.textContent = error.message;
        orderFormMessage.className = "form-message error";
    }
});


// ======================================================
// DETALHES DO PEDIDO
// ======================================================

async function openOrderDetails(orderId) {
    selectedOrderId = Number(orderId);

    orderDetailsMessage.textContent = "";
    orderDetailsMessage.className = "form-message";

    detailOrderItems.innerHTML = "";

    try {
        const response = await fetch(
            `/orders/${selectedOrderId}`,
            {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        if (handleUnauthorized(response)) {
            return;
        }

        if (!response.ok) {
            throw new Error(
                await getErrorMessage(
                    response,
                    "Não foi possível carregar o pedido."
                )
            );
        }

        const order = await response.json();

        if (!productsData.length) {
            await loadProducts();
        }

        orderDetailsTitle.textContent =
            `Pedido #${order.id}`;

        detailOrderType.textContent =
            formatOrderType(order.type);

        detailOrderStatus.innerHTML = `
            <span class="order-status ${getStatusClass(order.status)}">
                ${formatOrderStatus(order.status)}
            </span>
        `;

        detailOrderDate.textContent =
            formatDate(order.created_at);

        renderOrderDetailItems(order.items || []);

        orderDetailsModal.classList.add("open");

    } catch (error) {
        selectedOrderId = null;
        alert(error.message);
    }
}


function renderOrderDetailItems(items) {
    detailOrderItems.innerHTML = "";

    if (!items.length) {
        detailOrderItems.innerHTML = `
            <div class="order-detail-empty">
                Nenhum item vinculado a este pedido.
            </div>
        `;

        return;
    }

    items.forEach(item => {
        const product = getProduct(item.product_id);

        const element = document.createElement("div");

        element.className = "order-detail-item";

        element.innerHTML = `
            <div class="order-detail-product">
                <strong>
                    ${product ? product.name : `Produto #${item.product_id}`}
                </strong>

                <span>
                    ${product ? product.sku : `ID ${item.product_id}`}
                </span>
            </div>

            <div class="order-detail-quantity">
                <span>Quantidade</span>
                <strong>${item.quantity}</strong>
            </div>

            <div class="order-detail-item-actions">

                <button
                    type="button"
                    class="edit-detail-item"
                    data-item-id="${item.id}"
                    data-product-id="${item.product_id}"
                    data-quantity="${item.quantity}"
                >
                    Editar
                </button>

                <button
                    type="button"
                    class="delete-detail-item"
                    data-item-id="${item.id}"
                >
                    Remover
                </button>

            </div>
        `;

        detailOrderItems.appendChild(element);
    });
}


function closeOrderDetails() {
    orderDetailsModal.classList.remove("open");

    selectedOrderId = null;
    selectedOrderItemId = null;

    orderDetailsMessage.textContent = "";
    orderDetailsMessage.className = "form-message";
}


closeOrderDetailsModal.addEventListener(
    "click",
    closeOrderDetails
);

closeOrderDetailsButton.addEventListener(
    "click",
    closeOrderDetails
);


orderDetailsModal.addEventListener("click", function (event) {
    if (event.target === orderDetailsModal) {
        closeOrderDetails();
    }
});


// ======================================================
// ADICIONAR PRODUTO A PEDIDO EXISTENTE
// ======================================================

async function openAddOrderItemModal() {
    if (!selectedOrderId) {
        return;
    }

    addOrderItemForm.reset();

    detailProductQuantity.value = 1;

    addOrderItemMessage.textContent = "";
    addOrderItemMessage.className = "form-message";

    try {
        if (!productsData.length) {
            await loadProducts();
        }

        if (!productsData.length) {
            throw new Error(
                "Nenhum produto cadastrado."
            );
        }

        detailProductSelect.innerHTML = `
            <option value="">
                Selecione um produto
            </option>

            ${productsData.map(product => `
                <option value="${product.id}">
                    ${product.sku} - ${product.name}
                </option>
            `).join("")}
        `;

        addOrderItemModal.classList.add("open");

    } catch (error) {
        orderDetailsMessage.textContent =
            error.message;

        orderDetailsMessage.className =
            "form-message error";
    }
}


function closeAddItemModal() {
    addOrderItemModal.classList.remove("open");

    addOrderItemForm.reset();

    addOrderItemMessage.textContent = "";
    addOrderItemMessage.className = "form-message";
}


addDetailOrderItemButton.addEventListener(
    "click",
    openAddOrderItemModal
);

closeAddOrderItemModal.addEventListener(
    "click",
    closeAddItemModal
);

cancelAddOrderItemButton.addEventListener(
    "click",
    closeAddItemModal
);


addOrderItemModal.addEventListener(
    "click",
    function (event) {
        if (event.target === addOrderItemModal) {
            closeAddItemModal();
        }
    }
);


addOrderItemForm.addEventListener(
    "submit",
    async function (event) {
        event.preventDefault();

        addOrderItemMessage.textContent = "";
        addOrderItemMessage.className = "form-message";

        if (!selectedOrderId) {
            return;
        }

        const productId =
            Number(detailProductSelect.value);

        const quantity =
            Number(detailProductQuantity.value);

        if (!productId) {
            addOrderItemMessage.textContent =
                "Selecione um produto.";

            addOrderItemMessage.className =
                "form-message error";

            return;
        }

        if (!Number.isInteger(quantity) || quantity <= 0) {
            addOrderItemMessage.textContent =
                "A quantidade deve ser um número inteiro maior que zero.";

            addOrderItemMessage.className =
                "form-message error";

            return;
        }

        try {
            const response = await fetch(
                `/orders/${selectedOrderId}/items`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },

                    body: JSON.stringify({
                        product_id: productId,
                        quantity: quantity
                    })
                }
            );

            if (handleUnauthorized(response)) {
                return;
            }

            if (!response.ok) {
                throw new Error(
                    await getErrorMessage(
                        response,
                        "Não foi possível adicionar o produto."
                    )
                );
            }

            closeAddItemModal();

            await openOrderDetails(selectedOrderId);
            await loadOrders();

        } catch (error) {
            addOrderItemMessage.textContent =
                error.message;

            addOrderItemMessage.className =
                "form-message error";
        }
    }
);


// ======================================================
// EDITAR ITEM
// ======================================================

function openEditOrderItem(button) {
    if (!selectedOrderId) {
        return;
    }

    selectedOrderItemId =
        Number(button.dataset.itemId);

    const productId =
        Number(button.dataset.productId);

    const quantity =
        Number(button.dataset.quantity);

    const product = getProduct(productId);

    editOrderItemProduct.textContent =
        product
            ? `${product.sku} - ${product.name}`
            : `Produto #${productId}`;

    editOrderItemQuantity.value = quantity;

    editOrderItemMessage.textContent = "";
    editOrderItemMessage.className = "form-message";

    editOrderItemModal.classList.add("open");
}


function closeEditItemModal() {
    editOrderItemModal.classList.remove("open");

    selectedOrderItemId = null;

    editOrderItemForm.reset();

    editOrderItemMessage.textContent = "";
    editOrderItemMessage.className = "form-message";
}


closeEditOrderItemModal.addEventListener(
    "click",
    closeEditItemModal
);

cancelEditOrderItemButton.addEventListener(
    "click",
    closeEditItemModal
);


editOrderItemModal.addEventListener(
    "click",
    function (event) {
        if (event.target === editOrderItemModal) {
            closeEditItemModal();
        }
    }
);


editOrderItemForm.addEventListener(
    "submit",
    async function (event) {
        event.preventDefault();

        editOrderItemMessage.textContent = "";
        editOrderItemMessage.className = "form-message";

        if (!selectedOrderId || !selectedOrderItemId) {
            return;
        }

        const quantity =
            Number(editOrderItemQuantity.value);

        if (!Number.isInteger(quantity) || quantity <= 0) {
            editOrderItemMessage.textContent =
                "A quantidade deve ser um número inteiro maior que zero.";

            editOrderItemMessage.className =
                "form-message error";

            return;
        }

        try {
            const orderId = selectedOrderId;

            const response = await fetch(
                `/orders/${orderId}/items/${selectedOrderItemId}`,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },

                    body: JSON.stringify({
                        quantity: quantity
                    })
                }
            );

            if (handleUnauthorized(response)) {
                return;
            }

            if (!response.ok) {
                throw new Error(
                    await getErrorMessage(
                        response,
                        "Não foi possível atualizar o item."
                    )
                );
            }

            closeEditItemModal();

            await openOrderDetails(orderId);
            await loadOrders();

        } catch (error) {
            editOrderItemMessage.textContent =
                error.message;

            editOrderItemMessage.className =
                "form-message error";
        }
    }
);


// ======================================================
// REMOVER ITEM
// ======================================================

async function deleteOrderItem(itemId) {
    if (!selectedOrderId) {
        return;
    }

    const confirmed = window.confirm(
        "Deseja realmente remover este produto do pedido?"
    );

    if (!confirmed) {
        return;
    }

    orderDetailsMessage.textContent = "";
    orderDetailsMessage.className = "form-message";

    try {
        const orderId = selectedOrderId;

        const response = await fetch(
            `/orders/${orderId}/items/${itemId}`,
            {
                method: "DELETE",

                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        if (handleUnauthorized(response)) {
            return;
        }

        if (!response.ok) {
            throw new Error(
                await getErrorMessage(
                    response,
                    "Não foi possível remover o item."
                )
            );
        }

        await openOrderDetails(orderId);
        await loadOrders();

    } catch (error) {
        orderDetailsMessage.textContent =
            error.message;

        orderDetailsMessage.className =
            "form-message error";
    }
}


// ======================================================
// AÇÕES DOS ITENS NOS DETALHES
// ======================================================

detailOrderItems.addEventListener(
    "click",
    function (event) {
        const editButton =
            event.target.closest(".edit-detail-item");

        if (editButton) {
            openEditOrderItem(editButton);
            return;
        }

        const deleteButton =
            event.target.closest(".delete-detail-item");

        if (deleteButton) {
            deleteOrderItem(
                Number(deleteButton.dataset.itemId)
            );
        }
    }
);


// ======================================================
// AÇÕES DA TABELA DE PEDIDOS
// ======================================================

ordersTableBody.addEventListener(
    "click",
    function (event) {
        const detailButton =
            event.target.closest(".order-detail-button");

        if (detailButton) {
            openOrderDetails(
                detailButton.dataset.id
            );

            return;
        }

        const statusButton =
            event.target.closest(".order-status-button");

        if (statusButton) {
            openOrderStatus(
                statusButton.dataset.id
            );
        }
    }
);


// ======================================================
// STATUS
// ======================================================

function openOrderStatus(orderId) {
    const order = ordersData.find(
        order => Number(order.id) === Number(orderId)
    );

    if (!order) {
        return;
    }

    selectedOrderId = order.id;

    orderStatusTitle.textContent =
        `Alterar status — Pedido #${order.id}`;

    newOrderStatus.value = order.status;

    orderStatusMessage.textContent = "";
    orderStatusMessage.className = "form-message";

    orderStatusModal.classList.add("open");
}


function closeOrderStatus() {
    orderStatusModal.classList.remove("open");

    selectedOrderId = null;

    orderStatusMessage.textContent = "";
    orderStatusMessage.className = "form-message";
}


orderStatusForm.addEventListener(
    "submit",
    async function (event) {
        event.preventDefault();

        orderStatusMessage.textContent = "";
        orderStatusMessage.className = "form-message";

        if (!selectedOrderId) {
            return;
        }

        try {
            const response = await fetch(
                `/orders/${selectedOrderId}`,
                {
                    method: "PUT",

                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },

                    body: JSON.stringify({
                        status: newOrderStatus.value
                    })
                }
            );

            if (handleUnauthorized(response)) {
                return;
            }

            if (!response.ok) {
                throw new Error(
                    await getErrorMessage(
                        response,
                        "Não foi possível alterar o status do pedido."
                    )
                );
            }

            closeOrderStatus();

            await loadOrders();

        } catch (error) {
            orderStatusMessage.textContent =
                error.message;

            orderStatusMessage.className =
                "form-message error";
        }
    }
);


closeOrderStatusModal.addEventListener(
    "click",
    closeOrderStatus
);

cancelOrderStatusButton.addEventListener(
    "click",
    closeOrderStatus
);


orderStatusModal.addEventListener(
    "click",
    function (event) {
        if (event.target === orderStatusModal) {
            closeOrderStatus();
        }
    }
);


// ======================================================
// FILTROS
// ======================================================

orderSearch.addEventListener(
    "input",
    applyFilters
);

orderTypeFilter.addEventListener(
    "change",
    applyFilters
);

orderStatusFilter.addEventListener(
    "change",
    applyFilters
);


// ======================================================
// INICIALIZAÇÃO
// ======================================================

loadOrders();