# Autcom

🚀 Overview

This Flask web app lets users log in with GitHub, choose a repository, and generate contribution graph patterns by scheduling commits. Users can type a word or message, and the app automatically creates a GitHub Actions workflow that makes commits on specific dates to form that text on their contribution graph.

✨ Features

GitHub OAuth login and authentication

Select repositories from your GitHub account

Convert text into 5×7 pixel art patterns for contributions

Preview SVG of contribution pattern before applying

Automatically generate and push GitHub Actions workflow

Store user and pattern history in SQLite

🛠️ Tech Stack

Backend: Flask (Python)

Frontend: Jinja2 templates (HTML)

Database: SQLite

Auth: GitHub OAuth (via Authlib)

CI/CD: GitHub Actions

📦 Installation

Clone the repository:

git clone https://github.com/yourusername/yourrepo.git
cd yourrepo


Install dependencies:

pip install -r requirements.txt


Set up environment variables in .env:

SECRET_KEY=your_secret_key
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret


Run the app:

python app.py

📌 Usage

Log in with GitHub

Choose a repository

Enter text to generate a commit pattern

Preview your contribution graph SVG

Confirm to apply — the app creates a GitHub Actions workflow that handles commits automatically

🗄️ Database

The app uses users.db (SQLite) with two tables:

users: stores GitHub user info and tokens

patterns: stores text patterns, repositories, commit dates, and workflow info

⚠️ Disclaimer

Use responsibly. Automated commits will modify your contribution graph and repository history.
