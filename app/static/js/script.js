document.addEventListener("DOMContentLoaded", () => {
    const tabLinks = document.querySelectorAll(".tab-link"); // Кнопки вкладок
    const tabContents = document.querySelectorAll(".tab-content"); // Секции с контентом

    tabLinks.forEach((link) => {
        link.addEventListener("click", () => {
            // Убираем активный класс у всех вкладок и контента
            tabLinks.forEach((tab) => tab.classList.remove("active"));
            tabContents.forEach((content) => content.classList.remove("active"));

            // Добавляем активный класс к текущей вкладке и её контенту
            link.classList.add("active");
            const targetTab = document.getElementById(link.dataset.tab);
            targetTab.classList.add("active");
        });
    });
});
