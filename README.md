# IGniter

**Igniting access.**

## Requirements

### Backend
- Python 3.13

### Frontend
- Node.js v22.15
- npm 11.5.2

## Getting Started

### Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment:
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the backend server:
   ```bash
   uvicorn app.main:app --port 8000 --host 0.0.0.0 --reload
   ```

### Frontend
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

---

You can access the site at localhost:5173 and paste the link to the article in the textbox.

