  // Make alerts disappear after 5 seconds (5000ms)
  setTimeout(() => {
    document.querySelectorAll(".alert").forEach((alert) => {
      alert.style.opacity = "0";
      setTimeout(() => alert.remove(), 500);
    });
  }, 5000);