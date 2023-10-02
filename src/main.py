import math
from antlr4 import *
from reader import resolveEntryPoint
from constants import *

from grammar.YalpParser import YalpParser
from grammar.YalpLexer import YalpLexer
from grammar.YalpVisitor import YalpVisitor

from tables import ClassesTable, VariablesTable, LoopObject, FunctionsTable, TemporalsTable

entry_file = 'class.txt'
input_string = resolveEntryPoint(entry_file)

classes_table = ClassesTable()
variables_table = VariablesTable()
functions_table = FunctionsTable()
temporals_table = TemporalsTable()

def get_tree_line(tree):
  # Get the token interval associated with the tree node
  start_token_index = tree.getSourceInterval()[0]
  end_token_index = tree.getSourceInterval()[1]

  # Access the corresponding tokens and their line/column information
  start_token = token_stream.get(start_token_index)
  end_token = token_stream.get(end_token_index)

  start_line, start_column = start_token.line, start_token.column
  end_line, end_column = end_token.line, end_token.column

  print(f"Start Line: {start_line}, Start Column: {start_column}")
  print(f"End Line: {end_line}, End Column: {end_column}")

def get_ctx_line(ctx):
    # Get line and column information from ctx
    line = ctx.start.line
    column = ctx.start.column

    print(f"Line: {line}, Column: {column}")

class TypeCollectorVisitor(YalpVisitor):
  def __init__(self):
    super().__init__()
    self.types = {}
    self.parser = parser
    self.class_context = ''
    self.fun_context = ''
    self.check_later = {}
    self.let_id = 0

  def compileClass(self):
    if (self.class_context == ''): return

    current_class = classes_table.get(self.class_context)

    for function_name in current_class.functions:
      function = functions_table.get(function_name, self.class_context)
      if (function.let_num != 0):
        for id in range(function.let_num):
          let_name = f'let-{id + 1}'
          let_context = f'{self.class_context}-{function.name}'

          let = functions_table.get(let_name, let_context)
          let.updateOffset(function.size)
          function.addToSize(let.size)

      function.updateOffset(current_class.getSize())
      current_class.updateOffset(function.size)

  # Checks if the program contains main class and the
  def checkMain(self):
    key = 'Main'
    if (not classes_table.contains(key)):
      print('>> Error Main class doesnt exists')

    main_fun = functions_table.get('main', key)
    
    is_object_return = False
    current_class = main_fun.return_type
    while True:
      check_object = classes_table.get(current_class)
      if (check_object.getParent() == "Object" or current_class == "Object"):
        is_object_return = True
        break
      elif (check_object.getParent() == None):
        break
      else:
        current_class = check_object.getParent()

    if (
      main_fun is None
      or main_fun.num_params != 0
      or not is_object_return
    ):
      print('>> Function main(): object {}; doesnt exists in Main class')

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

    var = variables_table.get(var_name, self.class_context)

    current_class = classes_table.get(self.class_context)

    size = 0
    if (var_type == self.class_context):
      size = POINTER_SIZE

    try:
      size = classes_table.get(var_type).getSize()
    except: pass
    
    var.setSize(size)
    var.setOffset(current_class.getOffset())

    current_class.updateOffset(var.getSize())
    current_class.addVariable(var_name)
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
      return self.visitChildren(ctx)

    var = variables_table.get(var_name, var_context)

    function = functions_table.get(self.fun_context, self.class_context)

    size = 0
    if (var_type == self.class_context):
      size = POINTER_SIZE

    try:
      size = classes_table.get(var_type).getSize()
    except: pass
    
    var.setSize(size)
    var.setOffset(function.getSize())

    function.addParam(var_name, var_type, var.getSize())

    return self.visitChildren(ctx)

  # Visit a parse tree produced by YalpParser#funDeclaration.
  def visitFunDeclaration(self, ctx:YalpParser.FunDeclarationContext):
    self.let_id = 0
    fun_name = ctx.getChild(0).getText()
    fun_context = self.class_context
    fun_return_type = ctx.getChild(-4).getText()
    fun_param_num = math.ceil((ctx.getChildCount() - 8) / 2)

    self.fun_context = fun_name
    current_class = classes_table.get(self.class_context)

    if (fun_return_type == 'SELF_TYPE'):
      fun_return_type = fun_context

    added = functions_table.add(
      fun_name,
      fun_context,
      fun_return_type,
      fun_param_num
    )

    if (not added):
      print('>>>> Function', fun_name, 'already defined in', fun_context)

    current_class.addFunction(fun_name)
    return self.visitChildren(ctx)

  def visitLetTense(self, ctx:YalpParser.LetTenseContext):
    self.let_id += 1
    fun_name = f'let-{self.let_id}'
    fun_context = f'{self.class_context}-{self.fun_context}'
    fun_param_num = math.ceil((ctx.getChildCount() - 3) / 2)

    added = functions_table.add(
      fun_name,
      fun_context,
      None,
      fun_param_num
    )

    if (not added):
      print('>>>> Function', fun_name, 'already defined in', fun_context)
      return self.visitChildren(ctx)
    function = functions_table.get(self.fun_context, self.class_context)
    function.addLet()

    return self.visitChildren(ctx)

  def visitLetParam(self, ctx:YalpParser.LetParamContext):
    fun_name = f'let-{self.let_id}'
    fun_context = f'{self.class_context}-{self.fun_context}'

    var_name = ctx.getChild(0).getText()

    if (ctx.getChildCount() == 5):
      var_type = ctx.getChild(-3).getText()
      default_value = ctx.getChild(-1).getText()
    else:
      var_type = ctx.getChild(-1).getText()
      default_value = None
    
    var_context = f'{self.class_context}-{self.fun_context}-let-{self.let_id}'

    added = self.addVariable(
      var_name,
      var_type,
      var_context,
      default_value
    )

    if (not added):
      print('>>>> Variable:', var_name, 'already defined in function', self.fun_context)
      variable = variables_table.get(var_name, var_context)
      variable.setError()

    function = functions_table.get(fun_name, fun_context)
    var = variables_table.get(var_name, var_context)

    size = 0  
    if (var_type == self.class_context):
      size = POINTER_SIZE

    try:
      size = classes_table.get(var_type).getSize()
    except: pass
    
    var.setSize(size)
    var.setOffset(function.getSize())

    function.addParam(var_name, var_type, var.getSize())

    return self.visitChildren(ctx)

  # Visit a parse tree produced by YalpParser#r_class.
  def visitR_class(self, ctx:YalpParser.R_classContext):
    self.compileClass()
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
    ok_inherit = functions_table.inheritFunctions(parent, class_name)
    if not (ok_inherit):
      error = True
      print('>> Error in class', class_name, 'cannot override method from parent', parent)

    return self.visitChildren(ctx)

  def compile(self, tree):
    self.visit(tree)
    self.checkPending()
    self.compileClass()

class PostOrderVisitor(YalpVisitor):
  def __init__(self, types):
    self.parser = parser
    self.types = types
    self.class_context = ''
    self.fun_context = ''
    self.let_id = 0
    self.inherited_context = ''
    self.lastTemp = None
    self.loops = []
  
  # This function will update the context of the current visited branch
  def updateContext(self, node):
    node_type = type(node)
    if (node_type == YalpParser.R_classContext):
      self.class_context = node.getChild(1).getText()

      if (self.class_context not in unoverloading):
        print("", self.class_context)
      
    if (node_type == YalpParser.FunDeclarationContext):
      self.fun_context = node.getChild(0).getText()
      self.let_id = 0

      if (self.class_context not in unoverloading):
        print("   ", self.fun_context)
        

    if (node_type == YalpParser.LetTenseContext):
      self.let_id += 1

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
      
      is_inherited_return_type = False

      if (self.inherited_context != None):
        current_class = self.inherited_context
      else:
        current_class = self.class_context

      while True:
        current_class = classes_table.get(current_class)

        if (current_class.getParent() == child_types[-2]):
          is_inherited_return_type = True
          break
        elif (current_class.getParent() == None):
          break
        else:
          current_class = current_class.getParent()
      if (is_inherited_return_type): break

      if (i >= LIMIT or parent_class is None): 
        print('>>> Return type of', child_types[-2], 'cannot be assigned to', function.return_type, function.name, function.context)
        parent_class = ERROR_STRING
        break
      parent_class = classes_table.get(parent_class).getParent()
      i += 1

    return parent_class

  def checkFunctionCall(self, fun_name, full_params, class_name = None, children = []):
    print(f'      {fun_name}')
    
    for param in children:
      if (not param == ","):
        print(f'            PARAM {param}')
    print(f'            CALL {fun_name}')

    param_types = []
    for i in range(0, len(full_params), 2):
      param_types.append(full_params[i])

    class_context = self.class_context if class_name is None else class_name

    function = functions_table.get(fun_name, class_context)

    if (function is None):
      print(fun_name, class_context)
      print('>>> Function doesnt exists in class', class_context)
      return ERROR_STRING

    if (len(param_types) != function.num_params):
      print('>>>', function.name, 'expecting', len(function.param_types), 'but got', len(param_types), 'params')
      return ERROR_STRING

    hadError = False
    for i in range(len(param_types)):
      if (param_types[i] != function.param_types[i]):
        print('>>>', function.param_names[i], 'expected to be', function.param_types[i], 'but found', param_types[i], 'in function', function.name)
        hadError = True

    if (hadError):
      return ERROR_STRING

    if (function.is_inherited):
      self.inherited_context = class_context
    else:
      self.inherited_context = None

    return function.return_type

  def varFunctionCall(self, node, child_types, children):
    var_type = child_types[0]
    fun_name = node.getChild(2).getText()
    return self.checkFunctionCall(fun_name, child_types[4:-1], var_type, children[4:-1])

  def parentFunctionCall(self, node, child_types, children):
    var_type = node.getChild(2).getText()
    fun_name = node.getChild(4).getText()
    return self.checkFunctionCall(fun_name, child_types[6:-1], var_type, children[6:-1])

  def visit(self, tree):
    temporal_context = f'{self.class_context}-{self.fun_context}'
    if (self.lastTemp != None and self.lastTemp.context != temporal_context):
      self.lastTemp = None
      self.loops = []

    if isinstance(tree, TerminalNode):
      if (tree.getText() in unoverloading): return tree.getText()
      if (tree.getText() in ['SELF_TYPE', 'self']): return self.class_context
      if (tree.getText() in self.types.keys()): return self.types[tree.getText()]
      if (self.parser.symbolicNames[tree.symbol.type] != 'OBJ_ID'): return 'Void'

      obj_name = tree.getText()

      # Let defined in function
      local_id = self.let_id
      for temp_id in reversed(range(1, local_id + 1)):
        let_var = variables_table.get(obj_name, f'{self.class_context}-{self.fun_context}-let-{temp_id}')
        if (let_var is not None): 
          return let_var.type

      # Variable defined in function
      fun_var = variables_table.get(obj_name, self.class_context + '-' + self.fun_context)
      if (fun_var is not None): 
        return fun_var.type

      # Functions defined in class
      class_fun = functions_table.get(obj_name, self.class_context)
      if (class_fun is not None): 
        return class_fun.return_type
      
      # Variable defined in class
      class_var = variables_table.get(obj_name, self.class_context)
      if (class_var is not None):
        return class_var.type

      existing_function = functions_table.function_exists_with_name(obj_name)
      if (existing_function):
        return 'Void'

      print('Unknown', tree.getText())
      return 'Void'

    else:
      child_types = []
      original_children = []
      node_type = type(tree)
      child_count = tree.getChildCount()
      self.updateContext(tree)

      # Visit the children first
      for i in range(child_count):
        child = tree.getChild(i)

        if (child.getText() == "fi" or child.getText() == "pool"): self.loops.pop().end()
        if (child.getText() == "then" or child.getText() == "while"):
          next_condition = tree.getChild(i + 1).getText()
          if (next_condition == "true" or next_condition == "false"):
            # Saving temporary var
            if (self.lastTemp == None):
              current_id = 1
            else:
              current_id = self.lastTemp._id + 1

            added_temporal = temporals_table.add(current_id, temporal_context, next_condition)
            added_temporal.three_way_print()
            
            self.lastTemp = added_temporal

        if (child.getText() == "loop" 
            or child.getText() == "else" 
            or child.getText() == "then"):
            
          if (len(self.loops) == 0):
            current_id = 1
          else:
            current_id = self.loops[-1]._id + 1

          if (child.getText() == "else"): self.loops.pop().end()

          # TODO: Se tiene que obtener el return de la funcion
          # y guardarlo como un temporal
          if (self.lastTemp == None):
            # Saving temporary var
            current_id = 1

            added_temporal = temporals_table.add(current_id, temporal_context, "VOID")
            added_temporal.three_way_print()
            
            self.lastTemp = added_temporal

          lastLoop = LoopObject(
            current_id,
            temporal_context,
            self.lastTemp._id
          )
          self.loops.append(lastLoop)
          self.loops[-1].start(is_if=child.getText() == "then")

        original_children.append(child.getText())
        child_types.append(self.visit(child))

      if child_count == 1: return child_types[0]
      if (node_type == YalpParser.ParentesisContext): return child_types[1]
      if (node_type == YalpParser.InstructionsContext): return child_types[-3]
      if (node_type == YalpParser.Var_declarationsContext): 
        try:
          # print("entra en Var_declarationsContext", self.lastTemp.originalRule, tree.getText().split("<-")[-1])
          pass
        except:
          pass
        
        # print(functions_table.table.keys())
        # print("AYUDA", self.fun_context)
        if (self.lastTemp != None and self.lastTemp.originalRule == tree.getText().split("<-")[-1]):
          print(f'	{tree.getChild(0)} = t{self.lastTemp._id}')
        else:
          print(f'	{tree.getChild(0)} = {tree.getChild(-1).getText()}')
          
        
        return self.getVarDeclarationType(tree)
      if (node_type == YalpParser.FormalContext): return child_types[2]
      if (node_type == YalpParser.LetParamContext): return child_types[2]
      if (node_type == YalpParser.LocalFunCallContext): return self.checkFunctionCall(tree.getChild(0).getText(), child_types[2:-1], children=original_children[2:-1])

      if (node_type == YalpParser.LoopTenseContext):
        if (child_types[1] != 'Bool' and child_types[1] != 'Int'):
          print('>>>>>>', child_types[1], 'is a non valid operation for while')
          return ERROR_STRING

        if (ERROR_STRING in child_types):
          return ERROR_STRING

        return 'Object'

      if (node_type == YalpParser.IfTenseContext):
        if (child_types[1] != 'Bool' and child_types[1] != 'Int'):
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

          if (classes_table.get(right_type) is None):
            right_type = None
          else:
            right_type = classes_table.get(right_type).getParent()

          if (right_type is None):
            right_type = child_types[5]
            left_type = classes_table.get(left_type).getParent()

          i += 1
        return left_type

      if (node_type == YalpParser.LetTenseContext):
        let_name = f'let-{self.let_id}'
        let_context = f'{self.class_context}-{self.fun_context}'
        if (self.inherited_context != None):
          functions_table.get(let_name, let_context).set_return_type(self.inherited_context)
        else:
          functions_table.get(let_name, let_context).set_return_type(child_types[-1])

        return child_types[-1]

      if (
        node_type == YalpParser.BinaryArithmeticalContext
        or node_type == YalpParser.BinaryLogicalContext
      ):
        _, rightOperand =  child_types
        operator = tree.getChild(0)
        operatorType = self.parser.symbolicNames[operator.symbol.type]
        key = operatorType + '-' + rightOperand

        if (key not in TYPES):
          print('>>>> Cannot operate', leftOperand, 'with', operator)
          return ERROR_STRING

        return TYPES[key]

      if (
        node_type == YalpParser.ArithmeticalContext
        or node_type == YalpParser.LogicalContext
      ):
        try:
          # print("entra en ArithmeticalContext", self.lastTemp.originalRule, tree.getText())
          pass
        except:
          pass

        leftOperand, _, rightOperand =  child_types
        if isinstance(rightOperand, list):
          rightOperand, temp = rightOperand

        operator = tree.getChild(1)
        operatorType = self.parser.symbolicNames[operator.symbol.type]

        key = leftOperand + '-' + operatorType + '-' + rightOperand
        
        if (key not in TYPES):
          if (node_type == YalpParser.ArithmeticalContext):
            print('>>>> Cannot operate', leftOperand, 'with', rightOperand, self.class_context, self.fun_context)
          else:
            print('>>>> Cannot compare', leftOperand, 'with', rightOperand)

          return ERROR_STRING


        # print("key", key)
        # print("tree", tree.getText())
        context = f'{self.class_context}-{self.fun_context}'


        # Saving temporary var
        if (self.lastTemp == None):
          current_id = 1
        else:
          current_id = self.lastTemp._id + 1

        added_temporal = temporals_table.add(current_id, context, tree.getText())

        if (self.lastTemp != None):
          added_temporal.setRule(
            rule=tree.getText(),
            content=self.lastTemp.originalRule,
            _id=self.lastTemp._id
          )
        added_temporal.three_way_print()
        
        self.lastTemp = added_temporal

        return TYPES[key]

      if (node_type == YalpParser.AssignmentContext):
        try:
          # print("entra en AssignmentContext", self.lastTemp.originalRule, tree.getText().split("<-")[-1])
          pass
        except:
          pass
        if (self.lastTemp != None and tree.getText().split("<-")[-1] == self.lastTemp.originalRule):
          print(f'	{tree.getChild(0)} = t{self.lastTemp._id}')
        else:
          print(f'	{tree.getChild(0)} = {tree.getChild(-1).getText()}')
        

        if (ERROR_STRING in child_types):
          variable = tree.getChild(0)
          print('Cannot assign to', variable.getText())
          return ERROR_STRING

        if (child_types[0] == child_types[2]):
          return child_types[0]
        
        if (
          (
            child_types[0] == 'Bool'
            or child_types[0] == 'Int'
          ) 
            and 
          (
            child_types[2] == 'Bool'
            or child_types[2] == 'Int'
          )
        ):
          return child_types[0]

        # Checks parents types
        i = 0
        left_type = child_types[0]
        right_type = classes_table.get(child_types[2]).getParent()
        while True:
          if (left_type == right_type): break
          if (i == LIMIT): 
            print('>>> Check super class of this assignment', tree.getText())
            return ERROR_STRING

          right_type = classes_table.get(right_type).getParent()
          if (right_type is None):
            get_tree_line(tree)
            print('Cannot assign', child_types[0], 'with', child_types[2], 'in', variable)
            return ERROR_STRING

          i += 1
        return left_type

      if node_type == YalpParser.ObjCreationContext:
        object_type = tree.getChild(1).getText()

        if (classes_table.contains(object_type)):
          return object_type

        print('Type', object_type, 'doesnt exists')
        return ERROR_STRING
        
      if (node_type == YalpParser.FunDeclarationContext):
        if (ERROR_STRING in child_types):
          return ERROR_STRING
        return self.getFunctionDeclarationType(child_types)

      if (node_type == YalpParser.FunctionCallContext):
        isParentMethod = tree.getChild(1).getText() == '@'
        if isParentMethod:
          return self.parentFunctionCall(tree, child_types, children=original_children)

        if (ERROR_STRING in child_types):
          return ERROR_STRING
        
        return self.varFunctionCall(tree, child_types, children=original_children)

      if (node_type == YalpParser.R_classContext):
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
visitor.compile(parse_tree)

visitor = PostOrderVisitor(visitor.types)
visitor.visit(parse_tree)
# print(classes_table)

# for x in functions_table.table:
#   print('>>>', functions_table.table[x])