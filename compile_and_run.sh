#!/bin/bash
# filepath: /home/anthonyshaw/repos/new-programming-language/compile_and_run.sh

# This script demonstrates compiling and running a Vibe Language program

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check for input file
INPUT_FILE="$1"
if [ -z "$INPUT_FILE" ]; then
    INPUT_FILE="test.vpl"
    echo "No input file specified, using default: $INPUT_FILE"
fi

# Check if file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File $INPUT_FILE not found"
    exit 1
fi

# Get filename without extension
FILENAME=$(basename "$INPUT_FILE" .vpl)

echo "=== Compiling $INPUT_FILE ==="
echo

# Try different compilers based on what's available
if command -v llc &> /dev/null && [ -f "src/llvm_compiler.py" ]; then
    echo "Using LLVM compiler backend"
    python3 src/vibe_compiler.py "$INPUT_FILE" -b llvm -o "$FILENAME" --verbose
elif [ -f "src/simple_compiler.py" ]; then
    echo "Using simple assembly compiler backend"
    python3 src/vibe_compiler.py "$INPUT_FILE" -b simple -o "$FILENAME" --verbose
else
    echo "Using native compiler backend"
    python3 src/vibe_compiler.py "$INPUT_FILE" -o "$FILENAME" --verbose
fi

echo
echo "=== Running $FILENAME ==="
echo
./"$FILENAME"

echo
echo "=== Done ==="
