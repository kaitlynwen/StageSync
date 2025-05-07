// Get the edit modal
var editModal = document.getElementById("edit-group-modal");

var modalContent = editModal.querySelector(".modal-content"); // Select modal content area

// Get the button that opens the edit modal
var edit = document.querySelectorAll(".dropdown-edit");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

// Add click event listeners to all "Edit" buttons
edit.forEach(function (edit) {
  edit.addEventListener("click", function () {
    // Close the dropdown menu
    const dropdownMenu = edit
      .closest(".relative")
      .querySelector("[id^='dropdownMenu']");
    if (dropdownMenu) dropdownMenu.classList.add("hidden");

    const groupName = this.dataset.groupName;
    const groupId = this.dataset.groupId;

    // List of members in group
    const members = JSON.parse(this.dataset.members);

    // netIDs of members in group
    const memberNetids = members.map((item) => item.netid);

    // List of members
    const allMembers = JSON.parse(this.dataset.allMembers);

    // Filter members in group from all members
    // https://stackoverflow.com/questions/34901593/how-to-filter-an-array-from-all-elements-of-another-array
    const availableMembers = allMembers.filter(
      (item) => !memberNetids.includes(item.netid)
    );
    // console.log(availableMembers)

    // Update modal content dynamically
    modalContent.innerHTML = `
    <div class="flex justify-between items-center p-4 border-b border-neutral-200 dark:border-neutral-800">
      <h2 class="text-lg font-bold text-neutral-950 dark:text-neutral-200">Edit Group</h2>
      <button type="button" class="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 text-xl close">&times;</button>
    </div>

    <div class="p-4 space-y-4 overflow-y-auto">
      <label for="group-title" class="block mb-2 text-sm font-medium text-neutral-900 dark:text-neutral-200">
        Group Name <span class="text-red-500">*</span>
      </label>
      <input type="text" id="group-title" value="${groupName}" class="w-64 px-3 py-2 bg-neutral-50 border border-neutral-200 text-neutral-900 text-sm 
                    rounded-md focus:ring-indigo-500 focus:border-indigo-500 block
                    dark:bg-neutral-700 dark:border-neutral-700 dark:text-neutral-200 border-2" 
                    maxlength = 100/>
      <div class="flex justify-between items-start gap-4">
        <div class="w-1/2">
          <p class="text-sm font-medium text-neutral-900 dark:text-neutral-200 py-4">Remove Existing Members</p>
          <div id="remove-members"></div>
        </div>

        <div class="w-1/2">
          <p class="text-sm font-medium text-neutral-900 dark:text-neutral-200 py-4">Add New Members</p>
          <div id="add-members"></div>
        </div>
      </div>
    </div>

    <div class="sticky bottom-0 right-0 w-full bg-white dark:bg-neutral-800 p-4 border-t border-neutral-200 dark:border-neutral-600 flex justify-end">
      <button id="save-group" class="bg-indigo-500 hover:bg-indigo-700 text-neutral-200 px-4 py-2 rounded text-sm">
        Save
      </button>
    </div>`;

    let removeMembersHtml = "";
    for (let i = 0; i < members.length; i++) {
      const member = members[i];
      const id = `remove-${member.netid}`;
    
      removeMembersHtml += `
        <div>
          <input type="checkbox"
            id="${id}"
            class="remove-member-checkbox text-indigo-500 bg-neutral-100 border-neutral-300 rounded-sm 
            focus:ring-indigo-500 dark:focus:ring-indigo-600 dark:ring-offset-neutral-800 focus:ring-2 
            dark:bg-neutral-700 dark:border-neutral-700 dark:text-neutral-200 border-2 rounded-xs pl-2"
            value="${member.netid}" />
          <label for="${id}">${member.first_name} ${member.last_name}</label>
        </div>
      `;
    }    

    let addMembersHtml = "";
    for (let i = 0; i < availableMembers.length; i++) {
      const availableMember = availableMembers[i];
      const id = `add-${availableMember.netid}`;
    
      addMembersHtml += `
        <div>
          <input type="checkbox"
            id="${id}"
            class="add-member-checkbox text-indigo-500 bg-neutral-100 border-neutral-300 rounded-sm focus:ring-indigo-500 dark:focus:ring-indigo-600 dark:ring-offset-neutral-800 focus:ring-2 dark:bg-neutral-700 dark:border-neutral-600 rounded-xs"
            value="${availableMember.netid}" /> 
          <label for="${id}">${availableMember.first_name} ${availableMember.last_name}</label>
        </div>
      `;    
    }

    // Insert the generated checkboxes into the modal
    document.getElementById("remove-members").innerHTML = removeMembersHtml;
    document.getElementById("add-members").innerHTML = addMembersHtml;

    // Add event listener to close button
    editModal.querySelector(".close").onclick = function () {
      editModal.style.display = "none";
    };

    document
      .getElementById("save-group")
      .addEventListener("click", function () {
        // Disable the button + show spinner
        const saveBtn = document.getElementById('save-group');
        saveBtn.disabled = true;
        saveBtn.classList.add('opacity-60', 'cursor-not-allowed');
        saveBtn.innerHTML = `
          <span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>
          Saving...
        `;

        var newGroupName = document.getElementById("group-title").value;

        // Get all checked checkboxes for remove members
        const removeChecked = document.querySelectorAll(
          ".remove-member-checkbox:checked"
        );

        // Create an array of netid values of selected remove users
        const netidsToRemove = Array.from(removeChecked).map(
          (checkbox) => checkbox.value
        );

        console.log(netidsToRemove);

        // Get all checked checkboxes for remove members
        const addChecked = document.querySelectorAll(
          ".add-member-checkbox:checked"
        );

        // Create an array of netid values of selected remove users
        const netidsToAdd = Array.from(addChecked).map(
          (checkbox) => checkbox.value
        );

        // Get CSRF token for validation
        const csrfToken = document
          .querySelector('meta[name="csrf-token"]')
          .getAttribute("content");

        // Send update request to backend
        fetch("/update-group-info", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            groupId,
            groupName,
            newGroupName,
            remove: netidsToRemove,
            add: netidsToAdd,
          }),
        })
          .then((response) => response.json()) // Convert response to JSON
          .then((data) => {
            if (data.success) {
              location.reload();
              editModal.style.display = "none";
            } else {
              flashAlert(data.error, "error");
              editModal.style.display = "none";
            }
          })
          .catch((error) => {
            console.error("Fetch error:", error);
          });
      });
    // Show the modal
    editModal.style.display = "flex";
  });
});

// When the user clicks anywhere outside of the modal, close it
window.onclick = function (event) {
  if (event.target == editModal) {
    editModal.style.display = "none";
  }
};

// Create Group Modal (Utilizes Tailwind Flowbite)
document.getElementById("create-group").addEventListener("click", function () {
  const createBtn = this;
  const cancelBtn = document.getElementById("cancelBtn")
  const groupName = document.getElementById("new-group").value.trim();

  if (!groupName) {
    flashAlert("Group name cannot be empty", "error");
    return;
  }

  // Disable the button and update UI
  createBtn.disabled = true;
  cancelBtn.disabled = true;

  createBtn.classList.add("opacity-60", "cursor-not-allowed");
  cancelBtn.classList.add("opacity-60", "cursor-not-allowed");

  createBtn.innerHTML = `
    <span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>
    Creating...
  `;

  const csrfToken = document
    .querySelector('meta[name="csrf-token"]')
    .getAttribute("content");

  fetch("/create-group", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify({ groupName }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        document.getElementById("create-modal").classList.add("hidden");
        location.reload();
      } else {
        flashAlert(data.error, "error");
        // Re-enable on failure
        createBtn.disabled = false;
        cancelBtn.disabled = false;

        createBtn.classList.remove("opacity-60", "cursor-not-allowed");
        cancelBtn.classList.remove("opacity-60", "cursor-not-allowed");

        createBtn.innerHTML = "Create";
      }
    })
    .catch((error) => {
      console.error("Fetch error:", error);
      flashAlert("An error occurred. Please try again.", "error");
      // Re-enable on error
      createBtn.disabled = false;
      cancelBtn.disabled = false;

      createBtn.classList.remove("opacity-60", "cursor-not-allowed");
      cancelBtn.classList.remove("opacity-60", "cursor-not-allowed");

      createBtn.innerHTML = "Create";
    });
});

// Delete Group Modal (Utilizes Tailwind Flowbite)
var deleteModal = document.getElementById("delete-modal");

// Add click event listener to all "Delete" buttons
document.querySelectorAll(".dropdown-delete").forEach(function (deleteButton) {
  deleteButton.addEventListener("click", function () {
    // Close the dropdown menu
    const dropdownMenu = deleteButton
      .closest(".relative")
      .querySelector("[id^='dropdownMenu']");
    if (dropdownMenu) dropdownMenu.classList.add("hidden");

    const groupId = this.dataset.groupId;

    deleteModal.querySelector(
      "button[data-modal-hide='delete-modal']"
    ).dataset.groupId = groupId;

    deleteModal.classList.remove("hidden");
  });
});

deleteModal
  .querySelector("button[data-modal-hide='delete-modal']")
  .addEventListener("click", function () {
    const groupId = this.dataset.groupId;

    const csrfToken = document
      .querySelector('meta[name="csrf-token"]')
      .getAttribute("content");

    fetch("/delete-group", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ groupId }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          deleteModal.classList.add("hidden");
          location.reload();
        } else {
          flashAlert("An error occurred: " + data.message, "error");
          deleteModal.classList.add("hidden");
        }
      })
      .catch((error) => {
        console.error("Fetch error:", error);
        deleteModal.classList.add("hidden"); // Hide the modal on network error
      });
  });

// Close modal when user clicks outside of it
window.onclick = function (event) {
  if (event.target == deleteModal) {
    deleteModal.classList.add("hidden"); // Hide the modal when clicked outside
  }
};
