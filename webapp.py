from flask import Flask, render_template_string, jsonify, request
import database as db
import utils

app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sonic Bot Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; color: #fff; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        header { text-align: center; padding: 30px 0; }
        header h1 { font-size: 2.5em; color: #00d4ff; text-shadow: 0 0 20px rgba(0, 212, 255, 0.5); }
        header p { color: #aaa; margin-top: 10px; }
        .time-display { margin-top: 15px; font-size: 1.5em; color: #00ff88; font-weight: bold; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }
        .stat-card { background: rgba(255,255,255,0.1); border-radius: 15px; padding: 25px; text-align: center; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
        .stat-card h3 { font-size: 3em; color: #00d4ff; }
        .stat-card p { color: #aaa; margin-top: 5px; }
        .section { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 25px; margin: 20px 0; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
        .section h2 { color: #00d4ff; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #00d4ff; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        th { background: rgba(0,212,255,0.2); color: #00d4ff; }
        tr:hover { background: rgba(255,255,255,0.05); }
        .status { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }
        .status.online { background: #00ff88; box-shadow: 0 0 10px #00ff88; }
        .status.offline { background: #ff4444; box-shadow: 0 0 10px #ff4444; }
        .refresh-btn { background: linear-gradient(135deg, #00d4ff, #0099cc); border: none; color: white; padding: 12px 30px; border-radius: 25px; cursor: pointer; font-size: 1em; transition: transform 0.2s; }
        .refresh-btn:hover { transform: scale(1.05); }
        @media (max-width: 768px) { .container { padding: 10px; } header h1 { font-size: 1.8em; } }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 Sonic Bot Dashboard</h1>
            <p>Designed and Developed by Arnicka Studios</p>
            <p class="time-display"><span class="status online"></span><span id="currentTime">--:--:--</span></p>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <h3 id="userCount">0</h3>
                <p>Total Users</p>
            </div>
            <div class="stat-card">
                <h3 id="msgCount">0</h3>
                <p>Total Messages</p>
            </div>
            <div class="stat-card">
                <h3><span class="status online"></span>Active</h3>
                <p>Bot Status</p>
            </div>
        </div>

        <div class="section">
            <h2>👥 Registered Users</h2>
            <table>
                <thead>
                    <tr><th>User ID</th><th>Name</th><th>City</th><th>Registered</th></tr>
                </thead>
                <tbody id="usersTable">
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>🔍 Web Search</h2>
            <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                <input type="text" id="searchInput" placeholder="Ask anything..." style="flex: 1; padding: 12px; border-radius: 25px; border: none; outline: none; font-size: 1em;">
                <button class="refresh-btn" onclick="performSearch()">Search</button>
            </div>
            <div id="searchResults" style="background: rgba(0,0,0,0.2); padding: 15px; border-radius: 10px; min-height: 50px;"></div>
        </div>

        <div class="section">
            <h2>💬 Recent Messages</h2>
            <button class="refresh-btn" onclick="loadData()">🔄 Refresh</button>
            <table style="margin-top: 15px;">
                <thead>
                    <tr><th>Time</th><th>User</th><th>City</th><th>Message</th><th>Response</th></tr>
                </thead>
                <tbody id="messagesTable">
                </tbody>
            </table>
        </div>
    </div>

    <script>
        function updateTime() {
            const now = new Date();
            const timeString = now.toLocaleTimeString('en-US', { hour12: true });
            document.getElementById('currentTime').textContent = timeString;
        }
        
        function performSearch() {
            const query = document.getElementById('searchInput').value;
            if (!query) return;
            
            document.getElementById('searchResults').innerHTML = '🔍 Searching...';
            
            fetch('/api/search?q=' + encodeURIComponent(query))
                .then(res => res.json())
                .then(data => {
                    document.getElementById('searchResults').innerHTML = data.result;
                })
                .catch(err => {
                    document.getElementById('searchResults').innerHTML = 'Search failed. Please try again.';
                });
        }
        
        document.getElementById('searchInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') performSearch();
        });
        
        function loadData() {
            fetch('/api/data')
                .then(res => res.json())
                .then(data => {
                    document.getElementById('userCount').textContent = data.user_count;
                    document.getElementById('msgCount').textContent = data.msg_count;
                    
                    let usersHtml = '';
                    data.users.forEach(user => {
                        usersHtml += `<tr>
                            <td>${user[0]}</td>
                            <td>${user[1]}</td>
                            <td>${user[2]}</td>
                            <td>${user[3]}</td>
                        </tr>`;
                    });
                    document.getElementById('usersTable').innerHTML = usersHtml;

                    let msgsHtml = '';
                    data.messages.forEach(msg => {
                        msgsHtml += `<tr>
                            <td>${msg[0]}</td>
                            <td>${msg[1]}</td>
                            <td>${msg[2]}</td>
                            <td>${msg[3]}</td>
                            <td>${msg[4]}</td>
                        </tr>`;
                    });
                    document.getElementById('messagesTable').innerHTML = msgsHtml;
                });c
        }
        
        updateTime();
        setInterval(updateTime, 1000);
        loadData();
        setInterval(loadData, 10000);
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(INDEX_HTML)

@app.route("/api/data")
def api_data():
    users = db.get_all_users()
    messages = db.get_recent_messages(20)
    return jsonify({
        "users": users,
        "messages": messages,
        "user_count": len(users),
        "msg_count": len(db.get_recent_messages(10000))
    })

@app.route("/api/search")
def api_search():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"result": "Please enter a search query"})
    
    result = utils.search_web(query)
    return jsonify({"result": result or "No results found"})

def run_web():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    run_web()

