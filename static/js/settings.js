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
    const body = document.body;
  
    // --- Apply theme based on localStorage or system preference ---
    const savedTheme = localStorage.getItem("theme");
  
    if (savedTheme === "dark") {
      body.classList.add("dark");
      if (themeToggle) themeToggle.checked = true;
    } else if (!savedTheme && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      body.classList.add("dark");
      localStorage.setItem("theme", "dark");
      if (themeToggle) themeToggle.checked = true;
    }
  
    // --- Listen for toggle changes ---
    if (themeToggle) {
      themeToggle.addEventListener("change", () => {
        if (themeToggle.checked) {
          body.classList.add("dark");
          localStorage.setItem("theme", "dark");
        } else {
          body.classList.remove("dark");
          localStorage.setItem("theme", "light");
        }
      });
    }
  });
  