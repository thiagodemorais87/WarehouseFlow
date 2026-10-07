document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("access_token");

    if (!token) {
        window.location.href = "/login";
        return;
    }

    const optimizationForm = document.getElementById("optimizationForm");
    const locationsContainer = document.getElementById("optimizationLocations");
    const addLocationButton = document.getElementById("addLocationButton");
    const optimizeRouteButton = document.getElementById("optimizeRouteButton");
    const optimizationMessage = document.getElementById("optimizationMessage");
    const optimizationResults = document.getElementById("optimizationResults");

    const startId = document.getElementById("startId");
    const startX = document.getElementById("startX");
    const startY = document.getElementById("startY");

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

    let locationCounter = 0;


    function showMessage(message, type = "error") {
        optimizationMessage.textContent = message;
        optimizationMessage.className = `optimization-message ${type}`;
    }


    function clearMessage() {
        optimizationMessage.textContent = "";
        optimizationMessage.className = "optimization-message";
    }


    function getErrorMessage(data, fallback = "Não foi possível otimizar a rota.") {
        if (!data) {
            return fallback;
        }

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
                    value="${defaultId}"
                    placeholder="Ex.: A01"
                    required
                >
            </div>

            <div class="form-group">
                <label>Coordenada X</label>
                <input
                    type="number"
                    class="location-x"
                    value="${defaultX}"
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
                    value="${defaultY}"
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

        row
            .querySelector(".remove-location-button")
            .addEventListener("click", () => {
                row.remove();
                clearMessage();
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
                "Adicione pelo menos uma localização antes de otimizar a rota."
            );
            return false;
        }

        const startIdentifier = startId.value.trim();

        if (!startIdentifier) {
            showMessage("Informe o identificador do ponto de partida.");
            return false;
        }

        if (startX.value === "" || startY.value === "") {
            showMessage("Informe as coordenadas do ponto de partida.");
            return false;
        }

        const identifiers = new Set();

        for (const location of locations) {
            if (!location.id) {
                showMessage(
                    "Todas as localizações precisam de um identificador."
                );
                return false;
            }

            if (
                !Number.isFinite(location.x) ||
                !Number.isFinite(location.y)
            ) {
                showMessage(
                    `Informe coordenadas válidas para ${location.id}.`
                );
                return false;
            }

            if (location.id === startIdentifier) {
                showMessage(
                    `A localização "${location.id}" não pode ter o mesmo identificador do ponto de partida.`
                );
                return false;
            }

            if (identifiers.has(location.id)) {
                showMessage(
                    `O identificador "${location.id}" está repetido.`
                );
                return false;
            }

            identifiers.add(location.id);
        }

        return true;
    }


    function formatNumber(value, decimals = 2) {
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
            pointElement.textContent = point;

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
        distanceBefore.textContent = formatNumber(result.distance_before);
        distanceAfter.textContent = formatNumber(result.distance_after);
        distanceReduction.textContent = formatNumber(
            result.distance_reduction
        );
        reductionPercent.textContent =
            `${formatNumber(result.reduction_percent)}%`;

        originalDistance.textContent =
            `${formatNumber(result.distance_before)} unidades`;

        nearestNeighborDistance.textContent =
            `${formatNumber(result.nearest_neighbor_distance)} unidades`;

        twoOptDistance.textContent =
            `${formatNumber(result.two_opt_distance)} unidades`;

        renderRoute(originalRoute, result.original_route);
        renderRoute(
            nearestNeighborRoute,
            result.nearest_neighbor_route
        );
        renderRoute(twoOptRoute, result.two_opt_route);

        locationsCount.textContent = result.locations_count;

        executionTime.textContent =
            `${formatNumber(result.execution_time_ms, 3)} ms`;

        optimizationResults.hidden = false;

        optimizationResults.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }


    async function optimizeRoute(event) {
        event.preventDefault();

        clearMessage();

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

        optimizeRouteButton.disabled = true;
        optimizeRouteButton.textContent = "Otimizando...";

        try {
            const response = await fetch("/optimization/route", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (handleUnauthorized(response)) {
                return;
            }

            let data = null;

            try {
                data = await response.json();
            } catch {
                data = null;
            }

            if (!response.ok) {
                showMessage(
                    getErrorMessage(
                        data,
                        "Não foi possível otimizar a rota."
                    )
                );
                return;
            }

            renderResults(data);

            showMessage(
                "Rota otimizada com sucesso.",
                "success"
            );

        } catch (error) {
            console.error("Erro ao otimizar rota:", error);

            showMessage(
                "Não foi possível conectar ao servidor."
            );
        } finally {
            optimizeRouteButton.disabled = false;
            optimizeRouteButton.textContent = "Otimizar rota";
        }
    }


    addLocationButton.addEventListener("click", () => {
        createLocationRow();
        clearMessage();
    });

    optimizationForm.addEventListener(
        "submit",
        optimizeRoute
    );


    /*
     * Duas localizações iniciais para facilitar
     * o preenchimento e o teste da otimização.
     */
    createLocationRow({
        id: "A01"
    });

    createLocationRow({
        id: "B01"
    });
});