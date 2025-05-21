class Interpreter:
    def __init__(self):
        self.variables = {}
    
    def visit_BinOp(self, node):
        if node.op.type == 'PLUS':
            return self.visit(node.left) + self.visit(node.right)
        else:
            raise Exception(f"Unknown operator: {node.op.type}")
    
    def visit_Num(self, node):
        return node.value
    
    def visit_String(self, node):
        return node.value
    
    def visit_Var(self, node):
        var_name = node.value
        if var_name in self.variables:
            return self.variables[var_name]
        raise Exception(f"Variable '{var_name}' is not defined")
    
    def visit_Assign(self, node):
        var_name = node.left.value
        self.variables[var_name] = self.visit(node.right)
        return None
    
    def visit_HollaStmt(self, node):
        value = self.visit(node.expr)
        print(value)
        return None
    
    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method")
    
    def interpret(self, tree):
        if isinstance(tree, list):  # Handle multiple statements
            result = None
            for statement in tree:
                result = self.visit(statement)
            return result
        else:  # Single statement
            return self.visit(tree)