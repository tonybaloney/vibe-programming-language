> [!NOTE]
> This repository was "vibe coded" live on stream at Microsoft Build 2025 in 90 minutes.
> Everything in this repo is preserved from the original recording. https://www.youtube.com/live/67LKcINZTLk?si=asKpKAxDFUFHLNb1&t=23785

# Vibe Programming Language

A simple programming language with both interpreter and compiler options.

## Features

- Simple, clean syntax
- Variables with emoji assignment (➡️)
- String operations
- Print statements using `holla`

## Example

```
// This is our first Holla program
name ➡️ "World"
holla "Hello " + name
```

## Usage

### Using the Vibe Command-Line Tool

```bash
# Compile a program
./vibe compile program.vpl [-o output_name] [-b backend]

# Run a program using the interpreter
./vibe run program.vpl

# Show help
./vibe help
```

### Running the Interpreter Directly

```bash
python3 src/main.py <filename.vpl>
```

### Compiling to an Executable Directly

```bash
# Using the default compiler (native ARM64 assembly)
python3 src/vibe_compiler.py <filename.vpl> [-o output_name]

# Using the simple compiler (direct assembly)
python3 src/vibe_compiler.py <filename.vpl> -b simple [-o output_name]

# Using the LLVM compiler (requires LLVM tools)
python3 src/vibe_compiler.py <filename.vpl> -b llvm [-o output_name]
```

### Quick Compile and Run

```bash
# Compile and run a program in one step
./compile_and_run.sh [filename.vpl]
```

### Additional Options

- `-o, --output NAME`: Specify output name
- `-b, --backend TYPE`: Compiler backend (native, simple, llvm)
- `-v, --verbose`: Print verbose compilation information
- `--keep-temp`: Keep temporary files (assembly, object files)

## Requirements

- Python 3.6+
- For compilation:
  - GCC toolchain
  - ARM64 assembler (as)
  - LLVM toolchain (for LLVM backend)

## Architecture

The compiler pipeline consists of:

1. **Lexer/Tokenizer** (`tokenizer.py`): Converts source code into tokens
2. **Parser** (`parser.py`): Builds an Abstract Syntax Tree (AST) from tokens
3. **Compiler**: Generates target code from the AST
   - `compiler.py`: Direct ARM64 assembly generation
   - `simple_compiler.py`: Simplified ARM64 code generation
   - `llvm_compiler.py`: LLVM IR generation (for optimized compilation)

## File Structure

```
new-programming-language/
├── src/
│   ├── tokenizer.py       # Lexical analysis
│   ├── parser.py          # Syntax analysis
│   ├── interpreter.py     # Direct execution of AST
│   ├── compiler.py        # Native ARM64 compiler
│   ├── simple_compiler.py # Simplified ARM64 compiler
│   ├── llvm_compiler.py   # LLVM-based compiler
│   ├── main.py            # Interpreter main entry
│   └── vibe_compiler.py   # Unified compiler interface
├── vibe                   # Command-line tool wrapper
├── compile_and_run.sh     # Script to compile and run in one step
├── COMPILED.md            # Documentation about compilation
├── README.md              # Main documentation
├── test.vpl               # Basic example program
└── advanced_test.vpl      # Advanced example program
```

## Extending the Language

To add new features to the language, you need to update:

1. The tokenizer to recognize new syntax
2. The parser to build AST nodes for new constructs
3. The interpreter to handle new AST nodes
4. The compiler backends to generate code for new constructs
