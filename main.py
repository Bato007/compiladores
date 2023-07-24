from antlr4 import *
from YalpLexer import YalpLexer
from YalpParser import YalpParser
from YalpVisitor import YalpVisitor
from YalpListener import YalpListener

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

operators = {

}


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
        print('0', tree.getText())
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

# visitor = PostOrderVisitor(types)
# visitor.visit(parse_tree)
