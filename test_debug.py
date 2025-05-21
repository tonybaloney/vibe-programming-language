# Debug script
import sys
from src.tokenizer import Lexer
from src.parser import Parser
from src.interpreter import Interpreter

print("Starting debug script")

with open('test.vpl', 'r') as f:
    source = f.read()

print(f"Source content: '{source}'")

print("Creating lexer")
lexer = Lexer(source)
print("Tokenizing")
tokens = lexer.tokenize()
print("Tokens:")
for token in tokens:
    print(f"  {token}")

print("Creating parser")
parser = Parser(tokens)
print("Parsing")
ast = parser.parse()
print(f"AST type: {type(ast)}")

print("Creating interpreter")
interpreter = Interpreter()
print("Interpreting")
result = interpreter.interpret(ast)
print(f"Result: {result}")

print("Debug script complete")
