document.addEventListener("DOMContentLoaded", function () {
  var calendarEl = document.getElementById("calendar");
  if (!calendarEl) return;

  let userRole = "admin"; // Need to dynamically set based on logged-in user

  var calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "timeGridWeek",
    headerToolbar: { center: "dayGridMonth,timeGridWeek,timeGridDay" },

    // Automatically convert UTC to local time
    timeZone: "local",  // This ensures that the times are displayed in the user's local time zone

    events: function (info, successCallback, failureCallback) {
      fetch("/draft-schedule")
        .then((response) => response.json())
        .then((data) => {
          if (Array.isArray(data)) {
            const events = data.map((event) => {
              return {
                id: event.id,
                title: event.title,
                start: event.start,  // FullCalendar will handle UTC to local time conversion automatically
                end: event.end,  // FullCalendar will handle UTC to local time conversion automatically
                extendedProps: { location: event.location },
                color: event.color,  // Assign color dynamically
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
      alert(
        userRole !== "admin"
          ? "You do not have permission to edit this event"
          : "You can edit this event"
      );
    },

    eventResize: function(info) {
      const updatedEvent = {
        id: info.event.id,
        title: info.event.title,
        // Convert to UTC format (this is done by toISOString())
        start: info.event.start.toISOString(),
        end: info.event.end.toISOString(),
        location: info.event.extendedProps.location
      };

      console.log('Updated event:', updatedEvent); // Log the event here to check the times

      fetch("/update-event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(updatedEvent)
      })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to update event");
        }
        return response.json();
      })
      .then((data) => {
        console.log("Event updated successfully:", data);
        calendar.refetchEvents(); // Refetch events from the backend
      })
      .catch((error) => {
        console.error("Error updating event:", error);
        info.revert();
        calendar.refetchEvents();
      });
    },

    eventDrop: function(info) {
      // Extract updated event info
      const updatedEvent = {
        id: info.event.id,
        title: info.event.title,
        start: info.event.start.toISOString(),
        end: info.event.end ? info.event.end.toISOString() : null,
        location: info.event.extendedProps.location
      };

      // Send update to the server
      fetch("/update-event", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(updatedEvent)
      })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Failed to update event");
        }
        return response.json();
      })
      .then((data) => {
        console.log("Event moved successfully:", data);
      })
      .catch((error) => {
        console.error("Error moving event:", error);
        // Revert the move visually
        info.revert();
        calendar.refetchEvents();
      });
    },
  });

  calendar.render();

  // Add the "Discard" button functionality
  document
    .getElementById("discard-button")
    .addEventListener("click", function () {
      // Confirm the discard action
      fetch("/restore-draft-schedule", {
        method: "POST",
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Draft schedule restored:", data);
          calendar.refetchEvents(); // Reload events after restoring
        })
        .catch((error) => {
          console.error("Error restoring draft schedule:", error);
        });
    });

  // Add the "Publish" button functionality
  document
    .getElementById("publish-button")
    .addEventListener("click", function () {
      fetch("/publish-draft", {
        method: "POST",
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Schedule published:", data);
          calendar.refetchEvents(); // Reload events after publishing
        })
        .catch((error) => {
          console.error("Error publishing schedule:", error);
        });
    });
});
