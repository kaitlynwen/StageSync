document.addEventListener("DOMContentLoaded", function () {
  var calendarEl = document.getElementById("calendar");
  if (!calendarEl) return;

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

    editable: false,
    droppable: false,

    eventDidMount: function (info) {
      info.el.setAttribute("title", `${info.event.title} - ${info.event.extendedProps.location}`);
    },
  });

  calendar.render();
});
