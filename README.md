# GS-Stock_Dashboard REST API

This project provides a Django-based REST API to serve stock data stored as CSV files.

## Features
- **Dynamic Endpoints**: API endpoints are automatically derived from CSV filenames in the `data/` folder (e.g., `gs_barchart.csv` is served at `/barchart`).
- **RESTful Response**: Data is served as JSON with additional metadata.
- **Random Delay**: To simulate network latency or processing time, each response has a random delay between 0.1 and 2.0 seconds.

## Installation
The project requires Python 3.14+ (or compatible) with following dependencies:
- `django`
- `djangorestframework`
- `pandas`

A virtual environment `venv` has been set up for this project.

## Running the API
To start the API on `localhost:8080`, run:
```bash
source venv/bin/activate
python manage.py runserver 0.0.0.0:8080
```

## Available Endpoints
- `/barchart`
- `/investing_com`
- `/marketwatch`
- `/master_dataset`
- `/nasdaq`
- `/yahoo_finance`

## Response Format
```json
{
  "data": [
    {
      "Date": "2026-01-02",
      "Open": ...,
      ...
    }
  ]
}
```
