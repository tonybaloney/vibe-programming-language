#!/usr/bin/env python3
# filepath: /home/anthonyshaw/repos/new-programming-language/src/simple_compiler.py

import sys
import os
import subprocess
from tokenizer import Lexer
from parser import Parser, Num

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
        
        # If it's a number, convert to string
        if isinstance(node.expr, Num):
            self.emit("    // Convert number to string for printing")
            self.emit("    bl num_to_string")
        
        # Print the result (string pointer in x0)
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
            # Determine if this is numeric addition or string concatenation
            is_left_num = isinstance(node.left, Num)
            is_right_num = isinstance(node.right, Num)
            
            # Track if we're dealing with strings
            is_string_concat = False
            
            # First, generate code for left operand
            self.generate_expression(node.left)
            self.emit("    mov x19, x0")  # Save left operand
            
            # Check if we need to convert left number to string for string concatenation
            if is_left_num and not is_right_num:
                self.emit("    // Convert left number to string")
                self.emit("    bl num_to_string")
                self.emit("    mov x19, x0")  # Update saved value
                is_string_concat = True
            
            # Generate code for right operand
            self.generate_expression(node.right)
            self.emit("    mov x20, x0")  # Save right operand
            
            # Check if we need to convert right number to string
            if is_right_num and not is_left_num:
                self.emit("    // Convert right number to string")
                self.emit("    bl num_to_string")
                self.emit("    mov x20, x0")  # Update saved value
                is_string_concat = True
            
            # If either side was a string, we do string concatenation
            if is_string_concat or not (is_left_num and is_right_num):
                # String concatenation
                self.emit("    // String concatenation")
                self.emit("    mov x0, x19")  # First arg: left string
                self.emit("    mov x1, x20")  # Second arg: right string
                self.emit("    bl string_concat")
            else:
                # Numeric addition
                self.emit("    // Numeric addition")
                self.emit("    add x0, x19, x20")
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
        
        # Number to string conversion function
        result.append("num_to_string:")
        result.append("    // Save registers")
        result.append("    stp x29, x30, [sp, #-64]!")
        result.append("    stp x19, x20, [sp, #16]")
        result.append("    stp x21, x22, [sp, #32]")
        result.append("    stp x23, x24, [sp, #48]")
        result.append("    mov x29, sp")
        
        result.append("    // x0 contains the number to convert")
        result.append("    mov x19, x0")   # Save number
        
        # Allocate 24 bytes for string (enough for 64-bit numbers plus null)
        result.append("    mov x0, #0")    # let kernel choose address
        result.append("    mov x1, #24")   # length to allocate
        result.append("    mov x2, #3")    # PROT_READ | PROT_WRITE
        result.append("    mov x3, #0x22") # MAP_PRIVATE | MAP_ANONYMOUS
        result.append("    mov x4, #-1")   # fd (not used)
        result.append("    mov x5, #0")    # offset (not used)
        result.append("    mov x8, #222")  # mmap syscall number for ARM64
        result.append("    svc #0")
        result.append("    mov x20, x0")   # Save buffer address
        
        result.append("    // Check if number is 0 for special case")
        result.append("    cmp x19, #0")
        result.append("    bne num_to_string_not_zero")
        
        result.append("    // Handle 0 special case")
        result.append("    mov w1, #'0'")
        result.append("    strb w1, [x20]")
        result.append("    mov w1, #0")     # null terminator
        result.append("    strb w1, [x20, #1]")
        result.append("    mov x0, x20")    # Return buffer address
        result.append("    b num_to_string_done")
        
        result.append("num_to_string_not_zero:")
        result.append("    // Convert number to string by repeated division")
        result.append("    add x21, x20, #23")  # Start at end of buffer
        result.append("    mov w0, #0")         # Null terminator
        result.append("    strb w0, [x21]")     # Place at end
        result.append("    sub x21, x21, #1")   # Move pointer
        
        result.append("    mov x22, x19")       # Working copy of number
        result.append("    mov x23, #10")       # Divisor
        
        result.append("num_to_string_loop:")
        result.append("    cmp x22, #0")        # Check if we're done
        result.append("    beq num_to_string_reverse") # If number is 0, we're done
        
        result.append("    // Divide by 10 and get remainder")
        result.append("    udiv x24, x22, x23") # x24 = x22 / 10
        result.append("    msub x0, x24, x23, x22") # x0 = x22 - (x24 * 10) = remainder
        result.append("    mov x22, x24")       # Update number with quotient
        
        result.append("    // Convert remainder to ASCII and store")
        result.append("    add w0, w0, #'0'")   # Convert to ASCII
        result.append("    strb w0, [x21]")     # Store in buffer
        result.append("    sub x21, x21, #1")   # Move pointer
        
        result.append("    b num_to_string_loop")
        
        result.append("num_to_string_reverse:")
        result.append("    // x21 points to character before start of string")
        result.append("    add x21, x21, #1")   # Point to first character
        result.append("    // Calculate how many bytes to copy")
        result.append("    add x0, x20, #23")   # End of buffer
        result.append("    sub x1, x0, x21")    # Number of bytes until null terminator
        
        result.append("    // Copy from x21 to beginning of buffer")
        result.append("    mov x0, x20")        # Destination
        result.append("    mov x1, x21")        # Source
        
        result.append("    mov x0, x20")        # Return buffer address
        
        result.append("num_to_string_done:")
        result.append("    // Restore registers and return")
        result.append("    ldp x23, x24, [sp, #48]")
        result.append("    ldp x21, x22, [sp, #32]")
        result.append("    ldp x19, x20, [sp, #16]")
        result.append("    ldp x29, x30, [sp], #64")
        result.append("    ret")
        
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

def compile_file(input_filename, output_filename=None, debug=False):
    """Compile a Vibe Language source file into an ARM64 executable."""
    # Set default output filename if not provided
    if output_filename is None:
        output_filename = os.path.splitext(input_filename)[0]
    
    try:
        # Read source file
        with open(input_filename, 'r') as f:
            source = f.read()
        
        if debug:
            print(f"Source code:\n{source}\n")
        
        # Tokenize
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        if debug:
            print("Tokens:")
            for token in tokens:
                print(f"  {token}")
        
        # Parse
        parser = Parser(tokens)
        ast = parser.parse()
        
        if debug:
            print("\nAST structure:")
            print_ast(ast, 0)
            print()
        
        # Generate assembly
        code_generator = ARMCodeGenerator()
        assembly_code = code_generator.generate(ast)
        
        # Write assembly to file
        asm_filename = f"{output_filename}.s"
        with open(asm_filename, 'w') as f:
            f.write(assembly_code)
        
        if debug:
            print(f"Assembly code written to {asm_filename}")
            print("\nAssembly code preview:")
            lines = assembly_code.split('\n')
            for i, line in enumerate(lines[:20]):  # Print first 20 lines
                print(f"{i+1:4d}: {line}")
            if len(lines) > 20:
                print("...")
        else:
            print(f"Assembly code written to {asm_filename}")

def print_ast(node, level):
    """Helper function to print AST structure for debugging"""
    indent = "  " * level
    if isinstance(node, list):
        print(f"{indent}[List of statements]")
        for item in node:
            print_ast(item, level + 1)
    else:
        node_type = type(node).__name__
        if hasattr(node, 'value'):
            print(f"{indent}{node_type}: {node.value}")
        elif hasattr(node, 'op') and hasattr(node.op, 'type'):
            print(f"{indent}{node_type}: {node.op.type}")
            print(f"{indent}Left:")
            print_ast(node.left, level + 1)
            print(f"{indent}Right:")
            print_ast(node.right, level + 1)
        elif hasattr(node, 'expr'):
            print(f"{indent}{node_type}:")
            print_ast(node.expr, level + 1)
        else:
            print(f"{indent}{node_type}")
    
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
        print("Usage: simple_compiler.py <input_file> [output_file] [--debug]")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = None
    debug_mode = False
    
    for arg in sys.argv[2:]:
        if arg == '--debug':
            debug_mode = True
        elif output_filename is None:
            output_filename = arg
    
    compile_file(input_filename, output_filename, debug_mode)

if __name__ == "__main__":
    main()
