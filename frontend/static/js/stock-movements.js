
document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const API_URL = "/reports/stock-movements";
    const PAGE_SIZE = 20;
    const TIME_ZONE = "America/Sao_Paulo";

    let currentPage = 1;
    let totalRecords = 0;
    let loading = false;
    let initialized = false;
    let exporting = false;

    const $ = (id) => document.getElementById(id);

    const elements = {
        total: $("movementsTotal"),
        inbound: $("movementsInbound"),
        outbound: $("movementsOutbound"),
        balance: $("movementsBalance"),
        count: $("movementsResultsCount"),
        message: $("movementsReportMessage"),
        tbody: $("movementsTableBody"),
        start: $("movementsStartDate"),
        end: $("movementsEndDate"),
        type: $("movementsType"),
        status: $("movementsStatus"),
        product: $("movementsProduct"),
        apply: $("applyMovementsFilters"),
        clear: $("clearMovementsFilters"),
        export: $("exportMovementsCsv"),
        previous: $("movementsPrevious"),
        next: $("movementsNext"),
        pageInfo: $("movementsPageInfo")
    };

    // Executa somente em páginas que possuem o relatório.
    if (Object.values(elements).some((element) => !element)) {
        return;
    }

    const numberFormat = new Intl.NumberFormat("pt-BR");

    // AUTENTICAÇÃO E PERMISSÕES 

    function getToken() {
        if (window.WarehouseAuth) {
            return window.WarehouseAuth.getToken();
        }

        return localStorage.getItem("access_token");
    }

    function redirectUnauthorized() {
        if (window.WarehouseAuth) {
            window.WarehouseAuth.logout();
            return;
        }

        localStorage.removeItem("access_token");
        window.location.replace("/login");
    }

    async function canAccessReport() {
        if (!window.WarehouseAuth) {
            return false;
        }

        try {
            return await window.WarehouseAuth.hasRole(
                "ADMIN",
                "GESTOR"
            );
        } catch (error) {
            console.error(
                "Erro ao verificar permissão do relatório:",
                error
            );

            return false;
        }
    }

    // MENSAGENS E FORMATAÇÃO

    function showMessage(text) {
        elements.message.textContent = text;
    }

    function formatNumber(value) {
        return numberFormat.format(Number(value) || 0);
    }

    function formatDate(value) {
        if (!value) {
            return "—";
        }

        let text = String(value).trim();

        // Datas sem fuso são interpretadas como UTC.
        if (!/(Z|[+-]\d{2}:?\d{2})$/i.test(text)) {
            text += "Z";
        }

        const date = new Date(text);

        if (Number.isNaN(date.getTime())) {
            return "—";
        }

        return date.toLocaleString("pt-BR", {
            timeZone: TIME_ZONE,
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    // FILTROS

    function getFilters() {
        const params = new URLSearchParams();

        if (elements.start.value) {
            params.set(
                "date_from",
                elements.start.value
            );
        }

        if (elements.end.value) {
            params.set(
                "date_to",
                elements.end.value
            );
        }

        if (elements.type.value) {
            params.set(
                "type",
                elements.type.value
            );
        }

        if (elements.status.value) {
            params.set(
                "status",
                elements.status.value
            );
        }

        if (elements.product.value.trim()) {
            params.set(
                "product_id",
                elements.product.value.trim()
            );
        }

        return params;
    }

    function validateFilters() {
        if (
            elements.start.value &&
            elements.end.value &&
            elements.start.value > elements.end.value
        ) {
            showMessage(
                "A data inicial não pode ser posterior à data final."
            );

            return false;
        }

        const product = elements.product.value.trim();

        if (
            product &&
            (
                !Number.isSafeInteger(Number(product)) ||
                Number(product) < 1
            )
        ) {
            showMessage(
                "Informe um ID de produto válido."
            );

            return false;
        }

        return true;
    }

    // COMUNICAÇÃO COM A API

    async function apiFetch(url) {
        const token = getToken();

        if (!token) {
            redirectUnauthorized();
            throw new Error("Sessão não encontrada.");
        }

        const response = await fetch(url, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            redirectUnauthorized();
            throw new Error("Sessão expirada.");
        }

        if (response.status === 403) {
            throw new Error(
                "Você não tem permissão para consultar este relatório."
            );
        }

        if (response.status === 404) {
            throw new Error(
                "API de movimentações ainda não disponível nesta versão."
            );
        }

        if (!response.ok) {
            throw new Error(
                `Erro ao consultar o relatório (HTTP ${response.status}).`
            );
        }

        return response;
    }

    // INDICADORES

    function clearStats() {
        elements.total.textContent = "—";
        elements.inbound.textContent = "—";
        elements.outbound.textContent = "—";
        elements.balance.textContent = "—";
        elements.count.textContent = "0 registros";
    }

    function updateStats(data) {
        elements.total.textContent =
            formatNumber(data.total);

        elements.inbound.textContent =
            formatNumber(data.total_inbound);

        elements.outbound.textContent =
            formatNumber(data.total_outbound);

        elements.balance.textContent =
            formatNumber(data.net_quantity);

        elements.count.textContent =
            `${formatNumber(data.total)} registros`;
    }

    // CONSTRUÇÃO DA TABELA

    function addCell(row, value, className = "") {
        const cell = document.createElement("td");

        cell.textContent = value ?? "—";

        if (className) {
            cell.className = className;
        }

        row.appendChild(cell);

        return cell;
    }

    function renderRows(items) {
        elements.tbody.replaceChildren();

        for (const item of items) {
            const row = document.createElement("tr");

            addCell(
                row,
                formatDate(item.created_at)
            );

            addCell(
                row,
                `#${item.order_id}`
            );

            addCell(
                row,
                item.product_name
            );

            addCell(
                row,
                item.sku
            );

            const typeCell = document.createElement("td");
            const typeBadge = document.createElement("span");

            const isInbound =
                item.movement_type === "INBOUND";

            typeBadge.className =
                `movements-type ${
                    isInbound ? "inbound" : "outbound"
                }`;

            typeBadge.textContent =
                isInbound ? "Entrada" : "Saída";

            typeCell.appendChild(typeBadge);
            row.appendChild(typeCell);

            addCell(
                row,
                formatNumber(item.quantity)
            );

            const signed =
                Number(item.signed_quantity) || 0;

            addCell(
                row,
                `${signed > 0 ? "+" : ""}${formatNumber(signed)}`,
                signed >= 0
                    ? "movements-positive"
                    : "movements-negative"
            );

            addCell(
                row,
                item.order_status
            );

            elements.tbody.appendChild(row);
        }
    }

    // PAGINAÇÃO

    function updatePagination() {
        const pages = Math.max(
            1,
            Math.ceil(totalRecords / PAGE_SIZE)
        );

        elements.pageInfo.textContent =
            `Página ${currentPage} de ${pages}`;

        elements.previous.disabled =
            loading || currentPage <= 1;

        elements.next.disabled =
            loading || currentPage >= pages;
    }

    // CARREGAMENTO DO RELATÓRIO

    async function loadMovements() {
        // Sprint 08: verifica a permissão antes da API.
        if (!(await canAccessReport())) {
            showMessage(
                "Seu perfil não tem permissão para consultar este relatório."
            );

            return;
        }

        if (loading || !validateFilters()) {
            return;
        }

        loading = true;

        elements.apply.disabled = true;
        elements.export.disabled = true;

        updatePagination();
        showMessage("Carregando movimentações...");

        try {
            const params = getFilters();

            params.set(
                "skip",
                (currentPage - 1) * PAGE_SIZE
            );

            params.set(
                "limit",
                PAGE_SIZE
            );

            const response = await apiFetch(
                `${API_URL}?${params.toString()}`
            );

            const data = await response.json();

            if (!Array.isArray(data.items)) {
                throw new Error(
                    "Resposta inválida da API."
                );
            }

            totalRecords = Number(data.total) || 0;

            updateStats(data);
            renderRows(data.items);

            showMessage(
                data.items.length
                    ? ""
                    : "Nenhuma movimentação encontrada para os filtros."
            );

        } catch (error) {
            totalRecords = 0;

            clearStats();
            elements.tbody.replaceChildren();

            showMessage(
                error.message ||
                "Não foi possível carregar as movimentações."
            );

        } finally {
            loading = false;

            elements.apply.disabled = false;
            elements.export.disabled = false;

            updatePagination();
        }
    }

    // EXPORTAÇÃO CSV — SPRINT 08

    async function exportCsv() {
        // Verifica a permissão antes da exportação.
        if (!(await canAccessReport())) {
            showMessage(
                "Seu perfil não tem permissão para exportar este relatório."
            );

            return;
        }

        if (exporting || !validateFilters()) {
            return;
        }

        exporting = true;
        elements.export.disabled = true;

        try {
            const params = getFilters();

            const url =
                `${API_URL}.csv?${params.toString()}`;

            const response = await apiFetch(url);

            const blob = await response.blob();

            const objectUrl =
                URL.createObjectURL(blob);

            const link =
                document.createElement("a");

            link.href = objectUrl;
            link.download = "stock-movements-report.csv";

            document.body.appendChild(link);

            link.click();
            link.remove();

            setTimeout(() => {
                URL.revokeObjectURL(objectUrl);
            }, 1000);

            showMessage(
                "Arquivo CSV preparado para download."
            );

        } catch (error) {
            showMessage(
                error.message ||
                "Não foi possível exportar o relatório."
            );

        } finally {
            exporting = false;
            elements.export.disabled = loading;
        }
    }

    // APLICAÇÃO DOS FILTROS

    function applyFilters() {
        if (!validateFilters()) {
            return;
        }

        currentPage = 1;

        loadMovements();
    }

    // INICIALIZAÇÃO DO RELATÓRIO

    function initializeReport() {
        if (initialized) {
            return;
        }

        initialized = true;

        loadMovements();
    }

    // EVENTOS DOS FILTROS

    elements.apply.addEventListener(
        "click",
        applyFilters
    );

    elements.clear.addEventListener("click", () => {
        elements.start.value = "";
        elements.end.value = "";
        elements.type.value = "";
        elements.status.value = "";
        elements.product.value = "";

        currentPage = 1;

        loadMovements();
    });

    // EVENTOS DA PAGINAÇÃO

    elements.previous.addEventListener("click", () => {
        if (loading || currentPage <= 1) {
            return;
        }

        currentPage--;

        loadMovements();
    });

    elements.next.addEventListener("click", () => {
        if (
            loading ||
            currentPage * PAGE_SIZE >= totalRecords
        ) {
            return;
        }

        currentPage++;

        loadMovements();
    });

    // EVENTO DE EXPORTAÇÃO

    elements.export.addEventListener(
        "click",
        exportCsv
    );

    // INTEGRAÇÃO COM AS ABAS — SPRINT 08

    const movementsPanel =
        $("stockMovementsPanel");

    const movementsTab =
        $("stockMovementsTab");

    if (movementsPanel && movementsTab) {

        // Página de estoque com abas:
        // carrega somente após verificar a permissão.

        movementsTab.addEventListener(
            "click",
            async () => {
                if (!(await canAccessReport())) {
                    return;
                }

                initializeReport();
            }
        );

        // Caso o painel já esteja visível,
        // a consulta ainda passará pela verificação
        // de permissão dentro de loadMovements().

        if (!movementsPanel.hidden) {
            initializeReport();
        }

    } else {
        // Página independente do relatório:
        // mantém o carregamento automático original.
        // loadMovements() verifica a permissão.

        initializeReport();
    }
});
