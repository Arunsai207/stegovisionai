StegoVisionAI
Advanced Forensics Workspace · Academic / Research Edition
StegoVisionAI is a Windows-first web application built with FastAPI for image steganography workflows and introductory image forensics. It brings account registration and login, message encoding and extraction, image inspection, and analysis history into one local workspace.

This build also includes dual-image comparison, heuristic color-histogram similarity, per-user analytics, history deletion endpoints, and optional OpenCV face-region detection.
Scope note: StegoVisionAI is an academic/research tool, not a certified forensic product. Results are indicators for further investigation—not proof of authenticity, manipulation, identity, or hidden content.

Contents
- Features
- Requirements
- Quick start on Windows
- Manual setup in CMD
- First use
- Encode and extract a message
- Forensics and Advanced Lab
- API reference
- Configuration and data
- Run tests
- Troubleshooting
- Security and limitations
Features
Core workspace
- Account registration and login.
- Encode a secret message into a supported image and save the result as PNG.
- Extract a supported hidden payload using the matching passphrase.
- Inspect supported image properties and metadata.
- Calculate SHA-256 hashes.
- Review analysis history.
Advanced tools in this build
- Image comparison: compare two images' hashes, dimensions, and pixel-related properties.
- Color similarity: calculate a coarse color-histogram similarity score. This is heuristic and is not semantic image understanding.
- Face-region detection: use an OpenCV Haar cascade to locate candidate face regions. It does not identify a person or verify identity.
- Per-user analytics: summarize saved analyses by type.
- History management: API endpoints to delete one analysis or clear the current user's history.
Requirements
- Windows 10 or Windows 11.
- Python 3.12 or newer, installed from python.org.
- During installation, enable the Python launcher and Add Python to PATH when those options are available.
- Internet access on first setup so pip can install dependencies.
- A current browser such as Microsoft Edge or Google Chrome.
Check the installation in Command Prompt (CMD):
py --version
python --version
If neither command works, reinstall Python and enable PATH/launcher options, then open a new CMD window.
Quick start on Windows (recommended)
1. Download and extract the project ZIP.
2. Open the extracted StegoVisionAI folder. Confirm that run_windows.bat, requirements.txt, and the app folder are visible.
3. Double-click run_windows.bat.
4. On first run, the launcher creates a .venv virtual environment, upgrades pip, installs the dependencies, and starts the local web server. This can take a few minutes.
5. Read the URL printed in the Command Prompt window. Open it in your browser.
6. Keep the Command Prompt window open while using the app. To stop the server, return to that window and press Ctrl+C.
Default local addresses:
Purpose	URL
Application	http://127.0.0.1:8000/
Interactive API documentation	http://127.0.0.1:8000/docs
Health check	http://127.0.0.1:8000/api/health


If port 8000 is already occupied, run_windows.bat automatically selects port 8001. In that case, replace 8000 with 8001 in the URLs above. Always use the URL printed by the launcher.
Manual setup in Command Prompt
Use these steps if you prefer not to double-click the launcher.
1. Open the extracted StegoVisionAI folder in File Explorer.
2. Click the address bar, type cmd, and press Enter. A Command Prompt opens in that folder.
3. Run these commands one at a time:
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
4. Open http://127.0.0.1:8000/ in your browser.
If py -3.12 is unavailable but Python 3.12+ is installed, use py -3 -m venv .venv for the first command. If port 8000 is busy, change the last command to --port 8001 and open http://127.0.0.1:8001/. The manual command does not automatically choose a fallback port; the Windows launcher does.
First use
1. Open the application using the URL shown in CMD.
2. Choose the registration/create-account option if you do not already have an account.
3. Enter the requested account details and submit the form.
4. Sign in using the same email address and password.
5. Choose a workspace section such as Encode message, Extract message, Image forensics, or Advanced Lab.
Passwords are hashed before storage. Use a unique password and do not share account credentials or application secrets.
Encode and extract a message
Encode
1. Open Encode message.
2. Select a supported carrier image.
3. Enter the secret message and a passphrase, following the form's validation rules.
4. Start encoding and wait for the result.
5. If available, select Verify decode now to test the exact encoded PNG produced by the encoder.
6. Save the generated file, normally named with the suffix *_stegovision.png.
Extract
1. Open Extract message.
2. Upload the generated *_stegovision.png file—not the original carrier image.
3. Enter exactly the same passphrase used during encoding.
4. Start extraction and review the returned result.
Important: Keep the encoded PNG unchanged. Re-saving it as JPEG, editing it, or sending it through a service that recompresses images may damage the hidden payload. A 400 Bad Request response usually means that no supported payload was found, the image was changed, or the passphrase/integrity check failed. Read the message displayed in the application for the specific reason.
Image forensics and Advanced Lab
- Image forensics: review supported image properties/metadata and the SHA-256 hash.
- Image comparison: submit two images to compare their file hashes, dimensions, and pixel-related properties.
- Color similarity: view a heuristic color-histogram score. Similar colors do not prove that two images show the same subject or scene.
- Face-region detection: detect candidate face regions with OpenCV Haar cascades. This is region detection only—not facial recognition or identity verification.
- History and analytics: inspect available saved analysis records and per-user analysis summaries. History deletion is also available through the documented API endpoints.
Use only images, files, and camera sources you own or are authorized to analyze.
API reference
Start the app and open /docs on the active local port for interactive request schemas and response details.
Existing endpoints
Method	Endpoint	Purpose
POST	/api/auth/register	Register an account
POST	/api/auth/login	Log in
GET	/api/auth/me	Get the current authenticated user
POST	/api/encode	Encode a message into an image
POST	/api/decode	Extract a supported payload
POST	/api/forensics	Inspect an image
GET	/api/history	Retrieve available analysis history
GET	/api/health	Check service health


Advanced endpoints
Method	Endpoint	Purpose
POST	/api/compare	Compare two images
POST	/api/similarity	Calculate heuristic color similarity
POST	/api/faces/detect	Detect candidate face regions
GET	/api/analytics	Summarize analyses by type
DELETE	/api/history/{analysis_id}	Delete one history item
DELETE	/api/history	Clear the current user's history


The API requires the relevant authentication where applicable. Use /docs as the source of truth for the exact payload fields and responses in the installed build.
Configuration and data
- Database: SQLite; by default, stegovision.db is created in the application's working directory.
- DATABASE_PATH: optional path to a custom SQLite database file.
- APP_SECRET: signing secret. Set a strong private value for your environment; do not publish it or commit it to source control.
Example for the current CMD session (change the path to a folder that exists on your computer):
set APP_SECRET=replace-with-a-long-random-secret
set DATABASE_PATH=C:\StegoVisionData\stegovision.db
run_windows.bat
Create C:\StegoVisionData before starting the app if it does not already exist. These set commands apply only to the current CMD window. Do not put real secrets in screenshots, public repositories, or shared logs.
Run tests
From CMD in the project folder:
.venv\Scripts\activate
python -m pytest -q
A successful run ends with a passing-test summary. The exact result can vary if source code or dependency versions change.
Troubleshooting
Problem	What to do
py or python is not recognized	Install Python 3.12+, enable PATH/launcher options, and open a new CMD window.
Dependency installation fails	Check internet access and the Python version. Copy the complete pip error output for diagnosis.
Port 8000 is already in use	Use run_windows.bat and open the URL it prints; it should switch to port 8001.
The application page does not load	Confirm the server is still running in CMD and use the exact host and port printed there.
Registration says the email already exists	Sign in with the existing account.
Login fails	Check the email/password combination and try again.
No hidden payload is found	Upload the generated *_stegovision.png, not the original carrier image.
Passphrase or integrity mismatch	Use the exact original passphrase and ensure the encoded PNG has not been edited or recompressed.
Face detection is unavailable	Activate .venv and run python -m pip install -r requirements.txt, then restart the app.
Database path error	Confirm the parent directory in DATABASE_PATH exists and is writable.


Security and limitations
- This project is intended for local academic/research use, not as a certified forensic product.
- It does not provide trained deepfake or general-purpose steganography-classification models, semantic image embeddings, a face-embedding identity model, or production-grade real-time camera streaming.
- Similarity scores are heuristic. They are not proof of identity, authenticity, manipulation, or the presence/absence of a hidden payload.
- Face-region detection locates candidate regions; it does not identify people.
- The default server binds to 127.0.0.1 for local access. Do not expose this development server directly to the public internet without a security review and appropriate deployment controls.
- Analyze only content you own or are authorized to inspect.
Project structure
StegoVisionAI/
├── app/
│   ├── main.py             # FastAPI application and API routes
│   ├── auth.py             # Authentication helpers
│   ├── database.py         # SQLite setup and data access
│   ├── stego.py            # Encoding/decoding workflow
│   ├── forensics.py        # Image inspection helpers
│   ├── advanced.py         # Comparison, similarity, detection, analytics
│   └── static/             # Web interface assets
├── ml/                     # Baseline ML training notes/script
├── tests/                  # Automated tests
├── requirements.txt
├── run_windows.bat
└── README.md
Local development tip: keep the server terminal open while working, and use the active URL/port printed by the launcher rather than assuming port 8000 every time.