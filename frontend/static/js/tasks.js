
const tasksTableBody = document.getElementById("tasksTableBody");
const taskSearch = document.getElementById("taskSearch");
const taskTypeFilter = document.getElementById("taskTypeFilter");
const taskStatusFilter = document.getElementById("taskStatusFilter");

const newTaskButton = document.getElementById("newTaskButton");
const taskModal = document.getElementById("taskModal");
const closeTaskModalButton = document.getElementById("closeTaskModal");
const cancelTaskButton = document.getElementById("cancelTaskButton");

const taskForm = document.getElementById("taskForm");
const taskType = document.getElementById("taskType");
const taskOrder = document.getElementById("taskOrder");
const taskOperator = document.getElementById("taskOperator");
const taskFormMessage = document.getElementById("taskFormMessage");

const token = localStorage.getItem("access_token");
let tasksData = [];

let taskUsersData = [];

function formatTaskDate(date, showTime = false) {
    if (!date) return "—";

    const dateWithTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(date)
        ? date
        : `${date}Z`;

    const options = {
        timeZone: "America/Recife",
        day: "2-digit",
        month: "2-digit",
        year: "numeric"
    };

    if (showTime) {
        options.hour = "2-digit";
        options.minute = "2-digit";
        options.second = "2-digit";
    }

    return new Date(dateWithTimezone).toLocaleString("pt-BR", options);
}

function getTaskOperatorName(userId) {
    if (userId == null) {
        return "Não atribuído";
    }

    const user = taskUsersData.find(
        item => Number(item.id) === Number(userId)
    );

    return user
        ? (user.name || user.email || `Usuário #${userId}`)
        : `Usuário #${userId}`;
}

const taskTypes = {
    PICKING: "Separação",
    PUTAWAY: "Armazenamento",
    REPLENISHMENT: "Reposição"
};

const taskStatuses = {
    PENDING: "Pendente",
    IN_PROGRESS: "Em andamento",
    COMPLETED: "Concluída"
};

function renderTasks() {
    const search = taskSearch.value.trim().toLowerCase();
    const type = taskTypeFilter.value;
    const status = taskStatusFilter.value;

    const filteredTasks = tasksData.filter(task => {
        const matchesSearch =
            String(task.id).includes(search) ||
            String(task.order_id).includes(search);

        return matchesSearch &&
            (!type || task.type === type) &&
            (!status || task.status === status);
    });

    if (filteredTasks.length === 0) {
        tasksTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="tasks-loading">
                    Nenhuma tarefa encontrada.
                </td>
            </tr>
        `;
        return;
    }

    tasksTableBody.innerHTML = filteredTasks.map(task => `
        <tr>
            <td data-label="Tarefa">#${task.id}</td>
            <td data-label="Tipo">
                ${taskTypes[task.type] || task.type}
            </td>
            <td data-label="Pedido">#${task.order_id}</td>
            <td data-label="Operador">
                ${getTaskOperatorName(task.assigned_user_id)}
            </td>
            <td data-label="Status">
                ${taskStatuses[task.status] || task.status}
            </td>
            <td data-label="Data">
                ${formatTaskDate(task.created_at)}
            </td>
            
            <td data-label="Ações">
                <div class="task-actions">
                    <button
                        type="button"
                        class="task-details-button"
                        data-id="${task.id}"
                    >
                        Detalhes
                    </button>

                    <button
                        type="button"
                        class="task-edit-button"
                        data-id="${task.id}"
                    >
                        Editar
                    </button>
                </div>
            </td>
        </tr>
    `).join("");
}

async function loadTasks() {
    try {
        const response = await fetch("/tasks/", {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(
                typeof error.detail === "string"
                    ? error.detail
                    : "Não foi possível carregar as tarefas."
            );
        }

        tasksData = await response.json();

        try {
            const usersResponse = await fetch("/users/", {
                headers: {
                    Authorization: `Bearer ${token}`
                }
            });

            if (usersResponse.status === 401) {
                window.location.href = "/login";
                return;
            }

            if (usersResponse.ok) {
                taskUsersData = await usersResponse.json();
            } else {
                taskUsersData = [];
            }
        } catch (error) {
            taskUsersData = [];
        }

        renderTasks();

    } catch (error) {
        tasksTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="tasks-loading"></td>
            </tr>
        `;
        tasksTableBody.querySelector("td").textContent = error.message;
    }
}

taskSearch.addEventListener("input", renderTasks);
taskTypeFilter.addEventListener("change", renderTasks);
taskStatusFilter.addEventListener("change", renderTasks);

async function loadTaskFormData() {
    const headers = {
        Authorization: `Bearer ${token}`
    };

    const [ordersResponse, usersResponse] = await Promise.all([
        fetch("/orders/", { headers }),
        fetch("/users/", { headers })
    ]);

    if (ordersResponse.status === 401 || usersResponse.status === 401) {
        window.location.href = "/login";
        return false;
    }

    if (!ordersResponse.ok || !usersResponse.ok) {
        const failedResponse = !ordersResponse.ok
            ? ordersResponse
            : usersResponse;

        const error = await failedResponse.json();

        throw new Error(
            typeof error.detail === "string"
                ? error.detail
                : "Não foi possível carregar pedidos e usuários."
        );
    }

    const orders = await ordersResponse.json();
    const users = await usersResponse.json();

    taskOrder.innerHTML = '<option value="">Selecione o pedido</option>';

    orders.forEach(order => {
        const option = document.createElement("option");
        option.value = order.id;
        option.textContent = `Pedido #${order.id}`;
        taskOrder.appendChild(option);
    });

    taskOperator.innerHTML =
        '<option value="">Sem operador atribuído</option>';

    users.forEach(user => {
        const option = document.createElement("option");
        option.value = user.id;
        option.textContent = user.name || user.email || `Usuário #${user.id}`;
        taskOperator.appendChild(option);
    });

    return true;
}

function closeTaskModal() {
    taskModal.classList.remove("open");
    taskForm.reset();
    taskFormMessage.textContent = "";
    taskFormMessage.className = "task-form-message";
}

newTaskButton.addEventListener("click", async () => {
    taskForm.reset();
    taskFormMessage.textContent = "";
    taskFormMessage.className = "task-form-message";
    taskModal.classList.add("open");

    try {
        await loadTaskFormData();
    } catch (error) {
        taskFormMessage.textContent = error.message;
        taskFormMessage.className = "task-form-message error";
    }
});

closeTaskModalButton.addEventListener("click", closeTaskModal);
cancelTaskButton.addEventListener("click", closeTaskModal);

taskModal.addEventListener("click", event => {
    if (event.target === taskModal) {
        closeTaskModal();
    }
});

taskForm.addEventListener("submit", async event => {
    event.preventDefault();

    taskFormMessage.textContent = "";
    taskFormMessage.className = "task-form-message";

    const orderId = Number(taskOrder.value);
    const operatorId = taskOperator.value
        ? Number(taskOperator.value)
        : null;

    if (!taskType.value || !orderId) {
        taskFormMessage.textContent =
            "Selecione o tipo da tarefa e o pedido.";
        taskFormMessage.className = "task-form-message error";
        return;
    }

    const payload = {
        type: taskType.value,
        status: "PENDING",
        order_id: orderId,
        assigned_user_id: operatorId
    };

    try {
        const response = await fetch("/tasks/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        if (!response.ok) {
            const error = await response.json();

            throw new Error(
                typeof error.detail === "string"
                    ? error.detail
                    : "Não foi possível criar a tarefa."
            );
        }

        closeTaskModal();
        await loadTasks();

    } catch (error) {
        taskFormMessage.textContent = error.message;
        taskFormMessage.className = "task-form-message error";
    }
});


// Detalhes da tarefa

const taskDetailsModal = document.getElementById("taskDetailsModal");

function closeTaskDetailsModal() {
    taskDetailsModal.classList.remove("open");
}

async function openTaskDetails(taskId) {
    try {
        const response = await fetch(`/tasks/${taskId}`, {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(
                typeof error.detail === "string"
                    ? error.detail
                    : "Não foi possível carregar os detalhes."
            );
        }

        const task = await response.json();

        document.getElementById("taskDetailsTitle").textContent =
            `Tarefa #${task.id}`;

        document.getElementById("detailTaskType").textContent =
            taskTypes[task.type] || task.type;

        document.getElementById("detailTaskOrder").textContent =
            `Pedido #${task.order_id}`;

        document.getElementById("detailTaskOperator").textContent =
            getTaskOperatorName(task.assigned_user_id);

        document.getElementById("detailTaskStatus").textContent =
            taskStatuses[task.status] || task.status;

        document.getElementById("detailTaskDate").textContent =
            formatTaskDate(task.created_at, true);

        taskDetailsModal.classList.add("open");

    } catch (error) {
        alert(error.message);
    }
}

tasksTableBody.addEventListener("click", event => {
    const button = event.target.closest(".task-details-button");

    if (button) {
        openTaskDetails(button.dataset.id);
    }
});

document.getElementById("closeTaskDetails")
    .addEventListener("click", closeTaskDetailsModal);

document.getElementById("closeTaskDetailsButton")
    .addEventListener("click", closeTaskDetailsModal);

taskDetailsModal.addEventListener("click", event => {
    if (event.target === taskDetailsModal) {
        closeTaskDetailsModal();
    }
});


// Edição de tarefas

const taskEditModal = document.getElementById("taskEditModal");
const taskEditForm = document.getElementById("taskEditForm");
const taskEditTitle = document.getElementById("taskEditTitle");
const editTaskStatus = document.getElementById("editTaskStatus");
const editTaskOperator = document.getElementById("editTaskOperator");
const taskEditMessage = document.getElementById("taskEditMessage");

let editingTaskId = null;

function closeTaskEditModal() {
    taskEditModal.classList.remove("open");
    taskEditForm.reset();
    editingTaskId = null;
    taskEditMessage.textContent = "";
    taskEditMessage.className = "task-form-message";
}

async function openTaskEditModal(taskId) {
    const task = tasksData.find(
        item => Number(item.id) === Number(taskId)
    );

    if (!task) return;

    editingTaskId = task.id;
    taskEditTitle.textContent = `Editar tarefa #${task.id}`;
    editTaskStatus.value = task.status;

    taskEditMessage.textContent = "";
    taskEditMessage.className = "task-form-message";

    editTaskOperator.innerHTML =
        '<option value="">Carregando usuários...</option>';

    taskEditModal.classList.add("open");

    try {
        const response = await fetch("/users/", {
            headers: {
                Authorization: `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        if (!response.ok) {
            const error = await response.json();

            throw new Error(
                typeof error.detail === "string"
                    ? error.detail
                    : "Não foi possível carregar os usuários."
            );
        }

        const users = await response.json();

        editTaskOperator.innerHTML =
            '<option value="">Sem operador atribuído</option>';

        users.forEach(user => {
            const option = document.createElement("option");
            option.value = user.id;
            option.textContent =
                user.name || user.email || `Usuário #${user.id}`;

            editTaskOperator.appendChild(option);
        });

        editTaskOperator.value =
            task.assigned_user_id == null
                ? ""
                : String(task.assigned_user_id);

    } catch (error) {
        taskEditMessage.textContent = error.message;
        taskEditMessage.className = "task-form-message error";
        editTaskOperator.innerHTML =
            '<option value="">Não foi possível carregar usuários</option>';
    }
}

// Aproveita o listener da tabela para identificar o botão Editar.
tasksTableBody.addEventListener("click", event => {
    const button = event.target.closest(".task-edit-button");

    if (button) {
        openTaskEditModal(button.dataset.id);
    }
});

document.getElementById("closeTaskEdit")
    .addEventListener("click", closeTaskEditModal);

document.getElementById("cancelTaskEdit")
    .addEventListener("click", closeTaskEditModal);

taskEditModal.addEventListener("click", event => {
    if (event.target === taskEditModal) {
        closeTaskEditModal();
    }
});

taskEditForm.addEventListener("submit", async event => {
    event.preventDefault();

    if (editingTaskId === null) return;

    taskEditMessage.textContent = "";
    taskEditMessage.className = "task-form-message";

    const payload = {
        status: editTaskStatus.value,
        assigned_user_id: editTaskOperator.value
            ? Number(editTaskOperator.value)
            : null
    };

    const submitButton = taskEditForm.querySelector(
        'button[type="submit"]'
    );

    submitButton.disabled = true;

    try {
        const response = await fetch(`/tasks/${editingTaskId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (response.status === 401) {
            window.location.href = "/login";
            return;
        }

        if (!response.ok) {
            const error = await response.json();

            throw new Error(
                typeof error.detail === "string"
                    ? error.detail
                    : "Não foi possível atualizar a tarefa."
            );
        }

        closeTaskEditModal();
        await loadTasks();

    } catch (error) {
        taskEditMessage.textContent = error.message;
        taskEditMessage.className = "task-form-message error";

    } finally {
        submitButton.disabled = false;
    }
});



loadTasks();
