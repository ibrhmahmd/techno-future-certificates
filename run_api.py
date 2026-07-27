"""
Entry point for the Certificate Service API.
Run with: python run_api.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
