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

const currentDate = document.getElementById("currentDate");

if (currentDate) {
    const today = new Date();

    currentDate.textContent = today.toLocaleDateString("pt-BR", {
        day: "2-digit",
        month: "long",
        year: "numeric"
    });
}

// Indicadores do Dashboard

const dashboardToken = localStorage.getItem("access_token");

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
            `Não foi possível carregar os dados de ${endpoint}`
        );
    }

    return response.json();
}

function updateDashboardValue(elementId, value) {
    const element = document.getElementById(elementId);

    if (element) {
        element.textContent = value.toLocaleString("pt-BR");
    }
}

function formatRecentOrderDate(date) {
    if (!date) return "—";

    const dateWithTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(date)
        ? date
        : `${date}Z`;

    return new Date(dateWithTimezone).toLocaleString("pt-BR", {
        timeZone: "America/Recife",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
}

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
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 5);

    if (!recentOrders.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4">Nenhum pedido cadastrado.</td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = recentOrders.map(order => `
        <tr>
            <td data-label="Pedido">#${order.id}</td>
            <td data-label="Tipo">${types[order.type] || order.type}</td>
            <td data-label="Data">${formatRecentOrderDate(order.created_at)}</td>
            <td data-label="Status">
                <span class="recent-status status-${order.status.toLowerCase()}">
                    ${statuses[order.status] || order.status}
                </span>
            </td>
        </tr>
    `).join("");
}

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
                (total, item) => total + Number(item.quantity),
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
    }
];

    const results = await Promise.allSettled(
        endpoints.map(item => fetchDashboardData(item.url))
    );

    results.forEach((result, index) => {
        const item = endpoints[index];
        const element = document.getElementById(item.elementId);

            if (result.status === "fulfilled") {
            updateDashboardValue(
                item.elementId,
                item.calculate(result.value)
            );

            if (item.url === "/orders/") {
            renderOrdersStatusChart(result.value);
            renderRecentOrders(result.value);
        }
        } else {
            console.error(result.reason);

            if (element) {
                element.textContent = "Erro";
            }
        }
    });
}

function renderOrdersStatusChart(orders) {
    const chart = document.getElementById("ordersStatusChart");

    if (!chart) return;

    const statuses = [
        { key: "PENDING", label: "Pendentes", css: "chart-pending" },
        { key: "PROCESSING", label: "Em processamento", css: "chart-processing" },
        { key: "COMPLETED", label: "Concluídos", css: "chart-completed" },
        { key: "CANCELLED", label: "Cancelados", css: "chart-cancelled" }
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

loadDashboard();