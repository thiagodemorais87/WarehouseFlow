
document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("access_token");

    const elements = {
        runsCount: document.getElementById("pickingRunsCount"),
        averageReduction: document.getElementById("pickingAverageReduction"),
        averageDistance: document.getElementById("pickingAverageDistance"),
        resultsCount: document.getElementById("pickingResultsCount"),
        message: document.getElementById("pickingReportMessage"),
        tableBody: document.getElementById("pickingReportTableBody"),
        startDate: document.getElementById("pickingStartDate"),
        endDate: document.getElementById("pickingEndDate"),
        orderSearch: document.getElementById("pickingOrderSearch"),
        sourceFilter: document.getElementById("pickingSourceFilter"),
        clearFilters: document.getElementById("clearPickingFilters"),
        exportButton: document.getElementById("exportPickingCsv")
    };

    let pickingRuns = [];
    let reportLoaded = false;

    const numberFormat = new Intl.NumberFormat("pt-BR", {
        maximumFractionDigits: 2
    });

    function formatNumber(value) {
        const number = Number(value);
        return Number.isFinite(number) ? numberFormat.format(number) : "—";
    }


const REPORT_TIME_ZONE = "America/Sao_Paulo";

function parseExecutionDate(value) {
    if (!value) return null;

    let dateString = String(value).trim();

    if (!/(Z|[+-]\d{2}:\d{2})$/i.test(dateString)) {
        dateString += "Z";
    }

    const date = new Date(dateString);

    return Number.isNaN(date.getTime()) ? null : date;
}

function formatDate(value) {
    const date = parseExecutionDate(value);

    if (!date) return "—";

    return date.toLocaleString("pt-BR", {
        timeZone: REPORT_TIME_ZONE,
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit"
    });
}

function getDateKey(value) {
    const date = parseExecutionDate(value);

    if (!date) return "";

    const parts = new Intl.DateTimeFormat("en-US", {
        timeZone: REPORT_TIME_ZONE,
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
    }).formatToParts(date);

    const values = Object.fromEntries(
        parts.map(part => [part.type, part.value])
    );

    return `${values.year}-${values.month}-${values.day}`;
}


    function setMessage(text) {
        elements.message.textContent = text;
    }

    async function requestReport(endpoint, responseType = "json") {
        const response = await fetch(endpoint, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "/login";
            throw new Error("Sessão expirada. Faça login novamente.");
        }

        if (!response.ok) {
            throw new Error(
                `Erro ao acessar ${endpoint} (HTTP ${response.status}).`
            );
        }

        return responseType === "blob"
            ? response.blob()
            : response.json();
    }

    function createCell(row, value) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
    }

    function populateSources() {
        const sources = [...new Set(
            pickingRuns
                .map(run => run.source)
                .filter(Boolean)
        )].sort();

        elements.sourceFilter.replaceChildren(
            new Option("Todas as origens", "")
        );

        sources.forEach(source => {
            elements.sourceFilter.add(new Option(source, source));
        });
    }

    function getFilteredRuns() {
        const startDate = elements.startDate.value;
        const endDate = elements.endDate.value;
        const order = elements.orderSearch.value.trim();
        const source = elements.sourceFilter.value;

        return pickingRuns.filter(run => {
            const date = getDateKey(run.executed_at);

            if (startDate && (!date || date < startDate)) return false;
            if (endDate && (!date || date > endDate)) return false;

            if (order && !String(run.order_id ?? "").includes(order)) {
                return false;
            }

            if (source && run.source !== source) return false;

            return true;
        });
    }

    function renderTable() {
        const filteredRuns = getFilteredRuns();

        elements.tableBody.replaceChildren();

        elements.resultsCount.textContent =
            `${filteredRuns.length} registro${filteredRuns.length === 1 ? "" : "s"}`;

        if (!filteredRuns.length) {
            if (reportLoaded) {
                setMessage(
                    pickingRuns.length
                        ? "Nenhuma otimização encontrada para os filtros selecionados."
                        : "Nenhuma otimização registrada até o momento."
                );
            }
            return;
        }

        setMessage("");

        const fragment = document.createDocumentFragment();

        filteredRuns.forEach(run => {
            const row = document.createElement("tr");

            createCell(row, formatDate(run.executed_at));
            createCell(row, run.user_id ?? "—");
            createCell(row, run.order_id ?? "—");
            createCell(row, run.source ?? "—");
            createCell(row, formatNumber(run.locations_count));
            createCell(row, formatNumber(run.distance_before));
            createCell(row, formatNumber(run.distance_after));
            createCell(row, `${formatNumber(run.reduction_percent)}%`);
            createCell(row, `${formatNumber(run.execution_time_ms)} ms`);
            createCell(
                row,
                Array.isArray(run.two_opt_route)
                    ? run.two_opt_route.join(" → ")
                    : "—"
            );

            fragment.appendChild(row);
        });

        elements.tableBody.appendChild(fragment);
    }

    function updateSummary(summary) {
        elements.runsCount.textContent =
            formatNumber(summary.runs_count);

        elements.averageReduction.textContent =
            `${formatNumber(summary.average_reduction_percent)}%`;

        elements.averageDistance.textContent =
            formatNumber(summary.average_distance_reduction);
    }

    async function loadReport() {
        setMessage("Carregando histórico de otimizações...");

        const results = await Promise.allSettled([
            requestReport("/optimization/reports/summary"),
            requestReport("/optimization/reports/picking")
        ]);

        const [summaryResult, runsResult] = results;

        if (summaryResult.status === "fulfilled") {
            updateSummary(summaryResult.value);
        } else {
            elements.runsCount.textContent = "Erro";
            elements.averageReduction.textContent = "Erro";
            elements.averageDistance.textContent = "Erro";
            console.error("Erro nos indicadores:", summaryResult.reason);
        }

        if (
            runsResult.status === "fulfilled" &&
            Array.isArray(runsResult.value)
        ) {
            pickingRuns = runsResult.value;
            reportLoaded = true;
            populateSources();
            renderTable();
        } else {
            setMessage("Não foi possível carregar o histórico de otimizações.");
            console.error(
                "Erro no histórico:",
                runsResult.status === "rejected"
                    ? runsResult.reason
                    : "Resposta inesperada da API."
            );
        }
    }

    async function exportCsv() {
        const button = elements.exportButton;
        button.disabled = true;
        button.textContent = "Exportando...";

        try {
            const csv = await requestReport(
                "/optimization/reports/picking.csv",
                "blob"
            );

            const url = URL.createObjectURL(csv);
            const link = document.createElement("a");

            link.href = url;
            link.download = "picking-report.csv";

            document.body.appendChild(link);
            link.click();
            link.remove();

            setTimeout(() => URL.revokeObjectURL(url), 1000);
        } catch (error) {
            console.error("Erro ao exportar CSV:", error);
            alert("Não foi possível exportar o relatório de picking.");
        } finally {
            button.disabled = false;
            button.textContent = "Exportar CSV";
        }
    }

    [
        elements.startDate,
        elements.endDate,
        elements.orderSearch,
        elements.sourceFilter
    ].forEach(element => {
        element.addEventListener("input", renderTable);
    });

    elements.clearFilters.addEventListener("click", () => {
        elements.startDate.value = "";
        elements.endDate.value = "";
        elements.orderSearch.value = "";
        elements.sourceFilter.value = "";
        renderTable();
    });

    elements.exportButton.addEventListener("click", exportCsv);

    loadReport();
});
