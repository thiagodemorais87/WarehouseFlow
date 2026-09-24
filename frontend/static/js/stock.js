const stockTableBody = document.getElementById("stockTableBody");
const stockMessage = document.getElementById("stockMessage");
const stockSearch = document.getElementById("stockSearch");

const newStockButton = document.getElementById("newStockButton");

const stockModal = document.getElementById("stockModal");
const stockModalTitle = document.getElementById("stockModalTitle");

const closeStockModal = document.getElementById("closeStockModal");
const cancelStockButton = document.getElementById("cancelStockButton");

const stockForm = document.getElementById("stockForm");
const stockProduct = document.getElementById("stockProduct");
const stockLocation = document.getElementById("stockLocation");
const stockQuantity = document.getElementById("stockQuantity");
const stockQuantityLabel = document.getElementById("stockQuantityLabel");
const stockQuantityHint = document.getElementById("stockQuantityHint");

const stockFormMessage = document.getElementById("stockFormMessage");
const saveStockButton = document.getElementById("saveStockButton");

let stockData = [];
let productsData = [];
let locationsData = [];
let editingStockId = null;

async function loadStock() {
    stockMessage.textContent = "Carregando estoque...";
    stockMessage.style.display = "block";
    stockTableBody.innerHTML = "";

    try {
        const [stockResponse, productsResponse, locationsResponse] =
            await Promise.all([
                fetch("/stock/"),
                fetch("/products/"),
                fetch("/locations/")
            ]);

        if (!stockResponse.ok) {
            throw new Error("Não foi possível carregar o estoque.");
        }

        if (!productsResponse.ok) {
            throw new Error("Não foi possível carregar os produtos.");
        }

        if (!locationsResponse.ok) {
            throw new Error("Não foi possível carregar as posições.");
        }

        const stock = await stockResponse.json();
        const products = await productsResponse.json();
        const locations = await locationsResponse.json();

        productsData = products;
        locationsData = locations;

        stockData = stock.map((item) => {
            const product = products.find(
                (product) => product.id === item.product_id
            );

            const location = locations.find(
                (location) => location.id === item.location_id
            );

            return {
                ...item,
                productName: product?.name || "Produto não encontrado",
                productSku: product?.sku || "—",
                locationCode: location?.code || "Posição não encontrada"
            };
        });

        renderStock(stockData);

    } catch (error) {
        stockMessage.textContent = error.message;
        stockMessage.style.display = "block";
    }
}

function renderStock(items) {
    stockTableBody.innerHTML = "";

    if (items.length === 0) {
        stockMessage.textContent = "Nenhum registro de estoque encontrado.";
        stockMessage.style.display = "block";
        return;
    }

    stockMessage.style.display = "none";

    items.forEach((item) => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${item.productSku}</td>
            <td>${item.productName}</td>
            <td>${item.locationCode}</td>

            <td>
                <span class="stock-quantity">
                    ${item.quantity}
                </span>
            </td>

            <td>${formatDate(item.last_updated)}</td>

            <td>
                <div class="stock-actions">
                    <button
                        type="button"
                        class="stock-action-button"
                        data-id="${item.id}"
                    >
                        Ajustar
                    </button>
                </div>
            </td>
        `;

        stockTableBody.appendChild(row);
        
        const adjustButton = row.querySelector(".stock-action-button");

    adjustButton.addEventListener("click", function () {
    openEditStockModal(item.id);
        });
    });
}

function formatDate(date) {
    if (!date) {
        return "—";
    }

    return new Date(date).toLocaleString("pt-BR");
}

stockSearch.addEventListener("input", function () {
    const search = stockSearch.value
        .trim()
        .toLowerCase();

    const filteredStock = stockData.filter((item) => {
        return (
            item.productName.toLowerCase().includes(search) ||
            item.productSku.toLowerCase().includes(search) ||
            item.locationCode.toLowerCase().includes(search)
        );
    });

    renderStock(filteredStock);
});

function openNewStockModal() {
    editingStockId = null;

    stockForm.reset();

    stockModalTitle.textContent = "Adicionar ao estoque";
    stockQuantityLabel.textContent = "Quantidade a adicionar *";
    stockQuantityHint.textContent =
    "A quantidade informada será adicionada ao estoque atual.";
    saveStockButton.textContent = "Salvar";

    stockProduct.disabled = false;
    stockLocation.disabled = false;

    stockFormMessage.textContent = "";
    stockFormMessage.className = "form-message";

    populateStockSelects();

    stockModal.classList.add("open");
}

function closeStockFormModal() {
    stockModal.classList.remove("open");
    editingStockId = null;
}

newStockButton.addEventListener("click", openNewStockModal);
closeStockModal.addEventListener("click", closeStockFormModal);
cancelStockButton.addEventListener("click", closeStockFormModal);

stockModal.addEventListener("click", function (event) {
    if (event.target === stockModal) {
        closeStockFormModal();
    }
});

function populateStockSelects() {
    stockProduct.innerHTML =
        '<option value="">Selecione um produto</option>';

    stockLocation.innerHTML =
        '<option value="">Selecione uma posição</option>';

    productsData.forEach((product) => {
        const option = document.createElement("option");

        option.value = product.id;
        option.textContent = `${product.sku} - ${product.name}`;

        stockProduct.appendChild(option);
    });

    locationsData
        .filter((location) => location.is_active)
        .forEach((location) => {
            const option = document.createElement("option");

            option.value = location.id;
            option.textContent = location.code;

            stockLocation.appendChild(option);
        });
}

function openEditStockModal(stockId) {
    const item = stockData.find(
        (item) => item.id === stockId
    );

    if (!item) {
        return;
    }

    editingStockId = item.id;

    stockForm.reset();
    populateStockSelects();

    stockModalTitle.textContent = "Ajustar saldo";
    stockQuantityLabel.textContent = "Novo saldo *";
    stockQuantityHint.textContent =
    "Informe a quantidade total que deverá permanecer nesta posição.";
    saveStockButton.textContent = "Salvar alteração";

    stockProduct.value = item.product_id;
    stockLocation.value = item.location_id;
    stockQuantity.value = item.quantity;

    stockProduct.disabled = true;
    stockLocation.disabled = true;

    stockFormMessage.textContent = "";
    stockFormMessage.className = "form-message";

    stockModal.classList.add("open");
}

stockForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    stockFormMessage.textContent = "";
    stockFormMessage.className = "form-message";

    const productId = Number(stockProduct.value);
    const locationId = Number(stockLocation.value);
    const quantity = Number(stockQuantity.value);

    if (!productId || !locationId || Number.isNaN(quantity)) {
        stockFormMessage.textContent =
            "Preencha todos os campos obrigatórios.";
        stockFormMessage.className = "form-message error";
        return;
    }

    if (quantity < 0) {
        stockFormMessage.textContent =
            "A quantidade não pode ser negativa.";
        stockFormMessage.className = "form-message error";
        return;
    }

    let url;
    let method;
    let requestData;

    if (editingStockId) {
        url = `/stock/${editingStockId}`;
        method = "PUT";

        requestData = {
            quantity: quantity
        };
    } else {
        url = "/stock/";
        method = "POST";

        requestData = {
            product_id: productId,
            location_id: locationId,
            quantity: quantity
        };
    }

    saveStockButton.disabled = true;
    saveStockButton.textContent = "Salvando...";

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorData = await response.json();

            throw new Error(
                errorData.detail ||
                "Não foi possível atualizar o estoque."
            );
        }

        closeStockFormModal();

        await loadStock();

    } catch (error) {
        stockFormMessage.textContent = error.message;
        stockFormMessage.className = "form-message error";

    } finally {
        saveStockButton.disabled = false;
        saveStockButton.textContent = "Salvar";
    }
});



loadStock();