#!/usr/bin/env python3
# filepath: /home/anthonyshaw/repos/new-programming-language/src/llvm_compiler.py

import sys
import os
import subprocess
from tokenizer import Lexer
from parser import Parser

class LLVMCompiler:
    def __init__(self):
        self.llvm_code = []
        self.string_counter = 0
        self.variables = {}
        self.registers = {}
        self.reg_counter = 0
    
    def get_new_register(self):
        reg = f"%r{self.reg_counter}"
        self.reg_counter += 1
        return reg
    
    def emit(self, line):
        self.llvm_code.append(line)
    
    def compile(self, ast):
        # Generate module header
        self.emit("; ModuleID = 'vibe_program'")
        self.emit("target datalayout = \"e-m:e-i8:8:32-i16:16:32-i64:64-i128:128-n32:64-S128\"")
        self.emit("target triple = \"aarch64-unknown-linux-gnu\"")
        
        # Declare external functions
        self.emit("declare i32 @puts(i8* nocapture) nounwind")
        self.emit("@.str.newline = private unnamed_addr constant [2 x i8] c\"\\0A\\00\", align 1")
        
        # Begin main function
        self.emit("define i32 @main() {")
        self.emit("entry:")
        
        # Process the AST
        if isinstance(ast, list):
            for node in ast:
                self.compile_node(node)
        else:
            self.compile_node(ast)
        
        # Return from main
        self.emit("    ret i32 0")
        self.emit("}")
        
        # Helper functions for string operations
        self.generate_string_helpers()
        
        return "\n".join(self.llvm_code)
    
    def compile_node(self, node):
        node_type = type(node).__name__
        method_name = f"compile_{node_type}"
        if hasattr(self, method_name):
            getattr(self, method_name)(node)
        else:
            raise Exception(f"Unsupported node type: {node_type}")
    
    def compile_Assign(self, node):
        var_name = node.left.value
        
        # Evaluate right side
        value_reg = self.compile_expr(node.right)
        
        # Allocate variable if not already allocated
        if var_name not in self.variables:
            var_reg = self.get_new_register()
            self.emit(f"    {var_reg} = alloca i8*")
            self.variables[var_name] = var_reg
        
        # Store value
        var_reg = self.variables[var_name]
        self.emit(f"    store i8* {value_reg}, i8** {var_reg}")
    
    def compile_HollaStmt(self, node):
        # Evaluate expression
        value_reg = self.compile_expr(node.expr)
        
        # Call puts to print
        self.emit(f"    call i32 @puts(i8* {value_reg})")
    
    def compile_expr(self, node):
        node_type = type(node).__name__
        method_name = f"compile_{node_type}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(node)
        else:
            raise Exception(f"Unsupported expression node type: {node_type}")
    
    def compile_BinOp(self, node):
        if node.op.type == 'PLUS':
            # For our simple language, we'll assume this is string concatenation
            left_reg = self.compile_expr(node.left)
            right_reg = self.compile_expr(node.right)
            
            # Call string concatenation function
            result_reg = self.get_new_register()
            self.emit(f"    {result_reg} = call i8* @concat_strings(i8* {left_reg}, i8* {right_reg})")
            return result_reg
        else:
            raise Exception(f"Unsupported binary operator: {node.op.type}")
    
    def compile_Num(self, node):
        # Convert number to string
        string_reg = self.get_new_register()
        global_str = f"@.str.{self.string_counter}"
        self.string_counter += 1
        
        # Register global string constant
        num_str = str(node.value)
        str_type = f"[{len(num_str) + 1} x i8]"
        escaped_str = num_str + "\\00"
        self.emit(f"{global_str} = private unnamed_addr constant {str_type} c\"{escaped_str}\", align 1")
        
        # Get pointer to the string
        self.emit(f"    {string_reg} = getelementptr {str_type}, {str_type}* {global_str}, i64 0, i64 0")
        
        return string_reg
    
    def compile_String(self, node):
        # Create a global string constant
        string_reg = self.get_new_register()
        global_str = f"@.str.{self.string_counter}"
        self.string_counter += 1
        
        # Register global string constant
        escaped_str = node.value.replace("\"", "\\22") + "\\00"  # Add null terminator
        str_type = f"[{len(node.value) + 1} x i8]"
        self.emit(f"{global_str} = private unnamed_addr constant {str_type} c\"{escaped_str}\", align 1")
        
        # Get pointer to the string
        self.emit(f"    {string_reg} = getelementptr {str_type}, {str_type}* {global_str}, i64 0, i64 0")
        
        return string_reg
    
    def compile_Var(self, node):
        var_name = node.value
        if var_name not in self.variables:
            raise Exception(f"Undefined variable: {var_name}")
        
        var_reg = self.variables[var_name]
        load_reg = self.get_new_register()
        self.emit(f"    {load_reg} = load i8*, i8** {var_reg}")
        
        return load_reg
    
    def generate_string_helpers(self):
        # String concatenation function
        self.emit("define i8* @concat_strings(i8* %str1, i8* %str2) {")
        self.emit("entry:")
        
        # Get length of first string
        self.emit("    %len1 = call i64 @strlen(i8* %str1)")
        
        # Get length of second string
        self.emit("    %len2 = call i64 @strlen(i8* %str2)")
        
        # Calculate total length needed
        self.emit("    %total_len = add i64 %len1, %len2")
        self.emit("    %buf_len = add i64 %total_len, 1")  # +1 for null terminator
        
        # Allocate buffer for the result
        self.emit("    %buffer = call i8* @malloc(i64 %buf_len)")
        
        # Copy first string
        self.emit("    call i8* @strcpy(i8* %buffer, i8* %str1)")
        
        # Append second string
        self.emit("    %buffer_end = getelementptr i8, i8* %buffer, i64 %len1")
        self.emit("    call i8* @strcpy(i8* %buffer_end, i8* %str2)")
        
        # Return buffer
        self.emit("    ret i8* %buffer")
        self.emit("}")
        
        # External C functions
        self.emit("declare i64 @strlen(i8*)")
        self.emit("declare i8* @strcpy(i8*, i8*)")
        self.emit("declare i8* @malloc(i64)")

def compile_file(input_filename, output_filename=None):
    # Default output filename is input filename without extension
    if output_filename is None:
        output_filename = os.path.splitext(input_filename)[0]
    
    # Read source file
    with open(input_filename, 'r') as f:
        source = f.read()
    
    # Tokenize
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # Parse
    parser = Parser(tokens)
    ast = parser.parse()
    
    # Generate LLVM IR
    compiler = LLVMCompiler()
    llvm_ir = compiler.compile(ast)
    
    # Write IR to file
    ir_filename = f"{output_filename}.ll"
    with open(ir_filename, 'w') as f:
        f.write(llvm_ir)
    
    print(f"LLVM IR written to {ir_filename}")
    
    # Compile using LLVM tools
    try:
        # Check if LLVM tools are available
        try:
            subprocess.run(["which", "llc"], check=True, stdout=subprocess.PIPE)
        except subprocess.CalledProcessError:
            print("Error: LLVM compiler tools are not installed or not in PATH")
            print("Please install the LLVM toolchain for your system")
            sys.exit(1)
        
        print("Compiling LLVM IR to object file...")
        subprocess.run(["llc", "-march=aarch64", "-filetype=obj", "-o", f"{output_filename}.o", ir_filename], check=True)
        
        print("Linking...")
        subprocess.run(["gcc", "-o", output_filename, f"{output_filename}.o"], check=True)
        
        print(f"Executable created: {output_filename}")
        
        # Make the file executable
        os.chmod(output_filename, 0o755)
    except subprocess.SubprocessError as e:
        print(f"Compilation error: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: llvm_compiler.py <input_file> [output_file]")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    compile_file(input_filename, output_filename)

if __name__ == "__main__":
    main()
