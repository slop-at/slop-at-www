#!/bin/bash
# Start slop.at web server + Oxigraph

set -e

echo "🐐 Starting slop.at services..."

# Data directory for Oxigraph
SLOP_HOME="${SLOP_HOME:-$HOME/.slop-at}"
OXIGRAPH_DATA="$SLOP_HOME/oxigraph"
mkdir -p "$OXIGRAPH_DATA"

# Check if Oxigraph is already running
if lsof -Pi :7878 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Oxigraph already running on port 7878"
else
    echo "🧠 Starting Oxigraph on port 7878..."
    uvx oxigraph serve --location "$OXIGRAPH_DATA" --bind 127.0.0.1:7878 &
    OXIGRAPH_PID=$!
    echo "   Oxigraph PID: $OXIGRAPH_PID"

    # Wait for Oxigraph to be ready
    echo "   Waiting for Oxigraph to start..."
    for i in {1..10}; do
        if curl -s http://localhost:7878/query > /dev/null 2>&1; then
            echo "   ✅ Oxigraph ready!"
            break
        fi
        sleep 1
    done
fi

# Check if web server is already running
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Web server already running on port 8080"
else
    echo "🌐 Starting web server on port 8080..."
    uv run python server.py &
    SERVER_PID=$!
    echo "   Server PID: $SERVER_PID"

    # Wait for server to be ready
    echo "   Waiting for server to start..."
    for i in {1..10}; do
        if curl -s http://localhost:8080 > /dev/null 2>&1; then
            echo "   ✅ Server ready!"
            break
        fi
        sleep 1
    done
fi

echo ""
echo "🎉 slop.at is running!"
echo ""
echo "   Web:       http://localhost:8080"
echo "   Oxigraph:  http://localhost:7878"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Wait for interrupt
wait
