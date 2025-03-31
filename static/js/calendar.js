document.addEventListener("DOMContentLoaded", function () {
  var calendarEl = document.getElementById("calendar");
  if (!calendarEl) return;

  let userRole = "admin"; // Change dynamically based on logged-in user

  var calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "timeGridWeek",
    headerToolbar: { center: "dayGridMonth,timeGridWeek,timeGridDay" },

    events: function (info, successCallback, failureCallback) {
      fetch("/events")
        .then((response) => response.json())
        .then((data) => {
          console.log("Data received:", data);

          if (Array.isArray(data)) {
            const events = data.map((event) => ({
              title: event.title,
              start: event.start,
              end: event.end,
              extendedProps: { location: event.location },
              color: event.color  // Assigning color dynamically
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
      info.el.setAttribute("title", `${info.event.title} - ${info.event.extendedProps.location}`);
    },
  });

  calendar.render();
});
