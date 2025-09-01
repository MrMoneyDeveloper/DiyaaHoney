-- Top 5 attacking IPs in the last 24 hours
SELECT ip, COUNT(*) AS attempts
FROM connections
WHERE ts > NOW() - INTERVAL '24 hours'
GROUP BY ip
ORDER BY attempts DESC
LIMIT 5;

-- Delete connections older than 30 days
DELETE FROM connections
WHERE ts < NOW() - INTERVAL '30 days';

-- Who was logged in when an alert fired
SELECT a.ip, a.message, u.username
FROM alerts a
JOIN connections c ON a.ip = c.ip
LEFT JOIN users u ON c.user_id = u.id;
