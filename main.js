function updateMonthDisplay() {
    const currentDate = calendar.getDate(); // Get the current date from the calendar
    const monthYear = currentDate.toDate().toLocaleString('default', { month: 'long', year: 'numeric' });
    document.getElementById('currentMonth').textContent = monthYear;
}

document.addEventListener("DOMContentLoaded", function () {
    const Calendar = tui.Calendar;
    const calendar = new Calendar('#calendar', {
        defaultView: 'week', // Set default view to 'week'
        taskView: false, // Hide task rows
        milestoneView: false, // Hide milestone rows
        scheduleView: ['time'],
        useFormPopup: true,
        useDetailPopup: true,
        calendarId: 1,
        week: {
            taskView: false,
            eventView: ['time'],
        }
    });

    // Function to update the displayed month
    function updateMonthDisplay() {
        const currentDate = calendar.getDate();
        const monthYear = currentDate.toDate().toLocaleString('default', { month: 'long', year: 'numeric' });
        document.getElementById('currentMonth').textContent = monthYear;
    }

    // Update month display on load
    updateMonthDisplay();

    // Add event listeners for navigation buttons
    document.getElementById('prevBtn').addEventListener('click', () => {
        calendar.prev();
        updateMonthDisplay();
    });

    document.getElementById('nextBtn').addEventListener('click', () => {
        calendar.next();
        updateMonthDisplay();
    });

    // Function to update active view button
    function updateActiveView(view) {
        // Remove 'active' class from all buttons
        document.querySelectorAll('.btn-group .btn').forEach(button => button.classList.remove('active'));
        
        // Add 'active' class to the clicked button
        document.getElementById(view).classList.add('active');
    }

    // Event listeners for view buttons
    document.getElementById('monthView').addEventListener('click', function () {
        calendar.changeView('month', true);
        updateActiveView('monthView');
    });

    document.getElementById('weekView').addEventListener('click', function () {
        calendar.changeView('week', true);
        updateActiveView('weekView');
    });

    document.getElementById('dayView').addEventListener('click', function () {
        calendar.changeView('day', true);
        updateActiveView('dayView');
    });

    // Example events
    calendar.createEvents([
        {
            id: '1',
            calendarId: 'Rehos',
            title: 'Rehearsal Session',
            category: 'time',
            start: '2025-03-01T14:00:00',
            end: '2025-03-01T16:00:00'
        },
        {
            id: '2',
            calendarId: 'Rehos',
            title: 'Band Meeting',
            category: 'time',
            start: '2025-03-05T10:00:00',
            end: '2025-03-05T12:00:00'
        },
        {
            id: '3',
            calendarId: 'Rehos',
            title: 'Band Meeting',
            category: 'time',
            start: '2025-03-01T13:00:00',
            end: '2025-03-01T14:00:00'
        }
    ]);
});
