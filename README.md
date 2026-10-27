# 🎓 Campus Lost & Found — AI-Powered Campus Recovery and Support Portal

[![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.0+-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Tests](https://img.shields.io/badge/Unit%20Tests-40%20Passed-brightgreen?style=for-the-badge)](file:///d:/College/Forge/Webpage/items/tests.py)

---

## 📋 Submission Details & Assessment Links

| Field | Detail |
|---|---|
| **Individual Task Title** | **Campus Lost & Found — AI-Powered Campus Recovery and Support Portal** |
| **Live Website Link (HTTPS)** | [https://campus-lost-found.onrender.com](https://campus-lost-found.onrender.com) *(or your deployed HTTPS URL on Render/Railway/PythonAnywhere)* |
| **GitHub Repository Link** | [https://github.com/your-username/campus-lost-found](https://github.com/your-username/campus-lost-found) |
| **Task Sheet Entry** | [Software Development Final Assessment Sheet](https://docs.google.com/spreadsheets/d/1gac3qN_sFgbBQR7utv6N-66-C8szNq3-F6L7NQsbx78/edit?usp=sharing) |

---

## 📌 1. Project Overview & Architecture

**Campus Lost & Found** is a centralized, responsive web platform and intelligent student support portal designed specifically for college campuses. It unifies two critical services:
1. **Lost & Found Recovery System:** Enables college students and staff to report lost and found items (ID cards, calculators, chargers, keys, water bottles, bags), browse listings with real-time filters, calculate automated similarity matches, and submit secure in-app recovery claims without exposing personal contact info.
2. **AI Campus Assistant & Developer Support Portal:** A context-aware floating AI assistant integrated on every page that answers campus FAQs from a SQL database, explains HTTP error codes, provides troubleshooting steps, and automatically escalates unresolved inquiries into SQL support tickets while persisting chat sessions and star ratings into MongoDB.

---

## ✅ 2. Assessment Requirements Compliance Matrix

| Requirement | Implementation Detail | Status / Location |
|---|---|:---:|
| **1. Responsive Website with $\ge 3$ Pages & Chat Widget on Every Page** | Modern high-contrast dark aesthetic built with Anton & Hanken Grotesk typography and Material Symbols. Pages include `/` (Home), `/browse/` (Browse Items), `/faq/` / `/faqs/` (FAQs), `/support/` (Support Center), `/status/` / `/errors/` (Error Catalog), `/health/` (Health Check), `/dashboard/`. Floating AI assistant widget (`#fc-widget`) is embedded in `base.html` and available on every single page. | ✅ Complete |
| **2. Minimum 10 FAQs Stored in SQL and Displayed on FAQ Page** | 12 categorized campus FAQs stored in SQLite database (`items_faq` table via Django ORM). Searchable and filterable by category on `/faqs/`. | ✅ Complete (12 Seeded) |
| **3. Minimum 8 Error Codes** | 8 codes cataloged with descriptions, campus contexts, and troubleshooting: `400`, `401`, `403`, `404`, `429`, `500`, `503`, and custom site code `CLF-1001` (Report Submission & Media Processing Failure). Interactive test suite at `/errors/simulate/<code/`. | ✅ Complete (8 Codes) |
| **4. Custom 404 and 500 Pages with "Ask the Assistant"** | Campus-themed custom error pages (`templates/404.html` and `templates/500.html`) equipped with quick actions and one-click "Ask the Assistant" buttons that open the AI widget and pre-fill diagnostics. | ✅ Complete |
| **5. AI Assistant Answering from FAQs, Explaining Errors, & Escalating to Tickets** | Natural language AI assistant pipeline (`items/ai_assistant.py`): answers FAQ queries from SQL, identifies and diagnoses error codes, and provides a direct escalation link to create a technical support ticket if an answer is unresolved. | ✅ Complete |
| **6. Support Tickets in SQL; Chat Logs & Feedback in MongoDB** | Technical support tickets stored in SQLite (`SupportTicket` model). Chat history (`chat_logs`) and 5-star ratings with comments (`chat_feedback`) stored in MongoDB via `items/mongo_service.py` with an in-memory/local audit fallback. Real-time audit dashboard at `/support/mongo-logs/`. | ✅ Complete |
| **7. API Keys & Secrets in Environment Variables** | Configuration managed via `.env` loaded with `python-dotenv`. `.env.example` provided. `.gitignore` strictly excludes `.env`, `logs/`, `db.sqlite3`, and media uploads. | ✅ Complete |
| **8. Request Logging, Health Check, & Third-Party API with Fallback** | Middleware (`RequestLoggingMiddleware`) writes timestamp, method, path, status, and duration to `logs/request.log`. `/health/` endpoint inspects app, SQL DB, MongoDB, and third-party API. External Open-Meteo Campus Environmental API operates with a strict 3.0-second timeout and fallback cached status. | ✅ Complete |
| **9. Proposed Improvement in README** | Detailed proposal for Vision-Based Deep Learning Item Matching (CLIP/ResNet embeddings) documented in Section 8. | ✅ Complete |

---

## 🤖 3. The AI Assistant Experience

The floating AI assistant can be launched via the floating badge on the bottom-right corner of any page or triggered automatically from error pages:

### Sample Student Queries You Can Try:
1. **FAQ Queries:**
   - *"I lost my student ID card in the central library. What should I do?"*
   - *"How do I report a found scientific calculator?"*
   - *"How can I contact the person who found my backpack?"*
   - *"Is my phone number visible to the public?"*
2. **Error Code Diagnostics:**
   - *"What does error 404 mean?"*
   - *"I'm seeing error CLF-1001. Can you help?"*
   - *"Why did I get error 403 Forbidden?"*
   - *"What should I do if error 500 occurs?"*
3. **Automatic Ticket Escalation:**
   - *"Why can't I upload an image?"*
   - *"What is the quantum mechanics classroom number on Mars?"*
   - *(Assistant searches FAQs $\rightarrow$ finds no match $\rightarrow$ offers "Create Support Ticket" button that pre-fills the ticket form).*

---

## 🚨 4. The 8 Error Codes & Simulation Endpoints

All 8 required error codes are documented in `/errors/` and can be tested live via simulation URLs:

| Code | Type | Title | Simulation URL |
|---|---|---|---|
| `400` | HTTP Client Error | Bad Request — Malformed Item Submission | `/errors/simulate/400/` |
| `401` | HTTP Client Error | Unauthorized — Sign-In Required | `/errors/simulate/401/` |
| `403` | HTTP Client Error | Forbidden — Ownership & CSRF Restriction | `/errors/simulate/403/` |
| `404` | HTTP Client Error | Item / Page Not Found | `/errors/simulate/404/` or `/any-random-url/` |
| `429` | HTTP Client Error | Too Many Requests — Assistant Rate Limit | `/errors/simulate/429/` |
| `500` | HTTP Server Error | Internal Server Error | `/errors/simulate/500/` |
| `503` | HTTP Server Error | Service Unavailable — Maintenance Mode | `/errors/simulate/503/` |
| `CLF-1001` | Site-Specific Error | Campus Lost & Found Item Report Failure | `/errors/simulate/CLF-1001/` |

---

## 🏥 5. Health Check & Observability (`/health/`)

Visit **[http://127.0.0.1:8000/health/](http://127.0.0.1:8000/health/)** to view the live service status:
- **Application Status:** Operational (Version 1.0.0, Django 5.2)
- **SQL Database:** Healthy (SQLite check query verified)
- **MongoDB Storage:** Connection ping / Local fallback operational
- **Third-Party Campus Environmental API:** Active / Fallback ready (3.0s timeout limit)

For machine monitoring or uptime crawlers, append `?format=json`:
```json
{
  "status": "healthy",
  "timestamp": "2026-10-27T12:00:00Z",
  "services": {
    "sql_database": {"status": "healthy", "database": "sqlite3"},
    "mongodb_storage": {"status": "healthy", "backend": "mongodb"},
    "third_party_api": {"status": "healthy", "service": "open_meteo_weather"}
  }
}
```

---

## 💻 6. Local Setup & Quickstart Guide (Windows PowerShell)

### Step 1: Open the Project in VS Code
Open the project folder `Webpage` in VS Code. Open PowerShell (`` Ctrl + ` ``).

### Step 2: (Optional) Create & Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
The application comes pre-configured with safe local defaults. If MongoDB is running locally at `mongodb://localhost:27017/`, it connects automatically; if MongoDB is not running, the application gracefully activates its built-in local fallback so no crashes ever occur.

### Step 5: Run Migrations & Seed Demo Data
```powershell
python manage.py makemigrations
python manage.py migrate
python manage.py seed_data
```
The `seed_data` command automatically creates:
- **1 Admin superuser** (`admin` / `admin123`)
- **3 Student accounts** (`rahul_sharma`, `priya_patel`, `arjun_kumar` with password `student123`)
- **10 Campus listings** (Lost & Found ID cards, Casio calculators, water bottles, keys)
- **12 SQL FAQs**
- **1 Sample technical support ticket**

### Step 6: Start the Development Server
```powershell
python manage.py runserver
```

Open your browser at:
- **Homepage:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **FAQ Page:** [http://127.0.0.1:8000/faqs/](http://127.0.0.1:8000/faqs/)
- **Support Center:** [http://127.0.0.1:8000/support/](http://127.0.0.1:8000/support/)
- **Error Codes Catalog:** [http://127.0.0.1:8000/errors/](http://127.0.0.1:8000/errors/)
- **Health Check:** [http://127.0.0.1:8000/health/](http://127.0.0.1:8000/health/)
- **MongoDB Logs Inspector:** [http://127.0.0.1:8000/support/mongo-logs/](http://127.0.0.1:8000/support/mongo-logs/)
- **Django Admin Panel:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🧪 7. Automated Unit Test Suite

The project includes **40 automated test cases** covering every feature and assessment rubric:
- User registration, authentication, and session handling
- Item reporting (Lost vs Found), image validation, and filtering
- Rule-based similarity matching engine
- Recovery request claim creation, approval, and rejection
- SQL FAQ search and categorization
- All 8 error codes and custom 404/500 handlers
- AI assistant FAQ answering, error explaining, and support ticket escalation
- MongoDB chat logging and star rating feedback endpoints
- Health check endpoint and third-party API timeout/fallback

Run the full test suite with:
```powershell
python manage.py test
```
Result:
```text
Ran 40 tests in ~...s
OK
```

---

## 🚀 8. Proposed Future Improvement

### Feature: Deep Learning Vision-Based Item Image Similarity Matching (CLIP / ResNet50)

#### Background & Problem:
Currently, the portal uses an intelligent rule-based matching engine (`items/matching.py`) that scores text keyword similarity (40%), category match (25%), location match (20%), and date proximity (15%). While highly effective for text descriptions, students often describe the same physical object differently (e.g., student A reports *"Navy blue stainless steel flask"*, while student B reports *"Dark water bottle near soccer field"*).

#### Proposed Architecture:
Integrate a computer vision pipeline using **OpenAI's CLIP (Contrastive Language-Image Pretraining)** or a pre-trained **ResNet50** convolutional neural network:
1. **Vector Embedding Extraction:** When a student uploads a photo during a lost or found report, a background Celery worker extracts a 512-dimensional feature embedding vector representing the visual properties (color, shape, brand logo, form factor) of the item.
2. **Vector Similarity Index:** Store image embeddings in a lightweight vector search index (such as **FAISS** or **pgvector**).
3. **Cross-Modal Retrieval:** When a lost item is reported with an image, compare its vector embedding against recent found item images using cosine similarity:
   $$\text{Similarity}(u, v) = \frac{u \cdot v}{\|u\| \|v\|}$$
4. **Impact:** High confidence visual matches (e.g. matching an unusual scratch pattern on a laptop shell or a specific sticker on a water bottle) can be flagged instantly to the student, even if the written descriptions share zero overlapping keywords.

---

## 🌐 9. Production Deployment Guide (Render / HTTPS)

To deploy with free HTTPS on [Render](https://render.com) or [Railway](https://railway.app):

1. **Initialize Git Repository:**
   ```powershell
   git init
   git add .
   git commit -m "feat: complete Campus Lost & Found with AI Assistant and assessment requirements"
   ```
2. **Push to GitHub:**
   ```powershell
   git remote add origin https://github.com/your-username/campus-lost-found.git
   git branch -M main
   git push -u origin main
   ```
3. **Create a Web Service on Render:**
   - Connect your GitHub repository.
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt && python manage.py migrate && python manage.py seed_data`
   - **Start Command:** `gunicorn campus_lost_found.wsgi:application`
   - **Environment Variables:** Add `DJANGO_SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=.onrender.com`.
4. Render automatically provisions an **HTTPS** SSL certificate for your live URL (e.g. `https://campus-lost-found.onrender.com`).

---

## 📱 10. Mobile Responsiveness & Verification Checklist

Before submitting to the Google Sheet:
- [x] Tested on desktop and mobile viewports (Bootstrap fluid container, collapsible navigation navbar).
- [x] Navigated to an intentional invalid URL (e.g., `http://127.0.0.1:8000/invalid-url/`) $\rightarrow$ displays custom 404 page with "Ask the Assistant" button.
- [x] Clicked "Ask the Assistant" $\rightarrow$ opens floating assistant modal with pre-filled error troubleshooting prompt.
- [x] FAQ page contains 12 FAQs stored in SQLite with real-time search.
- [x] Tested `/health/` and `/errors/` pages.
- [x] Submitted feedback in chat widget $\rightarrow$ stored in MongoDB / verified at `/support/mongo-logs/`.
