function showTab(tab) {
    // Hide all tab contents
    document.getElementById("notifications-content").classList.add("hidden");
    document.getElementById("appearance-content").classList.add("hidden");

    // Remove active styles from both tabs
    document.getElementById("notifications").classList.remove("border-indigo-500", "text-indigo-500");
    document.getElementById("notifications").classList.add("border-transparent", "text-neutral-500", "dark:text-neutral-200");

    document.getElementById("appearance").classList.remove("border-indigo-500", "text-indigo-500");
    document.getElementById("appearance").classList.add("border-transparent", "text-neutral-500", "dark:text-neutral-200");

    // Show the selected tab content
    document.getElementById(`${tab}-content`).classList.remove("hidden");

    // Apply active styles to the selected tab
    document.getElementById(`${tab}`).classList.add("border-indigo-500", "text-indigo-500");
    document.getElementById(`${tab}`).classList.remove("border-transparent", "text-neutral-500", "dark:text-neutral-200");
  }
  
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
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
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
  