document.addEventListener("DOMContentLoaded", function () {
  const dropzone = document.getElementById("dropzone-label");
  const fileInput = document.getElementById("dropzone-file");
  const dropzoneContent = document.getElementById("dropzone-content");

  const maxSize = 5 * 1024 * 1024; // 5MB limit
  const allowedTypes = [
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  ];

  let isSubmitting = false; // To track if the form is submitting

  // Handle manual file selection (click)
  fileInput.addEventListener("change", function () {
    if (!isSubmitting) {
      handleFile(fileInput.files[0]);
    }
  });

  // Prevent default drag behaviors only when submitting
  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropzone.addEventListener(eventName, (event) => {
      if (isSubmitting) {
        event.preventDefault(); // Prevent the drag-and-drop if submitting
      }
    });
  });

  // Highlight dropzone when file is dragged over
  ["dragenter", "dragover"].forEach((eventName) => {
    dropzone.addEventListener(eventName, () => {
      if (!isSubmitting) {
        dropzone.classList.add("border-indigo-500", "bg-neutral-100");
      }
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
    if (isSubmitting) return; // Prevent dropping files during submission

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
      flashAlert("Invalid file type. Only XLSX allowed.", "error");
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

  const uploadForm = document.getElementById("upload-form");

  // Save the initial dropzone HTML for reset
  const originalDropzoneContent = dropzoneContent.innerHTML;

  // Reset dropzone on form reset
  uploadForm.addEventListener("reset", function () {
    // Reset dropzone HTML
    dropzoneContent.innerHTML = originalDropzoneContent;

    // Also hide the file name display (if visible)
    document.getElementById("file-name").classList.add("hidden");
    document.getElementById("file-name").textContent = "";

    // Re-enable the file input and dropzone interactions
    fileInput.disabled = false;
    dropzone.removeEventListener("click", disableClick);
  });

  const discardBtn = document.getElementById("discardBtn");
  const submitBtn = document.getElementById("submitBtn");

  // Disable click interaction during submission
  function disableClick(event) {
    if (isSubmitting) {
      event.preventDefault(); // Prevent file selection when submitting
    }
  }

  uploadForm.addEventListener("submit", function () {
    // Disable buttons
    discardBtn.disabled = true;
    submitBtn.disabled = true;

    isSubmitting = true;

    // Disable the click on the dropzone
    dropzone.addEventListener("click", disableClick);

    discardBtn.classList.add("opacity-60", "cursor-not-allowed");
    submitBtn.classList.add("opacity-60", "cursor-not-allowed");

    submitBtn.innerHTML = `
      <span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>
      Uploading...
    `;
  });
});
