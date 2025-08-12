document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");

    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (response.ok) {
                // Сохраняем токен
                localStorage.setItem("jwt", data.access_token);
                document.cookie = `access_token=${data.access_token}; path=/`;

                // Перенаправляем на GameService
                window.location.href = data.redirect_url;
            } else {
                document.getElementById("error-message").textContent = data.message || "Ошибка входа";
            }
        } catch (error) {
            console.error("Ошибка запроса:", error);
        }
    });
});
