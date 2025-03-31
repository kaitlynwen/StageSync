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
    
    // Fetch events from the backend dynamically
    events: function (info, successCallback, failureCallback) {
      fetch("/events")  // Adjust this URL based on your backend route
        .then((response) => response.json())  // Assume response is in JSON format
        .then((data) => {
          // Log the data to ensure it's in the correct format
          console.log("Data received:", data);
    
          // Check if data is an array before calling map
          if (Array.isArray(data)) {
            // Map the response data into the format FullCalendar expects
            const events = data.map((event) => ({
              title: event.title,
              start: event.start,
              end: event.end,
              extendedProps: {
                location: event.location
              },
            }));
            successCallback(events);  // Call FullCalendar's success callback with events
          } else {
            failureCallback("Data format is not an array");
          }
        })
        .catch((error) => {
          console.error("Error fetching events:", error);
          failureCallback(error);  // Call FullCalendar's failure callback if there’s an error
        });
    },    

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
