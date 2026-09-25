const productsTableBody = document.getElementById("productsTableBody");
const productsMessage = document.getElementById("productsMessage");
const productSearch = document.getElementById("productSearch");
const newProductButton = document.getElementById("newProductButton");
const productModal = document.getElementById("productModal");
const closeProductModal = document.getElementById("closeProductModal");
const cancelProductButton = document.getElementById("cancelProductButton");

const productForm = document.getElementById("productForm");
const productFormMessage = document.getElementById("productFormMessage");
const saveProductButton = document.getElementById("saveProductButton");
const productModalTitle = document.getElementById("productModalTitle");

const deleteProductModal = document.getElementById("deleteProductModal");
const deleteProductName = document.getElementById("deleteProductName");
const closeDeleteModal = document.getElementById("closeDeleteModal");
const cancelDeleteButton = document.getElementById("cancelDeleteButton");
const confirmDeleteButton = document.getElementById("confirmDeleteButton");
const deleteProductMessage = document.getElementById("deleteProductMessage");

const token = localStorage.getItem("access_token");

let productToDelete = null;
let editingProductId = null;

async function loadProducts(search = "") {
    productsMessage.textContent = "Carregando produtos...";
    productsMessage.style.display = "block";
    productsTableBody.innerHTML = "";

    try {
        let url = "/products/";

        if (search) {
            url += `?search=${encodeURIComponent(search)}`;
        }

        const response = await fetch(url, {
            headers: {
        "Authorization": `Bearer ${token}`
    }
});

        if (!response.ok) {
            const data = await response.json();

            throw new Error(
                data.detail || "Não foi possível carregar os produtos."
            );
        }

        const products = await response.json();

        renderProducts(products);

    } catch (error) {
        productsMessage.textContent = error.message;
        productsMessage.style.display = "block";
    }
}

function renderProducts(products) {
    productsTableBody.innerHTML = "";

    if (products.length === 0) {
        productsMessage.textContent = "Nenhum produto cadastrado.";
        productsMessage.style.display = "block";
        return;
    }

    productsMessage.style.display = "none";

    products.forEach((product) => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${product.sku}</td>
            <td>${product.name}</td>
            <td>${product.description || "—"}</td>
            <td>${formatWeight(product.weight)}</td>
            <td>${formatVolume(product.volume)}</td>
            <td>
                <div class="product-actions">
                    <button
                        type="button"
                        class="product-action-button edit-product-button"
                        data-id="${product.id}"
                    >
                        Editar
                    </button>

                    <button
                        type="button"
                        class="product-action-button delete-product-button"
                        data-id="${product.id}"
                    >
                        Excluir
                    </button>
                </div>
            </td>
        `;

        productsTableBody.appendChild(row);

    const editButton = row.querySelector(".edit-product-button");

editButton.addEventListener("click", function () {
    openEditProductModal(product);
    });

    const deleteButton = row.querySelector(".delete-product-button");

deleteButton.addEventListener("click", function () {
    openDeleteModal(product);
});

closeDeleteModal.addEventListener("click", closeDeleteProductModal);

cancelDeleteButton.addEventListener("click", closeDeleteProductModal);

deleteProductModal.addEventListener("click", function (event) {
    if (event.target === deleteProductModal) {
        closeDeleteProductModal();
    }
});
    });
}

function openEditProductModal(product) {
    editingProductId = product.id;

    productModalTitle.textContent = "Editar produto";
    saveProductButton.textContent = "Salvar alterações";

    document.getElementById("sku").value = product.sku;
    document.getElementById("name").value = product.name;
    document.getElementById("description").value = product.description || "";
    document.getElementById("weight").value = product.weight ?? "";
    document.getElementById("volume").value = product.volume ?? "";

    productFormMessage.textContent = "";
    productFormMessage.className = "form-message";

    productModal.classList.add("open");
}

function openDeleteModal(product) {
    productToDelete = product;

    deleteProductName.textContent = `"${product.name}"`;

    deleteProductMessage.textContent = "";
    deleteProductMessage.className = "form-message";

    deleteProductModal.classList.add("open");
}

function closeDeleteProductModal() {
    deleteProductModal.classList.remove("open");
    productToDelete = null;
}

confirmDeleteButton.addEventListener("click", async function () {
    if (!productToDelete) {
        return;
    }

    try {
        confirmDeleteButton.disabled = true;
        confirmDeleteButton.textContent = "Excluindo...";

        const response = await fetch(`/products/${productToDelete.id}`, {
            method: "DELETE",
            headers: {
        "Authorization": `Bearer ${token}`
    }
});

        if (!response.ok) {
            let message = "Não foi possível excluir o produto.";

            try {
                const data = await response.json();

                if (typeof data.detail === "string") {
                    message = data.detail;
                }
            } catch {
                // Resposta sem JSON.
            }

            throw new Error(message);
        }

        closeDeleteProductModal();

        await loadProducts(productSearch.value.trim());

    } catch (error) {
        deleteProductMessage.textContent = error.message;
        deleteProductMessage.className = "form-message error";

    } finally {
        confirmDeleteButton.disabled = false;
        confirmDeleteButton.textContent = "Excluir";
    }
});

function formatWeight(weight) {
    if (weight === null || weight === undefined) {
        return "—";
    }

    return `${weight} kg`;
}

function formatVolume(volume) {
    if (volume === null || volume === undefined) {
        return "—";
    }

    return `${volume} m³`;
}

let searchTimeout;

productSearch.addEventListener("input", function () {
    clearTimeout(searchTimeout);

    searchTimeout = setTimeout(() => {
        loadProducts(productSearch.value.trim());
    }, 300);
});

function openProductModal() {
    editingProductId = null;

    productForm.reset();

    productModalTitle.textContent = "Novo produto";
    saveProductButton.textContent = "Cadastrar produto";

    productFormMessage.textContent = "";
    productFormMessage.className = "form-message";

    productModal.classList.add("open");
}

function closeModal() {
    productModal.classList.remove("open");
}

newProductButton.addEventListener("click", openProductModal);
closeProductModal.addEventListener("click", closeModal);
cancelProductButton.addEventListener("click", closeModal);

productModal.addEventListener("click", function (event) {
    if (event.target === productModal) {
        closeModal();
    }
});

productForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    productFormMessage.textContent = "";
    productFormMessage.className = "form-message";

    const sku = document.getElementById("sku").value.trim();
    const name = document.getElementById("name").value.trim();
    const description = document.getElementById("description").value.trim();
    const weight = document.getElementById("weight").value;
    const volume = document.getElementById("volume").value;

    if (!sku || !name) {
        showFormError("SKU e nome são obrigatórios.");
        return;
    }

    const product = {
        sku: sku,
        name: name,
        description: description || null,
        weight: weight === "" ? null : Number(weight),
        volume: volume === "" ? null : Number(volume)
    };

    try {
        saveProductButton.disabled = true;

saveProductButton.textContent = editingProductId
    ? "Salvando..."
    : "Cadastrando...";

        const url = editingProductId
    ? `/products/${editingProductId}`
    : "/products/";

const method = editingProductId
    ? "PUT"
    : "POST";

const response = await fetch(url, {
    method: method,
    headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify(product)
});

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                typeof data.detail === "string"
                    ? data.detail
                    : "Não foi possível cadastrar o produto."
            );
        }

        closeModal();

        await loadProducts(productSearch.value.trim());

    } catch (error) {
        showFormError(error.message);

    } finally {
        saveProductButton.disabled = false;

saveProductButton.textContent = editingProductId
    ? "Salvar alterações"
    : "Cadastrar produto";
    }
});

function showFormError(message) {
    productFormMessage.textContent = message;
    productFormMessage.className = "form-message error";
}

loadProducts();