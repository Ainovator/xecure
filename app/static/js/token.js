const CHECK_INTERVAL = 120000;

function checkSession() {
    const userRole = document.getElementById('user-role').getAttribute('data-role');

    // Если пользователь - администратор, пропускаем проверку сессии
    if (userRole === 'admin') {
        console.log('Пользователь — администратор, сессия не проверяется.');
        return;
    }

    // Иначе выполняем проверку сессии
    fetch('/check-session', { method: 'GET' })
        .then(response => {
            if (!response.ok) {
                // Если токен истек, перенаправляем пользователя на страницу входа
                alert('Сессия истекла. Вы будете перенаправлены на страницу входа.');
                window.location.href = '/login';
            }
        })
        .catch(error => {
            console.error('Ошибка проверки сессии:', error);
        });
}

setInterval(checkSession, CHECK_INTERVAL);
