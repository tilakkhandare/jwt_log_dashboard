# Flask Log Rotation & JWT-Protected `/logs` Dashboard Endpoint

This project implements size-based log rotation using Python's `logging.handlers.RotatingFileHandler` and exposes a JWT-protected `/logs` endpoint to retrieve the most recent `N` log entries.

## Features
1. **Size-Based Log Rotation (`RotatingFileHandler`)**: Writes structured logs to `logs/app.log`, rotating automatically at `10 KB` and keeping up to 3 backup files (`app.log.1`, `app.log.2`, `app.log.3`).
2. **JWT Authentication (`Flask-JWT-Extended`)**: Protects `/logs` and `/activity` endpoints so only authenticated users can inspect logs.
3. **Recent Log Retrieval (`GET /logs?lines=N`)**: Uses `collections.deque` to efficiently read the last `N` lines from the active log file (defaults to `20`).
4. **Activity Generator & Automated Tests**: Includes `/activity` endpoint and `test_app.py` to test log generation, file rotation, and authenticated log retrieval.

## Setup & Run

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run automated verification tests**:
   ```bash
   python test_app.py
   ```

3. **Start the server**:
   ```bash
   python app.py
   ```

## API Usage Examples

### 1. Login to obtain a JWT token
```bash
curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 2. Generate sample log activity
```bash
curl -X POST http://127.0.0.1:5000/activity \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"count": 15, "message": "Processed user order"}'
```

### 3. View the last N log entries
```bash
curl -X GET "http://127.0.0.1:5000/logs?lines=10" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```
