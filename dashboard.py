# dashboard.py
from flask import Flask, render_template_string, jsonify
import os
from datetime import datetime

app = Flask(__name__)

# HTML template with AJAX update
TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Intrusion Log Dashboard</title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
</head>
<body class="bg-light">
    <div class="container my-5">
        <h1 class="mb-2 text-center">Intrusion Log Dashboard</h1>
        <div class="d-flex justify-content-between align-items-center mb-3">
            <small class="text-muted" id="lastRefresh">Last refresh: {{ now }}</small>
            <input type="text" id="search" onkeyup="filterTable()" class="form-control w-25" placeholder="Search logs…">
        </div>
        <div class="card shadow-sm">
            <div class="card-body p-0">
                <table class="table table-striped table-hover mb-0" id="logTable">
                    <thead class="thead-dark">
                        <tr>
                            <th scope="col">Timestamp</th>
                            <th scope="col">Message</th>
                        </tr>
                    </thead>
                    <tbody id="logBody">
                        {% for timestamp, message in entries %}
                        <tr>
                            <td>{{ timestamp }}</td>
                            <td>{{ message }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        function filterTable() {
            const query = document.getElementById('search').value.toLowerCase();
            document.querySelectorAll('#logBody tr').forEach(row => {
                row.style.display = row.innerText.toLowerCase().includes(query) ? '' : 'none';
            });
        }

        async function fetchLogs() {
            const res = await fetch('/api/logs');
            const data = await res.json();
            const tbody = document.getElementById('logBody');
            const searchTerm = document.getElementById('search').value.toLowerCase();
            tbody.innerHTML = '';
            data.entries.forEach(([timestamp, message]) => {
                const row = document.createElement('tr');
                row.innerHTML = `<td>${timestamp}</td><td>${message}</td>`;
                if (!timestamp.toLowerCase().includes(searchTerm) && !message.toLowerCase().includes(searchTerm)) {
                    row.style.display = 'none';
                }
                tbody.appendChild(row);
            });
            document.getElementById('lastRefresh').textContent = 'Last refresh: ' + data.now;
        }

        // Initial fetch and periodic updates
        fetchLogs();
        setInterval(fetchLogs, 10000);
    </script>
</body>
</html>
"""

LOG_FILES = ['honeypot.log', 'alerts.log']

@app.route('/')
def index():
    # Render initial page with combined logs
    entries = []
    for log_file in LOG_FILES:
        if os.path.exists(log_file):
            with open(log_file) as f:
                lines = f.read().splitlines()
            for line in lines:
                parts = line.strip().split(' - ', 1)
                if len(parts) == 2:
                    entries.append((parts[0], f"[{os.path.basename(log_file)}] {parts[1]}"))
    # Sort by timestamp descending
    entries.sort(key=lambda x: x[0], reverse=True)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return render_template_string(TEMPLATE, entries=entries, now=now)

@app.route('/api/logs')
def api_logs():
    # Provide combined logs as JSON
    entries = []
    for log_file in LOG_FILES:
        if os.path.exists(log_file):
            with open(log_file) as f:
                lines = f.read().splitlines()
            for line in lines:
                parts = line.strip().split(' - ', 1)
                if len(parts) == 2:
                    entries.append((parts[0], f"[{os.path.basename(log_file)}] {parts[1]}"))
    entries.sort(key=lambda x: x[0], reverse=True)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return jsonify({'now': now, 'entries': entries})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
