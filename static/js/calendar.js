document.addEventListener("DOMContentLoaded", function () {
  var calendarEl = document.getElementById("calendar");
  if (!calendarEl) return;

  var calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "timeGridWeek",
    headerToolbar: { center: "dayGridMonth,timeGridWeek,timeGridDay" },
    timeZone: "local",  // Make sure FullCalendar uses the local time zone

    events: function (info, successCallback, failureCallback) {
      fetch("/events")
        .then((response) => response.json())
        .then((data) => {
          console.log("Data received:", data);

          if (Array.isArray(data)) {
            const events = data.map((event) => {
              // FullCalendar will automatically handle the conversion from UTC to local time
              return {
                id: event.id,
                title: event.title,
                start: event.start,  // Already in ISO format with time zone info
                end: event.end,  // Already in ISO format with time zone info
                extendedProps: { location: event.location },
                color: event.color  // Assign color dynamically
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
    editable: false,
    droppable: false,
  });

  calendar.render();
});
