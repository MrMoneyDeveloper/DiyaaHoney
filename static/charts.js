fetch('/stats')
  .then(r => r.json())
  .then(data => {
    const ctx = document.getElementById('ipChart');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map(d => d.ip),
        datasets: [{
          label: 'Hits',
          data: data.map(d => d.hits),
          backgroundColor: 'rgba(54, 162, 235, 0.5)'
        }]
      }
    });
  });
