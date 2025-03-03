document.addEventListener("DOMContentLoaded", function () {
  // Load Sidebar
  function loadSidebar() {
      fetch("./sidebar-admin.html")
          .then((response) => response.text())
          .then((data) => {
              let sidebar = document.getElementById("sidebar-container");
              if (sidebar) {
                  sidebar.innerHTML = data;
              }
          })
          .catch((error) => console.error("Error loading sidebar:", error));
  }

  loadSidebar(); // Call sidebar function

  // Initialize FullCalendar
  var calendarEl = document.getElementById("calendar");
  if (!calendarEl) return;

  var calendar = new FullCalendar.Calendar(calendarEl, {
      initialView: "timeGridWeek",
      headerToolbar: { center: "dayGridMonth,timeGridWeek,timeGridDay" },
      events: [
          { 
            title: "Rehearsal 1",
            start: "2025-03-10T10:00:00",
            end: "2025-03-10T12:00:00",
          },
          { 
            title: "Rehearsal 2",
            start: "2025-03-12T14:00:00",
            end: "2025-03-12T16:00:00",
          },
          {
            title: 'Social Event',
            start: "2025-03-03T14:00:00",
            end: "2025-03-03T16:00:00",
          },
      ],
      eventColor: "var(--secondary-blue)",
  });

  calendar.render();
});
