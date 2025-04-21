document.addEventListener("DOMContentLoaded", function () {
  var calendarEl = document.getElementById("calendar");
  if (!calendarEl) return;

  let userRole = "admin"; // Dynamically set based on logged-in user

  // Grab modal DOM element
  const modalEl = document.getElementById("event-modal");
  const editModalEl = document.getElementById("edit-event-modal");

  // Initialize Flowbite modal
  const modal = new Modal(modalEl);
  const editModal = new Modal(editModalEl);

  var calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "timeGridWeek",
    customButtons: {
      myCustomButton: {
        text: "add event",
        click: function () {
          modal.show(); // Show modal when the button is clicked
        },
      },
    },
    headerToolbar: {
      right: "myCustomButton today prev,next",
      center: "dayGridMonth,timeGridWeek,timeGridDay",
      left: "title",
    },
    timeZone: "local", // Automatically convert UTC to local time
    events: function (info, successCallback, failureCallback) {
      fetch("/draft-schedule")
        .then((response) => response.json())
        .then((data) => {
          if (Array.isArray(data)) {
            const events = data.map((event) => {
              return {
                id: event.id,
                title: event.title,
                start: event.start, // FullCalendar handles UTC to local time
                end: event.end,
                extendedProps: {
                  location: event.location,
                  groupid: event.groupid,
                },
                color: event.color,
              };
            });
            successCallback(events);
          } else {
            failureCallback("Data format is not an array");
          }
        })
        .catch((error) => {
          console.error("Error fetching events:", error);
          failureCallback(error);
        });
    },
    scrollTime: "16:00:00",
    editable: userRole === "admin",
    droppable: userRole === "admin",
    eventResizableFromStart: userRole === "admin",
    eventDurationEditable: userRole === "admin",
    eventStartEditable: userRole === "admin",
    eventClick: function (info) {
      if (userRole !== "admin") {
        flashAlert("You do not have permission to edit this event", "error");
        return;
      }

      // Populate modal fields
      document.getElementById("edit-event-id").value = info.event.id;
      document.getElementById("edit-event-title").value = info.event.title;
      document.getElementById("edit-location").value =
        info.event.extendedProps.location;
      document.getElementById("edit-start-time").value = formatDate(
        info.event.start
      );
      document.getElementById("edit-end-time").value = info.event.end
        ? formatDate(info.event.end)
        : "";
      document.getElementById("edit-group").value =
        info.event.extendedProps.groupid != ""
          ? info.event.extendedProps.groupid
          : "disabled";

      // Show edit modal
      editModal.show();
    },
    eventResize: function (info) {
      const updatedEvent = {
        id: info.event.id,
        title: info.event.title,
        start: info.event.start,
        end: info.event.end,
        location: info.event.extendedProps.location,
        groupid: info.event.extendedProps.groupid,
      };
      console.log("Updated event:", updatedEvent);
      
      const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

      fetch("/update-event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(updatedEvent),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Failed to update event");
          }
          return response.json();
        })
        .then((data) => {
          console.log("Event updated successfully:", data);
          flashAlert("Event updated successfully.", "success");
        })
        .catch((error) => {
          console.error("Error updating event:", error);
          info.revert(); // Revert event back to original position
        });
    },
    eventDrop: function (info) {
      const updatedEvent = {
        id: info.event.id,
        title: info.event.title,
        start: info.event.start.toISOString(),
        end: info.event.end ? info.event.end.toISOString() : null,
        location: info.event.extendedProps.location,
        groupid: info.event.extendedProps.groupid,
      };

      const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

      fetch("/update-event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(updatedEvent),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error("Failed to update event");
          }
          return response.json();
        })
        .then((data) => {
          console.log("Event moved successfully:", data);
          flashAlert("Event moved successfully.", "success");
        })
        .catch((error) => {
          console.error("Error moving event:", error);
          info.revert(); // Revert the move visually
        });
    },
  });

  calendar.render();

  // Add the "Discard" button functionality
  document
    .getElementById("discard-button")
    .addEventListener("click", async function (e) {
      const btn = e.currentTarget;
      btn.disabled = true;
      const originalHTML = btn.innerHTML;
      btn.innerHTML = `<span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>Restoring...`;

      try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
        const response = await fetch("/restore-draft-schedule", {
          method: "POST",
          headers: {"X-CSRFToken": csrfToken,}
        });
        flashAndReload("Schedule restored successfully.", "success");
      } catch (error) {
        flashAlert("Failed to restore schedule.", "error");
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
      }
    });

  // Add the "Publish" button functionality
  document
    .getElementById("publish-button")
    .addEventListener("click", async function (e) {
      const btn = e.currentTarget;
      btn.disabled = true;
      const originalHTML = btn.innerHTML;
      btn.innerHTML = `<span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>Publishing...`;

      try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
        const response = await fetch("/publish-draft", { method: "POST",
          headers: {"X-CSRFToken": csrfToken,}
         });
        const data = await response.json();
        flashAndReload("Schedule published", "success");
      } catch (error) {
        flashAlert("Failed to publish schedule.", "error");
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
      }
    });

  // Event form submission
  document
    .getElementById("event-form")
    .addEventListener("submit", async function (e) {
      e.preventDefault();

      const submitBtn = e.submitter;

      const title = document.getElementById("event-title").value;
      const location = document.getElementById("location").value;
      const start = document.getElementById("start-time").value;
      const end = document.getElementById("end-time").value;
      const groupId = document.getElementById("group").value;

      if (end < start) {
        flashAlert("Event end time cannot be before start time.", "error");
        return;
      }

      if (!title || !location || !start || !end) {
        flashAlert("Please fill in all required fields.", "warning");
        return;
      }

      const startUtc = safeParseDate(start).toISOString();
      const endUtc = safeParseDate(end).toISOString();

      const eventData = {
        title,
        location,
        start: startUtc,
        end: endUtc,
        group_id: groupId,
      };

      await withLoading(submitBtn, async () => {
        try {
          const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
          const response = await fetch("/add-event", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken, },
            body: JSON.stringify(eventData),
          });

          const result = await response.json();

          if (response.ok) {
            modal.hide();
            flashAndReload("Event added successfully", "success");
          } else {
            flashAlert(result.error || "Something went wrong!", "error");
            modal.hide();
          }
        } catch (err) {
          console.error("Error submitting event:", err);
          flashAlert("Failed to submit event.", "error");
          modal.hide();
        }
      });
    });

  // Edit Event form
  document
    .getElementById("edit-event-form")
    .addEventListener("submit", async function (e) {
      e.preventDefault();

      const submitBtn = e.submitter;

      const id = document.getElementById("edit-event-id").value;
      const title = document.getElementById("edit-event-title").value;
      const location = document.getElementById("edit-location").value;
      const start = safeParseDate(
        document.getElementById("edit-start-time").value
      ).toISOString();
      const end = safeParseDate(
        document.getElementById("edit-end-time").value
      ).toISOString();
      const groupid = document.getElementById("edit-group").value;

      if (end < start) {
        flashAlert("Event end time cannot be before start time.", "error");
        return;
      }

      const updatedEvent = { id, title, location, start, end, groupid };
      const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

      await withLoading(submitBtn, async () => {
        try {
          const res = await fetch("/update-event", {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken, },
            body: JSON.stringify(updatedEvent),
          });

          const result = await res.json();

          if (res.ok) {
            editModal.hide(); // Close the edit modal
            flashAndReload("Event updated successfully", "success");
          } else {
            flashAlert(result.error || "Failed to update event.", "error");
            editModal.hide();
          }
        } catch (error) {
          console.error("Update error:", error);
          flashAlert("Unexpected error while updating.", "error");
        }
      });
    });

  document
    .getElementById("delete-event-button")
    .addEventListener("click", async function (e) {
      const btn = e.currentTarget;

      if (!confirm("Are you sure you want to delete this event?")) return;

      const eventId = document.getElementById("edit-event-id").value;

      btn.disabled = true;
      const originalHTML = btn.innerHTML;
      btn.innerHTML = `<span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>Deleting...`;

      const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
      
      try {
        const res = await fetch("/delete-event", {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken,},
          body: JSON.stringify({ event_id: eventId }),
        });

        if (res.ok) {
          editModal.hide();
          flashAndReload("Event deleted.", "success");
        } else {
          const result = await res.json();
          flashAlert(result.error || "Failed to delete event.", "error");
          editModal.hide();
        }
      } catch (error) {
        flashAlert("Error deleting event.", "error");
      } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
      }
    });
});

function safeParseDate(date) {
  const d = new Date(date);
  return isNaN(d) ? new Date() : d;
}

function formatDate(date) {
  const d = safeParseDate(date);
  if (isNaN(d)) {
    console.error("Invalid date:", date);
    return ""; // Return empty or handle error case
  }
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  const generateBtn = document.getElementById('generateBtn');

  if (!form || !generateBtn) return;

  form.addEventListener('submit', (e) => {
    // Disable the button + show spinner
    generateBtn.disabled = true;
    generateBtn.classList.add('opacity-60', 'cursor-not-allowed');
    generateBtn.innerHTML = `
      <span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>
      Generating...
    `;
  });
});

// Helper function to display loading spinner while performing async tasks
function withLoading(button, asyncCallback) {
  const originalHTML = button.innerHTML;
  button.disabled = true;
  button.innerHTML = `<span class="animate-spin inline-block w-4 h-4 border-2 border-t-transparent border-white rounded-full mr-2"></span>Loading...`;

  return asyncCallback().finally(() => {
    button.disabled = false;
    button.innerHTML = originalHTML;
  });
}