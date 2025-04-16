document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.getElementById("theme-toggle");
  const html = document.documentElement;

  const savedTheme = localStorage.getItem("theme");

  if (savedTheme === "dark") {
    html.classList.add("dark");
    if (themeToggle) themeToggle.checked = true;
  } else if (savedTheme === "light") {
    html.classList.remove("dark");
    if (themeToggle) themeToggle.checked = false;
  } else {
    const prefersDark = window.matchMedia(
      "(prefers-color-scheme: dark)"
    ).matches;
    if (prefersDark) {
      html.classList.add("dark");
      if (themeToggle) themeToggle.checked = true;
    } else {
      html.classList.remove("dark");
      if (themeToggle) themeToggle.checked = false;
    }
  }

  if (themeToggle) {
    themeToggle.addEventListener("change", () => {
      if (themeToggle.checked) {
        html.classList.add("dark");
        localStorage.setItem("theme", "dark");
      } else {
        html.classList.remove("dark");
        localStorage.setItem("theme", "light");
      }
    });
  }
});
