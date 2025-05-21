#!/usr/bin/env python3
# filepath: /home/anthonyshaw/repos/new-programming-language/src/simple_compiler.py

import sys
import os
import subprocess
from tokenizer import Lexer
from parser import Parser

class ARMCodeGenerator:
    def __init__(self):
        self.string_literals = []
        self.string_counter = 0
        self.variables = {}
        self.var_counter = 0
        self.assembly = []
    
    def add_string_literal(self, string):
        label = f".LC{self.string_counter}"
        self.string_literals.append((label, string))
        self.string_counter += 1
        return label
    
    def add_variable(self, name):
        if name not in self.variables:
            self.variables[name] = f"var_{self.var_counter}"
            self.var_counter += 1
        return self.variables[name]
    
    def emit(self, instruction):
        self.assembly.append(instruction)
    
    def generate(self, ast):
        # Generate the data section for string literals and variables
        self.emit(".arch armv8-a")
        self.emit(".global _start")
        
        # Process the AST
        if isinstance(ast, list):
            for node in ast:
                self.generate_node(node)
        else:
            self.generate_node(ast)
        
        # Generate exit code
        self.emit("    // Exit cleanly")
        self.emit("    mov x0, #0")      # status = 0
        self.emit("    mov x8, #93")     # exit syscall for ARM64
        self.emit("    svc #0")
        
        # Compile the final assembly
        return self.get_assembly_code()
    
    def generate_node(self, node):
        # Determine node type and call appropriate method
        node_type = type(node).__name__
        method_name = f"generate_{node_type}"
        if hasattr(self, method_name):
            getattr(self, method_name)(node)
        else:
            raise Exception(f"Unsupported node type: {node_type}")
    
    def generate_Assign(self, node):
        var_name = node.left.value
        var_label = self.add_variable(var_name)
        
        # Generate code for right-hand side expression
        self.generate_expression(node.right)
        
        # Store result to variable
        self.emit(f"    // Assign to {var_name}")
        self.emit(f"    adrp x1, {var_label}")
        self.emit(f"    add x1, x1, :lo12:{var_label}")
        self.emit("    str x0, [x1]")
    
    def generate_HollaStmt(self, node):
        # Generate code for the expression to print
        self.generate_expression(node.expr)
        
        # Print the result (assume it's a string pointer in x0)
        self.emit("    // Call print function")
        self.emit("    bl print_string")
    
    def generate_expression(self, node):
        node_type = type(node).__name__
        
        if node_type == 'BinOp':
            self.generate_BinOp(node)
        elif node_type == 'Num':
            self.generate_Num(node)
        elif node_type == 'String':
            self.generate_String(node)
        elif node_type == 'Var':
            self.generate_Var(node)
        else:
            raise Exception(f"Unsupported expression node type: {node_type}")
    
    def generate_BinOp(self, node):
        if node.op.type == 'PLUS':
            # String concatenation
            self.emit("    // String concatenation")
            
            # Get left operand
            self.generate_expression(node.left)
            self.emit("    mov x19, x0")  # Save left operand to callee-saved register
            
            # Get right operand
            self.generate_expression(node.right)
            self.emit("    mov x20, x0")  # Save right operand to callee-saved register
            
            # Set up arguments for concat function
            self.emit("    mov x0, x19")  # First arg: left string
            self.emit("    mov x1, x20")  # Second arg: right string
            
            # Call concat function
            self.emit("    bl string_concat")
        else:
            raise Exception(f"Unsupported operator: {node.op.type}")
    
    def generate_Num(self, node):
        self.emit(f"    // Load number {node.value}")
        self.emit(f"    mov x0, #{node.value}")
    
    def generate_String(self, node):
        string_label = self.add_string_literal(node.value)
        self.emit(f"    // Load string \"{node.value}\"")
        self.emit(f"    adrp x0, {string_label}")
        self.emit(f"    add x0, x0, :lo12:{string_label}")
    
    def generate_Var(self, node):
        var_name = node.value
        if var_name not in self.variables:
            raise Exception(f"Undefined variable: {var_name}")
        
        var_label = self.variables[var_name]
        self.emit(f"    // Load variable {var_name}")
        self.emit(f"    adrp x0, {var_label}")
        self.emit(f"    add x0, x0, :lo12:{var_label}")
        self.emit("    ldr x0, [x0]")
    
    def get_assembly_code(self):
        # Combine all parts into a complete assembly file
        result = []
        
        # Data section
        result.append(".data")
        
        # String literals
        for label, string in self.string_literals:
            result.append(f"{label}:")
            escaped_string = string.replace('"', '\\"')
            result.append(f'    .string "{escaped_string}"')
        
        # Variables
        for name, label in self.variables.items():
            result.append(f"{label}:")
            result.append("    .quad 0")
        
        # Add newline string
        result.append("newline:")
        result.append('    .string "\\n"')
        
        # Text section with helper functions
        result.append(".text")
        
        # String print function
        result.append("print_string:")
        result.append("    // Save registers")
        result.append("    stp x29, x30, [sp, #-16]!")
        result.append("    mov x29, sp")
        
        result.append("    // Call write syscall")
        result.append("    mov x1, x0")        # string to print
        result.append("    mov x0, #1")        # file descriptor (stdout)
        
        # Get string length (simplified - assumes null termination)
        result.append("    mov x2, #0")        # length counter
        result.append("print_string_loop:")
        result.append("    ldrb w3, [x1, x2]") # Load byte
        result.append("    cbz w3, print_string_done")  # If zero, end of string
        result.append("    add x2, x2, #1")    # Increment length
        result.append("    b print_string_loop")
        
        result.append("print_string_done:")
        result.append("    mov x8, #64")       # write syscall
        result.append("    svc #0")
        
        # Print newline
        result.append("    adrp x1, newline")
        result.append("    add x1, x1, :lo12:newline")
        result.append("    mov x2, #1")        # length is 1
        result.append("    mov x8, #64")       # write syscall
        result.append("    svc #0")
        
        result.append("    // Restore registers and return")
        result.append("    ldp x29, x30, [sp], #16")
        result.append("    ret")
        
        # String concatenation function (proper implementation)
        result.append("string_concat:")
        result.append("    // Save registers")
        result.append("    stp x29, x30, [sp, #-48]!")
        result.append("    stp x19, x20, [sp, #16]")
        result.append("    stp x21, x22, [sp, #32]")
        result.append("    mov x29, sp")
        
        # Save input strings
        result.append("    mov x19, x0")   # first string
        result.append("    mov x20, x1")   # second string
        
        # Calculate length of first string
        result.append("    mov x21, #0")   # length counter for first string
        result.append("strlen_loop1:")
        result.append("    ldrb w3, [x19, x21]")  # Load byte
        result.append("    cbz w3, strlen_done1")  # If zero, end of string
        result.append("    add x21, x21, #1")     # Increment length
        result.append("    b strlen_loop1")
        result.append("strlen_done1:")
        
        # Calculate length of second string
        result.append("    mov x22, #0")   # length counter for second string
        result.append("strlen_loop2:")
        result.append("    ldrb w3, [x20, x22]")  # Load byte
        result.append("    cbz w3, strlen_done2")  # If zero, end of string
        result.append("    add x22, x22, #1")     # Increment length
        result.append("    b strlen_loop2")
        result.append("strlen_done2:")
        
        # Calculate total length needed (len1 + len2 + 1 for null terminator)
        result.append("    add x2, x21, x22")     # total length = len1 + len2
        result.append("    add x2, x2, #1")       # + 1 for null terminator
        
        # Allocate memory using mmap
        result.append("    mov x0, #0")           # let kernel choose address
        result.append("    mov x1, x2")           # length to allocate
        result.append("    mov x2, #3")           # PROT_READ | PROT_WRITE
        result.append("    mov x3, #0x22")        # MAP_PRIVATE | MAP_ANONYMOUS
        result.append("    mov x4, #-1")          # fd (not used)
        result.append("    mov x5, #0")           # offset (not used)
        result.append("    mov x8, #222")         # mmap syscall number for ARM64
        result.append("    svc #0")
        result.append("    mov x4, x0")           # save buffer address
        
        # Copy first string
        result.append("    mov x0, x4")           # destination
        result.append("    mov x1, x19")          # source (first string)
        result.append("    mov x2, x21")          # bytes to copy
        result.append("copy_loop1:")
        result.append("    cbz x2, copy_done1")   # if counter is 0, done
        result.append("    ldrb w3, [x1], #1")    # load byte and increment source
        result.append("    strb w3, [x0], #1")    # store byte and increment destination
        result.append("    sub x2, x2, #1")       # decrement counter
        result.append("    b copy_loop1")
        result.append("copy_done1:")
        
        # Copy second string
        result.append("    mov x1, x20")          # source (second string)
        result.append("    mov x2, x22")          # bytes to copy
        result.append("copy_loop2:")
        result.append("    cbz x2, copy_done2")   # if counter is 0, done
        result.append("    ldrb w3, [x1], #1")    # load byte and increment source
        result.append("    strb w3, [x0], #1")    # store byte and increment destination
        result.append("    sub x2, x2, #1")       # decrement counter
        result.append("    b copy_loop2")
        result.append("copy_done2:")
        
        # Add null terminator
        result.append("    mov w3, #0")           # null byte
        result.append("    strb w3, [x0]")        # store at end of string
        
        # Return new string buffer
        result.append("    mov x0, x4")
        
        # Restore registers and return
        result.append("    ldp x21, x22, [sp, #32]")
        result.append("    ldp x19, x20, [sp, #16]")
        result.append("    ldp x29, x30, [sp], #48")
        result.append("    ret")
        
        # Main code
        result.append("_start:")
        
        # Add the main program code
        result.extend(self.assembly)
        
        # Ensure we end with a newline
        return '\n'.join(result) + '\n'

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
    
    # Generate assembly
    code_generator = ARMCodeGenerator()
    assembly_code = code_generator.generate(ast)
    
    # Write assembly to file
    asm_filename = f"{output_filename}.s"
    with open(asm_filename, 'w') as f:
        f.write(assembly_code)
    
    print(f"Assembly code written to {asm_filename}")
    
    # Assemble and link
    try:
        print("Assembling...")
        subprocess.run(["as", "-o", f"{output_filename}.o", asm_filename], check=True)
        
        print("Linking...")
        subprocess.run(["ld", "-o", output_filename, f"{output_filename}.o"], check=True)
        
        print(f"Executable created: {output_filename}")
        
        # Make the file executable
        os.chmod(output_filename, 0o755)
    except subprocess.SubprocessError as e:
        print(f"Compilation error: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: simple_compiler.py <input_file> [output_file]")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) > 2 else None
    
    compile_file(input_filename, output_filename)

if __name__ == "__main__":
    main()
