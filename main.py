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
    y.concat(s);
    1 + 1;
  };
};

class DB2 {
  s : Int <- 1;
  f() : Int {
    s <- s + 1;
  };
};
'''

RETURN_INTEGER = [
   ["INTEGER", "OPERATOR_PLUS", "INTEGER"],
   ["INTEGER", "OPERATOR_DIVIDE", "INTEGER"],
   ["INTEGER", "OPERATOR_MULTIPLY", "INTEGER"],
   ["INTEGER", "OPERATOR_MINUS", "INTEGER"],
   ["OPERATOR_TILDE", "INTEGER"],
]
RETURN_BOOL = [
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
      pass
    else:


      # Visit the children first
      for i in range(tree.getChildCount()):
        child = tree.getChild(i)
        self.visit(child)

      if type(tree) == YalpParser.Var_declarationsContext:
        pattern = r'(:|<-\s*)'
        parts = re.split(pattern, tree.getText())

        if (parts and len(parts) >= 3):
          cleaned_var = re.sub(r'\s+', '', parts[0])
          cleaned_type = re.sub(r'\s+', '', parts[2])

          if (cleaned_var in self.types):
             self.types[cleaned_var] = cleaned_type

        if (parts and len(parts) == 5):
          cleaned_value = re.sub(r'\s+', '', parts[4])
          print(f'0 variable {cleaned_var} declaration value: {cleaned_value} type: {cleaned_type} \n')
        elif (parts and len(parts) == 3):
          print(f'0 variable {cleaned_var} type: {cleaned_type} \n')
        else:
          raise("Unexpected var definition")

        return
      # Visit the current node if it's a ParserRuleContext
      elif type(tree) == YalpParser.R_classContext:
        print('1', tree.getText())
        # class_name = tree.CLASS_ID().getText()
        # self.current_class = class_name
        # self.symbol_table[class_name] = {}
        # if tree.RESERVED_INHERITS():
        #     parent_class_name = tree.CLASS_ID(1).getText()
        #     self.symbol_table[class_name].update(self.symbol_table[parent_class_name])

        # # Process the features
        # for feature_ctx in tree.feature():
        #     self.visit(feature_ctx)

      elif type(tree) == YalpParser.FeatureContext:
        print('2', tree.getText())
        # Process the feature rule
        # if tree.OBJ_ID(0):
        #     attribute_name = tree.OBJ_ID(0).getText()
        #     attribute_type = tree.CLASS_ID().getText()
        #     self.symbol_table[self.current_class][attribute_name] = attribute_type
        # else:
        #     method_name = tree.OBJ_ID(1).getText()
        #     method_return_type = tree.CLASS_ID().getText()
        #     self.symbol_table[self.current_class][method_name] = method_return_type
        #     for formal_ctx in tree.formal():
        #         arg_name = formal_ctx.OBJ_ID(0).getText()
        #         arg_type = formal_ctx.CLASS_ID().getText()
        #         self.symbol_table[self.current_class][arg_name] = arg_type

      elif type(tree) == YalpParser.ExprContext:
        # Handle expressions here
        token_name = ""
        if (tree.getText() in self.types):
            token_name = self.types[tree.getText()]
        else:
          chidren_nodes = []
          self.process_child(tree, chidren_nodes)
          print("entroooo en el else", tree.getText(), chidren_nodes)


        print(f'3 expressions value: {tree.getText()} token_name: {token_name} \n')
        pass

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
print("Types:", types)

visitor = PostOrderVisitor(types)
visitor.visit(parse_tree)
