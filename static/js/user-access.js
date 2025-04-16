// dealing with requests to remove admins
document
  .getElementById("unauthorize-button")
  .addEventListener("click", function () {
    // Get all checked checkboxes
    const checkedCheckboxes = document.querySelectorAll(
      ".member-checkbox:checked"
    );

    // Create an array of netid values of selected users
    const netidsToRemove = Array.from(checkedCheckboxes).map(
      (checkbox) => checkbox.value
    );

    // console.log("NetIDs:", netidsToRemove); for testing

    if (netidsToRemove.length > 0) {
      // Send the data to the server (via AJAX or form submission)
      fetch("/unauthorize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ netids: netidsToRemove }),
      })
        .then((response) => response.json())
        .then((data) => {

          // console.log("Data:", data); for testing

          if (data.success) {
            alert("Selected Members Unauthorized successfully");
            location.reload(); // Reload the page to reflect changes
          } else {
            alert("An error occurred: " + data.message);
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          alert("An error occurred. Please try again.");
        });
    } else {
      alert("Please select at least one user.");
    }
  });

// dealing with requests to add admins
document
  .getElementById("authorize-form")
  .addEventListener("submit", function (event) {
    event.preventDefault(); // Prevent the form from submitting normally

    const netid = document.getElementById("netid").value.trim();

    if (netid) {
      // Send a request to add the user as an admin
      fetch("/authorize", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ netid: netid }),
      })
        .then((response) => response.json())
        .then((data) => {
          if (data.success) {
            // Adding multiple members and alerting may be tedious
            // alert("User has been added as an admin successfully!");
            location.reload(); // Reload the page to reflect the changes
          } else {
            alert("An error occurred: " + data.message);
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          alert("An error occurred. Please try again.");
        });
    } else {
      alert("Please enter a valid NetID.");
    }
  });
