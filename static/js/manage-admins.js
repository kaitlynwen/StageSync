document.getElementById("remove-admin-button").addEventListener("click", function () {
  const checkedCheckboxes = document.querySelectorAll(".admin-checkbox:checked");
  const netidsToRemove = Array.from(checkedCheckboxes).map(cb => cb.value);

  if (netidsToRemove.length > 0) {
    const currentUserNetid = document.getElementById("current-user-netid").dataset.netid;

    if (netidsToRemove.includes(currentUserNetid)) {
      // Show confirmation modal
      const deleteModal = document.getElementById("self-remove-modal");
      deleteModal.classList.remove("hidden");
      document.body.style.overflow = 'hidden';

      document.getElementById("confirm-self-remove").onclick = function () {
        // Set value in hidden input
        document.getElementById("netids-to-remove").value = JSON.stringify(netidsToRemove);
        // Submit the form
        document.getElementById("remove-admin-form").submit();
        deleteModal.classList.add("hidden");
        document.body.style.overflow = '';
      };

      document.getElementById("cancel-self-remove").onclick = function () {
        deleteModal.classList.add("hidden");
        document.body.style.overflow = '';
      };

    } else {
      document.getElementById("netids-to-remove").value = JSON.stringify(netidsToRemove);
      document.getElementById("remove-admin-form").submit();
    }

  } else {
    flashAlert("Please select at least one user.", "error");
  }
});

document.getElementById("addAdminBtn").addEventListener("click", function (e) {
  const dropdown = document.getElementById("memberDropdown");
  const selectedValue = dropdown.value;

  if (!selectedValue) {
    e.preventDefault();
    flashAlert("Please select a member before adding.", "error");
  }
});
