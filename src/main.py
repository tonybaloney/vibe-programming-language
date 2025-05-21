import sys
from tokenizer import Lexer
from parser import Parser
from interpreter import Interpreter

def run_file(filename):
    with open(filename, 'r') as f:
        source = f.read()
    run(source)

def run(source):
    try:
        print("Tokenizing source...")
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        for token in tokens:
            print(f"  {token}")
        
        print("Parsing tokens...")
        parser = Parser(tokens)
        ast = parser.parse()
        print(f"AST: {type(ast)}")
        
        print("Interpreting AST...")
        interpreter = Interpreter()
        result = interpreter.interpret(ast)
        print(f"Result: {result}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error: {e}")

def main():
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        # Interactive REPL mode
        print("Vibe Language Interpreter (REPL)")
        print("Type 'exit()' to exit")
        while True:
            try:
                line = input(">>> ")
                if line == "exit()":
                    break
                run(line)
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()