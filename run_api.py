#!/usr/bin/env python
"""
Run the ILI Data Alignment System API server.

Usage:
    python run_api.py
    python run_api.py --host 0.0.0.0 --port 8000
    python run_api.py --reload  # development mode

Then open http://localhost:8000/docs for Swagger UI
"""

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="ILI Data Alignment System API")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    uvicorn.run(
        "src.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

