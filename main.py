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
        self.types = []
        self.parser = parser

    def getRuleContext(self):
        return None

    def enterExpr(self, ctx):
        for i in range(ctx.getChildCount()):
            child = ctx.getChild(i)
            if isinstance(child, TerminalNode):
                symbol = child.symbol
                token_name = self.parser.symbolicNames[symbol.type]
                self.types.append(token_name)
            # else:
            #     rule_name = self.parser.ruleNames[child.getRuleIndex()]
            #     self.types.append(rule_name)

class PostOrderVisitor(YalpVisitor):
  def __init__(self):
    self.symbol_table = {}
    self.current_class = None
    self.types = []

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
        print('0', tree.getText(), type(tree).__name__, tree.value)
        return
      # Visit the current node if it's a ParserRuleContext
      elif type(tree) == YalpParser.R_classContext:
        # Process the r_class rule
        print('1', tree.getText(), type(tree).__name__, tree.value)
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
        print('2', tree.getText(), type(tree).__name__, tree.value)
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
        print('3', tree.getText(), type(tree).__name__, tree.value)
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

visitor = PostOrderVisitor()

walker = ParseTreeWalker()
# Optionally add a listener and let it walk the tree
listener = TypeCollectorListener()
walker.walk(listener, parse_tree)

types = listener.types
print("Types:", types)

# visitor.visit(parse_tree)
