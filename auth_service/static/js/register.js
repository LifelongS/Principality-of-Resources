document.addEventListener("DOMContentLoaded", () => {
    const registerForm = document.getElementById("register-form");
    const errorMessage = document.getElementById("error-message");

    registerForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirm-password").value;

        // Проверяем, что пароли совпадают
        if (password !== confirmPassword) {
            errorMessage.textContent = "Пароли не совпадают!";
            return;
        }

        try {
            const response = await fetch("/api/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                alert("Регистрация успешна! Переход на страницу входа.");
                window.location.href = data.redirect_url || "/login";
            } else {
                errorMessage.textContent = data.message || "Ошибка регистрации.";
            }
        } catch (error) {
            console.error("Ошибка при регистрации:", error);
            errorMessage.textContent = "Ошибка сервера. Попробуйте позже.";
        }
    });
});
