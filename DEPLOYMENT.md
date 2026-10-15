# 🚀 Deployment Guide for EcoCode AI

EcoCode AI is an interactive **Streamlit** application that utilizes WebSockets, CodeCarbon background tracking, and AST sandboxed execution.

---

## 🌟 Recommended: Streamlit Community Cloud (100% Free & 1-Click)

The official and easiest way to deploy any Streamlit application for free:

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - EcoCode AI"
   git branch -M main
   git remote add origin https://github.com/<your-username>/Eco-Code-AI.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Community Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
   - Click **"New app"**.
   - Select your repository (`<your-username>/Eco-Code-AI`), branch (`main`), and set **Main file path** to `app.py`.
   - Click **"Advanced settings"** -> **"Secrets"**, and paste your API key:
     ```toml
     GEMINI_API_KEY = "your_actual_gemini_api_key"
     ```
   - Click **"Deploy!"**. Your app will be live with a free `*.streamlit.app` URL within 2 minutes!

---

## 🐳 Option 2: Render.com (Free Web Service / Docker)

Render supports persistent Python web applications and Docker containers:

1. Push your repository to GitHub.
2. Go to [render.com](https://render.com) and create a **New Web Service**.
3. Connect your GitHub repository.
4. Choose **Docker** environment (it automatically detects the included `Dockerfile`), or **Python 3**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
5. In **Environment Variables**, add:
   - `GEMINI_API_KEY`: your Gemini API key.
6. Click **Deploy Web Service**.

---

## 🤗 Option 3: Hugging Face Spaces (Free Cloud Hosting)

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **"Create new Space"**.
2. Select **Streamlit** as the Space SDK.
3. Push your repository code to the Hugging Face Git remote.
4. Go to **Settings** -> **Variables and secrets** and add `GEMINI_API_KEY`.

---

## ⚠️ Why Not Vercel?

**Vercel** is built for serverless Jamstack architectures (Next.js, static HTML, short-lived stateless Lambdas).
- Streamlit requires a persistent, long-lived Python server with continuous bidirectional WebSockets (`_stcore/stream`) to communicate between the browser and Python process.
- Serverless platforms like Vercel freeze and terminate execution after requests (10-60s limit), which breaks Streamlit's reactive session state and background subprocess monitoring (CodeCarbon).
- For a seamless live experience, **Streamlit Community Cloud** or **Render** are the ideal free hosting choices for this architecture.
