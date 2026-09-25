const passwordInput = document.getElementById("password");
const passwordToggle = document.getElementById("passwordToggle");
const eyeOpen = document.getElementById("eyeOpen");
const eyeClosed = document.getElementById("eyeClosed");
const loginForm = document.querySelector(".login-form");
const loginMessage = document.getElementById("loginMessage");

if (passwordToggle) {
    passwordToggle.addEventListener("click", function () {
        const passwordIsHidden = passwordInput.type === "password";

        if (passwordIsHidden) {
            passwordInput.type = "text";
            eyeOpen.classList.add("hidden");
            eyeClosed.classList.remove("hidden");
            passwordToggle.setAttribute("aria-label", "Ocultar senha");
        } else {
            passwordInput.type = "password";
            eyeOpen.classList.remove("hidden");
            eyeClosed.classList.add("hidden");
            passwordToggle.setAttribute("aria-label", "Mostrar senha");
        }
    });
}

function showLoginError(message) {
    let box = document.getElementById("login-error");
    if (!box) {
        box = document.createElement("p");
        box.id = "login-error";
        box.style.color = "#b42318";
        box.style.marginTop = "12px";
        box.style.fontSize = "0.9rem";
        loginForm.appendChild(box);
    }
    box.textContent = message;
}

if (loginForm) {
    loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    loginMessage.textContent = "";

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Não foi possível realizar o login."
            );
        }

        localStorage.setItem("access_token", data.access_token);

        window.location.href = "/dashboard";

    } catch (error) {
        loginMessage.textContent = error.message;
    }
});
}
