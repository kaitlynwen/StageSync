document.addEventListener("DOMContentLoaded", function () {
  const dropzone = document.getElementById("dropzone-label");
  const fileInput = document.getElementById("dropzone-file");
  const dropzoneContent = document.getElementById("dropzone-content");

  const maxSize = 5 * 1024 * 1024; // 5MB limit
  const allowedTypes = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv",
  ];

  // Handle manual file selection (click)
  fileInput.addEventListener("change", function () {
    handleFile(fileInput.files[0]);
  });

  // Prevent default drag behaviors
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => event.preventDefault());
  });

  // Highlight dropzone when file is dragged over
  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, () => {
      dropzone.classList.add("border-indigo-500", "bg-neutral-100");
    });
  });

  // Remove highlight when dragging ends
  ["dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, () => {
      dropzone.classList.remove("border-indigo-500", "bg-neutral-100");
    });
  });

  // Handle dropped files
  dropzone.addEventListener("drop", (event) => {
    const file = event.dataTransfer.files[0]; // Get the dropped file
    if (file) {
      handleFile(file);

      // Assign the dropped file to the hidden file input
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      fileInput.files = dataTransfer.files;
    }
  });

  function handleFile(file) {
    if (!file) return;

    if (!allowedTypes.includes(file.type)) {
      flashAlert("Invalid file type. Only XLSX or CSV allowed.", "error");
      return;
    }

    if (file.size > maxSize) {
      flashAlert(
        "File size exceeds 5MB. Please upload a smaller file.",
        "error"
      );
      return;
    }

    // Update UI to show selected file name
    dropzoneContent.innerHTML = `<p class="text-sm font-semibold text-green-600">Selected: ${file.name}</p>`;
  }
});