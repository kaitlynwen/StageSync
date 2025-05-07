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

let isSubmitting = false;

document
  .getElementById("submit-button")
  .addEventListener("click", async function (e) {
    if (isSubmitting) return;
    isSubmitting = true;

    e.preventDefault();

    const btn = e.currentTarget;
    btn.disabled = true;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = `
      <span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>
      Saving...`;
    btn.classList.add("opacity-60", "cursor-not-allowed");

    try {
      const csrfToken = document
        .querySelector('meta[name="csrf-token"]')
        .getAttribute("content");

      const form = btn.closest("form");
      const formData = new FormData(form);

      const response = await fetch(form.action || "/update-settings", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Server error: " + response.status);
      }

      flashAndReload("Notification preferences saved!", "success");
    } catch (error) {
      console.error(error);
      flashAlert("Failed to save preferences.", "error");
      btn.disabled = false;
      btn.innerHTML = originalHTML;
      isSubmitting = false;
    }
  });
