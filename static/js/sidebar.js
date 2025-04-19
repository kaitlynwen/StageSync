const toggleButton = document.querySelector(
  '[data-drawer-toggle="logo-sidebar"]'
);
const sidebar = document.getElementById("logo-sidebar");

toggleButton?.addEventListener("click", () => {
  sidebar.classList.toggle("-translate-x-full");
});
