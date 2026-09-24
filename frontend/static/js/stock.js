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

    stockModalTitle.textContent = "Ajustar estoque";
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

loadStock();