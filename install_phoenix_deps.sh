#!/bin/bash
# Script to install Phoenix and OpenTelemetry dependencies

echo "🚀 Installing Phoenix Observability Dependencies"
echo "=============================================="

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first."
    exit 1
fi

echo "📦 Installing dependencies..."
uv pip install -e .

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "🔍 Verifying installations:"
echo "----------------------------"

# Check Phoenix
echo -n "Arize Phoenix: "
uv pip show arize-phoenix | grep Version || echo "Not installed"

echo -n "OpenTelemetry SDK: "
uv pip show opentelemetry-sdk | grep Version || echo "Not installed"

echo -n "OpenInference LlamaIndex: "
uv pip show openinference-instrumentation-llama-index | grep Version || echo "Not installed"

echo ""
echo "📝 Next steps:"
echo "1. Set environment variables in .env file"
echo "2. Run: python main/examples/test_phoenix_integration.py"
echo "3. Check Phoenix UI at http://localhost:6006"