document.addEventListener("DOMContentLoaded", () => {
    function getToken() {
        return localStorage.getItem('jwt') || 
               document.cookie.replace(/(?:(?:^|.*;\s*)access_token\s*=\s*([^;]*).*$)|^.*$/, '$1');
    }

    async function loadResources() {
        try {
            const response = await fetch('/resources', {
                headers: { 'Authorization': `Bearer ${getToken()}` }
            });

            if (response.ok) {
                const data = await response.json();
                document.getElementById('wood').textContent = data.wood;
                document.getElementById('stone').textContent = data.stone;
                document.getElementById('gold').textContent = data.gold;
            }
        } catch (error) {
            console.error('Ошибка загрузки ресурсов:', error);
        }
    }

    document.getElementById('collect-btn').addEventListener('click', async () => {
        try {
            const response = await fetch('/collect_resources', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${getToken()}`,
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();
            if (response.ok) {
                document.getElementById('wood').textContent = result.resources.wood;
                document.getElementById('stone').textContent = result.resources.stone;
                document.getElementById('gold').textContent = result.resources.gold;
                document.getElementById('message').textContent = 'Ресурсы собраны!';
            } else {
                document.getElementById('message').textContent = result.message || 'Ошибка';
            }
        } catch (error) {
            console.error('Ошибка:', error);
        }
    });


    loadResources();
});
