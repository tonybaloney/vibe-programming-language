from parser import AST, BinOp, Num, String, Var, Assign, HollaStmt

class CodeGenerator:
    def __init__(self):
        self.variables = {}
        self.data_section = []
        self.text_section = []
        self.string_counter = 0
        self.output = []
        
    def generate_string_label(self):
        label = f".LC{self.string_counter}"
        self.string_counter += 1
        return label
    
    def visit_BinOp(self, node):
        # String concatenation support
        if node.op.type == 'PLUS':
            # Check if either operand is a string
            if hasattr(node.left, 'token') and node.left.token.type == 'STRING' or \
               hasattr(node.right, 'token') and node.right.token.type == 'STRING':
                return self.generate_string_concat(node)
            else:
                # Handle numeric addition
                self.visit(node.left)
                self.text_section.append("    mov x1, x0")  # Save left result
                self.visit(node.right)
                self.text_section.append("    add x0, x1, x0")  # Add right to left
                return "x0"  # Result is in x0
        else:
            raise Exception(f"Unknown operator: {node.op.type}")
    
    def generate_string_concat(self, node):
        # Simplified string concatenation - in a real compiler this would be more complex
        # We'll use C standard library's sprintf for simplicity
        
        # Load strings or string representations into registers
        left_reg = self.visit(node.left)
        self.text_section.append("    mov x1, x0")  # Save left string address
        
        right_reg = self.visit(node.right)
        self.text_section.append("    mov x2, x0")  # Save right string address
        
        # Allocate buffer for result (simplified)
        buffer_label = self.generate_string_label()
        self.data_section.append(f"{buffer_label}:")
        self.data_section.append("    .skip 256")  # Allocate 256 bytes for result
        
        # Load buffer address
        self.text_section.append(f"    adrp x0, {buffer_label}")
        self.text_section.append(f"    add x0, x0, :lo12:{buffer_label}")
        
        # Call sprintf (simplified - in real implementation we'd need to properly call external functions)
        self.text_section.append("    bl _string_concat")  # Call our string concatenation helper
        
        return "x0"  # Result buffer address is in x0
    
    def visit_Num(self, node):
        self.text_section.append(f"    mov x0, #{node.value}")
        return "x0"
    
    def visit_String(self, node):
        string_label = self.generate_string_label()
        escaped_value = node.value.replace('"', '\\"')
        
        self.data_section.append(f"{string_label}:")
        self.data_section.append(f'    .string "{escaped_value}"')
        
        self.text_section.append(f"    adrp x0, {string_label}")
        self.text_section.append(f"    add x0, x0, :lo12:{string_label}")
        
        return "x0"
    
    def visit_Var(self, node):
        var_name = node.value
        if var_name in self.variables:
            var_offset = self.variables[var_name]
            self.text_section.append(f"    ldr x0, [x29, #{var_offset}]")
            return "x0"
        else:
            raise Exception(f"Variable '{var_name}' is not defined")
    
    def visit_Assign(self, node):
        var_name = node.left.value
        
        # Evaluate the right side expression
        self.visit(node.right)
        
        # Store result in stack frame
        if var_name not in self.variables:
            # Allocate new variable at next available stack position
            var_offset = len(self.variables) * 8
            self.variables[var_name] = var_offset
            
        var_offset = self.variables[var_name]
        self.text_section.append(f"    str x0, [x29, #{var_offset}]")
        
        return "x0"
    
    def visit_HollaStmt(self, node):
        # Evaluate expression
        self.visit(node.expr)
        # x0 now contains the result to print
        
        # Call printf
        self.text_section.append("    bl _print_value")
        
        return "x0"
    
    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")
    
    def generate_header(self):
        self.output.append(".global _start")
        self.output.append(".extern printf")  # External C library function
        
        # Define our helper functions
        self.output.append("_print_value:")
        self.output.append("    stp x29, x30, [sp, #-16]!")  # Save frame pointer and link register
        self.output.append("    mov x29, sp")               # Set up frame pointer
        
        # Check if value in x0 is a string (implementation simplified)
        self.output.append("    mov x1, x0")                # First argument to printf
        self.output.append("    adrp x0, printf_format")
        self.output.append("    add x0, x0, :lo12:printf_format")
        self.output.append("    bl printf")
        
        self.output.append("    ldp x29, x30, [sp], #16")   # Restore frame and link register
        self.output.append("    ret")
        
        self.output.append("_string_concat:")
        # Simple implementation - assumes x1 and x2 are string pointers, x0 is result buffer
        self.output.append("    stp x29, x30, [sp, #-16]!")
        self.output.append("    mov x29, sp")
        
        self.output.append("    mov x3, x0")  # Save buffer address
        self.output.append("    mov x0, x3")  # Set buffer as first arg
        self.output.append("    adrp x4, concat_format")
        self.output.append("    add x4, x4, :lo12:concat_format")
        self.output.append("    mov x0, x4")  # Format string
        self.output.append("    bl sprintf")  # Call sprintf(format, str1, str2)
        
        self.output.append("    mov x0, x3")  # Return buffer address
        self.output.append("    ldp x29, x30, [sp], #16")
        self.output.append("    ret")
    
    def generate_data_section(self):
        self.output.append(".section .data")
        self.output.append("printf_format:")
        self.output.append('    .string "%s\\n"')
        self.output.append("concat_format:")
        self.output.append('    .string "%s%s"')
        
        for data in self.data_section:
            self.output.append(data)
    
    def generate_program_entry(self):
        self.output.append(".section .text")
        self.output.append("_start:")
        self.output.append("    stp x29, x30, [sp, #-16]!")  # Save frame pointer and link register
        self.output.append("    mov x29, sp")               # Set up frame pointer
        
        # Reserve stack space for variables
        stack_size = max(16, len(self.variables) * 8)
        if stack_size % 16 != 0:  # Ensure 16-byte alignment
            stack_size += 8
        self.output.append(f"    sub sp, sp, #{stack_size}")
        
        # Add main program code
        for instruction in self.text_section:
            self.output.append(instruction)
        
        # Clean up and exit
        self.output.append(f"    add sp, sp, #{stack_size}")
        self.output.append("    ldp x29, x30, [sp], #16")  # Restore frame and link register
        
        # Exit system call
        self.output.append("    mov x0, #0")      # Exit code 0
        self.output.append("    mov x8, #93")     # exit syscall number for arm64
        self.output.append("    svc #0")          # Make syscall
    
    def compile(self, ast):
        if isinstance(ast, list):
            for node in ast:
                self.visit(node)
        else:
            self.visit(ast)
            
        self.generate_header()
        self.generate_data_section()
        self.generate_program_entry()
        
        return '\n'.join(self.output)
