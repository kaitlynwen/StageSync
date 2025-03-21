// drag-drop.js

document.addEventListener("DOMContentLoaded", function () {
    // Get file input and drop zone
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("file-input");
    const fileName = document.getElementById("file-name");
    const fileInfo = document.querySelector(".file-info");
  
    // If drop zone exists, add event listeners for drag-and-drop functionality
    if (dropZone && fileInput) {
      // Prevent default behavior for drag over
      dropZone.addEventListener("dragover", (event) => {
        event.preventDefault();
        dropZone.classList.add("border-neutral-300", "bg-pink-100");
      });
  
      // Remove styling when drag leaves the drop zone
      dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("border-neutral-300", "bg-pink-100");
      });
  
      // Handle file drop
      dropZone.addEventListener("drop", (event) => {
        event.preventDefault();
        dropZone.classList.remove("border-neutral-300", "bg-pink-100");
        const file = event.dataTransfer.files[0];
        if (file) {
          fileInput.files = event.dataTransfer.files;
          updateFileInfo();
        }
      });
    }
  
    // Function to trigger file input when drop zone is clicked
    function triggerFileInput() {
      fileInput.click();
    }
  
    // Function to update file info display
    function updateFileInfo() {
      const selectedFile = fileInput.files[0];
      if (selectedFile) {
        fileName.textContent = selectedFile.name;
        fileInfo.classList.remove("hidden");
      } else {
        fileName.textContent = "No file selected";
        fileInfo.classList.add("hidden");
      }
    }
  
    // Attach the triggerFileInput to the drop zone for clicking
    dropZone.addEventListener("click", triggerFileInput);
  });
  