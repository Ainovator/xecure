document.addEventListener("DOMContentLoaded", () => {
    const tabLinks = document.querySelectorAll(".tab-link");
    const tabContents = document.querySelectorAll(".tab-content");
  
    tabLinks.forEach((link) => {
      link.addEventListener("click", () => {
        tabLinks.forEach((tab) => tab.classList.remove("active"));
        tabContents.forEach((content) => content.classList.remove("active"));
  
        link.classList.add("active");
        const targetTab = document.getElementById(link.dataset.tab);
        targetTab.classList.add("active");
      });
    });
  });
  