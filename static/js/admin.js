document.addEventListener("DOMContentLoaded", function () {
    // Get CSS variables from :root
    function getCSSVariable(name) {
      return getComputedStyle(document.documentElement)
        .getPropertyValue(name)
        .trim();
    }
  
    // Example usage
    let primaryColor = getCSSVariable("--primary");
    let secondaryColor = getCSSVariable("--secondary");
  
    // Initialize FullCalendar
    var calendarEl = document.getElementById("calendar");
    if (!calendarEl) return;
  
    let userRole = "admin"; // Change dynamically based on logged-in user
  
    var calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: "timeGridWeek",
      headerToolbar: { center: "dayGridMonth,timeGridWeek,timeGridDay" },
      events: [
        {
          title: "Rehearsal 1",
          start: "2025-03-16T10:00:00",
          end: "2025-03-16T12:00:00",
        },
        {
          title: "Rehearsal 2",
          start: "2025-03-18T14:00:00",
          end: "2025-03-18T16:00:00",
        },
        {
          title: "Social Event",
          start: "2025-03-20T14:00:00",
          end: "2025-03-20T16:00:00",
        },
      ],
      eventColor: secondaryColor,
      editable: userRole === "admin",
      droppable: userRole === "admin",
      eventClick: function (info) {
        alert(
          userRole !== "admin"
            ? "You do not have permission to edit this event"
            : "You can edit this event"
        );
      },
    });
  
    calendar.render();
  
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
        dropZone.classList.add("border-pink-500", "bg-pink-100");
      });
  
      // Remove styling when drag leaves the drop zone
      dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("border-pink-500", "bg-pink-100");
      });
  
      // Handle file drop
      dropZone.addEventListener("drop", (event) => {
        event.preventDefault();
        dropZone.classList.remove("border-pink-500", "bg-pink-100");
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

  // dealing with requests to remove admins
  document.getElementById('remove-admin-button').addEventListener('click', function() {
    // Get all checked checkboxes
    const checkedCheckboxes = document.querySelectorAll('.admin-checkbox:checked');
    
    // Create an array of netid values of selected users
    const netidsToRemove = Array.from(checkedCheckboxes).map(checkbox => checkbox.value);

    if (netidsToRemove.length > 0) {
        // Send the data to the server (via AJAX or form submission)
        fetch('/remove-admins', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ netids: netidsToRemove }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Admin permissions removed successfully');
                location.reload();  // Reload the page to reflect changes
            } else {
                alert('An error occurred. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred. Please try again.');
        });
    } else {
        alert('Please select at least one user.');
    }
});

// dealing with requests to add admins
document.getElementById('add-admin-form').addEventListener('submit', function(event) {
  event.preventDefault();  // Prevent the form from submitting normally
  
  const netid = document.getElementById('netid').value.trim();

  if (netid) {
      // Send a request to add the user as an admin
      fetch('/add-admin', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify({ netid: netid }),
      })
      .then(response => response.json())
      .then(data => {
          if (data.success) {
              alert('User has been added as an admin successfully!');
              location.reload();  // Reload the page to reflect the changes
          } else {
              alert('An error occurred: ' + data.message);
          }
      })
      .catch(error => {
          console.error('Error:', error);
          alert('An error occurred. Please try again.');
      });
  } else {
      alert('Please enter a valid NetID.');
  }
});