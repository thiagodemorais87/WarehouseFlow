
// ======================================================
// MENU DO USUÁRIO
// ======================================================

const userMenuButton = document.getElementById("userMenuButton");
const userDropdown = document.getElementById("userDropdown");

if (userMenuButton && userDropdown) {
    userMenuButton.addEventListener("click", function (event) {
        event.stopPropagation();
        userDropdown.classList.toggle("open");
    });

    document.addEventListener("click", function () {
        userDropdown.classList.remove("open");
    });

    userDropdown.addEventListener("click", function (event) {
        event.stopPropagation();
    });
}


// ======================================================
// DATA ATUAL
// ======================================================

const currentDate = document.getElementById("currentDate");

if (currentDate) {
    const today = new Date();

    currentDate.textContent = today.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "long",
        year: "numeric"
    });
}


// ======================================================
// CONFIGURAÇÕES DO DASHBOARD
// ======================================================

// Limite provisório definido para a Sprint 07.
// Um produto com saldo inferior a 15 unidades
// será considerado com estoque baixo.
const LOW_STOCK_THRESHOLD = 15;

const dashboardToken = localStorage.getItem("access_token");


// ======================================================
// REQUISIÇÕES À API
// ======================================================

async function fetchDashboardData(endpoint) {
    const response = await fetch(endpoint, {
        headers: {
            Authorization: `Bearer ${dashboardToken}`
        }
    });

    if (response.status === 401) {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
        throw new Error("Sessão expirada.");
    }

    if (!response.ok) {
        throw new Error(
            `Não foi possível carregar os dados de ${endpoint} (${response.status}).`
        );
    }

    return response.json();
}


// ======================================================
// ATUALIZAÇÃO DOS INDICADORES
// ======================================================

function updateDashboardValue(elementId, value) {
    const element = document.getElementById(elementId);

    if (!element) return;

    element.textContent = typeof value === "number"
        ? value.toLocaleString("pt-BR")
        : String(value);
}

function showDashboardValueError(elementId) {
    const element = document.getElementById(elementId);

    if (element) {
        element.textContent = "Erro";
    }
}

function formatPercentage(value) {
    const number = Number(value);

    if (value === null ||
        value === undefined ||
        !Number.isFinite(number)) {
        throw new Error("Percentual de redução inválido.");
    }

    return `${number.toLocaleString("pt-BR", {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    })}%`;
}


// ======================================================
// INDICADOR DE ESTOQUE BAIXO - SPRINT 07
// ======================================================

function calculateLowStockProducts(products, stock) {
    if (!Array.isArray(products) || !Array.isArray(stock)) {
        throw new Error("Dados de produtos ou estoque inválidos.");
    }

    // Acumula o saldo de cada produto em todas as posições.
    const stockByProduct = new Map();

    stock.forEach(item => {
        const productId = String(item.product_id);
        const quantity = Number(item.quantity) || 0;

        const currentQuantity =
            stockByProduct.get(productId) || 0;

        stockByProduct.set(
            productId,
            currentQuantity + quantity
        );
    });

    // Percorre todos os produtos cadastrados.
    // Produtos sem registros de estoque possuem saldo zero.
    return products.filter(product => {
        const productId = String(product.id);

        const totalQuantity =
            stockByProduct.get(productId) || 0;

        return totalQuantity < LOW_STOCK_THRESHOLD;
    }).length;
}


// ======================================================
// FORMATAÇÃO DE DATAS
// ======================================================

function formatRecentOrderDate(date) {
    if (!date) return "—";

    const dateWithTimezone =
        /(?:Z|[+-]\d{2}:\d{2})$/i.test(date)
            ? date
            : `${date}Z`;

    const parsedDate = new Date(dateWithTimezone);

    if (Number.isNaN(parsedDate.getTime())) {
        return "—";
    }

    return parsedDate.toLocaleString("pt-BR", {
        timeZone: "America/Recife",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
}


// ======================================================
// PEDIDOS RECENTES
// ======================================================

function renderRecentOrders(orders) {
    const tbody = document.getElementById("recentOrdersBody");

    if (!tbody) return;

    const types = {
        INBOUND: "Recebimento",
        OUTBOUND: "Expedição"
    };

    const statuses = {
        PENDING: "Pendente",
        PROCESSING: "Em processamento",
        COMPLETED: "Concluído",
        CANCELLED: "Cancelado"
    };

    const recentOrders = [...orders]
        .sort(
            (a, b) =>
                new Date(b.created_at) -
                new Date(a.created_at)
        )
        .slice(0, 5);

    if (!recentOrders.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4">
                    Nenhum pedido cadastrado.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = "";

    recentOrders.forEach(order => {
        const row = document.createElement("tr");

        const idCell = document.createElement("td");
        idCell.dataset.label = "Pedido";
        idCell.textContent = `#${order.id}`;

        const typeCell = document.createElement("td");
        typeCell.dataset.label = "Tipo";
        typeCell.textContent =
            types[order.type] || order.type || "—";

        const dateCell = document.createElement("td");
        dateCell.dataset.label = "Data";
        dateCell.textContent =
            formatRecentOrderDate(order.created_at);

        const statusCell = document.createElement("td");
        statusCell.dataset.label = "Status";

        const statusBadge = document.createElement("span");

        const knownStatuses = Object.keys(statuses);

        const safeStatus = knownStatuses.includes(order.status)
            ? order.status.toLowerCase()
            : "unknown";

        statusBadge.className =
            `recent-status status-${safeStatus}`;

        statusBadge.textContent =
            statuses[order.status] ||
            order.status ||
            "—";

        statusCell.appendChild(statusBadge);

        row.append(
            idCell,
            typeCell,
            dateCell,
            statusCell
        );

        tbody.appendChild(row);
    });
}


// ======================================================
// GRÁFICO DE PEDIDOS POR STATUS
// ======================================================

function renderOrdersStatusChart(orders) {
    const chart = document.getElementById("ordersStatusChart");

    if (!chart) return;

    const statuses = [
        {
            key: "PENDING",
            label: "Pendentes",
            css: "chart-pending"
        },
        {
            key: "PROCESSING",
            label: "Em processamento",
            css: "chart-processing"
        },
        {
            key: "COMPLETED",
            label: "Concluídos",
            css: "chart-completed"
        },
        {
            key: "CANCELLED",
            label: "Cancelados",
            css: "chart-cancelled"
        }
    ];

    const total = orders.length;

    chart.innerHTML = statuses.map(status => {
        const count = orders.filter(
            order => order.status === status.key
        ).length;

        const percentage = total > 0
            ? (count / total) * 100
            : 0;

        return `
            <div class="chart-item">
                <div class="chart-label">
                    <span>${status.label}</span>
                    <strong>${count}</strong>
                </div>

                <div class="chart-track">
                    <div
                        class="chart-bar ${status.css}"
                        style="width: ${percentage}%"
                    ></div>
                </div>
            </div>
        `;
    }).join("");
}


// ======================================================
// MENSAGENS DE ERRO DOS PEDIDOS
// ======================================================

function showOrdersError() {
    const chart = document.getElementById("ordersStatusChart");
    const tbody = document.getElementById("recentOrdersBody");

    if (chart) {
        chart.textContent =
            "Não foi possível carregar o gráfico de pedidos.";
    }

    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4">
                    Não foi possível carregar os pedidos recentes.
                </td>
            </tr>
        `;
    }
}


// ======================================================
// CARREGAMENTO PRINCIPAL DO DASHBOARD
// ======================================================

async function loadDashboard() {

    const endpoints = [
        {
            url: "/products/",
            elementId: "totalProducts",
            calculate: products => products.length
        },
        {
            url: "/stock/",
            elementId: "totalStock",
            calculate: stock =>
                stock.reduce(
                    (total, item) =>
                        total + Number(item.quantity || 0),
                    0
                )
        },
        {
            url: "/orders/",
            elementId: "pendingOrders",
            calculate: orders =>
                orders.filter(
                    order => order.status === "PENDING"
                ).length
        },
        {
            url: "/tasks/",
            elementId: "activeTasks",
            calculate: tasks =>
                tasks.filter(
                    task => task.status === "IN_PROGRESS"
                ).length
        },
        {
            url: "/optimization/reports/summary",
            elementId: "averageRouteReduction",
            calculate: summary =>
                formatPercentage(
                    summary.average_reduction_percent
                )
        }
    ];

    // Consulta cada endpoint apenas uma vez.
    const results = await Promise.allSettled(
        endpoints.map(
            item => fetchDashboardData(item.url)
        )
    );

    // Guarda os dados de produtos e estoque
    // para calcular o indicador adicional.
    let productsData = null;
    let stockData = null;

    results.forEach((result, index) => {
        const item = endpoints[index];

        if (result.status === "fulfilled") {
            try {
                const data = result.value;

                // Os quatro endpoints de listagem
                // devem retornar arrays.
                if (
                    item.url !== "/optimization/reports/summary" &&
                    !Array.isArray(data)
                ) {
                    throw new Error(
                        `Formato inesperado na resposta de ${item.url}`
                    );
                }

                const calculatedValue = item.calculate(data);

                updateDashboardValue(
                    item.elementId,
                    calculatedValue
                );

                if (item.url === "/products/") {
                    productsData = data;
                }

                if (item.url === "/stock/") {
                    stockData = data;
                }

                if (item.url === "/orders/") {
                    renderOrdersStatusChart(data);
                    renderRecentOrders(data);
                }

            } catch (error) {
                console.error(error);
                showDashboardValueError(item.elementId);

                if (item.url === "/orders/") {
                    showOrdersError();
                }
            }

        } else {
            console.error(result.reason);
            showDashboardValueError(item.elementId);

            if (item.url === "/orders/") {
                showOrdersError();
            }
        }
    });

    // ==================================================
    // CÁLCULO DO ESTOQUE BAIXO
    // ==================================================

    if (productsData !== null && stockData !== null) {
        try {
            const lowStockCount = calculateLowStockProducts(
                productsData,
                stockData
            );

            updateDashboardValue(
                "lowStockProducts",
                lowStockCount
            );

        } catch (error) {
            console.error(
                "Erro ao calcular produtos com estoque baixo:",
                error
            );

            showDashboardValueError("lowStockProducts");
        }

    } else {
        showDashboardValueError("lowStockProducts");
    }
}


// ======================================================
// INICIALIZAÇÃO
// ======================================================

loadDashboard();
