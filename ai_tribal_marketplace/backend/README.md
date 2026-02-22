---
# 🎨 Indian Tribal Art Analyzer (Local AI Backend)

A FastAPI backend that analyzes Indian tribal artwork images using a  **fully local Vision LLM (LLaVA via Ollama)** .

No OpenAI API.
No billing.
Runs entirely on your machine.
---
# 🏗 Tech Stack

* 🐍 Python 3.10+
* ⚡ FastAPI
* 🗄 SQLAlchemy
* 🤖 Ollama
* 👁 LLaVA Vision Model
* 🖼 Pillow

---

# 📦 1️⃣ Install Ollama

## 🔹 Windows

Download installer from:

👉 [https://ollama.com/download](https://ollama.com/download)

After installation, verify:

```bash
ollama --version
```

---

# 🚀 2️⃣ Start Ollama Server

```bash
ollama serve
```

Leave this running.

Ollama runs locally at:

```
http://localhost:11434
```

---

# 🤖 3️⃣ Download Vision Model

Pull the LLaVA model (only once):

```bash
ollama pull llava
```

Optional (higher quality, more RAM needed):

```bash
ollama pull llava:13b
```

---

# 💻 System Requirements

Minimum:

* 8GB RAM
* CPU supported

Recommended:

* 16GB RAM
* GPU optional

---

# 🐍 4️⃣ Setup Python Backend

## Create virtual environment

```bash
python -m venv venv
```

Activate:

Linux/Mac:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install fastapi uvicorn sqlalchemy pillow ollama
```

If using PostgreSQL:

```bash
pip install psycopg2-binary
```

---

# 🗄 5️⃣ Configure Database

Make sure your database is configured in:

```
database.py
```

If using SQLite for testing, you can use:

```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
```

---

# ▶️ 6️⃣ Run Backend Server

From project root:

```bash
uvicorn app.main:app --reload
```

If your structure is different:

```bash
uvicorn main:app --reload
```

You should see:

```
Uvicorn running on http://127.0.0.1:8000
```

---

# 🧪 7️⃣ Test API

Open browser:

```
http://127.0.0.1:8000/docs
```

You’ll see Swagger UI.

---

# 🎨 Creator Endpoint

POST:

```
/generate/
```

Upload:

* Image file

Optional query params:

* `languages=hindi,tamil`
* `length=medium`
* `tone=poetic`
* `audience=general`

---

# 📚 Scholar Endpoint

POST:

```
/generate/history
```

Upload:

* Image file

Optional:

* `question=Explain its symbolism`

---

# 📜 View Past Results

GET:

```
/history/
```

---

# 🧠 How It Works

```text
User Uploads Image
        ↓
Temp File Created
        ↓
Ollama (llava) Vision Model
        ↓
Structured JSON Output
        ↓
Translation Engine
        ↓
Stored in Database
```

---

# ⚠ Important Notes

## Ollama Must Be Running

If you see:

```
Connection refused to localhost:11434
```

Start Ollama:

```bash
ollama serve
```

---

## Model Timeout

If request takes too long:

* Increase RAM
* Switch to smaller model (`llava`)
* Increase timeout in `routes.py`

---

## JSON Parsing Issues

Local models sometimes add extra text.

Your backend already:

* Cleans markdown fences
* Parses safely

---

# 🔥 Development Workflow

Start Ollama:

```bash
ollama serve
```

In another terminal:

```bash
uvicorn app.main:app --reload
```

Test via:

```
http://127.0.0.1:8000/docs
```

---

# 🛑 Stop Everything

Stop FastAPI:

```
CTRL + C
```

Stop Ollama:

```
CTRL + C
```

---
