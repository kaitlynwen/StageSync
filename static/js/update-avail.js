function showTab(tab) {
    // Hide all tab contents
    document.getElementById("weekly-content").classList.add("hidden");
    document.getElementById("one-time-content").classList.add("hidden");

    // Remove active styles from both tabs
    document.getElementById("weekly-tab").classList.remove("border-indigo-500", "text-indigo-500");
    document.getElementById("weekly-tab").classList.add("border-transparent", "text-neutral-500", "dark:text-neutral-200");

    document.getElementById("one-time-tab").classList.remove("border-indigo-500", "text-indigo-500");
    document.getElementById("one-time-tab").classList.add("border-transparent", "text-neutral-500", "dark:text-neutral-200");

    // Show the selected tab content
    document.getElementById(`${tab}-content`).classList.remove("hidden");

    // Apply active styles to the selected tab
    document.getElementById(`${tab}-tab`).classList.add("border-indigo-500", "text-indigo-500");
    document.getElementById(`${tab}-tab`).classList.remove("border-transparent", "text-neutral-500", "dark:text-neutral-200");
  }

  const weeklyPattern = /^(\d{1,2}:\d{2}(AM|PM)-\d{1,2}:\d{2}(AM|PM))(;\s*\d{1,2}:\d{2}(AM|PM)-\d{1,2}:\d{2}(AM|PM))*$/;
  const oneTimePattern = /^(\d{1,2}\/\d{1,2}\.\d{1,2}:\d{2}(AM|PM)-\d{1,2}:\d{2}(AM|PM))(;\s*\d{1,2}\/\d{1,2}\.\d{1,2}:\d{2}(AM|PM)-\d{1,2}:\d{2}(AM|PM))*$/;

  function validateConflicts() {
    const isWeeklyVisible = !document.getElementById("weekly-content").classList.contains("hidden");
    const isOneTimeVisible = !document.getElementById("one-time-content").classList.contains("hidden");

    if (isWeeklyVisible) {
      const weeklyInputs = document.querySelectorAll('input[name$="_conflicts"]');
      for (const input of weeklyInputs) {
        const value = input.value.trim();
        if (value && !weeklyPattern.test(value)) {
          showErrorModal("Please use correct formatting: HH:MMAM/PM - HH:MMAM/PM separated by semicolons.");
          return false;
        }
      }
    }

    if (isOneTimeVisible) {
      const oneTimeInput = document.getElementById('one-time-conflict');
      const value = oneTimeInput.value.trim();
      if (value) {
        if (!oneTimePattern.test(value)) {
          showErrorModal("Please use correct formatting: MM/DD.HH:MMAM/PM - MM/DD.HH:MMAM/PM separated by semicolons.");
          return false;
        }

        // Check for past dates
        const now = new Date();
        const conflicts = value.split(';');
        for (const conflict of conflicts) {
          const match = conflict.trim().match(/^(\d{1,2})\/(\d{1,2})\./);
          if (match) {
            let [_, monthStr, dayStr] = match;
            const month = parseInt(monthStr, 10) - 1; 
            const day = parseInt(dayStr, 10);
            const year = now.getFullYear();
            const conflictDate = new Date(year, month, day);

            // If the conflict date is before today
            if (conflictDate.setHours(0,0,0,0) < now.setHours(0,0,0,0)) {
              alert(`One-time conflict date ${month + 1}/${day} is in the past. Please remove or fix it.`);
              return false;
            }
          }
        }
      }
    }

    return true;
  }

  document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    const saveBtn = document.getElementById('saveBtn');
  
    if (!form || !saveBtn) return;
  
    form.addEventListener('submit', (e) => {
      if (!validateConflicts()) {
        e.preventDefault();
        return;
      }
  
      // Disable the button + show spinner
      saveBtn.disabled = true;
      saveBtn.classList.add('opacity-60', 'cursor-not-allowed');
      saveBtn.innerHTML = `
        <span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>
        Saving...
      `;
    });
  });
  