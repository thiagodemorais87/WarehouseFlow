const passwordInput = document.getElementById("password");
const passwordToggle = document.getElementById("passwordToggle");

const eyeOpen = document.getElementById("eyeOpen");
const eyeClosed = document.getElementById("eyeClosed");

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