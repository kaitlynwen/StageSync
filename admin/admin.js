document.addEventListener("DOMContentLoaded", function () {
  // Load Sidebar
  function loadSidebar() {
      fetch("./sidebar-admin.html")
          .then((response) => response.text())
          .then((data) => {
              let sidebar = document.getElementById("sidebar-container");
              if (sidebar) {
                  sidebar.innerHTML = data; // Insert the sidebar HTML
                  console.log("Sidebar content loaded:", data);
                  setActiveNavLink(); // Call the function after content is loaded
              }
          })
          .catch((error) => console.error("Error loading sidebar:", error));
  }

  loadSidebar(); // Call sidebar function

  function setActiveNavLink() {
      let sidebar = document.getElementById("sidebar-container");
      if (!sidebar) {
          console.log("Sidebar container not found!");
          return;
      }

      let navLinks = sidebar.querySelectorAll(".nav-link");
      console.log("Found nav-links:", navLinks);

      let currentPath = window.location.pathname.replace(/\/$/, ""); // Normalize path

      navLinks.forEach(link => {
          let linkPath = new URL(link.href).pathname.replace(/\/$/, ""); // Normalize link path

          console.log("Comparing:", linkPath);  // Log each link's pathname

          if (linkPath === currentPath) {
              console.log("Adding active class to:", link);
              link.classList.add("active");
          } else {
              link.classList.remove("active");
          }
      });
  }

  // Initialize FullCalendar
  var calendarEl = document.getElementById("calendar");
  if (!calendarEl) return;

  // Assume userRole is dynamically set
  let userRole = 'admin';  // Change dynamically based on logged-in user

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
              start: "2025-03-15T14:00:00",
              end: "2025-03-15T16:00:00",
          },
      ],
      eventColor: "var(--secondary)",
      editable: userRole === 'admin', // Only admins can edit
      droppable: userRole === 'admin', // Only admins can drag and drop
      eventClick: function(info) {
          if (userRole !== 'admin') {
              alert('You do not have permission to edit this event');
          } else {
              alert('You can edit this event');
          }
      }
  });

  calendar.render();
});
