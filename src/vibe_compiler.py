#!/usr/bin/env python3
# filepath: /home/anthonyshaw/repos/new-programming-language/src/vibe_compiler.py

import sys
import os
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Vibe Programming Language Compiler")
    parser.add_argument('input_file', help='Source file to compile')
    parser.add_argument('-o', '--output', help='Output executable name')
    parser.add_argument('-b', '--backend', choices=['native', 'simple', 'llvm'], 
                        default='native', help='Compiler backend to use')
    parser.add_argument('-v', '--verbose', action='store_true', 
                        help='Print verbose compilation information')
    parser.add_argument('--keep-temp', action='store_true',
                        help='Keep temporary files (assembly, object files)')
    
    args = parser.parse_args()
    
    # Determine output filename
    output_file = args.output
    if not output_file:
        output_file = os.path.splitext(os.path.basename(args.input_file))[0]
    
    # Choose compiler backend
    if args.backend == 'native':
        from compiler import compile_file
    elif args.backend == 'simple':
        from simple_compiler import compile_file
    elif args.backend == 'llvm':
        from llvm_compiler import compile_file
    
    # Print information
    if args.verbose:
        print(f"Compiling {args.input_file} to {output_file} using {args.backend} backend")
    
    # Compile the file
    compile_file(args.input_file, output_file)
    
    # Remove temporary files if needed
    if not args.keep_temp:
        temp_files = [f"{output_file}.s", f"{output_file}.o", f"{output_file}.ll"]
        for file in temp_files:
            if os.path.exists(file):
                if args.verbose:
                    print(f"Removing temporary file: {file}")
                os.unlink(file)
    
    print(f"Compilation complete: {output_file}")

if __name__ == "__main__":
    main()
