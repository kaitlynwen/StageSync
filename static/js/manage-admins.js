// dealing with requests to remove admins
document
  .getElementById("remove-admin-button")
  .addEventListener("click", function () {
    // Get all checked checkboxes
    const checkedCheckboxes = document.querySelectorAll(
      ".admin-checkbox:checked"
    );

    // Create an array of netid values of selected users
    const netidsToRemove = Array.from(checkedCheckboxes).map(
      (checkbox) => checkbox.value
    );

    // console.log("NetIDs:", netidsToRemove); for testing

    if (netidsToRemove.length > 0) {
      // Send the data to the server (via AJAX or form submission)
      fetch("/remove-admins", {
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
            alert("Admin permissions removed successfully");
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