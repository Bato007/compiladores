import math
from antlr4 import *
from reader import resolveEntryPoint

from grammar.YalpParser import YalpParser
from grammar.YalpLexer import YalpLexer
from grammar.YalpVisitor import YalpVisitor

from tables import ClassesTable, VariablesTable, VariableObject, FunctionObject, FunctionsTable

entry_file = 'class.txt'
input_string = resolveEntryPoint(entry_file)

# print(input_string)

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

ERROR_STRING = 'ERROR'
default_init = {
  'Int': 0,
  'Bool': 'false',
}
uninherable = ['Bool', 'Int', 'String']
unoverloading = ['Object', 'IO', 'Bool', 'Int', 'String']

classes_table = ClassesTable()
variables_table = VariablesTable()

class TypeCollectorVisitor(YalpVisitor):
  def __init__(self):
    super().__init__()
    self.types = {}
    self.parser = parser
    self.check_later = {}

  # Checks if the program contains main class and the
  def checkMain():
    key = 'Main'
    if (not classes_table.contains(key)):
      print('>> Error Main class doesnt exists')

    mainClass = classes_table[key]

  # This is to check if it inherets first and then the class is defined (the one inhered)
  def checkPending(self): 
    for key in self.check_later:
      if (classes_table.contains(key)): continue
      class_name = self.check_later[key]
      print('>> Error in class', class_name, 'cannot inheret from class', key, 'since it doesnt exists')
      self.types[class_name] = ERROR_STRING 

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

  # Visit a parse tree produced by YalpParser#r_class.
  def visitR_class(self, ctx:YalpParser.R_classContext):
    class_name = ctx.getChild(1).getText()
    is_inherable = ctx.getChild(2).getText()
    parent = 'Object'
    error = False

    # If the class has a parent
    if ('inherits' == is_inherable.lower()):
      inhered_class = ctx.getChild(3).getText()

      if (
        inhered_class in uninherable    # Checks if its String, Bool or Int
        or inhered_class == class_name  # Avoids recursive herency
      ):
        error = True
        print('>> Error in class', class_name, 'cannot inheret from class', inhered_class)
      else:
        parent = inhered_class

      # Checks if the class is not defined yet
      if (not classes_table.contains(inhered_class)):
        self.check_later[inhered_class] = class_name

    # Class is already defined
    if (classes_table.contains(class_name)):
      error = True
      if (class_name in unoverloading):
        print('>> Error in class', class_name, 'cannot override this class')
      else:
        print('>> Error in class', class_name, 'is already defined')

    if (error):
      self.types[class_name] = ERROR_STRING 

    classes_table.add(class_name, parent)

    return self.visitChildren(ctx)

class PostOrderVisitor(YalpVisitor):
  def __init__(self, types):
    self.parser = parser
    self.types = types

  def getChildContext(self, tree, context):
    node_type = type(tree)
    if (node_type == YalpParser.R_classContext):
      return tree.getChild(1).getText()
      
    if (node_type == YalpParser.FunDeclarationContext):
      return tree.getChild(0).getText()
    return context

  def addVariable(self, tree, type, context):
    child_count = tree.getChildCount()
    var_name = tree.getChild(0).getText()
    value = None

    if (child_count > 1):
      value = tree.getChild(2).getText()

    added = variables_table.add(
      var_name,
      type,
      context,
      value
    )

    if (not added):
      print('>>>>>>', var_name, 'already exists in context', context)
      return ERROR_STRING

    return type

  def addFunction(self, node, child_types):
    child_count = node.getChildCount()
    last_index = child_count - 1

    fun_name = node.getChild(0).getText()
    fun_return_type = child_types[last_index - 3]
    num_params = math.ceil((child_count - 9) / 2)
    fun_code_type = child_types[last_index - 1]

    print(fun_name, fun_return_type, num_params, fun_code_type, child_types)
    
    return fun_return_type

  def visit(self, tree, context = None):
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
      node_type = type(tree)
      child_count = tree.getChildCount()
      child_context = self.getChildContext(tree, context)

      for i in range(child_count):
        child = tree.getChild(i)
        child_type = self.visit(child, child_context)

        child_types.append(child_type)

      if child_count == 1:
        return child_types[0]

      if (node_type == YalpParser.LoopTenseContext):
        if (child_types[1] != 'Bool'):
          print('>>>>>>', child_types[1], 'is a non valid operation for while')
          return ERROR_STRING

        if (ERROR_STRING in child_types):
          return ERROR_STRING

        return 'Object'

      if (node_type == YalpParser.IfTenseContext):

        # TODO: implicit cast
        if (child_types[1] != 'Bool'):
          print('>>>>>>', child_types[1], 'is a non valid operation for if')
          return ERROR_STRING

        if (ERROR_STRING in child_types):
          return ERROR_STRING
        
        if (child_types[3] == child_types[5]):
          return child_types[3]

        # TODO: when child types are diff then check parents
        # print('wuuuu>>>',child_types)
        return 'Void'

      if (
        node_type == YalpParser.VariableContext
        or node_type == YalpParser.FormalContext
      ):
        return child_types[2]
      
      if (node_type == YalpParser.Var_declarationsContext):
        return self.addVariable(
          tree,
          child_types[2],
          context
        )

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

          return ERROR_STRING

        return TYPES[key]

      if (node_type == YalpParser.Expr_paramsContext):
        return 'Void'

      if (node_type == YalpParser.FunDeclarationContext):
        if (ERROR_STRING in child_types):
          return ERROR_STRING

        # return self.addFunction(...)
        return 'Int'

      if (node_type == YalpParser.AssignmentContext):
        if (ERROR_STRING in child_types):
          variable = tree.getChild(0)
          print('Cannot assign to', variable.getText())
          return ERROR_STRING

        if (child_types[0] != child_types[2]):
          # TODO: Chacke 
          variable = tree.getChild(0)
          print('Cannot assign', child_types[0], 'with', child_types[2])
          return ERROR_STRING

        return child_types[0]
      
      if (node_type == YalpParser.FunctionCallContext):
        if (ERROR_STRING in child_types):
          return ERROR_STRING
        
        # TODO: Make this get the function type
        return 'Void'

      if (node_type == YalpParser.R_classContext):
        # print(tree.getChild(1).getText(), child_types)
        if (ERROR_STRING in child_types):
          return ERROR_STRING
        
        return tree.getChild(1).getText()

      class_types = list(filter(lambda a: a != 'Void', child_types))

      if (ERROR_STRING in class_types):
        print ('Type validation failed', class_types)
        return

      print('Type validation completed', class_types)

input_stream = InputStream(input_string)
lexer = YalpLexer(input_stream)
token_stream = CommonTokenStream(lexer)
parser = YalpParser(token_stream)
parse_tree = parser.r()

visitor = TypeCollectorVisitor()
visitor.visit(parse_tree)
visitor.checkPending()

visitor = PostOrderVisitor(visitor.types)
visitor.visit(parse_tree)

print(variables_table)