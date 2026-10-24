
document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("access_token");

    if (!token) {
        window.location.href = "/login";
        return;
    }

    // ==========================================
    // ELEMENTOS DA INTERFACE
    // ==========================================

    // Seleção do modo
    const manualModeButton = document.getElementById("manualModeButton");
    const orderModeButton = document.getElementById("orderModeButton");

    const manualOptimizationCard = document.getElementById("manualOptimizationCard");
    const orderOptimizationCard = document.getElementById("orderOptimizationCard");

    // Otimização manual
    const optimizationForm = document.getElementById("optimizationForm");
    const locationsContainer = document.getElementById("optimizationLocations");
    const addLocationButton = document.getElementById("addLocationButton");
    const optimizeRouteButton = document.getElementById("optimizeRouteButton");
    const optimizationMessage = document.getElementById("optimizationMessage");

    const startId = document.getElementById("startId");
    const startX = document.getElementById("startX");
    const startY = document.getElementById("startY");

    // Otimização por pedido
    const orderOptimizationForm = document.getElementById("orderOptimizationForm");
    const optimizationOrderId = document.getElementById("optimizationOrderId");
    const orderOptimizationMessage = document.getElementById("orderOptimizationMessage");
    const optimizeOrderButton = document.getElementById("optimizeOrderButton");

    // Motor
    const optimizationEngineStatus = document.getElementById(
        "optimizationEngineStatus"
    );

    // Resultados
    const optimizationResults = document.getElementById("optimizationResults");

    const distanceBefore = document.getElementById("distanceBefore");
    const distanceAfter = document.getElementById("distanceAfter");
    const distanceReduction = document.getElementById("distanceReduction");
    const reductionPercent = document.getElementById("reductionPercent");

    const originalDistance = document.getElementById("originalDistance");
    const nearestNeighborDistance = document.getElementById("nearestNeighborDistance");
    const twoOptDistance = document.getElementById("twoOptDistance");

    const originalRoute = document.getElementById("originalRoute");
    const nearestNeighborRoute = document.getElementById("nearestNeighborRoute");
    const twoOptRoute = document.getElementById("twoOptRoute");

    const locationsCount = document.getElementById("locationsCount");
    const executionTime = document.getElementById("executionTime");

    // Estado da aplicação
    let engineOnline = false;
    let locationCounter = 0;
    let ordersLoaded = false;
    let ordersLoading = false;
    let currentMode = "manual";
    let requestInProgress = false;


    // ==========================================
    // MENSAGENS
    // ==========================================

    function setMessage(element, message, type = "error") {
        if (!element) return;

        element.textContent = message;
        element.className = message
            ? `optimization-message ${type}`
            : "optimization-message";
    }

    function showMessage(message, type = "error") {
        setMessage(optimizationMessage, message, type);
    }

    function clearMessage() {
        setMessage(optimizationMessage, "");
    }

    function showOrderMessage(message, type = "error") {
        setMessage(orderOptimizationMessage, message, type);
    }

    function clearOrderMessage() {
        setMessage(orderOptimizationMessage, "");
    }

    function getErrorMessage(
        data,
        fallback = "Não foi possível realizar a operação."
    ) {
        if (!data) return fallback;

        if (typeof data.detail === "string") {
            return data.detail;
        }

        if (Array.isArray(data.detail)) {
            return data.detail
                .map((item) => item.msg || "Erro de validação")
                .join(" ");
        }

        if (Array.isArray(data.errors)) {
            return data.errors.join(" ");
        }

        return fallback;
    }

    function handleUnauthorized(response) {
        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "/login";
            return true;
        }

        return false;
    }


    // ==========================================
    // ESTADO DOS BOTÕES
    // ==========================================

    function updateActionButtons() {
        optimizeRouteButton.disabled =
            !engineOnline || requestInProgress;

        optimizeOrderButton.disabled =
            !engineOnline ||
            requestInProgress ||
            ordersLoading ||
            optimizationOrderId.disabled ||
            !optimizationOrderId.value;
    }


    // ==========================================
    // ALTERNÂNCIA ENTRE MODOS
    // ==========================================

    function setOptimizationMode(mode) {
        const isManual = mode === "manual";

        currentMode = isManual ? "manual" : "order";

        manualOptimizationCard.hidden = !isManual;
        orderOptimizationCard.hidden = isManual;

        manualModeButton.classList.toggle("active", isManual);
        orderModeButton.classList.toggle("active", !isManual);

        manualModeButton.setAttribute(
            "aria-pressed",
            String(isManual)
        );

        orderModeButton.setAttribute(
            "aria-pressed",
            String(!isManual)
        );

        // Não mostra resultados de outro modo
        optimizationResults.hidden = true;

        clearMessage();
        clearOrderMessage();

        // Carrega pedidos ao abrir o modo pela primeira vez
        if (!isManual && !ordersLoaded && !ordersLoading) {
            loadOutboundOrders();
        }

        updateActionButtons();
    }

    manualModeButton.addEventListener("click", () => {
        setOptimizationMode("manual");
    });

    orderModeButton.addEventListener("click", () => {
        setOptimizationMode("order");
    });


    // ==========================================
    // VERIFICAÇÃO DO MOTOR
    // ==========================================

    function setEngineStatus(status, label) {
        engineOnline = status === "online";

        if (optimizationEngineStatus) {
            optimizationEngineStatus.dataset.status = status;
            optimizationEngineStatus.textContent = label;
        }

        updateActionButtons();
    }

    async function checkEngineHealth() {
        setEngineStatus("checking", "Verificando motor...");

        try {
            const response = await fetch("/health");

            const data = await response.json();

            if (response.ok && data.status === "ok") {
                const version = data.version
                    ? ` (${data.version})`
                    : "";

                setEngineStatus(
                    "online",
                    `Motor online${version}`
                );

                return true;
            }

            setEngineStatus("offline", "Motor offline");
            return false;

        } catch (error) {
            console.error(
                "Erro ao verificar motor de otimização:",
                error
            );

            setEngineStatus("offline", "Motor offline");
            return false;
        }
    }


    // ==========================================
    // LOCALIZAÇÕES MANUAIS
    // ==========================================

    function createLocationRow(values = {}) {
        locationCounter += 1;

        const row = document.createElement("div");
        row.className = "optimization-location-row";
        row.dataset.locationRow = "true";

        const defaultId = values.id || `LOC${locationCounter}`;
        const defaultX = values.x ?? "";
        const defaultY = values.y ?? "";

        row.innerHTML = `
            <div class="form-group">
                <label>Identificador</label>
                <input
                    type="text"
                    class="location-id"
                    placeholder="Ex.: A01"
                    required
                >
            </div>

            <div class="form-group">
                <label>Coordenada X</label>
                <input
                    type="number"
                    class="location-x"
                    step="any"
                    placeholder="0"
                    required
                >
            </div>

            <div class="form-group">
                <label>Coordenada Y</label>
                <input
                    type="number"
                    class="location-y"
                    step="any"
                    placeholder="0"
                    required
                >
            </div>

            <button
                type="button"
                class="remove-location-button"
            >
                Remover
            </button>
        `;

        row.querySelector(".location-id").value = defaultId;
        row.querySelector(".location-x").value = defaultX;
        row.querySelector(".location-y").value = defaultY;

        row.querySelector(".remove-location-button")
            .addEventListener("click", () => {
                row.remove();
                clearMessage();
                optimizationResults.hidden = true;
            });

        locationsContainer.appendChild(row);
    }

    function getLocations() {
        const rows = locationsContainer.querySelectorAll(
            ".optimization-location-row"
        );

        return Array.from(rows).map((row) => ({
            id: row.querySelector(".location-id").value.trim(),
            x: Number(row.querySelector(".location-x").value),
            y: Number(row.querySelector(".location-y").value)
        }));
    }

    function validateLocations(locations) {
        if (locations.length === 0) {
            showMessage(
                "Adicione pelo menos uma localização antes de otimizar."
            );
            return false;
        }

        const startIdentifier = startId.value.trim();

        if (!startIdentifier) {
            showMessage(
                "Informe o identificador do ponto de partida."
            );
            return false;
        }

        if (startX.value === "" || startY.value === "") {
            showMessage(
                "Informe as coordenadas do ponto de partida."
            );
            return false;
        }

        const identifiers = new Set();

        const rows = locationsContainer.querySelectorAll(
            ".optimization-location-row"
        );

        for (const row of rows) {
            const id = row.querySelector(".location-id").value.trim();
            const xInput = row.querySelector(".location-x");
            const yInput = row.querySelector(".location-y");

            if (!id) {
                showMessage(
                    "Todas as localizações precisam de um identificador."
                );
                return false;
            }

            if (
                xInput.value === "" ||
                yInput.value === "" ||
                !Number.isFinite(Number(xInput.value)) ||
                !Number.isFinite(Number(yInput.value))
            ) {
                showMessage(
                    `Informe coordenadas válidas para ${id}.`
                );
                return false;
            }

            if (id === startIdentifier) {
                showMessage(
                    `A localização "${id}" não pode ter o mesmo identificador do ponto de partida.`
                );
                return false;
            }

            if (identifiers.has(id)) {
                showMessage(
                    `O identificador "${id}" está repetido.`
                );
                return false;
            }

            identifiers.add(id);
        }

        return true;
    }


    // ==========================================
    // FORMATAÇÃO DOS RESULTADOS
    // ==========================================

    function formatNumber(value, decimals = 2) {
        if (value === null || value === undefined || value === "") {
            return "—";
        }

        const number = Number(value);

        if (!Number.isFinite(number)) {
            return "—";
        }

        return number.toLocaleString("pt-BR", {
            minimumFractionDigits: 0,
            maximumFractionDigits: decimals
        });
    }

    function renderRoute(container, route) {
        container.innerHTML = "";

        if (!Array.isArray(route) || route.length === 0) {
            container.textContent = "—";
            return;
        }

        route.forEach((point, index) => {
            const pointElement = document.createElement("span");
            pointElement.className = "route-point";

            pointElement.textContent =
                typeof point === "object" && point !== null
                    ? String(point.id ?? point.code ?? "Local")
                    : String(point);

            container.appendChild(pointElement);

            if (index < route.length - 1) {
                const arrow = document.createElement("span");
                arrow.className = "route-arrow";
                arrow.textContent = "→";

                container.appendChild(arrow);
            }
        });
    }

    function renderResults(result) {
        distanceBefore.textContent =
            formatNumber(result.distance_before);

        distanceAfter.textContent =
            formatNumber(result.distance_after);

        distanceReduction.textContent =
            formatNumber(result.distance_reduction);

        reductionPercent.textContent =
            `${formatNumber(result.reduction_percent)}%`;

        originalDistance.textContent =
            `${formatNumber(result.distance_before)} unidades`;

        nearestNeighborDistance.textContent =
            `${formatNumber(result.nearest_neighbor_distance)} unidades`;

        twoOptDistance.textContent =
            `${formatNumber(result.two_opt_distance)} unidades`;

        renderRoute(
            originalRoute,
            result.original_route
        );

        renderRoute(
            nearestNeighborRoute,
            result.nearest_neighbor_route
        );

        renderRoute(
            twoOptRoute,
            result.two_opt_route
        );

        locationsCount.textContent =
            result.locations_count ?? "—";

        executionTime.textContent =
            `${formatNumber(result.execution_time_ms, 3)} ms`;

        optimizationResults.hidden = false;

        optimizationResults.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }


    // ==========================================
    // OTIMIZAÇÃO MANUAL
    // ==========================================

    async function optimizeRoute(event) {
        event.preventDefault();

        if (requestInProgress) return;

        clearMessage();
        optimizationResults.hidden = true;

        if (!engineOnline) {
            const online = await checkEngineHealth();

            if (!online) {
                showMessage(
                    "Motor de otimização indisponível."
                );
                return;
            }
        }

        const locations = getLocations();

        if (!validateLocations(locations)) {
            return;
        }

        const payload = {
            start: {
                id: startId.value.trim(),
                x: Number(startX.value),
                y: Number(startY.value)
            },
            locations
        };

        requestInProgress = true;
        updateActionButtons();

        optimizeRouteButton.textContent = "Otimizando...";

        try {
            const response = await fetch("/optimization/route", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (handleUnauthorized(response)) return;

            const data = await response.json();

            if (!response.ok) {
                showMessage(
                    getErrorMessage(
                        data,
                        "Não foi possível otimizar a rota."
                    )
                );
                return;
            }

            if (currentMode === "manual") {
                renderResults(data);
                showMessage(
                    "Rota otimizada com sucesso.",
                    "success"
                );
            }

        } catch (error) {
            console.error(
                "Erro ao otimizar rota manual:",
                error
            );

            showMessage(
                "Não foi possível conectar ao servidor."
            );

        } finally {
            requestInProgress = false;
            optimizeRouteButton.textContent = "Otimizar rota";
            updateActionButtons();
        }
    }


    // ==========================================
    // CARREGAMENTO DOS PEDIDOS OUTBOUND
    // ==========================================

    async function loadOutboundOrders() {
        if (ordersLoading) return;

        ordersLoading = true;
        ordersLoaded = false;

        clearOrderMessage();

        optimizationOrderId.disabled = true;
        optimizationOrderId.replaceChildren(
            new Option("Carregando pedidos...", "")
        );

        updateActionButtons();

        try {
            const response = await fetch(
                "/orders/?type=OUTBOUND&limit=500",
                {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );

            if (handleUnauthorized(response)) return;

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    getErrorMessage(
                        data,
                        "Não foi possível carregar os pedidos."
                    )
                );
            }

            if (!Array.isArray(data)) {
                throw new Error(
                    "A API retornou um formato inesperado."
                );
            }

            // Garante que apenas pedidos de saída sejam exibidos
            const outboundOrders = data.filter(
                (order) =>
                    String(order.type).toUpperCase() === "OUTBOUND"
            );

            optimizationOrderId.replaceChildren(
                new Option("Selecione um pedido de saída", "")
            );

            if (outboundOrders.length === 0) {
                optimizationOrderId.replaceChildren(
                    new Option(
                        "Nenhum pedido de saída encontrado",
                        ""
                    )
                );

                showOrderMessage(
                    "Não existem pedidos OUTBOUND disponíveis. Cadastre um pedido de saída na página Pedidos."
                );

                ordersLoaded = true;
                return;
            }

            outboundOrders.forEach((order) => {
                const itemCount = Array.isArray(order.items)
                    ? order.items.length
                    : 0;

                const label =
                    `Pedido #${order.id} — ${order.status}` +
                    ` — ${itemCount} item(ns)`;

                optimizationOrderId.add(
                    new Option(label, String(order.id))
                );
            });

            optimizationOrderId.disabled = false;
            ordersLoaded = true;

            clearOrderMessage();

        } catch (error) {
            console.error(
                "Erro ao carregar pedidos OUTBOUND:",
                error
            );

            optimizationOrderId.replaceChildren(
                new Option(
                    "Erro ao carregar pedidos",
                    ""
                )
            );

            showOrderMessage(
                error.message ||
                "Não foi possível conectar ao servidor."
            );

        } finally {
            ordersLoading = false;
            updateActionButtons();
        }
    }


    // ==========================================
    // OTIMIZAÇÃO POR PEDIDO
    // ==========================================

    async function optimizeSelectedOrder(event) {
        event.preventDefault();

        if (requestInProgress) return;

        clearOrderMessage();
        optimizationResults.hidden = true;

        const orderId = Number(optimizationOrderId.value);

        if (!Number.isInteger(orderId) || orderId < 1) {
            showOrderMessage(
                "Selecione um pedido de saída válido."
            );
            return;
        }

        if (!engineOnline) {
            const online = await checkEngineHealth();

            if (!online) {
                showOrderMessage(
                    "Motor de otimização indisponível."
                );
                return;
            }
        }

        requestInProgress = true;
        updateActionButtons();

        optimizeOrderButton.textContent = "Otimizando pedido...";

        try {
            const response = await fetch(
                "/optimization/route/by-order",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        order_id: orderId
                    })
                }
            );

            if (handleUnauthorized(response)) return;

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    getErrorMessage(
                        data,
                        "Não foi possível otimizar o pedido."
                    )
                );
            }

            if (currentMode === "order") {
                renderResults(data);

                showOrderMessage(
                    `Pedido #${orderId} otimizado com sucesso.`,
                    "success"
                );
            }

        } catch (error) {
            console.error(
                "Erro ao otimizar pedido:",
                error
            );

            showOrderMessage(
                error.message ||
                "Não foi possível conectar ao servidor."
            );

        } finally {
            requestInProgress = false;
            optimizeOrderButton.textContent = "Otimizar pedido";
            updateActionButtons();
        }
    }


    // ==========================================
    // EVENTOS
    // ==========================================

    // Adicionar localização manual
    addLocationButton.addEventListener("click", () => {
        createLocationRow();
        clearMessage();
        optimizationResults.hidden = true;
    });

    // Enviar otimização manual
    optimizationForm.addEventListener(
        "submit",
        optimizeRoute
    );

    // Selecionar pedido
    optimizationOrderId.addEventListener("change", () => {
        clearOrderMessage();
        optimizationResults.hidden = true;
        updateActionButtons();
    });

    // Enviar otimização por pedido
    orderOptimizationForm.addEventListener(
        "submit",
        optimizeSelectedOrder
    );


    // ==========================================
    // INICIALIZAÇÃO
    // ==========================================

    // Localizações iniciais para testes manuais
    createLocationRow({
        id: "A01"
    });

    createLocationRow({
        id: "B01"
    });

    // Inicia no modo manual
    setOptimizationMode("manual");

    // Verifica disponibilidade do motor
    checkEngineHealth();
});
