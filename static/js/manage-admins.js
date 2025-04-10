document.getElementById("remove-admin-button").addEventListener("click", function () {
  const checkedCheckboxes = document.querySelectorAll(".admin-checkbox:checked");
  const netidsToRemove = Array.from(checkedCheckboxes).map(cb => cb.value);

  if (netidsToRemove.length > 0) {
    // Set value in hidden input
    document.getElementById("netids-to-remove").value = JSON.stringify(netidsToRemove);
    // Submit the form
    document.getElementById("remove-admin-form").submit();
  } else {
    alert("Please select at least one user.");
  }
});
