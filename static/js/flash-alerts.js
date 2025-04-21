// Make alerts disappear after 5 seconds (5000ms)
setTimeout(() => {
  document.querySelectorAll(".alert").forEach((alert) => {
    alert.style.opacity = "0";
    setTimeout(() => alert.remove(), 500);
  });
}, 5000);

function flashAlert(message, category = "info", duration = 3000) {
  // Ensure the alert container exists
  let container = document.getElementById("alert-container");
  if (!container) {
    // If not, create and append it
    container = document.createElement("div");
    container.id = "alert-container";
    container.className =
      "flex flex-col fixed top-4 right-4 space-y-2 z-50 w-1/4";
    document.body.appendChild(container);
  }

  const iconMap = {
    success: "bxs-check-circle",
    error: "bxs-error",
    warning: "bxs-error-circle",
    info: "bxs-info-circle",
  };

  const colorMap = {
    success: "bg-green-100 border-green-400 text-green-700",
    error: "bg-red-100 border-red-400 text-red-700",
    warning: "bg-yellow-100 border-yellow-400 text-yellow-700",
    info: "bg-blue-100 border-blue-400 text-blue-700",
  };

  const alert = document.createElement("div");
  alert.className = `alert px-4 py-3 rounded-md relative transition-opacity duration-300 opacity-100 border ${
    colorMap[category] || colorMap.info
  }`;
  alert.setAttribute("role", "alert");

  alert.innerHTML = `
        <div class="flex justify-between items-center">
          <strong class="font-bold flex items-center">
            <i class="bx ${iconMap[category] || iconMap.info} bx-sm mr-2"></i>
            ${category.charAt(0).toUpperCase() + category.slice(1)}!
          </strong>
          <button onclick="this.parentElement.parentElement.remove()" class="flex hover:opacity-75">
            <i class="bx bx-x bx-sm"></i>
          </button>
        </div>
        <span class="block sm:inline">${message}</span>
      `;

  container.appendChild(alert);

  if (duration > 0) {
    setTimeout(() => {
      alert.classList.add("opacity-0");
      setTimeout(() => alert.remove(), 300);
    }, duration);
  }
}

function flashAndReload(message, type) {
  flashAlert(message, type);
  setTimeout(() => location.reload(), 600);
}