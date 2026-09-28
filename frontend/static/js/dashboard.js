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