#!/usr/bin/env python3
"""
Simple Flask server for testing
"""

from flask import Flask, jsonify, request

# Initialize Flask app
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    """Root endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Simple test server is running"
    })

@app.route("/api/echo", methods=["POST"])
def echo():
    """Echo endpoint - returns what was sent"""
    data = request.json if request.is_json else {}
    return jsonify({
        "received": data,
        "message": "Echo successful"
    })

if __name__ == "__main__":
    # Use port 8080 which is more commonly open
    port = 8080
    print(f"Starting simple test server on http://localhost:{port}")
    app.run(host="127.0.0.1", port=port, debug=True) 