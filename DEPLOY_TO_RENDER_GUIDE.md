# COMPLETE GUIDE: DEPLOY FLASK APP TO RENDER

## PREP YOUR CODE (10 steps)

**STEP 1:** Open VS Code in your project folder

**STEP 2:** Right-click in folder → New File → name it `requirements.txt`

**STEP 3:** Paste this into requirements.txt:
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
gunicorn==21.2.0
```

**STEP 4:** Save the file (Ctrl+S)

**STEP 5:** Right-click in folder → New File → name it `render.yaml`

**STEP 6:** Paste this into render.yaml:
```yaml
services:
  - type: web
    name: flask-adventure-game
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "gunicorn app:app"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

**STEP 7:** Save the file (Ctrl+S)

**STEP 8:** Open app.py, find the bottom where it says `if __name__ == "__main__":`

**STEP 9:** Change `app.run(debug=True)` to `app.run(debug=False, host='0.0.0.0')`

**STEP 10:** Save app.py

---

## GET CODE ON GITHUB (16 steps)

**STEP 11:** Go to github.com

**STEP 12:** Sign up for account (if you don't have one) or log in

**STEP 13:** Click green "New" button (top left)

**STEP 14:** Repository name: `flask-adventure-game`

**STEP 15:** Leave it Public

**STEP 16:** Don't check any boxes

**STEP 17:** Click "Create repository"

**STEP 18:** GitHub shows you a page with commands - LEAVE THIS OPEN

**STEP 19:** Open Command Prompt/Terminal on your computer

**STEP 20:** Navigate to your project folder:
```
cd C:\Users\Uggr\Desktop\flask_db_adv
```

**STEP 21:** Type this and press Enter:
```
git init
```

**STEP 22:** Type this and press Enter:
```
git add .
```

**STEP 23:** Type this and press Enter:
```
git commit -m "first commit"
```

**STEP 24:** Copy the command from GitHub that looks like:
```
git remote add origin https://github.com/YOUR_USERNAME/flask-adventure-game.git
```
Paste into terminal, press Enter

**STEP 25:** Type this and press Enter:
```
git push -u origin master
```

**STEP 26:** Enter GitHub username and password when prompted

---

## DEPLOY ON RENDER (16 steps)

**STEP 27:** Go to render.com

**STEP 28:** Click "Get Started for Free"

**STEP 29:** Sign up with GitHub (easiest option)

**STEP 30:** Authorize Render to access GitHub

**STEP 31:** Click "New +" button (top right)

**STEP 32:** Select "Web Service"

**STEP 33:** Find your `flask-adventure-game` repo in the list, click "Connect"

**STEP 34:** Name: `flask-adventure-game`

**STEP 35:** Region: Choose closest to you

**STEP 36:** Branch: `master`

**STEP 37:** Build Command: should auto-fill from render.yaml

**STEP 38:** Start Command: should auto-fill from render.yaml

**STEP 39:** Select "Free" plan

**STEP 40:** Click "Create Web Service"

**STEP 41:** Wait 5-10 minutes for it to deploy

**STEP 42:** Click the URL at top of page to see your live site

---

## TROUBLESHOOTING

**If deployment fails:**
- Check the logs in Render dashboard
- Make sure all files are committed to GitHub
- Make sure requirements.txt has correct package names
- Make sure render.yaml is spelled correctly (not render.yml)

**If app loads but crashes:**
- Check if SECRET_KEY is set
- Check database is working (SQLite might not persist on Render - may need to switch to PostgreSQL)

**If you need to update the app:**
1. Make changes locally
2. In terminal: `git add .`
3. In terminal: `git commit -m "description of changes"`
4. In terminal: `git push`
5. Render will auto-deploy the changes

---

## TOTAL: 42 STEPS





