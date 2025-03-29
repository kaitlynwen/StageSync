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