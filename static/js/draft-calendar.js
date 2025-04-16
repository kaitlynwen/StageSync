function formatDate(date) {
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0"); // Month is 0-indexed
  const day = String(d.getDate()).padStart(2, "0");
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

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
        alert("You do not have permission to edit this event");
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

      fetch("/update-event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
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
          calendar.refetchEvents();
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

      fetch("/update-event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
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
          calendar.refetchEvents();
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
    .addEventListener("click", function () {
      fetch("/restore-draft-schedule", { method: "POST" })
        .then((response) => response.json())
        .then((data) => {
          console.log("Draft schedule restored:", data);
          calendar.refetchEvents();
        })
        .catch((error) => {
          console.error("Error restoring draft schedule:", error);
        });
    });

  // Add the "Publish" button functionality
  document
    .getElementById("publish-button")
    .addEventListener("click", function () {
      fetch("/publish-draft", { method: "POST" })
        .then((response) => response.json())
        .then((data) => {
          console.log("Schedule published:", data);
          calendar.refetchEvents();
        })
        .catch((error) => {
          console.error("Error publishing schedule:", error);
        });
    });

  document
    .getElementById("event-form")
    .addEventListener("submit", async function (e) {
      e.preventDefault();

      const title = document.getElementById("event-title").value;
      const location = document.getElementById("location").value;
      const start = document.getElementById("start-time").value;
      const end = document.getElementById("end-time").value;
      const groupId = document.getElementById("group").value;

      if (!title || !location || !start || !end) {
        alert("Please fill in all required fields.");
        return;
      }

      // Convert start and end times to UTC
      const startUtc = new Date(start).toISOString(); // Convert to ISO string in UTC
      const endUtc = new Date(end).toISOString(); // Convert to ISO string in UTC

      const eventData = {
        title,
        location,
        start: startUtc,
        end: endUtc,
        group_id: groupId, // Optionally rename this on the backend
      };

      try {
        const response = await fetch("/add-event", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(eventData),
        });

        const result = await response.json();

        if (response.ok) {
          alert("Event added successfully!");
          document.getElementById("event-form").reset();

          modal.hide();

          calendar.refetchEvents();
        } else {
          alert(result.error || "Something went wrong!");
        }
      } catch (err) {
        console.error("Error submitting event:", err);
        alert("Failed to submit event.");
      }
    });
});

document
  .getElementById("edit-event-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const editModalEl = document.getElementById("edit-event-modal");
    const editModal = new Modal(editModalEl);

    const id = document.getElementById("edit-event-id").value;
    const title = document.getElementById("edit-event-title").value;
    const location = document.getElementById("edit-location").value;
    const start = new Date(
      document.getElementById("edit-start-time").value
    ).toISOString();
    const end = new Date(
      document.getElementById("edit-end-time").value
    ).toISOString();
    const groupid = document.getElementById("edit-group").value;

    const updatedEvent = { id, title, location, start, end, groupid };

    try {
      const res = await fetch("/update-event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updatedEvent),
      });

      if (res.ok) {
        alert("Event updated successfully!");
        editModal.hide();  // Manually hide the modal via class
        window.location.reload(); // Reload the page to ensure all changes are reflected
      } else {
        const result = await res.json();
        alert(result.error || "Failed to update event.");
      }
    } catch (error) {
      console.error("Update error:", error);
    }
  });


document
  .getElementById("delete-event-button")
  .addEventListener("click", async function () {
    const eventId = document.getElementById("edit-event-id").value;
    const editModalEl = document.getElementById("edit-event-modal");
    const editModal = new Modal(editModalEl);

    if (!confirm("Are you sure you want to delete this event?")) return;

    try {
      const res = await fetch(`/delete-event/${eventId}`, { method: "DELETE" });

      if (res.ok) {
        alert("Event deleted.");
        editModal.hide(); // Hide the modal after delete
      } else {
        const result = await res.json();
        alert(result.error || "Failed to delete event.");
      }
    } catch (error) {
      console.error("Delete error:", error);
    }
  });
