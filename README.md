##Autocom
---

## 🚀 Overview
This Flask web app lets users log in with GitHub, choose a repository, and generate contribution graph patterns by scheduling commits. Users can type a word or message, and the app automatically creates a GitHub Actions workflow that makes commits on specific dates to form that text on their contribution graph.

---

## ✨ Features
- GitHub OAuth login and authentication  
- Select repositories from your GitHub account  
- Convert text into 5×7 pixel art patterns for contributions  
- Preview SVG of contribution pattern before applying  
- Automatically generate and push GitHub Actions workflow  
- Store user and pattern history in SQLite  

---

## 🛠️ Tech Stack
- **Backend:** Flask (Python)  
- **Frontend:** Jinja2 templates (HTML)  
- **Database:** SQLite  
- **Auth:** GitHub OAuth (via Authlib)  
- **CI/CD:** GitHub Actions  

---

<img width="865" height="168" alt="image" src="https://github.com/user-attachments/assets/292e9c30-5423-4c2e-bfb4-e2fe32de5dd5" />


## 📦 Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/JB1071017/autcom.git
   cd autcom
   pip install -r requirements.txt
'''
Set up environment variables in .env:
```bash
SECRET_KEY=your_secret_key
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

python app.py
'''

