#!/usr/bin/env python3
# filepath: /home/anthonyshaw/repos/new-programming-language/src/compile.py

import sys
import os
import subprocess
from tokenizer import Lexer
from parser import Parser
from compiler import CodeGenerator

def compile_file(input_filename, output_filename=None):
    # Default output filename is input filename without extension + ".o"
    if output_filename is None:
        output_filename = os.path.splitext(input_filename)[0]
        
    # Read source file
    with open(input_filename, 'r') as f:
        source = f.read()
    
    # Generate assembly
    asm_code = compile_to_assembly(source)
    
    # Write assembly to temporary file
    asm_filename = f"{output_filename}.s"
    with open(asm_filename, 'w') as f:
        f.write(asm_code)
    
    print(f"Assembly code written to {asm_filename}")
    
    # Assemble and link
    try:
        print("Assembling and linking...")
        # For ARM64 we'll use the gcc toolchain
        subprocess.run(["as", "-o", f"{output_filename}.o", asm_filename], check=True)
        subprocess.run(["gcc", "-o", output_filename, f"{output_filename}.o"], check=True)
        print(f"Compiled executable written to {output_filename}")
        
        # Make the file executable
        os.chmod(output_filename, 0o755)
    except subprocess.SubprocessError as e:
        print(f"Compilation error: {e}")
        sys.exit(1)

def compile_to_assembly(source):
    # Tokenize
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # Parse
    parser = Parser(tokens)
    ast = parser.parse()
    
    # Generate code
    code_generator = CodeGenerator()
    assembly_code = code_generator.compile(ast)
    
    return assembly_code

def main():
    if len(sys.argv) < 2:
        print("Usage: compile.py <input_file> [output_file]")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    compile_file(input_filename, output_filename)

if __name__ == "__main__":
    main()
