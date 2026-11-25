from tasktracker import app

if __name__ == "__main__":
    print("Start TaskTracker...")
    print("Address: http://localhost:5001")
    print("Ctrl+C to stop server")
    app.run(debug=True, host="0.0.0.0", port=5001)
