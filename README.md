# GS-Stock Smooth Dashboard

A premium, full-stack financial data visualization engine that generates smooth, realistic stock data based on historical trends using a **Momentum-Driven Random Walk** model.

## 🚀 Overview
This application transitions from static CSV analysis to a dynamic, PostgreSQL-backed generation engine. Every 5 seconds, the engine generates a statistically consistent "future" record for Goldman Sachs (GS) stock, maintaining a rolling 100-record history for the frontend dashboard.

### Key Features
- **Smooth Stochastic Engine**: Uses Geometric Brownian Motion with 1-Year Momentum Tracking and Mean Reversion to generate lifelike market moves.
- **PostgreSQL Driven**: Maintains a fixed-size dataset with a "One In, One Out" FIFO logic.
- **Monochromatic Dashboard**: A React-based (Vite) interface featuring glassmorphism, Area charts (Recharts), and real-time refresh timers.
- **Trend Awareness**: The generator analyzes the slope of the last 252 trading days (1 year) to apply a realistic macro-drift to the micro-refreshes.

## 🛠️ Installation & Setup

### 1. Database (PostgreSQL)
Ensure you have a PostgreSQL instance running. The application expects:
- **Host**: `localhost`
- **Port**: `5431`
- **Database**: `yahoo_finance`
- **User**: `postgres`
- **Password**: `mysecretpassword`

### 2. Backend (Django)
1. **Activate Virtual Environment**:
   ```bash
   source venv/bin/activate
   ```
2. **Install Dependencies**:
   ```bash
   pip install django djangorestframework pandas psycopg2-binary django-cors-headers
   ```
3. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```
4. **Seed Database from CSV**:
   ```bash
   python manage.py migrate_csv_to_db
   ```
5. **Start Server**:
   ```bash
   python manage.py runserver 8080
   ```

### 3. Frontend (React Dashboard)
1. **Navigate to Dashboard**:
   ```bash
   cd dashboard
   ```
2. **Install Dependencies**:
   ```bash
   npm install
   ```
3. **Start Dashboard**:
   ```bash
   npm run dev -- --port 3000
   ```

## 📊 Available API Endpoints
- **GET `/yahoo-finance/latest`**: Returns the last 100 records for charting + generates the next smooth point + deletes the oldest point.

## 🛠️ Architecture Decisions
Detailed documentation of the generation models, database migrations, and aesthetic choices are maintained in the [agent_task_log.md](./agent_task_log.md).
