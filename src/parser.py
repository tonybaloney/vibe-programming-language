class AST:
    pass

class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class String(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Var(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Assign(AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class HollaStmt(AST):
    def __init__(self, expr):
        self.expr = expr

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0]
    
    def error(self):
        raise Exception(f"Parser error at line {self.current_token.line}")
    
    def advance(self):
        self.pos += 1
        if self.pos >= len(self.tokens):
            self.current_token = None
        else:
            self.current_token = self.tokens[self.pos]
    
    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.advance()
        else:
            self.error()
    
    def factor(self):
        token = self.current_token
        
        if token.type == 'NUMBER':
            self.eat('NUMBER')
            return Num(token)
        elif token.type == 'STRING':
            self.eat('STRING')
            return String(token)
        elif token.type == 'IDENTIFIER':
            self.eat('IDENTIFIER')
            return Var(token)
        else:
            self.error()
    
    def term(self):
        node = self.factor()
        
        while self.current_token is not None and self.current_token.type == 'PLUS':
            token = self.current_token
            self.eat('PLUS')
            node = BinOp(left=node, op=token, right=self.factor())
            
        return node
    
    def expr(self):
        return self.term()
    
    def assignment_statement(self):
        left = Var(self.current_token)
        self.eat('IDENTIFIER')
        self.eat('ASSIGN')
        right = self.expr()
        return Assign(left, right)
    
    def holla_statement(self):
        self.eat('HOLLA')
        expr = self.expr()
        return HollaStmt(expr)
    
    def statement(self):
        if self.current_token.type == 'IDENTIFIER':
            return self.assignment_statement()
        elif self.current_token.type == 'HOLLA':
            return self.holla_statement()
        else:
            self.error()
    
    def program(self):
        statements = []
        while self.current_token is not None and self.current_token.type != 'EOF':
            statements.append(self.statement())
        return statements
    
    def parse(self):
        return self.program()