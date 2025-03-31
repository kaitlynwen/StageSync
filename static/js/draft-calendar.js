document.addEventListener("DOMContentLoaded", function () {
  var calendarEl = document.getElementById("calendar");
  if (!calendarEl) return;

  let userRole = "admin"; // need to dynamically based on logged-in user

  var calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "timeGridWeek",
    headerToolbar: { center: "dayGridMonth,timeGridWeek,timeGridDay" },

    events: function (info, successCallback, failureCallback) {
      fetch("/draft-schedule")
        .then((response) => response.json())
        .then((data) => {
          console.log("Data received:", data);

          if (Array.isArray(data)) {
            const events = data.map((event) => ({
              title: event.title,
              start: event.start,
              end: event.end,
              extendedProps: { location: event.location },
              color: event.color, // Assigning color dynamically
            }));
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

    editable: userRole === "admin",
    droppable: userRole === "admin",

    eventClick: function (info) {
      alert(
        userRole !== "admin"
          ? "You do not have permission to edit this event"
          : "You can edit this event"
      );
    },

    eventDidMount: function (info) {
      info.el.setAttribute(
        "title",
        `${info.event.title} - ${info.event.extendedProps.location}`
      );
    },
  });

  calendar.render();

  // Add the "Discard" button functionality
  document
    .getElementById("discard-button")
    .addEventListener("click", function () {
      // Confirm the discard action
      // Make a POST request to restore the draft schedule
      fetch("/restore-draft-schedule", {
        method: "POST",
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Draft schedule restored:", data);
          // Refetch events after restoring the draft schedule
          calendar.refetchEvents(); // This will reload the events from the draft schedule
        })
        .catch((error) => {
          console.error("Error restoring draft schedule:", error);
        });
    });

  // Add the "Publish" button functionality
  document
    .getElementById("publish-button")
    .addEventListener("click", function () {
      // Confirm the publish action
      // Make a POST request to publish the draft schedule
      fetch("/publish-draft", {
        method: "POST",
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Schedule published:", data);
          // Refetch events after publishing the schedule
          calendar.refetchEvents(); // This will reload the events from the events table
        })
        .catch((error) => {
          console.error("Error publishing schedule:", error);
        });
    });
});
