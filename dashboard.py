import os
import subprocess
import signal
import json
import time
from flask import Flask, render_template, jsonify, request, send_file

app = Flask(__name__, template_folder="dashboard/templates", static_folder="dashboard/static")

TRAINER_PROCESS = None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_training():
    global TRAINER_PROCESS
    
    if TRAINER_PROCESS and TRAINER_PROCESS.poll() is None:
        return jsonify({"status": "error", "message": "Training already running"}), 400
        
    data = request.json
    generations = data.get("generations", 50)
    pop_size = data.get("pop_size", 300)
    seed = data.get("seed", 42)
    
    cmd = [
        "python", "-u", "trainer.py",
        "--generations", str(generations),
        "--pop-size", str(pop_size),
        "--seed", str(seed),
        "--monitor"
    ]
    
    try:
        # Start process
        TRAINER_PROCESS = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return jsonify({"status": "success", "message": "Training started", "pid": TRAINER_PROCESS.pid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/stop", methods=["POST"])
def stop_training():
    global TRAINER_PROCESS
    
    if TRAINER_PROCESS and TRAINER_PROCESS.poll() is None:
        TRAINER_PROCESS.terminate()
        TRAINER_PROCESS = None
        return jsonify({"status": "success", "message": "Training stopped"})
    
    return jsonify({"status": "warning", "message": "No running training found"})

@app.route("/stats")
def get_stats():
    # Check if process is still running
    running = TRAINER_PROCESS is not None and TRAINER_PROCESS.poll() is None
    
    stats = {}
    if os.path.exists("monitor.json"):
        try:
            with open("monitor.json", "r", encoding="utf-8") as f:
                stats = json.load(f)
        except:
            stats = {}
            
    return jsonify({"running": running, "stats": stats})

@app.route("/transpile", methods=["POST"])
def transpile_champion():
    # Transpile current champion to dist/evoname.js
    try:
        # We use the committed model path if available, or the latest run's champion?
        # The dashboard should probably use the latest run's champion for testing.
        # But trainer.py saves to runs/ID/artifacts/champion.pkl
        # We need to find the latest run.
        
        # Helper to find latest run
        runs_dir = "runs"
        if not os.path.exists(runs_dir):
             return jsonify({"status": "error", "message": "No runs found"}), 404
             
        runs = sorted([d for d in os.listdir(runs_dir) if os.path.isdir(os.path.join(runs_dir, d))])
        if not runs:
             return jsonify({"status": "error", "message": "No runs found"}), 404
             
        latest_run = runs[-1]
        champion_path = os.path.join(runs_dir, latest_run, "artifacts", "champion.pkl")
        
        if not os.path.exists(champion_path):
            return jsonify({"status": "error", "message": "Champion not found in latest run"}), 404
            
        cmd = [
            "python", "transpiler.py",
            "--input", champion_path,
            "--output", "dist/evoname.js"
        ]
        
        subprocess.run(cmd, check=True)
        return jsonify({"status": "success", "message": "Transpilation complete"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/champion.js")
def get_champion_js():
    if os.path.exists("dist/evoname.js"):
        return send_file("dist/evoname.js")
    return "console.error('No champion compiled yet');", 404

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("dashboard/templates", exist_ok=True)
    os.makedirs("dashboard/static", exist_ok=True)
    app.run(debug=True, port=5000)
