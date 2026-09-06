Personal Portfolio Flask Site - Module 1
Created with Codex assistance
=============================

Description
-----------
This project is a Flask website containing a home page, contact page, and
projects page.

Requirements
------------
- Python 3.10 or newer
- Flask

How to Run the Site on Windows
------------------------------
1. Open PowerShell or Command Prompt.

2. Change to the solution folder (the folder that contains the `homePage`
   folder):

   cd "path\to\module_1"

3. Create a virtual environment:

   python -m venv .venv

4. Activate the virtual environment.

   PowerShell:
   .\.venv\Scripts\Activate.ps1

   Command Prompt:
   .venv\Scripts\activate.bat

5. Install Flask:

   python -m pip install Flask

6. Start the Flask development server:

   python run.py

7. Open the site in a web browser at:

   http://localhost:8080/

Available Pages
---------------
- Home: http://localhost:8080/
- Contact: http://localhost:8080/contact
- Projects: http://localhost:8080/projects

Stopping the Site
-----------------
Return to the terminal where the server is running and press Ctrl+C.

Running the Site Again
----------------------
After the virtual environment has been created, use these commands from the
solution folder:

   .\.venv\Scripts\Activate.ps1
   python run.py

Notes
-----
- The `--debug` option reloads the server automatically when source files are
  changed. It is intended for development only.
- If PowerShell prevents virtual-environment activation, run the Flask command
  after activating the environment in Command Prompt instead.
