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
LIMIT = 50
default_init = {
  'Int': 0,
  'Bool': 'false',
}
uninherable = ['Bool', 'Int', 'String']
unoverloading = ['Object', 'IO', 'Bool', 'Int', 'String']

classes_table = ClassesTable()
variables_table = VariablesTable()
functions_table = FunctionsTable()

class TypeCollectorVisitor(YalpVisitor):
  def __init__(self):
    super().__init__()
    self.types = {}
    self.parser = parser
    self.class_context = ''
    self.fun_context = ''
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

  # Adds variable to table
  def addVariable(self, var_name, var_type, var_context, var_default = None):
    return variables_table.add(
      var_name,
      var_type,
      var_context,
      var_default
    )

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
  
  # Visit a parse tree produced by YalpParser#var_declarations.
  def visitVar_declarations(self, ctx:YalpParser.Var_declarationsContext):
    var_name = ctx.getChild(0).getText()
    var_type = ctx.getChild(2).getText()
    var_value = None

    if (ctx.getChildCount() > 3):
      var_value = ctx.getChild(-1).getText()

    added = self.addVariable(
      var_name,
      var_type,
      self.class_context,
      var_value
    )

    if (not added):
      print('>>>> Variable:', var_name, 'already defined in class', self.class_context)
      variable = variables_table.get(var_name, self.class_context)
      variable.setError()
    return self.visitChildren(ctx)

  # Visit a parse tree produced by YalpParser#formal.
  def visitFormal(self, ctx:YalpParser.FormalContext):
    var_name = ctx.getChild(0).getText()
    var_type = ctx.getChild(-1).getText()
    var_context = self.class_context + '-' + self.fun_context

    added = self.addVariable(
      var_name,
      var_type,
      var_context
    )

    if (not added):
      print('>>>> Variable:', var_name, 'already defined in function', self.fun_context)
      variable = variables_table.get(var_name, var_context)
      variable.setError()

    function = functions_table.get(self.fun_context, self.class_context)
    function.addParam(var_name, var_type)

    return self.visitChildren(ctx)

  # Visit a parse tree produced by YalpParser#funDeclaration.
  def visitFunDeclaration(self, ctx:YalpParser.FunDeclarationContext):
    fun_name = ctx.getChild(0).getText()
    fun_context = self.class_context
    fun_return_type = ctx.getChild(-4).getText()
    self.fun_context = fun_name

    if (fun_return_type == 'SELF_TYPE'):
      fun_return_type = fun_context

    added = functions_table.add(
      fun_name,
      fun_context,
      fun_return_type
    )

    if (not added):
      print('>>>> Function', fun_name, 'already defined in', fun_context)

    return self.visitChildren(ctx)

  # Visit a parse tree produced by YalpParser#r_class.
  def visitR_class(self, ctx:YalpParser.R_classContext):
    class_name = ctx.getChild(1).getText()
    is_inherable = ctx.getChild(2).getText()
    parent = None
    error = False
    self.class_context = class_name

    if (class_name != 'Object'):
      parent = 'Object'

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
    self.class_context = ''
    self.fun_context = ''
  
  # This function will update the context of the current visited branch
  def updateContext(self, node):
    node_type = type(node)
    if (node_type == YalpParser.R_classContext):
      self.class_context = node.getChild(1).getText()
      
    if (node_type == YalpParser.FunDeclarationContext):
      self.fun_context = node.getChild(0).getText()

  def getVarDeclarationType(self, node):
    var_name = node.getChild(0).getText()
    variable = variables_table.get(var_name, self.class_context)

    if (variable is None):
      print('>>>>>> Variable', var_name, 'doesnt exists in context', self.class_context)
      return ERROR_STRING

    return variable.type

  def getFunctionDeclarationType(self, child_types):
    function = functions_table.get(self.fun_context, self.class_context)

    if (function.return_type == child_types[-2]):
      return function.return_type

    if (child_types[-2] == 'Void'): return 'Void'

    i = 0
    parent_class = classes_table.get(child_types[-2]).getParent()
    while (True):
      if (function.return_type == parent_class): break
      if (i == LIMIT or parent_class is None): 
        print('>>> Return type of', child_types[-2], 'cannot be assigned to', function.return_type, function.name, function.context)
        parent_class = ERROR_STRING
        break
      parent_class = classes_table.get(parent_class).getParent()
      i += 1

    return parent_class

  def visit(self, tree):
    if isinstance(tree, TerminalNode):
      if (tree.getText() in unoverloading): return tree.getText()
      if (tree.getText() in ['SELF_TYPE', 'self']): return self.class_context
      if (tree.getText() in self.types.keys()): return self.types[tree.getText()]
      if (self.parser.symbolicNames[tree.symbol.type] != 'OBJ_ID'): return 'Void'

      obj_name = tree.getText()

      # Variable defined in class
      class_var = variables_table.get(obj_name, self.class_context)
      if (class_var is not None):
        return class_var.type

      # Functions defined in class
      class_fun = functions_table.get(obj_name, self.class_context)
      if (class_fun is not None): 
        return class_fun.return_type

      # Variable defined in function
      fun_var = variables_table.get(obj_name, self.class_context + '-' + self.fun_context)
      if (fun_var is not None): 
        return fun_var.type

      print('-==============================', tree.getText())
      return 'Void'

    else:
      child_types = []
      node_type = type(tree)
      child_count = tree.getChildCount()
      self.updateContext(tree)

      # Visit the children first
      for i in range(child_count):
        child = tree.getChild(i)
        child_types.append(self.visit(child))

      if child_count == 1: return child_types[0]
      if (node_type == YalpParser.ParentesisContext): return child_types[1]
      if (node_type == YalpParser.InstructionsContext): return child_types[-3]
      if (node_type == YalpParser.Var_declarationsContext): return self.getVarDeclarationType(tree)
      if (node_type == YalpParser.FormalContext): return child_types[2]

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

        i = 0
        left_type = child_types[3]
        right_type = classes_table.get(child_types[5]).getParent()
        while True:
          if (left_type == right_type): break
          if (i == LIMIT): 
            print('>>> Check super class of this')
            left_type = ERROR_STRING
            break

          right_type = classes_table.get(right_type).getParent()
          if (right_type is None):
            right_type = child_types[5]
            left_type = classes_table.get(left_type).getParent()

          i += 1
        return left_type

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

        return self.getFunctionDeclarationType(child_types)

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
        # variables = tree.getChild(0).getText().split(".")
        # params =  tree.getChild(2).getText()

        print(tree.getText(), child_count, child_types)

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