
(() => {
    "use strict";

    const $ = id => document.getElementById(id);

    const managementTab = $("ordersManagementTab");
    const reportTab = $("ordersReportTab");
    const managementPanel = $("ordersManagementPanel");
    const reportPanel = $("ordersReportPanel");

    if (!managementTab || !reportTab ||
        !managementPanel || !reportPanel) return;

    const PAGE_SIZE = 20;
    let currentPage = 1;
    let totalRecords = 0;
    let loadedOnce = false;
    let loading = false;
    let currentController = null;
    let filters = {};

    const fmt = new Intl.NumberFormat("pt-BR");

    // ==========================================
    // ABAS
    // ==========================================

    function setTab(report) {
        managementPanel.hidden = report;
        reportPanel.hidden = !report;

        managementTab.classList.toggle("active", !report);
        reportTab.classList.toggle("active", report);

        managementTab.setAttribute(
            "aria-selected", String(!report)
        );

        reportTab.setAttribute(
            "aria-selected", String(report)
        );

        if (report && !loadedOnce) {
            loadReport();
        }
    }

    managementTab.addEventListener(
        "click", () => setTab(false)
    );

    reportTab.addEventListener(
        "click", () => setTab(true)
    );

    setTab(false);

    // ==========================================
    // AUTENTICAÇÃO
    // ==========================================

    function getToken() {
        return localStorage.getItem("access_token");
    }

    function redirectUnauthorized() {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
    }

    // ==========================================
    // MENSAGENS E PARÂMETROS
    // ==========================================

    function showMessage(message) {
        $("ordersReportMessage").textContent = message;
    }

    function buildParams(includePagination = true) {
        const params = new URLSearchParams();

        Object.entries(filters).forEach(([key, value]) => {
            if (value !== "" && value != null) {
                params.set(key, value);
            }
        });

        if (includePagination) {
            params.set(
                "skip",
                String((currentPage - 1) * PAGE_SIZE)
            );
            params.set("limit", String(PAGE_SIZE));
        }

        return params;
    }

    function readFilters() {
        const dateFrom = $("reportOrdersStartDate").value;
        const dateTo = $("reportOrdersEndDate").value;

        if (dateFrom && dateTo && dateFrom > dateTo) {
            throw new Error(
                "A data inicial não pode ser posterior à data final."
            );
        }

        return {
            date_from: dateFrom,
            date_to: dateTo,
            type: $("reportOrdersType").value,
            status: $("reportOrdersStatus").value
        };
    }

    // ==========================================
    // FORMATAÇÃO
    // ==========================================

    function formatDate(value) {
        if (!value) return "—";

        const source = String(value);

        const normalized =
            /(?:Z|[+-]\d{2}:?\d{2})$/i.test(source)
                ? source
                : `${source}Z`;

        const parsed = new Date(normalized);

        if (Number.isNaN(parsed.getTime())) {
            return "—";
        }

        return parsed.toLocaleString("pt-BR", {
            timeZone: "America/Recife",
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    const typeLabels = {
        INBOUND: "Recebimento",
        OUTBOUND: "Expedição"
    };

    const statusLabels = {
        PENDING: "Pendente",
        PROCESSING: "Em processamento",
        COMPLETED: "Concluído",
        CANCELLED: "Cancelado"
    };

    function cell(row, value) {
        const td = document.createElement("td");
        td.textContent = String(value ?? "—");
        row.appendChild(td);
        return td;
    }

    function pillCell(row, label, cssClass) {
        const td = document.createElement("td");
        const pill = document.createElement("span");

        pill.className = cssClass;
        pill.textContent = label;

        td.appendChild(pill);
        row.appendChild(td);
    }

    function numericValue(value) {
        const number = Number(value);
        return Number.isFinite(number) ? number : 0;
    }

    // ==========================================
    // RENDERIZAÇÃO DO RELATÓRIO
    // ==========================================

    function render(data) {
        const items = Array.isArray(data.items)
            ? data.items
            : [];

        totalRecords = Math.max(
            0,
            numericValue(data.total ?? items.length)
        );

        const body = $("reportOrdersTableBody");
        body.replaceChildren();

        let itemsOnPage = 0;
        let quantityOnPage = 0;
        let tasksOnPage = 0;

        let itemsKnown = true;
        let quantityKnown = true;
        let tasksKnown = true;

        items.forEach(order => {
            const id =
                order.id ?? order.order_id ?? "—";

            const itemCount =
                order.items_count ??
                order.total_items ??
                (Array.isArray(order.items)
                    ? order.items.length
                    : null);

            const quantity =
                order.total_quantity ??
                order.quantity ??
                null;

            const taskCount =
                order.tasks_count ??
                order.total_tasks ??
                (Array.isArray(order.tasks)
                    ? order.tasks.length
                    : null);

            if (itemCount == null) {
                itemsKnown = false;
            } else {
                itemsOnPage += numericValue(itemCount);
            }

            if (quantity == null) {
                quantityKnown = false;
            } else {
                quantityOnPage += numericValue(quantity);
            }

            if (taskCount == null) {
                tasksKnown = false;
            } else {
                tasksOnPage += numericValue(taskCount);
            }

            const row = document.createElement("tr");

            cell(row, `#${id}`);
            cell(row, formatDate(order.created_at));

            pillCell(
                row,
                typeLabels[order.type] || order.type || "—",
                "orders-report-type"
            );

            pillCell(
                row,
                statusLabels[order.status] ||
                    order.status ||
                    "—",
                `orders-report-status ${
                    String(order.status || "").toLowerCase()
                }`
            );

            cell(
                row,
                itemCount == null
                    ? "—"
                    : fmt.format(numericValue(itemCount))
            );

            cell(
                row,
                quantity == null
                    ? "—"
                    : fmt.format(numericValue(quantity))
            );

            cell(
                row,
                taskCount == null
                    ? "—"
                    : fmt.format(numericValue(taskCount))
            );

            body.appendChild(row);
        });

        $("reportOrdersTotal").textContent =
            fmt.format(totalRecords);

        $("reportOrdersItems").textContent =
            itemsKnown ? fmt.format(itemsOnPage) : "—";

        $("reportOrdersQuantity").textContent =
            quantityKnown ? fmt.format(quantityOnPage) : "—";

        $("reportOrdersTasks").textContent =
            tasksKnown ? fmt.format(tasksOnPage) : "—";

        $("reportOrdersCount").textContent =
            `${fmt.format(totalRecords)} registro(s)`;

        const pages = Math.max(
            1,
            Math.ceil(totalRecords / PAGE_SIZE)
        );

        $("reportOrdersPageInfo").textContent =
            `Página ${currentPage} de ${pages}`;

        $("reportOrdersPrevious").disabled =
            currentPage <= 1;

        $("reportOrdersNext").disabled =
            currentPage >= pages;

        showMessage(
            items.length
                ? ""
                : "Nenhum pedido encontrado para os filtros selecionados."
        );
    }

    function resetDisplay() {
        $("reportOrdersTableBody").replaceChildren();

        [
            "reportOrdersTotal",
            "reportOrdersItems",
            "reportOrdersQuantity",
            "reportOrdersTasks"
        ].forEach(id => {
            $(id).textContent = "—";
        });

        $("reportOrdersCount").textContent = "0 registros";
        $("reportOrdersPageInfo").textContent = "Página 1 de 1";

        $("reportOrdersPrevious").disabled = true;
        $("reportOrdersNext").disabled = true;
    }

    // ==========================================
    // TRATAMENTO DE ERROS
    // ==========================================

    async function errorText(response) {
        if (response.status === 404) {
            return (
                "A API /reports/orders ainda não está " +
                "disponível nesta versão do backend."
            );
        }

        if (response.status === 403) {
            return (
                "Seu perfil não tem permissão " +
                "para acessar este relatório."
            );
        }

        try {
            const json = await response.json();

            if (typeof json.detail === "string") {
                return json.detail;
            }
        } catch (_) {
            // Resposta sem JSON
        }

        return (
            `Não foi possível carregar o relatório ` +
            `(HTTP ${response.status}).`
        );
    }

    // ==========================================
    // CONSULTA À API
    // ==========================================

    async function loadReport() {
        if (currentController) {
            currentController.abort();
        }

        const controller = new AbortController();

        currentController = controller;
        loading = true;
        loadedOnce = true;

        $("reportOrdersPrevious").disabled = true;
        $("reportOrdersNext").disabled = true;

        showMessage("Carregando relatório...");

        try {
            const token = getToken();

            if (!token) {
                return redirectUnauthorized();
            }

            const response = await fetch(
                `/reports/orders?${buildParams()}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    },
                    signal: controller.signal
                }
            );

            if (response.status === 401) {
                return redirectUnauthorized();
            }

            if (!response.ok) {
                throw new Error(await errorText(response));
            }

            const data = await response.json();

            if (!data || !Array.isArray(data.items)) {
                throw new Error(
                    "A resposta da API não possui " +
                    "uma lista de pedidos válida."
                );
            }

            render(data);
        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            resetDisplay();

            showMessage(
                error.message || "Falha ao consultar pedidos."
            );
        } finally {
            if (currentController === controller) {
                currentController = null;
                loading = false;
            }
        }
    }

    // ==========================================
    // FILTROS
    // ==========================================

    $("ordersReportFilters").addEventListener(
        "submit",
        event => {
            event.preventDefault();

            try {
                filters = readFilters();
                currentPage = 1;
                loadReport();
            } catch (error) {
                showMessage(error.message);
            }
        }
    );

    $("clearOrdersReportFilters").addEventListener(
        "click",
        () => {
            $("ordersReportFilters").reset();

            filters = {};
            currentPage = 1;

            loadReport();
        }
    );

    // ==========================================
    // PAGINAÇÃO
    // ==========================================

    $("reportOrdersPrevious").addEventListener(
        "click",
        () => {
            if (loading || currentPage <= 1) {
                return;
            }

            currentPage -= 1;
            loadReport();
        }
    );

    $("reportOrdersNext").addEventListener(
        "click",
        () => {
            if (
                loading ||
                currentPage * PAGE_SIZE >= totalRecords
            ) {
                return;
            }

            currentPage += 1;
            loadReport();
        }
    );

    // ==========================================
    // EXPORTAÇÃO CSV
    // ==========================================

    $("exportOrdersCsv").addEventListener(
        "click",
        async () => {
            const button = $("exportOrdersCsv");

            try {
                const token = getToken();

                if (!token) {
                    return redirectUnauthorized();
                }

                button.disabled = true;

                const response = await fetch(
                    `/reports/orders.csv?${buildParams(false)}`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`
                        }
                    }
                );

                if (response.status === 401) {
                    return redirectUnauthorized();
                }

                if (!response.ok) {
                    throw new Error(
                        await errorText(response)
                    );
                }

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);

                const link = document.createElement("a");

                link.href = url;
                link.download = "relatorio-pedidos.csv";

                document.body.appendChild(link);
                link.click();
                link.remove();

                URL.revokeObjectURL(url);

                showMessage(
                    "Arquivo CSV preparado para download."
                );
            } catch (error) {
                showMessage(
                    error.message ||
                    "Não foi possível exportar o CSV."
                );
            } finally {
                button.disabled = false;
            }
        }
    );

    resetDisplay();
})();
