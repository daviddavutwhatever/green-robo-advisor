# Put the Green Robo Advisor online (free, about 10 minutes)

The result is a public link such as `https://green-robo-advisor.streamlit.app` that anyone in class can open in a browser. Nothing needs to be installed.

The app runs on **Streamlit Community Cloud** (free) and reads the code from **GitHub** (free).

## 1. Put the project on GitHub

1. Create a free account at https://github.com (skip this if you have one).
2. Click **+ → New repository**.
   - Name: `green-robo-advisor`
   - Visibility: **Public**
   - Tick **Add a README file**
   - Click **Create repository**.
3. In the new repository, click **Add file → Upload files**.
4. Unzip the project. Open the `green-robo` folder and drag **everything inside it** into the upload area: `green_robo_advisor/`, `tests/`, `docs/`, `run_demo.py`, `environment.yml` and the rest. Then click **Commit changes**.
5. **Important:** check that the hidden folder `.streamlit` (holds the dark theme) was uploaded too.
   - **Mac:** hidden files are invisible in Finder. Press **Cmd + Shift + .** to show them before dragging.
   - **Windows:** in File Explorer, choose **View → Show → Hidden items**.
   - If it is still missing, create it on GitHub instead: **Add file → Create new file**, name it `.streamlit/config.toml`, and paste the content of that file.

## 2. Deploy on Streamlit Community Cloud

1. Go to https://share.streamlit.io and click **Continue with GitHub**. Allow access.
2. Click **Create app → Deploy a public app from GitHub**.
3. Fill in:
   - **Repository:** `your-username/green-robo-advisor`
   - **Branch:** `main`
   - **Main file path:** `green_robo_advisor/app.py`
   - **App URL:** choose a name, e.g. `green-robo-advisor` (it becomes `green-robo-advisor.streamlit.app`).
4. Optional: under **Advanced settings**, choose Python **3.12**.
5. Click **Deploy**. The first start installs the packages from `green_robo_advisor/requirements.txt` and takes a few minutes. After that, the app opens.

Share the link with the class.

## 3. Good to know

- **Updates:** change a file on GitHub (or upload a new version) and the app updates itself within a minute.
- **Sleep:** an app that has had no visitors for a while goes to sleep. The next visitor sees a button to wake it up, and it is back in under a minute. Open the link yourself shortly before the presentation.
- **Data:** the app opens with the offline **sample** data (10 ESG ETFs), so it does not depend on Yahoo Finance.
- **Two dependency files:** `green_robo_advisor/requirements.txt` is used online. `environment.yml` stays for working locally with conda.
- **Problems:** on share.streamlit.io, open the app's **Manage app** panel (bottom right) to see the log. The most common cause is a file that was not uploaded.
