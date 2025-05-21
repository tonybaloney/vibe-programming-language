class Token:
    def __init__(self, type, value=None, line=1):
        self.type = type
        self.value = value
        self.line = line
    
    def __repr__(self):
        if self.value:
            return f"Token({self.type}, {repr(self.value)})"
        return f"Token({self.type})"

class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.current_char = self.source[0] if len(self.source) > 0 else None
    
    def advance(self):
        self.pos += 1
        if self.pos >= len(self.source):
            self.current_char = None
        else:
            if self.source[self.pos] == '\n':
                self.line += 1
            self.current_char = self.source[self.pos]
    
    def peek(self, n=1):
        peek_pos = self.pos + n
        if peek_pos >= len(self.source):
            return None
        return self.source[peek_pos]
    
    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()
    
    def skip_comment(self):
        if self.current_char == '/' and self.peek() == '/':
            self.advance()  # Skip first '/'
            self.advance()  # Skip second '/'
            
            # Skip until end of line
            while self.current_char is not None and self.current_char != '\n':
                self.advance()
            
            # Skip the newline
            if self.current_char == '\n':
                self.advance()
    
    def get_string(self):
        result = ""
        # Skip the opening quote
        self.advance()
        
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        
        # Skip the closing quote
        if self.current_char == '"':
            self.advance()
        else:
            raise Exception(f"Unterminated string at line {self.line}")
            
        return result
    
    def get_number(self):
        result = ""
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        
        return int(result)
    
    def get_identifier(self):
        result = ""
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        
        return result
    
    def is_emoji_assignment(self):
        # Check for ➡️ (right arrow emoji)
        return self.current_char == '➡' and self.peek() == '️'
    
    def tokenize(self):
        tokens = []
        
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
                
            if self.current_char == '/' and self.peek() == '/':
                self.skip_comment()
                continue
                
            if self.current_char == '"':
                tokens.append(Token('STRING', self.get_string(), self.line))
            elif self.current_char.isdigit():
                tokens.append(Token('NUMBER', self.get_number(), self.line))
            elif self.current_char.isalpha() or self.current_char == '_':
                identifier = self.get_identifier()
                if identifier == 'holla':
                    tokens.append(Token('HOLLA', line=self.line))
                else:
                    tokens.append(Token('IDENTIFIER', identifier, self.line))
            elif self.is_emoji_assignment():
                self.advance()  # Skip ➡
                self.advance()  # Skip ️ (variation selector)
                tokens.append(Token('ASSIGN', line=self.line))
            elif self.current_char == '+':
                self.advance()
                tokens.append(Token('PLUS', line=self.line))
            else:
                raise Exception(f"Invalid character: {self.current_char} at line {self.line}")
                
        tokens.append(Token('EOF', line=self.line))
        return tokens