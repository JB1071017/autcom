from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import datetime  # Keep this for datetime.date and datetime.timedelta
from pathlib import Path
import requests
import yaml
import os
import base64
import json
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import sqlite3
from datetime import datetime as dt  # Import for current timestamp
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Allow insecure transport for development
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# GitHub OAuth configuration
oauth = OAuth(app)
github = oauth.register(
    name='github',
    client_id=os.environ.get('GITHUB_CLIENT_ID'),
    client_secret=os.environ.get('GITHUB_CLIENT_SECRET'),
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'repo'},
)

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         github_id INTEGER UNIQUE,
         github_login TEXT,
         access_token TEXT,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS patterns
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         user_id INTEGER,
         text_pattern TEXT,
         repo_name TEXT,
         commit_dates TEXT,
         workflow_created BOOLEAN,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         FOREIGN KEY (user_id) REFERENCES users (id))
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# 5x7 font map (A-Z, 0-9, space)
FONT = {
    "A": ["01110","10001","10001","11111","10001","10001","10001"],
    "B": ["11110","10001","11110","10001","10001","10001","11110"],
    "C": ["01111","10000","10000","10000","10000","10000","01111"],
    "D": ["11110","10001","10001","10001","10001","10001","11110"],
    "E": ["11111","10000","11110","10000","10000","10000","11111"],
    "F": ["11111","10000","11110","10000","10000","10000","10000"],
    "G": ["01111","10000","10000","10111","10001","10001","01111"],
    "H": ["10001","10001","10001","11111","10001","10001","10001"],
    "I": ["11111","00100","00100","00100","00100","00100","11111"],
    "J": ["11111","00100","00100","00100","10100","10100","01100"],
    "K": ["10001","10010","10100","11000","10100","10010","10001"],
    "L": ["10000","10000","10000","10000","10000","10000","11111"],
    "M": ["10001","11011","10101","10101","10001","10001","10001"],
    "N": ["10001","11001","10101","10011","10001","10001","10001"],
    "O": ["01110","10001","10001","10001","10001","10001","01110"],
    "P": ["11110","10001","11110","10000","10000","10000","10000"],
    "Q": ["01110","10001","10001","10001","10101","10010","01101"],
    "R": ["11110","10001","11110","10100","10010","10001","10001"],
    "S": ["11111","10000","11111","00001","00001","10001","11111"],
    "T": ["11111","00100","00100","00100","00100","00100","00100"],
    "U": ["10001","10001","10001","10001","10001","10001","11111"],
    "V": ["10001","10001","10001","10001","10001","01010","00100"],
    "W": ["10001","10001","10101","10101","10101","10101","01010"],
    "X": ["10001","01010","00100","00100","00100","01010","10001"],
    "Y": ["10001","01010","00100","00100","00100","00100","00100"],
    "Z": ["11111","00001","00010","00100","01000","10000","11111"],
    "0": ["01110","10001","10011","10101","11001","10001","01110"],
    "1": ["00100","01100","00100","00100","00100","00100","01110"],
    "2": ["11111","00001","00001","11111","10000","10000","11111"],
    "3": ["11111","00001","00001","11111","00001","00001","11111"],
    "4": ["10001","10001","10001","11111","00001","00001","00001"],
    "5": ["11111","10000","10000","11111","00001","00001","11111"],
    "6": ["11111","10000","10000","11111","10001","10001","11111"],
    "7": ["11111","00001","00010","00100","01000","01000","01000"],
    "8": ["11111","10001","10001","11111","10001","10001","11111"],
    "9": ["11111","10001","10001","11111","00001","00001","11111"],
    " ": ["00000","00000","00000","00000","00000","00000","00000"]
}

# default_branch = repo['default_branch']  # usually "main" or "master"

def next_sunday(today=None):
    """Return the next Sunday date from today (including today if it's Sunday)."""
    if today is None:
        today = datetime.date.today()  # Use datetime.date explicitly
    # weekday(): Monday=0 ... Sunday=6repo
    days_ahead = (6 - today.weekday()) % 7
    return today + datetime.timedelta(days=days_ahead)

def build_weeks_and_dates(message):
    """
    Build:
      - weeks: list of columns, each column is list of 7 strings '1'/'0' (Sunday..Saturday)
      - commit_dates: list of datetime.date where bit == '1'
    """
    start_date = next_sunday()
    weeks = []
    commit_dates = []
    col_offset = 0

    for ch in message.upper():
        if ch not in FONT:
            ch = " "
        matrix = FONT[ch]  # matrix is list of 7 strings length 5

        # for each column of the character (0..4) plus a spacing column (5)
        for col in range(6):
            col_bits = ["0"] * 7
            if col < 5:
                for row in range(7):
                    if matrix[row][col] == "1":
                        col_bits[row] = "1"
                        # compute date corresponding to this week column + row
                        commit_day = start_date + datetime.timedelta(weeks=col_offset + col, days=row)
                        commit_dates.append(commit_day)
            # append week column
            weeks.append(col_bits)
        col_offset += 6

    # sort and unique commit dates
    commit_dates = sorted(set(commit_dates))
    return start_date, weeks, commit_dates

def generate_svg(weeks, cell_size=12, gap=4, margin=10,
              filled_color="#239A3B", empty_color="#EBEDF0"):
    """Generate SVG as string."""
    weeks_count = len(weeks)
    if weeks_count == 0:
        return ""

    width = margin * 2 + weeks_count * cell_size + (weeks_count - 1) * gap
    height = margin * 2 + 7 * cell_size + (7 - 1) * gap

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    ]

    svg_parts.append(f'<rect width="100%" height="100%" fill="white" />')

    for col_index, col in enumerate(weeks):
        x = margin + col_index * (cell_size + gap)
        for row_index, bit in enumerate(col):
            y = margin + row_index * (cell_size + gap)
            color = filled_color if bit == "1" else empty_color
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" rx="2" ry="2" fill="{color}" />'
            )

    svg_parts.append("</svg>")
    return "\n".join(svg_parts)

def create_workflow_yaml(dates, repo_name):
    """Create GitHub Actions workflow YAML for automated commits."""
    workflow = {
        'name': 'Auto Commit for Contribution Pattern',
        'on': {
            'schedule': [],
            'workflow_dispatch': {}  # Allow manual triggering
        },
        'jobs': {
            'commit': {
                'runs-on': 'ubuntu-latest',
                'steps': [
                    {
                        'name': 'Checkout repository',
                        'uses': 'actions/checkout@v4'
                    },
                    {
                        'name': 'Setup Git',
                        'run': 'git config user.name "github-actions[bot]" && git config user.email "github-actions[bot]@users.noreply.github.com"'
                    },
                    {
                        'name': 'Create commit',
                        'run': 'echo "Automated commit for contribution pattern - $(date)" >> contributions.log && git add contributions.log && git commit -m "Auto commit: $(date)" || exit 0'
                    },
                    {
                        'name': 'Push changes',
                        'run': 'git push'
                    }
                ]
            }
        }
    }
    
    # Add scheduled triggers for each date
    for date in dates:
        # Convert to cron format: minute hour day month day_of_week
        cron_time = f"0 12 {date.day} {date.month} *"  # Run at 12:00 UTC on each date
        workflow['on']['schedule'].append({'cron': cron_time})
    
    return yaml.dump(workflow, default_flow_style=False, sort_keys=False)




def get_user_by_github_id(github_id):
    """Get user from database by GitHub ID."""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE github_id = ?', (github_id,)
    ).fetchone()
    conn.close()
    return user

def create_user(github_id, github_login, access_token):
    """Create new user in database."""
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO users (github_id, github_login, access_token) VALUES (?, ?, ?)',
            (github_id, github_login, access_token)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # User already exists, update access token
        conn.execute(
            'UPDATE users SET access_token = ? WHERE github_id = ?',
            (access_token, github_id)
        )
        conn.commit()
    finally:
        conn.close()

def save_pattern(user_id, text_pattern, repo_name, commit_dates, workflow_created):
    """Save pattern to database."""
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO patterns (user_id, text_pattern, repo_name, commit_dates, workflow_created) VALUES (?, ?, ?, ?, ?)',
        (user_id, text_pattern, repo_name, json.dumps([d.isoformat() for d in commit_dates]), workflow_created)
    )
    conn.commit()
    conn.close()

def get_user_patterns(user_id):
    """Get all patterns for a user."""
    conn = get_db_connection()
    patterns = conn.execute(
        'SELECT * FROM patterns WHERE user_id = ? ORDER BY created_at DESC', (user_id,)
    ).fetchall()
    conn.close()
    return patterns

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # Generate state parameter for security
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    
    redirect_uri = 'https://autcom.onrender.com/authorize'
    return github.authorize_redirect(redirect_uri, state=state)

@app.route('/authorize')
def authorize():
    try:
        # Verify state parameter
        if session.get('oauth_state') != request.args.get('state'):
            return "Invalid state parameter", 400
            
        token = github.authorize_access_token()
        if not token:
            return "Authorization failed: No token received"
        
        # Get user info from GitHub
        headers = {'Authorization': f'token {token["access_token"]}'}
        user_response = requests.get('https://api.github.com/user', headers=headers)
        
        if user_response.status_code != 200:
            return "Failed to get user info from GitHub"
        
        user_data = user_response.json()
        
        # Store user in database
        create_user(user_data['id'], user_data['login'], token['access_token'])
        
        # Store in session
        session['user_id'] = user_data['id']
        session['github_login'] = user_data['login']
        session['access_token'] = token['access_token']
        
        # Clear state
        session.pop('oauth_state', None)
        
        return redirect(url_for('dashboard'))
    except Exception as e:
        return f"Error during authorization: {str(e)}"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's repositories
    headers = {'Authorization': f'token {session["access_token"]}'}
    response = requests.get('https://api.github.com/user/repos', headers=headers)
    
    if response.status_code != 200:
        return f"Error fetching repositories: {response.json()}"
    
    repos = response.json()
    
    # Get user's previous patterns
    user_patterns = get_user_patterns(session['user_id'])
    
    return render_template('dashboard.html', 
                         repos=repos, 
                         patterns=user_patterns,
                         github_login=session['github_login'])

@app.route('/generate', methods=['POST'])
def generate_pattern():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    import base64

    data = request.json
    text = data.get('text', '').strip()
    repo_full_name = data.get('repo')  # Must be "username/repo"

    if not text:
        return jsonify({'error': 'Text is required'}), 400
    if not repo_full_name:
        return jsonify({'error': 'Repository is required'}), 400

    # Generate contribution pattern
    start_date, weeks, commit_dates = build_weeks_and_dates(text)
    svg_content = generate_svg(weeks)
    workflow_yaml = create_workflow_yaml(commit_dates, repo_full_name)

    headers = {'Authorization': f'token {session["access_token"]}'}

    # 1️⃣ Get repository info to fetch default branch
    repo_info_resp = requests.get(f'https://api.github.com/repos/{repo_full_name}', headers=headers)
    if repo_info_resp.status_code != 200:
        return jsonify({
            'error': 'Failed to fetch repository info. Make sure the repository exists and you have access.',
            'details': repo_info_resp.json()
        }), 400
    repo_info = repo_info_resp.json()
    default_branch = repo_info.get('default_branch', 'main')

    # 2️⃣ Ensure .github/workflows folder exists safely
    workflows_url = f"https://api.github.com/repos/{repo_full_name}/contents/.github/workflows?ref={default_branch}"
    folder_resp = requests.get(workflows_url, headers=headers)

    if folder_resp.status_code == 404:
        # Try to create placeholder file to create the folder
        placeholder_url = f"https://api.github.com/repos/{repo_full_name}/contents/.github/workflows/README.md"
        placeholder_content = base64.b64encode(b"# Workflows folder").decode('utf-8')
        create_folder_resp = requests.put(
            placeholder_url,
            json={
                "message": "Create workflows folder",
                "content": placeholder_content,
                "branch": default_branch
            },
            headers=headers
        )
        if create_folder_resp.status_code not in (200, 201):
            return jsonify({
                'error': 'Failed to create workflows folder. Make sure you have write access to this repository and the branch is not protected.',
                'details': create_folder_resp.json()
            }), 400

    # 3️⃣ Create the actual workflow file
    workflow_url = f"https://api.github.com/repos/{repo_full_name}/contents/.github/workflows/contribution-pattern.yml"
    workflow_content = {
        "message": "Add automated contribution workflow",
        "content": base64.b64encode(workflow_yaml.encode('utf-8')).decode('utf-8'),
        "branch": default_branch
    }

    response = requests.put(workflow_url, json=workflow_content, headers=headers)
    workflow_created = response.status_code in (200, 201)

    if not workflow_created:
        return jsonify({
            'error': 'Failed to create workflow file. Make sure you have write access and the repository is valid.',
            'details': response.json()
        }), 400

    # 4️⃣ Save pattern if workflow was created
    save_pattern(session['user_id'], text, repo_full_name, commit_dates, workflow_created)

    # 5️⃣ Return result
    result = {
        'text': text,
        'start_date': start_date.isoformat(),
        'commit_dates': [d.isoformat() for d in commit_dates],
        'svg': svg_content,
        'workflow_created': workflow_created,
        'weeks_count': len(weeks)
    }

    return jsonify(result)



@app.route('/preview', methods=['POST'])
def preview_pattern():
    data = request.json
    print("Received data:", data)
    text = data.get('text', '').strip()
    repo_full_name = data.get('repo')
    print("Text:", text, "Repo:", repo_full_name)
    
    if not text:
        return jsonify({'error': 'Text is required'}), 400
    
    start_date, weeks, commit_dates = build_weeks_and_dates(text)
    svg_content = generate_svg(weeks)
    
    return jsonify({
        'text': text,
        'start_date': start_date.isoformat(),
        'commit_dates': [d.isoformat() for d in commit_dates],
        'svg': svg_content,
        'weeks_count': len(weeks)
    })

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

