// Get the modal
var modal = document.getElementById("edit-group-modal");

var modalContent = modal.querySelector(".modal-content"); // Select modal content area

// Get the button that opens the modal
var buttons = document.querySelectorAll(".dropdown-edit");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// Add click event listeners to all "Edit" buttons
buttons.forEach(function (btn) {
  btn.addEventListener("click", function () {
    // Close the dropdown menu
    const dropdownMenu = btn.closest(".relative").querySelector("[id^='dropdownMenu']");
    if (dropdownMenu) dropdownMenu.classList.add("hidden");

    const groupName = this.dataset.groupName;
    const groupId = this.dataset.groupId;

    // List of members in group
    const members = JSON.parse(this.dataset.members);
    // console.log(members)

    // netIDs of members in group
    const memberNetids = members.map(item => item.netid);
    // console.log(memberNetids);

    // List of members
    const allMembers = JSON.parse(this.dataset.allMembers);
    // console.log(allMembers)

    // Filter members in group from all members
    // https://stackoverflow.com/questions/34901593/how-to-filter-an-array-from-all-elements-of-another-array
    const availableMembers = allMembers.filter(item => !memberNetids.includes(item.netid));
    // console.log(availableMembers)

    // Update modal content dynamically
    modalContent.innerHTML = `
      <span class="close">&times;</span>
      <h2 class="text-lg font-bold text-indigo-500 py-4">Change Group Name:</h2>
      <input type="text" id="group-title" value="${groupName}" />
      <div class="flex justify-between items-start">
        <div class="w-1/2">
          <h2 class="text-lg font-bold text-indigo-500 py-4">Check to Remove Existing Members:</h2>
          <div id="remove-members"></div>
      </div>

        <div class="w-1/2">
          <h2 class="text-lg font-bold text-indigo-500 py-4">Check to Add New Members:</h2>
          <div id="add-members"></div>
        </div>
      </div>
      <br>
      <div style="display: flex; justify-content: flex-end;">
        <button id="save-group" class="bg-indigo-500 hover:bg-indigo-700 text-white px-2 py-1 rounded text-sm mb-2">
          Save
        </button>
      </div>
    `;

    let removeMembersHtml = '';
    for (let i = 0; i < members.length; i++) {
      const member = members[i];
      removeMembersHtml += `
          <input type="checkbox"
          class="remove-member-checkbox"
          value="${member.netid}" /> 
          ${member.first_name} ${member.last_name}
        <br />
      `;
    }

    let addMembersHtml = '';
    for (let i = 0; i < availableMembers.length; i++) {
      const availableMember = availableMembers[i];
      addMembersHtml += `
          <input type="checkbox"
          class="add-member-checkbox"
          value="${availableMember.netid}" /> 
          ${availableMember.first_name} ${availableMember.last_name}
        <br />
      `;
    }


    // Insert the generated checkboxes into the modal
    document.getElementById("remove-members").innerHTML = removeMembersHtml;
    document.getElementById("add-members").innerHTML = addMembersHtml;

    // Add event listener to close button
    modal.querySelector(".close").onclick = function () {
      modal.style.display = "none";
    };

    document.getElementById("save-group").addEventListener("click", function () {

      var newGroupName = document.getElementById("group-title").value;

      // Get all checked checkboxes for remove members
      const removeChecked = document.querySelectorAll(
        ".remove-member-checkbox:checked"
      );

      // Create an array of netid values of selected remove users
      const netidsToRemove = Array.from(removeChecked).map(
        (checkbox) => checkbox.value
      );

      // Get all checked checkboxes for remove members
      const addChecked = document.querySelectorAll(
        ".add-member-checkbox:checked"
      );

      // Create an array of netid values of selected remove users
      const netidsToAdd = Array.from(addChecked).map(
        (checkbox) => checkbox.value
      );

      // Send update request to backend
      fetch("/update-group-info", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ groupId, groupName, newGroupName, 
          remove: netidsToRemove, add: netidsToAdd }),
      })
        .then(response => response.json()) // Convert response to JSON
        .then(data => {
          if (data.success) {
            alert("Changes saved!");
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
window.onclick = function (event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}