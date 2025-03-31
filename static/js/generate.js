document.getElementById('generate-button').addEventListener('click', function () {
    // Show loading message or spinner (optional)
    alert('Generating schedule...');
    
    // Make an AJAX request to the backend to generate the schedule
    fetch('/generate_schedule', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    .then(response => response.json())
    .then(data => {
      // Show success message or update the page with new schedule
      alert('Schedule generated successfully');
      console.log(data.schedule); // This will give the generated schedule
      // Optionally, you can update the page with the schedule data here
    })
    .catch(error => {
      console.error('Error:', error);
      alert('Error generating the schedule');
    });
  });