"""
dashboard.py — Call Analytics Dashboard (Day 8 feature)

A lightweight aiohttp web server that serves a real-time analytics dashboard
by querying the local SQLite database.
"""

import os
import sqlite3
from pathlib import Path
from aiohttp import web
from database import _get_connection

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Arthashathi Call Analytics</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f8fafc;
            color: #1e293b;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 {
            color: #0f172a;
            margin-bottom: 40px;
        }
        .dashboard-container {
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 1000px;
            width: 100%;
        }
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            padding: 32px 24px;
            flex: 1;
            min-width: 200px;
            text-align: center;
            transition: transform 0.2s ease-in-out;
        }
        .card:hover {
            transform: translateY(-2px);
        }
        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 12px;
        }
        .card-value {
            font-size: 3.5rem;
            font-weight: 700;
            color: #0f172a;
            margin: 0;
            line-height: 1;
        }
        .card.success .card-value { color: #16a34a; }
        .card.failed .card-value { color: #dc2626; }
        .footer {
            margin-top: 40px;
            color: #94a3b8;
            font-size: 0.9rem;
        }
        .refresh-notice {
            margin-top: 12px;
            font-size: 0.85rem;
            color: #cbd5e1;
        }
    </style>
    <!-- Auto-refresh every 5 seconds -->
    <meta http-equiv="refresh" content="5">
</head>
<body>
    <h1>Arthashathi Call Analytics</h1>
    
    <div class="dashboard-container">
        <div class="card">
            <div class="card-title">Total Calls</div>
            <p class="card-value">__TOTAL_CALLS__</p>
        </div>
        
        <div class="card success">
            <div class="card-title">Successful</div>
            <p class="card-value">__SUCCESSFUL_CALLS__</p>
        </div>
        
        <div class="card failed">
            <div class="card-title">Failed</div>
            <p class="card-value">__FAILED_CALLS__</p>
        </div>
    </div>
    
    <div class="footer">
        Data queried live from SQLite. Auto-refreshing every 5 seconds.
    </div>
</body>
</html>
"""

async def handle_dashboard(request):
    """Handle requests to the dashboard and fetch live stats."""
    total_calls = 0
    successful_calls = 0
    failed_calls = 0
    
    try:
        with _get_connection() as conn:
            # Check if table exists first
            table_exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='call_analytics'"
            ).fetchone()
            
            if table_exists:
                total_calls = conn.execute("SELECT COUNT(*) FROM call_analytics").fetchone()[0]
                successful_calls = conn.execute("SELECT COUNT(*) FROM call_analytics WHERE outcome = 'SUCCESS'").fetchone()[0]
                failed_calls = conn.execute("SELECT COUNT(*) FROM call_analytics WHERE outcome = 'FAILED'").fetchone()[0]
    except Exception as e:
        print(f"Error querying analytics DB: {e}")

    html_content = HTML_TEMPLATE.replace(
        "__TOTAL_CALLS__", str(total_calls)
    ).replace(
        "__SUCCESSFUL_CALLS__", str(successful_calls)
    ).replace(
        "__FAILED_CALLS__", str(failed_calls)
    )
    return web.Response(text=html_content, content_type='text/html')

async def handle_api(request):
    """Day 8 JSON API for React Frontend"""
    total = 0; success = 0; failed = 0
    history = []; task_stats = {}
    try:
        with _get_connection() as conn:
            if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='call_analytics'").fetchone():
                total = conn.execute("SELECT COUNT(*) FROM call_analytics").fetchone()[0]
                success = conn.execute("SELECT COUNT(*) FROM call_analytics WHERE outcome = 'SUCCESS'").fetchone()[0]
                failed = conn.execute("SELECT COUNT(*) FROM call_analytics WHERE outcome = 'FAILED'").fetchone()[0]
                rows = conn.execute("SELECT started_at, duration_seconds, channel, language, task_type, outcome, success_reason FROM call_analytics ORDER BY id DESC LIMIT 20").fetchall()
                for r in rows:
                    history.append({
                        "started_at": r[0], "duration_seconds": r[1], "channel": r[2],
                        "language": r[3], "task_type": r[4], "outcome": r[5], "success_reason": r[6]
                    })
                for r in conn.execute("SELECT task_type, COUNT(*) FROM call_analytics GROUP BY task_type").fetchall():
                    task_stats[r[0] or "Unknown"] = r[1]
    except Exception as e:
        print(f"Error querying DB for API: {e}")
    
    rate = round((success / total * 100), 1) if total > 0 else 0
    return web.json_response({
        "total_calls": total, "successful_calls": success, "failed_calls": failed,
        "success_rate": rate, "history": history, "task_stats": task_stats
    }, headers={'Access-Control-Allow-Origin': '*'})

def main():
    app = web.Application()
    app.add_routes([
        web.get('/', handle_dashboard),
        web.get('/api/stats', handle_api)
    ])
    port = int(os.environ.get("DASHBOARD_PORT", 8080))
    print(f"Starting Arthashathi Analytics Dashboard on http://localhost:{port}")
    web.run_app(app, host="127.0.0.1", port=port)

if __name__ == '__main__':
    main()
