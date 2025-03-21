// calendar.js
document.addEventListener("DOMContentLoaded", function () {
  // Get CSS variables from :root
  function getCSSVariable(name) {
    return getComputedStyle(document.documentElement)
      .getPropertyValue(name)
      .trim();
  }

  // Example usage
  let primaryColor = getCSSVariable("--primary");
  let secondaryColor = getCSSVariable("--secondary");

  // Initialize FullCalendar
  var calendarEl = document.getElementById("calendar");
  if (!calendarEl) return;

  let userRole = "admin"; // Change dynamically based on logged-in user

  var calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: "timeGridWeek",
    headerToolbar: { center: "dayGridMonth,timeGridWeek,timeGridDay" },
    events: [
      {
        title: "Rehearsal 1",
        start: "2025-03-16T10:00:00",
        end: "2025-03-16T12:00:00",
      },
      {
        title: "Rehearsal 2",
        start: "2025-03-18T14:00:00",
        end: "2025-03-18T16:00:00",
      },
      {
        title: "Social Event",
        start: "2025-03-20T14:00:00",
        end: "2025-03-20T16:00:00",
      },
    ],
    eventColor: secondaryColor,
    editable: userRole === "admin",
    droppable: userRole === "admin",
    eventClick: function (info) {
      alert(
        userRole !== "admin"
          ? "You do not have permission to edit this event"
          : "You can edit this event"
      );
    },
  });

  calendar.render();
});
