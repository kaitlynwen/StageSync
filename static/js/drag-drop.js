document.getElementById("dropzone-file").addEventListener("change", function(event) {
  const file = event.target.files[0]; 
  const maxSize = 5 * 1024 * 1024; // 5MB limit

  if (file) {
    if (!["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "text/csv"].includes(file.type)) {
      alert("Invalid file type. Only XSLX or CSV allowed.");
      event.target.value = ""; // Reset file input
    } else if (file.size > maxSize) {
      alert("File size exceeds 5MB. Please upload a smaller file.");
      event.target.value = "";
    }
  }
});

document.addEventListener("DOMContentLoaded", function () {
  const fileInput = document.getElementById("dropzone-file");
  const dropzoneLabel = document.getElementById("dropzone-label");
  const dropzoneContent = document.getElementById("dropzone-content");
  const fileNameDisplay = document.getElementById("file-name");

  fileInput.addEventListener("change", function () {
    if (fileInput.files.length > 0) {
      const fileName = fileInput.files[0].name;

      // Update the UI to show the selected file
      dropzoneContent.innerHTML = `<p class="text-sm font-semibold text-green-600">Selected: ${fileName}</p>`;
      fileNameDisplay.textContent = `📂 ${fileName}`;
      fileNameDisplay.classList.remove("hidden");
    }
  });
});

// Make alerts disappear after 5 seconds (5000ms)
setTimeout(() => {
  document.querySelectorAll(".alert").forEach((alert) => {
    alert.style.opacity = "0";
    setTimeout(() => alert.remove(), 500); // Smooth removal after fading out
  });
}, 5000);