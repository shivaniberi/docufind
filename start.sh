#!/bin/bash
# FastMCP Document Server - Startup Script
# Run this to quickly start the entire application

echo "🚀 FastMCP Document Server - Startup Script"
echo "==========================================="

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup first:"
    echo "   python3.12 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate venv
source venv/bin/activate

# Kill any existing processes on ports 8000 and 8001
echo "🛑 Killing any existing processes..."
pkill -9 -f "python run_server_fixed.py" 2>/dev/null || true
pkill -9 -f "python serve_test_ui.py" 2>/dev/null || true
sleep 1

# Start API Server
echo "📍 Starting API Server on http://127.0.0.1:8000..."
python run_server_fixed.py &
API_PID=$!
sleep 3

# Start Test UI Server
echo "📍 Starting Test UI Server on http://127.0.0.1:8001..."
python serve_test_ui.py &
UI_PID=$!
sleep 2

echo ""
echo "✅ Both servers started!"
echo "════════════════════════════════════════"
echo "📍 API Server: http://127.0.0.1:8000"
echo "📍 Test UI:    http://127.0.0.1:8001/test_ui.html"
echo "════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for both processes
wait $API_PID $UI_PID
