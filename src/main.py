from antlr4 import *
from grammar.YalpParser import YalpParser
from grammar.YalpLexer import YalpLexer
from grammar.YalpListener import YalpListener
from grammar.YalpVisitor import YalpVisitor

input_string = '''
class DB {
  -- this is another comment
  helloString : String <- "Hello";
  byeString : String <- "Bye";

  g(y:String) : Int {
    y.concat(s, "wuuu");
    1 - 3 * (2 - 3);
    1 = true;
    1 + "1";
    1 + 1;
  };

  flag : Bool <- true;
  thisAnotherFun(y:Int, well:String, pepe:Bool) : Int {
    while flag = true loop
      flag <- false
    pool;
  };
};

class DB2 {
  s : Int <- 1;
  blue : Bool <- true;
  f() : Int {
    if blue then
      s <- s + 1 - 3 * (2 - 3)
    else
      s <- 34 * (5 + 23) / 23 + 32
    fi;
  };
};
'''

TYPES = {
  'Int-OPERATOR_PLUS-Int': 'Int',
  'Int-OPERATOR_MINUS-Int': 'Int',
  'Int-OPERATOR_DIVIDE-Int': 'Int',
  'Int-OPERATOR_MULTIPLY-Int': 'Int',
  'OPERATOR_TILDE-Int': 'Int',
  # Integers
  'Int-OPERATOR_LESS-Int': 'Bool',
  'Int-OPERATOR_EQUALS-Int': 'Bool',
  'Int-OPERATOR_LESS_EQUAL-Int': 'Bool',
  # Booleans
  'OPERATOR_TILDE-Bool': 'Bool',
  'RESERVED_NOT-Bool': 'Bool',
  'Bool-OPERATOR_LESS-Bool': 'Bool',
  'Bool-OPERATOR_LESS_EQUAL-Bool': 'Bool',
  'Bool-OPERATOR_EQUALS-Bool': 'Bool',
  # String
  'String-OPERATOR_LESS-String': 'Bool',
  'String-OPERATOR_EQUALS-String': 'Bool',
  'String-OPERATOR_LESS_EQUAL-String': 'Bool',
}

class TypeCollectorVisitor(YalpVisitor):
  def __init__(self):
    super().__init__()
    self.types = {}
    self.parser = parser

  # Visit a parse tree produced by YalpParser#string.
  def visitString(self, ctx:YalpParser.StringContext):
    self.types[ctx.getText()] = 'String'
    return self.visitChildren(ctx)

  # Visit a parse tree produced by YalpParser#bool.
  def visitBoolean(self, ctx:YalpParser.BooleanContext):
    self.types[ctx.getText()] = 'Bool'
    return self.visitChildren(ctx)

  # Visit a parse tree produced by YalpParser#int.
  def visitInt(self, ctx:YalpParser.IntContext):
    self.types[ctx.getText()] = 'Int'
    return self.visitChildren(ctx)

  # Visit a parse tree produced by YalpParser#variable.
  def visitVariable(self, ctx:YalpParser.VariableContext):
    if ctx.getChildCount() == 1:
      child = ctx.getChild(0)

      key = self.parser.symbolicNames[child.symbol.type]
      self.types[child.getText()] = key
    else:
      varName = ctx.getChild(0)
      varType = ctx.getChild(2)
      self.types[varName.getText()] = varType.getText()

    return self.visitChildren(ctx)

  # Visit a parse tree produced by YalpParser#objectId.
  def visitObjectId(self, ctx:YalpParser.ObjectIdContext):
    return self.visitChildren(ctx)

  # Visit a parse tree produced by YalpParser#formal.
  def visitFormal(self, ctx:YalpParser.FormalContext):
    return self.visitChildren(ctx)

  # Visit a parse tree produced by YalpParser#var_declarations.
  def visitVar_declarations(self, ctx:YalpParser.Var_declarationsContext):
    return self.visitChildren(ctx)

  # Visit a parse tree produced by YalpParser#feature.
  def visitFeature(self, ctx:YalpParser.FeatureContext):
    return self.visitChildren(ctx)

class PostOrderVisitor(YalpVisitor):
  def __init__(self, types):
    self.parser = parser
    self.types = types

  def visit(self, tree):
    if isinstance(tree, TerminalNode):
      # Handle terminal nodes (tokens) here if needed
      key = self.parser.symbolicNames[tree.symbol.type]

      if (tree.getText() in self.types.keys()):
        return self.types[tree.getText()]
      elif (tree.getText() == 'String'):
        return 'String'
      elif (tree.getText() == 'Int'):
        return 'Int'
      elif (tree.getText() == 'Bool'):
        return 'Bool'
      elif (key == 'OBJ_ID'):
        return key
      else:
        return 'Void'

    else:
      # Visit the children first
      child_types = []
      child_count = tree.getChildCount()
      for i in range(child_count):
        child = tree.getChild(i)
        child_type = self.visit(child)

        child_types.append(child_type)

      if child_count == 1:
        return child_types[0]

      node_type = type(tree)
    
      if (node_type == YalpParser.LoopTenseContext):
        if (child_types[1] != 'Bool'):
          print('>>>>>>', child_types[1], 'is a non valid operation')
          return 'ERROR'

        if ('ERROR' in child_types):
          return 'ERROR'

        # TODO: is void?
        return 'Void'

      if (node_type == YalpParser.IfTenseContext):
        if (child_types[1] != 'Bool'):
          print('>>>>>>', child_types[1], 'is a non valid operation')
          return 'ERROR'

        if ('ERROR' in child_types):
          return 'ERROR'

        # TODO: is void?
        return 'Void'

      if (
        node_type == YalpParser.VariableContext
        or node_type == YalpParser.Var_declarationsContext
        or node_type == YalpParser.FormalContext
      ):
        return child_types[2]
      
      if (node_type == YalpParser.ParentesisContext):
        return child_types[1]

      if (
        node_type == YalpParser.ArithmeticalContext
        or node_type == YalpParser.LogicalContext
      ):
        leftOperand, _, rightOperand =  child_types
        operator = tree.getChild(1)
        operatorType = self.parser.symbolicNames[operator.symbol.type]

        key = leftOperand + '-' + operatorType + '-' + rightOperand
        if (key not in TYPES):
          if (node_type == YalpParser.ArithmeticalContext):
            print('>>>> Cannot operate', leftOperand, 'with', rightOperand)
          else:
            print('>>>> Cannot compare', leftOperand, 'with', rightOperand)

          return 'ERROR'

        return TYPES[key]

      if (node_type == YalpParser.Expr_paramsContext):
        return 'Void'

      if (node_type == YalpParser.FunDeclarationContext):
        if ('ERROR' in child_types):
          return 'ERROR'

        # TODO: GEt fun type
        return 'Int'

      if (node_type == YalpParser.AssignmentContext):
        if ('ERROR' in child_types):
          variable = tree.getChild(0)
          print('Cannot assign to', variable.getText())
          return 'ERROR'

        if (child_types[0] != child_types[2]):
          variable = tree.getChild(0)
          print('Cannot assign', child_types[0], 'with', child_types[2])
          return 'ERROR'

        return child_types[0]
      
      if (node_type == YalpParser.FunctionCallContext):
        if ('ERROR' in child_types):
          return 'ERROR'
        
        # TODO: Make this get the function type
        return 'Void'

      if (node_type == YalpParser.R_classContext):
        if ('ERROR' in child_types):
          return 'ERROR'
        
        return tree.getText()[5:].split('{')[0]

      class_types = list(filter(lambda a: a != 'Void', child_types))

      if ('ERROR' in class_types):
        print ('Type validation failed', class_types)
        return

      print('Type validation completed', class_types)

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

visitor = TypeCollectorVisitor()
visitor.visit(parse_tree)
# print("Types:", visitor.types)

visitor = PostOrderVisitor(visitor.types)
visitor.visit(parse_tree)
