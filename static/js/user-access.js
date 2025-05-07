// dealing with requests to remove admins
document
  .getElementById("unauthorize-button")
  .addEventListener("click", function () {
    // Get all checked checkboxes
    const checkedCheckboxes = document.querySelectorAll(
      ".member-checkbox:checked"
    );

    const button = this;

    // Get CSRF token for validation
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

    // Create an array of netid values of selected users
    const netidsToRemove = Array.from(checkedCheckboxes).map(
      (checkbox) => checkbox.value
    );

    // console.log("NetIDs:", netidsToRemove); for testing

    if (netidsToRemove.length === 0) {
      flashAlert("Please select at least one user.", "error");
      return;
    }

    const currentUserNetid = document.getElementById("current-user-netid").dataset.netid;

    if (netidsToRemove.includes(currentUserNetid)) {
      // Show confirmation modal
      const deleteModal = document.getElementById("self-remove-modal");
      deleteModal.classList.remove("hidden");
      document.body.style.overflow = 'hidden'; 

      // When confirm button is clicked
      document.getElementById("confirm-self-remove").onclick = function () {
        button.disabled = true;
        button.classList.add('opacity-60', 'cursor-not-allowed');
        button.innerHTML = `<span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>Removing...`;
        
        fetch("/unauthorize", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({ netids: netidsToRemove }),
        })
          .then((response) => response.json())
          .then(() => {
            location.reload(); // Reload the page to reflect changes
          })
          .catch((error) => {
            console.error("Error:", error);
            flashAlert("An error occurred. Please try again.", "error");
          });
        deleteModal.classList.add("hidden");
        document.body.style.overflow = '';
      };

      document.getElementById("cancel-self-remove").onclick = function () {
        deleteModal.classList.add("hidden");
        document.body.style.overflow = '';
      };
    } else {
      button.disabled = true;
      button.classList.add('opacity-60', 'cursor-not-allowed');
      button.innerHTML = `<span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>Removing...`;
        
      fetch("/unauthorize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ netids: netidsToRemove }),
      })
        .then((response) => response.json())
        .then(() => {
          location.reload(); // Reload the page to reflect changes
        })
        .catch((error) => {
          console.error("Error:", error);
          flashAlert("An error occurred. Please try again.", "error");
        });
    }
  });

// dealing with requests to authorize new netids
document
  .getElementById("authorize-form")
  .addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent the form from submitting normally

    const netid = document.getElementById("netid").value.trim();
    const button = document.getElementById("authorizeBtn");

    // Get CSRF token for validation
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

    if (netid) {
      // Send a request to add the user as an admin
      button.disabled = true;
      button.classList.add('opacity-60', 'cursor-not-allowed');
      button.innerHTML = `<span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>Adding...`;
      fetch("/authorize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ netid: netid }),
      })
        .then((response) => response.json())
        .then(() => {
          location.reload(); // Reload the page to reflect changes
        })
        .catch((error) => {
          console.error("Error:", error);
          flashAlert("An error occurred. Please try again.", "error");
        });
    } else {
      flashAlert("Please enter a valid NetID.", "error");
    }
  });
