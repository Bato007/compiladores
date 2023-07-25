from antlr4 import *
from YalpLexer import YalpLexer
from YalpParser import YalpParser
from YalpVisitor import YalpVisitor
from YalpListener import YalpListener
import re

input_string = '''
class DB {
  -- this is another comment
  helloString : String <- "Hello";
  byeString : String <- "Bye";
  g(y:String) : Int {
    y.concat(s, "wuuu");
    1 + 1;
  };
};

class DB2 {
  s : Int <- 1;
  f() : Int {
    1-1;
    "1" + 3;
    s <- s + 1;
    1*1;
    1/1;
    not 1;
    1<2;
    1<=2;
    1=2;
    ~2;
    true + false;
    false - false;
    false * true;
    false / false;
    not true;
    true < false;
    true <= true;
    false = false;
    ~ true;
    "hola" + "adios";
    "hola" - "adios";
    "hola" * "adios";
    "hola" / "adios";
    not "hola";
    "hola" < "adios";
    "hola" <= "adios";
    "hola" = "adios";
    ~"adios";
    "hola" * 2;
    true + 3;
    false / 2;
    2 + "a";
  };
};
'''
TRANSLATIONS = {
  'INT': 'INTEGER'
}

ARITHMETIC_OPERATORS = [
  'OPERATOR_PLUS',
  'OPERATOR_DIVIDE',
  'OPERATOR_MULTIPLY',
  'OPERATOR_MINUS',
  'RESERVED_NOT',
  'OPERATOR_TILDE'
]

TYPES = [
  ["INTEGER", "OPERATOR_PLUS", "INTEGER"] ,
  ["INTEGER", "OPERATOR_DIVIDE", "INTEGER"],
  ["INTEGER", "OPERATOR_MULTIPLY", "INTEGER"],
  ["INTEGER", "OPERATOR_MINUS", "INTEGER"],
  ["OPERATOR_TILDE", "INTEGER"],
  # Integers
  ["INTEGER", "OPERATOR_LESS", "INTEGER"],
  ["INTEGER", "OPERATOR_EQUALS", "INTEGER"],
  ["INTEGER", "OPERATOR_LESS_EQUAL", "INTEGER"],
  # Booleans
  ["OPERATOR_TILDE", "RESERVED_TRUE"],
  ["OPERATOR_TILDE", "RESERVED_FALSE"],
  ["RESERVED_NOT", "RESERVED_TRUE"],
  ["RESERVED_NOT", "RESERVED_FALSE"],
  ["RESERVED_TRUE", "OPERATOR_LESS", "RESERVED_TRUE"],
  ["RESERVED_FALSE", "OPERATOR_LESS", "RESERVED_FALSE"],
  ["RESERVED_TRUE", "OPERATOR_LESS", "RESERVED_FALSE"],
  ["RESERVED_FALSE", "OPERATOR_LESS", "RESERVED_TRUE"],
  ["RESERVED_TRUE", "OPERATOR_LESS_EQUAL", "RESERVED_TRUE"],
  ["RESERVED_FALSE", "OPERATOR_LESS_EQUAL", "RESERVED_FALSE"],
  ["RESERVED_TRUE", "OPERATOR_LESS_EQUAL", "RESERVED_FALSE"],
  ["RESERVED_FALSE", "OPERATOR_LESS_EQUAL", "RESERVED_TRUE"],
  ["RESERVED_TRUE", "OPERATOR_EQUALS", "RESERVED_TRUE"],
  ["RESERVED_FALSE", "OPERATOR_EQUALS", "RESERVED_FALSE"],
  ["RESERVED_TRUE", "OPERATOR_EQUALS", "RESERVED_FALSE"],
  ["RESERVED_FALSE", "OPERATOR_EQUALS", "RESERVED_TRUE"],
  # String
  ["STRING", "OPERATOR_LESS", "STRING"],
  ["STRING", "OPERATOR_EQUALS", "STRING"],
  ["STRING", "OPERATOR_LESS_EQUAL", "STRING"],
]

class TypeCollectorListener(YalpListener):  # Change the base class to YourGrammarListener
  def __init__(self):
    super().__init__()
    self.types = {}
    self.parser = parser

  def getRuleContext(self):
    return None

  def process_child(self, child):
    if isinstance(child, TerminalNode):
      symbol = child.symbol
      token_name = self.parser.symbolicNames[symbol.type]
      
      if (child.getText() in self.types):
        if (self.types[child.getText()] != token_name):
          raise ("Mismo hijo con diferente token")
      
      self.types[child.getText()] = token_name
    else:
        # Operando de forma recursiva hasta no tener reglas, sino tokens individuales
        for j in range(child.getChildCount()):
            sub_child = child.getChild(j)
            self.process_child(sub_child)

  def enterExpr(self, ctx):
    for i in range(ctx.getChildCount()):
      child = ctx.getChild(i)
      self.process_child(child)

class PostOrderVisitor(YalpVisitor):
  def __init__(self, types):
    self.symbol_table = {}
    self.current_class = None
    self.types = types

  def process_child(self, child, chidren_nodes):
    if isinstance(child, TerminalNode):
      chidren_nodes.append(
        self.types[child.getText()]
      ) 
    else:
      # Operando de forma recursiva hasta no tener reglas, sino tokens individuales
      for j in range(child.getChildCount()):
        sub_child = child.getChild(j)
        self.process_child(sub_child, chidren_nodes)

  def visit(self, tree):
    if isinstance(tree, TerminalNode):
      # Handle terminal nodes (tokens) here if needed
      if (tree.getText() in self.types.keys()):
        return self.types[tree.getText()]
      else:
        return 'Void'
    else:

      # Visit the children first
      child_types = []
      for i in range(tree.getChildCount()):
        child = tree.getChild(i)
        child_type = self.visit(child)

        child_types.append(child_type)

      if type(tree) == YalpParser.Var_declarationsContext:
        pattern = r'(:|<-\s*)'
        parts = re.split(pattern, tree.getText())

        if (parts and len(parts) >= 3):
          cleaned_var = re.sub(r'\s+', '', parts[0])
          cleaned_type = re.sub(r'\s+', '', parts[2]).upper()

          if (cleaned_type in TRANSLATIONS.keys()):
            cleaned_type = TRANSLATIONS.get(cleaned_type)

          if (cleaned_var in self.types):
            self.types[cleaned_var] = cleaned_type

      # Visit the current node if it's a ParserRuleConte
      elif type(tree) == YalpParser.ExprContext:
        if (tree.getText() in self.types):
          token_name = self.types[tree.getText()]
        else:
          chidren_nodes = []
          self.process_child(tree, chidren_nodes)

          if (chidren_nodes not in TYPES):
            temp = chidren_nodes[:]
            if 'OPERATOR_ASSIGNMENT' in chidren_nodes:
              temp = chidren_nodes[2:]
            for operator in ARITHMETIC_OPERATORS:
              if (
                operator in temp
                and temp not in TYPES
              ):
                print(f'Error in: {tree.getText()} rule {temp} not valid \n')

# Create an input stream of the expression
input_stream = InputStream(input_string)

# Create a lexer that reads from the input stream
lexer = YalpLexer(input_stream)

# Create a stream of tokens from the lexer
token_stream = CommonTokenStream(lexer)

# Create a parser that reads from the token stream
parser = YalpParser(token_stream)

# Start the parsing process by calling the 'r' rule
parse_tree = parser.r()

walker = ParseTreeWalker()
listener = TypeCollectorListener()
walker.walk(listener, parse_tree)
types = listener.types
# print("Types:", types)

visitor = PostOrderVisitor(types)
visitor.visit(parse_tree)
