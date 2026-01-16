#!/bin/bash
# Stop slop.at services

echo "🛑 Stopping slop.at services..."

# Stop web server
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null ; then
    echo "   Stopping web server (port 8080)..."
    lsof -Pi :8080 -sTCP:LISTEN -t | xargs kill
    echo "   ✅ Web server stopped"
else
    echo "   ℹ️  Web server not running"
fi

# Stop Oxigraph
if lsof -Pi :7878 -sTCP:LISTEN -t >/dev/null ; then
    echo "   Stopping Oxigraph (port 7878)..."
    lsof -Pi :7878 -sTCP:LISTEN -t | xargs kill
    echo "   ✅ Oxigraph stopped"
else
    echo "   ℹ️  Oxigraph not running"
fi

echo "🎉 Services stopped"
