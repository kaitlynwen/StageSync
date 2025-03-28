// Get the modal
var modal = document.getElementById("edit-group-modal");

var modalContent = modal.querySelector(".modal-content"); // Select modal content area

// Get the button that opens the modal
var buttons = document.querySelectorAll(".edit-group-btn");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// Add click event listeners to all "Edit" buttons
buttons.forEach(function(btn) {
  btn.addEventListener("click", function() {
    var groupName = this.dataset.groupName;

    // Update modal content dynamically
    modalContent.innerHTML = `
      <span class="close">&times;</span>
      <h2 class="text-lg font-bold text-orange-500 py-4">Change Group Name:</h2>
      <input type="text" id="group-title" value="${groupName}" />
      <button id="save-group" class="bg-pink-500 hover:bg-pink-700 text-white px-2 py-1 rounded text-sm mb-2">
      Save
      </button>
    `;

    // Add event listener to close button
    modal.querySelector(".close").onclick = function() {
      modal.style.display = "none";
    };

    document.getElementById("save-group").addEventListener("click", function () {
    
      var newGroupName = document.getElementById("group-title").value;

      // Send update request to backend
      fetch("/update-group-name", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ groupName, newGroupName }),
      })
        .then(response => response.json()) // Convert response to JSON
        .then(data => {
          if (data.success) {
            alert("Group name updated successfully");
            modal.style.display = "none";
            location.reload();
          } else {
            alert("An error occured: " + data.message);
            modal.style.display = "none"; // Close modal on success
          }
        })
        .catch(error => {
          console.error("Fetch error:", error);
        });
    });
    // Show the modal
    modal.style.display = "block";
  });
});

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}