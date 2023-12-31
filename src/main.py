import math
from antlr4 import *
from reader import resolveEntryPoint
from constants import *

from grammar.YalpParser import YalpParser
from grammar.YalpLexer import YalpLexer
from grammar.YalpVisitor import YalpVisitor
from file import CreateFile

from tables import ClassesTable, VariablesTable, LoopObject, FunctionsTable, TemporalsTable, BASE_SIZES
from utils import return_correct_mips

import os

entry_file = 'class.txt'
input_string = resolveEntryPoint(entry_file)

temporals_set = set()

classes_table = ClassesTable()
variables_table = VariablesTable()
functions_table = FunctionsTable()
temporals_table = TemporalsTable()
extracted_strings = {}

original_three_way_file = CreateFile("three_way.txt")
intermittent_address_three_way_file = CreateFile("intermittent_address.txt")
address_three_way_file = CreateFile("final.txt")

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
    if var_default == "true":
        var_default = 1

    return variables_table.add(
      var_name,
      var_type,
      var_context,
      var_default
    )

  # Visit a parse tree produced by YalpParser#string.
  def visitString(self, ctx:YalpParser.StringContext):
    extracted_strings[f'string{len(extracted_strings) + 1}'] = ctx.getText()
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

    # intermittent_address_three_way_file.add_line_to_txt("add let")
    return self.visitChildren(ctx)

  def visitLetParam(self, ctx:YalpParser.LetParamContext):
    fun_name = f'let-{self.let_id}'
    fun_context = f'{self.class_context}-{self.fun_context}'

    var_name = ctx.getChild(0).getText()

    if (ctx.getChildCount() == 5):
      var_type = ctx.getChild(-3).getText()
      default_value = ctx.getChild(-1).getText()
    
      if (var_type == "Int"):
        try:
          default_value = int(default_value)
        except:
          default_value = None

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
    self.freeTemps = []
    self.functionsTemp = []
    self.loops = []
    self.temporal_context = ''
    self.lastArg = -1
    self.freeArgs = []
  
  # This function will update the context of the current visited branch
  def updateContext(self, node):
    node_type = type(node)
    if (node_type == YalpParser.R_classContext):
      self.class_context = node.getChild(1).getText()

      # if (self.class_context not in unoverloading):
      #   intermittent_address_three_way_file.add_line_to_txt(f'{self.class_context}')
      #   original_three_way_file.add_line_to_txt(f'{self.class_context}')
      
    if (node_type == YalpParser.FunDeclarationContext):
      self.fun_context = node.getChild(0).getText()
      self.let_id = 0

      intermittent_address_three_way_file.add_line_to_txt(f'{self.class_context}-{self.fun_context}:')

      if (self.fun_context == "out_string"):
        intermittent_address_three_way_file.add_line_to_txt(f'      li $v0, 4')
        intermittent_address_three_way_file.add_line_to_txt(f'      la $t0, 0($a0)')
        intermittent_address_three_way_file.add_line_to_txt(f'      syscall')
      elif (self.fun_context == "out_int"):
        intermittent_address_three_way_file.add_line_to_txt(f'      li $v0, 1')
        intermittent_address_three_way_file.add_line_to_txt(f'      move $a0, $t0')
        intermittent_address_three_way_file.add_line_to_txt(f'      syscall')
      elif (self.fun_context == "substr"):
        intermittent_address_three_way_file.add_line_to_txt(f'      bge $a1, $a0, swap_values')
        intermittent_address_three_way_file.add_line_to_txt(f'      j continue')
        intermittent_address_three_way_file.add_line_to_txt(f'      swap_values:')
        intermittent_address_three_way_file.add_line_to_txt(f'             move $a2, $a0')
        intermittent_address_three_way_file.add_line_to_txt(f'             move $a0, $a1')
        intermittent_address_three_way_file.add_line_to_txt(f'             move $a1, $a2')

        intermittent_address_three_way_file.add_line_to_txt(f'      continue:')
        intermittent_address_three_way_file.add_line_to_txt(f'      move $s0, $t7')
        intermittent_address_three_way_file.add_line_to_txt(f'      la $s1, destination_string')
        intermittent_address_three_way_file.add_line_to_txt(f'      copy_loop:')
        intermittent_address_three_way_file.add_line_to_txt(f'            lb $t2, 0($s0)')
        intermittent_address_three_way_file.add_line_to_txt(f'            sb $t2, 0($s1)')
        intermittent_address_three_way_file.add_line_to_txt(f'            addi $s0, $s0, 1')
        intermittent_address_three_way_file.add_line_to_txt(f'            addi $s1, $s1, 1')
        intermittent_address_three_way_file.add_line_to_txt(f'            addi $a1, $a1, 1')
        intermittent_address_three_way_file.add_line_to_txt(f'            bne $a0, $a1, copy_loop ')
        intermittent_address_three_way_file.add_line_to_txt(f'      li $t2, 0')
        intermittent_address_three_way_file.add_line_to_txt(f'      sb $t2, 0($s1)')
        intermittent_address_three_way_file.add_line_to_txt(f'      la $a0, destination_string')
      elif (self.fun_context == "type_name"):
        intermittent_address_three_way_file.add_line_to_txt(f'      lw $v0, 0($t7)')

      original_three_way_file.add_line_to_txt(f'{self.fun_context}:')
        

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
    if (self.class_context != 'Main' and self.fun_context != 'main'):
      intermittent_address_three_way_file.add_line_to_txt(f'      jr $ra')

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

  def checkFunctionCall(self, fun_name, full_params, class_name = None, children = [], called_by=None, child_types = []):
    inner_params = []
    class_context = self.class_context if class_name is None else class_name

    # intermittent_address_three_way_file.add_line_to_txt(f'\n')
    original_three_way_file.add_line_to_txt(f'      {self.fun_context}-{fun_name}')
  
    def get_correct_context(var_name):
        is_not = False
        if (var_name[0] == "~"):
          var_name = var_name[1:]
          is_not = True

        let_context = None
        for possible_let in reversed(range(self.let_id + 1)) : 
          key = f'{self.class_context}-{self.fun_context}-let-{possible_let + 1}-{var_name}'
          try:
            variables_table.table[key]
            let_context = key
            break
          except:
            pass

        function_context = variables_table.get(var_name, self.class_context+"-"+self.fun_context)
        class_context = variables_table.get(var_name, self.class_context)

        if (let_context != None):
          var_name = let_context
        elif (function_context != None):
          var_name = f'{self.class_context}-{self.fun_context}-{var_name}'
        elif (class_context != None):
          var_name = f'{self.class_context}-{var_name}'
        elif (self.lastTemp != None and self.lastTemp.unlabeledRule == var_name):
          var_name = f'{self.temporal_context}-t{self.lastTemp._id}'

        if (is_not):
          # var_name = f'~{var_name}'
          var_name = f'{var_name}'
        
        return var_name

    used_args = []
    i = 0
    for param in children:
      if (not param == ","):
        inner_params.append(param)

        if (self.lastTemp != None and param == self.lastTemp.intermediaryRule):
          # Es funcion, igual ocupa un id del lastArg
          original_three_way_file.add_line_to_txt(f'            PARAM t{self.lastTemp._id}')
          if ("." in param):
            if ("new" in param or "self" in param):
              intermittent_address_three_way_file.add_line_to_txt(f'      la $a1, Object_instance')
            else:
              if len(self.freeArgs) > 0:
                self.lastArg = self.freeArgs[0]
                del self.freeArgs[0]
              else:
                self.lastArg += 1
              intermittent_address_three_way_file.add_line_to_txt(f'      lw $a{self.lastArg}, {get_correct_context(param.split(".")[0])}($gp)')
          
          # intermittent_address_three_way_file.add_line_to_txt(f'      jal {self.class_context}_{param.split(".")[-1].replace("(", "").replace(")", "")}')
          # Guardamos el resultado por si lo necesitamos
          # intermittent_address_three_way_file.add_line_to_txt(f'      move ${self.temporal_context}-t{self.lastTemp._id}, $v0')
        else:
          if len(self.freeArgs) > 0:
            self.lastArg = self.freeArgs[0]
            del self.freeArgs[0]
          else:
            self.lastArg += 1
          original_three_way_file.add_line_to_txt(f'            PARAM {get_correct_context(param)}')
          param = get_correct_context(param)
          try:
            param = int(param)
            intermittent_address_three_way_file.add_line_to_txt(f'      li $a{self.lastArg}, {param}')
          except:
            if not ("." in param and full_params[i] != "String"):
              intermittent_address_three_way_file.add_line_to_txt(f'      la $a{self.lastArg}, {param}')
        
        i += 1
        used_args.append(self.lastArg)
    
    self.freeArgs = list(set(self.freeArgs + used_args))
    
    self.temporal_context = f'{self.class_context}-{self.fun_context}'
    if (called_by != None):
      function_call = f'{called_by}.{fun_name}({",".join(inner_params)})'
    else:
      function_call = f'{fun_name}({",".join(inner_params)})'

    # Saving temporary var
    if (self.lastTemp == None):
      current_id = 1
      temporals_set.add(f't{current_id}')
    elif len(self.freeTemps) > 0:
      current_id = self.freeTemps[0]
      del self.freeTemps[-1]
      temporals_set.add(f't{current_id}')
    else:
      current_id = self.lastTemp._id + 1
      temporals_set.add(f't{current_id}')


    added_temporal = temporals_table.add(current_id, self.temporal_context, function_call)
    # Saving temporary var
    if (len(self.functionsTemp) > 0):
      for _function_call_id in self.functionsTemp:
        last_function_call_id = _function_call_id
        inner_value = temporals_table.get(temporal_context=self.temporal_context, _id=last_function_call_id)

        for inner_param in inner_params:
          if (inner_value == inner_param):
              added_temporal.setRule(
                rule=added_temporal.intermediaryRule,
                content=inner_value,
                _id=last_function_call_id
              )
    # print("added_temporal ", added_temporal)
    # added_temporal.three_way_print(tab="            ")
    self.lastTemp = added_temporal
    self.functionsTemp.append(current_id)
    original_three_way_file.add_line_to_txt(f'            t{current_id} = CALL {fun_name}')
    
    # intermittent_address_three_way_file.add_line_to_txt(f'            t{current_id} = CALL {fun_name}')
    if functions_table.get(fun_name, self.class_context) == None:
      if (self.new_context != None and self.new_context not in unoverloading):
        while True:
          if (functions_table.get(fun_name, self.new_context) == None):
            self.new_context = classes_table.get(self.new_context).parent
          else:
            break

        if (functions_table.get(fun_name, self.new_context).context != self.new_context):
          intermittent_address_three_way_file.add_line_to_txt(f'      jal {functions_table.get(fun_name, self.new_context).context}-{fun_name}\n')
        else:
          intermittent_address_three_way_file.add_line_to_txt(f'      jal {self.new_context}-{fun_name}\n')
      else:
        intermittent_address_three_way_file.add_line_to_txt(f'      jal String-{fun_name}\n')
    elif (functions_table.get(fun_name, self.class_context).is_inherited):
      if (fun_name == 'type_name'):
        intermittent_address_three_way_file.add_line_to_txt(f'      la $t7 class_{child_types[0]}\n')
      else:
        intermittent_address_three_way_file.add_line_to_txt(f'      jal {functions_table.get(fun_name, self.class_context).getContext()}-{fun_name}\n')
    else:
      intermittent_address_three_way_file.add_line_to_txt(f'      jal {self.class_context}-{fun_name}\n')

    self.freeArgs = []
    self.lastArg = -1
    # Guardamos el resultado por si lo necesitamos
    intermittent_address_three_way_file.add_line_to_txt(f'      move $t0, $v0')
    # intermittent_address_three_way_file.add_line_to_txt(f'      la $a0, {self.temporal_context}-t{current_id}')
    # intermittent_address_three_way_file.add_line_to_txt(f'      sw $v0, {self.temporal_context}-t{current_id}($a0)')

    param_types = []
    for i in range(0, len(full_params), 2):
      param_types.append(full_params[i])

  
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
    return self.checkFunctionCall(fun_name, child_types[4:-1], var_type, children[4:-1], children[0], child_types=child_types)

  def parentFunctionCall(self, node, child_types, children):
    var_type = node.getChild(2).getText()
    fun_name = node.getChild(4).getText()
    return self.checkFunctionCall(fun_name, child_types[6:-1], var_type, children[6:-1], children[2], child_types=child_types)

  def visit(self, tree):
    self.temporal_context = f'{self.class_context}-{self.fun_context}'
    if (self.lastTemp != None and self.lastTemp._id > 8):
      self.freeTemps = [0, 1, 2, 3, 4, 5, 6, 7, 8]

    if (self.lastTemp != None and self.lastTemp.context != self.temporal_context):
      self.lastTemp = None
      self.freeTemps = []
      self.loops = []
      self.functionsTemp = []
      self.lastArg = -1
      self.freeArgs = []

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
      return_value_temporary = []
      child_types = []
      original_children = []
      node_type = type(tree)
      child_count = tree.getChildCount()
      self.updateContext(tree)

      # Visit the children first
      for i in range(child_count):
        child = tree.getChild(i)

        child_text = child.getText()

        if (
          (child_text == 'fi' or child_text == 'pool' or child_text == 'else')
          and (len(return_value_temporary) > 0)
        ):
          new_return_temporary = return_value_temporary.pop()
          new_return_temporary.setReturnValue(child_types[-1])
          
          intermittent_address_three_way_file.add_line_to_txt(new_return_temporary.three_way_print())
          intermittent_address_three_way_file.add_line_to_txt(f'        return {self.temporal_context}-t{new_return_temporary._id}')

          original_three_way_file.add_line_to_txt(new_return_temporary.three_way_print())
          original_three_way_file.add_line_to_txt(f'        return t{new_return_temporary._id}')

        if (child.getText() == "fi" or child.getText() == "pool"): 
          res = self.loops.pop().end()
          original_three_way_file.add_line_to_txt(res)
          intermittent_address_three_way_file.add_line_to_txt(res)

          
        if (child.getText() == "pool"): 
          res = self.loops.pop().end(is_while=True)
          original_three_way_file.add_line_to_txt(res)
          intermittent_address_three_way_file.add_line_to_txt(res)
          

        if (child.getText() == "then" or child.getText() == "while"):
          next_condition = tree.getChild(i + 1).getText()
          if (next_condition == "true" or next_condition == "false"):
            # Saving temporary var
            if (self.lastTemp == None):
              current_id = 1
              temporals_set.add(f't{current_id}')
            else:
              if (len(self.freeTemps) > 0):
                reusable_id = self.freeTemps[0]
                del self.freeTemps[-1]
                current_id = reusable_id
              else:
                current_id = self.lastTemp._id + 1
              temporals_set.add(f't{current_id}')

            added_temporal = temporals_table.add(current_id, self.temporal_context, next_condition)
            original_three_way_file.add_line_to_txt(added_temporal.three_way_print())
            
            self.lastTemp = added_temporal

        if (
          child.getText() == "while" 
          or child.getText() == "else" 
          or child.getText() == "then"
          or child.getText() == "loop"
        ):
          if (len(self.loops) == 0):
            current_id = 1
          else:
            current_id = self.loops[-1]._id + 1

          if (child.getText() == "else"): self.loops.pop().end()

          # TODO: Se tiene que obtener el return de la funcion
          # y guardarlo como un temporal
          if (self.lastTemp == None and child.getText() != "while" ):
            # Saving temporary var
            current_id = 1
            temporals_set.add(f't{current_id}')

            added_temporal = temporals_table.add(current_id, self.temporal_context, "VOID")
            original_three_way_file.add_line_to_txt(added_temporal.three_way_print())
            
            return_value_temporary.append(added_temporal)
            self.lastTemp = added_temporal

          if (child.getText() == "while"):
            if (len(self.freeTemps) > 0):
              reusable_id = self.freeTemps[0]
              next_id = reusable_id
            else:
              next_id = self.lastTemp._id + 1 if (self.lastTemp != None) else 1

            temporals_set.add(f't{current_id}')
            lastLoop = LoopObject(
              current_id,
              self.temporal_context,
              next_id
            )
          else:
            if (len(self.freeTemps) > 0):
              reusable_id = self.freeTemps[0]
              if_condition = reusable_id
            else:
              if_condition = self.lastTemp._id

            lastLoop = LoopObject(
              current_id,
              self.temporal_context,
              if_condition
            )
          self.loops.append(lastLoop)
          original_three_way_file.add_line_to_txt(self.loops[-1].start(
            is_if=child.getText() == "then", is_while=child.getText() == "loop"))
          intermittent_address_three_way_file.add_line_to_txt(self.loops[-1].start(is_if=child.getText() == "then", is_while=child.getText() == "loop"))

        original_children.append(child.getText())
        child_types.append(self.visit(child))

      if child_count == 1: return child_types[0]
      if (node_type == YalpParser.ParentesisContext): return child_types[1]
      if (node_type == YalpParser.InstructionsContext): return child_types[-3]
      if (node_type == YalpParser.Var_declarationsContext):
        return self.getVarDeclarationType(tree)
      if (node_type == YalpParser.FormalContext): return child_types[2]
      if (node_type == YalpParser.LetParamContext): return child_types[2]
      if (node_type == YalpParser.LocalFunCallContext): 
        return self.checkFunctionCall(tree.getChild(0).getText(), child_types[2:-1], children=original_children[2:-1], child_types=child_types)

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
        def get_correct_context(var_name):
            let_context = None
            for possible_let in reversed(range(self.let_id + 1)) : 
              key = f'{self.class_context}-{self.fun_context}-let-{possible_let + 1}-{var_name}'
              try:
                variables_table.table[key]
                let_context = key
                break
              except:
                pass

            function_context = variables_table.get(var_name, self.class_context+"-"+self.fun_context)
            class_context = variables_table.get(var_name, self.class_context)

            if (let_context != None):
              var_name = let_context
            elif (function_context != None):
              var_name = f'{self.class_context}-{self.fun_context}-{var_name}'
            elif (class_context != None):
              var_name = f'{self.class_context}-{var_name}'
            
            # TODO: get correct param name
            if (var_name == "Factorial-factorial-n" or var_name == "Fibonacci-fibonacci-n"):
              var_name = "Main-n"
            return var_name
    
        leftOperand, _, rightOperand =  child_types
        leftOperandText, _Text, rightOperandText = original_children
        labeledLeftOperandText = get_correct_context(leftOperandText)
        labeledRightOperandText = get_correct_context(rightOperandText)

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


        # Saving temporary var
        def get_correct_temp():
          if (self.lastTemp == None):
            current_id = 1
            temporals_set.add(f't{current_id}')
          elif len(self.freeTemps) > 0:
            current_id = self.freeTemps[0]
            del self.freeTemps[-1]
            temporals_set.add(f't{current_id}')
          else:
            current_id = self.lastTemp._id + 1
            temporals_set.add(f't{current_id}')
          return current_id

        labeled_tree = [labeledLeftOperandText, _Text, labeledRightOperandText]
        current_id = get_correct_temp() - 1
        
        if (leftOperandText != labeledLeftOperandText):
            current_id += 1
            left_id = current_id
            added_temporal = temporals_table.add(left_id, self.temporal_context, labeledLeftOperandText,
                                                unlabeledRule="".join(labeled_tree))
            temporals_set.add(f't{left_id}')
            intermittent_address_three_way_file.add_line_to_txt(added_temporal.move_address(
              labeledOperandText=labeledLeftOperandText,
              current_id=left_id
            ))
            if (self.lastTemp != None):
              added_temporal.setRule(
                rule="".join(labeled_tree),
                content=self.lastTemp.unlabeledRule,
                _id=self.lastTemp._id
              )
            # self.lastTemp = added_temporal
            labeled_tree = [f't{left_id}', _Text, labeledRightOperandText]
            
        if (rightOperandText != labeledRightOperandText):
            current_id += 1
            right_id = current_id
            temporals_set.add(f't{right_id}')
            added_temporal = temporals_table.add(right_id, self.temporal_context, labeledRightOperandText,
                                                unlabeledRule="".join(labeled_tree))
            intermittent_address_three_way_file.add_line_to_txt(added_temporal.move_address(
              labeledOperandText=labeledRightOperandText,
              current_id=right_id
            ))
            if (self.lastTemp != None):
              added_temporal.setRule(
                rule="".join(labeled_tree),
                content=self.lastTemp.unlabeledRule,
                _id=self.lastTemp._id
              )
            # self.lastTemp = added_temporal
            try:
              labeled_tree = [f't{left_id}', _Text, f't{right_id}']
            except:
              if (self.lastTemp.unlabeledRule == labeledLeftOperandText):
                labeled_tree = [f'{self.lastTemp._id}', _Text, f't{right_id}']
              else:
                labeled_tree = [labeledLeftOperandText, _Text, f't{right_id}']
        
        temporals_set.add(f't{current_id + 1}')
        added_temporal = temporals_table.add(current_id + 1, self.temporal_context, "".join(labeled_tree),
                                             unlabeledRule=f'{"".join(original_children)}')


        if (self.lastTemp != None):
          added_temporal.setRule(
            rule="".join(labeled_tree),
            content=self.lastTemp.unlabeledRule,
            _id=self.lastTemp._id
          )
        # Checking if is function call
        for tempId in self.functionsTemp:
          inner_value = temporals_table.get(temporal_context=self.temporal_context, _id=tempId)
          if (inner_value == labeledLeftOperandText):
                added_temporal.setRule(
                  rule=added_temporal.intermediaryRule,
                  content=inner_value,
                  _id=tempId
                )
          elif (inner_value == labeledRightOperandText):
                added_temporal.setRule(
                  rule=added_temporal.intermediaryRule,
                  content=inner_value,
                  _id=tempId
                )

        if (len(self.loops) == 0):
          current_id = 1
        else:
          current_id = self.loops[-1]._id + 1
        
        intermittent_address_three_way_file.add_line_to_txt(added_temporal.three_way_print_context(
          context=self.temporal_context,
          labeled_tree=labeled_tree,
          current_id=current_id
        ))
        original_three_way_file.add_line_to_txt(added_temporal.three_way_print())
        
        self.lastTemp = added_temporal

        return TYPES[key]

      if (node_type == YalpParser.AssignmentContext):
        let_context = None
        for possible_let in reversed(range(self.let_id + 1)) : 
          key = f'{self.class_context}-{self.fun_context}-let-{possible_let + 1}-{tree.getChild(0).getText()}'
          try:
            variables_table.table[key]
            let_context = key
            break
          except:
            pass

        function_context = variables_table.get(tree.getChild(0).getText(), self.class_context+"-"+self.fun_context)
        class_context = variables_table.get(tree.getChild(0).getText(), self.class_context)

        var_name = ''
        if (let_context != None):
          var_name = let_context
        elif (function_context != None):
          var_name = f'{self.class_context}-{self.fun_context}-{tree.getChild(0)}'
        elif (class_context != None):
          var_name = f'{self.class_context}-{tree.getChild(0)}'

        if (self.lastTemp != None and tree.getText().split("<-")[-1] == self.lastTemp.unlabeledRule):
          self.freeTemps.append(self.lastTemp._id)
          
          intermittent_address_three_way_file.add_line_to_txt(f'      {var_name} = {self.temporal_context}-t{self.lastTemp._id}')
          original_three_way_file.add_line_to_txt(f'	{tree.getChild(0)} = t{self.lastTemp._id}')
        elif (len(self.functionsTemp) > 0):
          last_function_call_id = self.functionsTemp[-1]
          inner_value = temporals_table.get(temporal_context=self.temporal_context, _id=last_function_call_id)
          temporal_assignment = tree.getText().split("<-")[-1].replace(inner_value, f't{last_function_call_id}')
          self.freeTemps.append(last_function_call_id)

          if ("new" in temporal_assignment):
            temporal_assignment = temporal_assignment.replace("new", "")
            temporal_assignment = temporal_assignment.replace('(', '').replace(')', '')
            
          intermittent_address_three_way_file.add_line_to_txt(f'      {var_name} = {self.temporal_context}-{temporal_assignment}')
          original_three_way_file.add_line_to_txt(f'	{tree.getChild(0)} = {temporal_assignment}')
        else:
          let_context = None
          inner_param = tree.getChild(-1).getText()
          
          is_not = False
          if (inner_param[0] == "~"):
            inner_param = inner_param[1:]
            is_not = True

          for possible_let in reversed(range(self.let_id + 1)) : 
            key = f'{self.class_context}-{self.fun_context}-let-{possible_let + 1}-{inner_param}'
            try:
              variables_table.table[key]
              let_context = key
              break
            except:
              pass

          function_context = variables_table.get(inner_param, self.class_context+"-"+self.fun_context)
          class_context = variables_table.get(inner_param, self.class_context)

          if (let_context != None):
            inner_param = let_context
          elif (function_context != None):
            inner_param = f'{self.class_context}-{self.fun_context}-{inner_param}'
          elif (class_context != None):
            inner_param = f'{self.class_context}-{inner_param}'

          if (is_not):
            inner_param = f'{inner_param}'
            # inner_param = f'~{inner_param}'

          if ("new" in inner_param):
            inner_param = inner_param.replace("new", "")
            inner_param = inner_param.replace('(', '').replace(')', '')

          param_lower = inner_param.replace('-', '_')
          if (child_types[0] in uninherable):          
            print('ENTRA', var_name)
            intermittent_address_three_way_file.add_line_to_txt(f'      la $t1, {param_lower}')
            intermittent_address_three_way_file.add_line_to_txt(f'      sw $t0, 0($t1)')

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
        self.new_context = object_type

        if (classes_table.contains(object_type)):
          if len(self.freeArgs) > 0:
            self.lastArg = self.freeArgs[0]
            del self.freeArgs[-1]
          else:
            self.lastArg += 1

          intermittent_address_three_way_file.add_line_to_txt(f'      la $a{self.lastArg}, {tree.getChild(1).getText()}_instance')
            
          return object_type

        print('Type', object_type, 'doesnt exists')
        return ERROR_STRING

      if (node_type == YalpParser.IsVoidExprContext):
        return 'Bool'

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

class_table_size = classes_table.getSize(variables_table, functions_table)

temporal_dic = {}
current_offset = class_table_size
temp_size = BASE_SIZES['Int']

for temporal in temporals_set:
  temporal_dic[temporal] = current_offset
  current_offset += temp_size

for temp_key in temporals_table.table:
  temporal = temporals_table.table.get(temp_key)
  temp_name = f't{temporal._id}'
  temporal.setOffset(temporal_dic[temp_name])

# Gets the absolute offsets
absolute_offset = 0
for item in classes_table.table:
  class_item = classes_table.table.get(item)

  # We check the absolute offset of the variables
  for var_name in class_item.variables:
    var_item = variables_table.table.get(f'{class_item.name}-{var_name}')
    var_item.setAbsoluteOffset(absolute_offset)
    absolute_offset += var_item.size

  for fun_name in class_item.functions:
    fun_item = functions_table.table.get(f'{class_item.name}-{fun_name}')

    fun_item.set_absolute_return_offset(absolute_offset)
    absolute_offset += fun_item.return_size

    if (fun_item.let_num == 0 and fun_item.num_params == 0):
      continue

    # We check the absolute offset of the functions params
    for fun_var_name in fun_item.param_names:
      key = f'{class_item.name}-{fun_name}-{fun_var_name}'
      var_fun_item = variables_table.table.get(key)
      
      var_fun_item.setAbsoluteOffset(absolute_offset)
      absolute_offset += var_fun_item.size

    if (fun_item.let_num == 0):
      continue

    # We check the absolute offset of the lets params
    for let_id in range(fun_item.let_num):
      let_id += 1
      key1 = f'{class_item.name}-{fun_name}-let-{let_id}'
      key2 = f'{class_item.name}-{fun_name}-let,{let_id}'

      # Because some lets for some reason have , instead of -
      final_key = ''
      let_fun = None

      if (key1 in functions_table.table):
        let_fun = functions_table.table.get(key1)

      if (key2 in functions_table.table):
        let_fun = functions_table.table.get(key2)

        functions_table.table[key1] = let_fun # We correct the key
      
      let_fun.set_absolute_return_offset(absolute_offset)
      absolute_offset += let_fun.return_size

      # Now we check for every let param
      for let_param in let_fun.param_names:
        let_param_item = variables_table.table.get(f'{key1}-{let_param}')

        let_param_item.setAbsoluteOffset(absolute_offset)
        absolute_offset += let_param_item.size

# Using readlines()
intermittent_address_three_way_file.close_txt_file()
file1 = open('intermittent_address.txt', 'r')
Lines = file1.readlines()

address_three_way_file.add_line_to_txt(".data")

for classes in classes_table.table:
  address_three_way_file.add_line_to_txt(f'   class_{classes}: .asciiz "{classes}"')

address_three_way_file.add_line_to_txt(f'   destination_string: .space 20 ')

for extracted_string in extracted_strings:
  address_three_way_file.add_line_to_txt(f'   {extracted_string}: .asciiz {extracted_strings[extracted_string]}')

for var in variables_table.table:
  value = variables_table.table[var].init_value

  if (value != None):
    address_three_way_file.add_line_to_txt(f'   {var.replace("-", "_")}: .word  {value}')
  else:
    address_three_way_file.add_line_to_txt(f'   {var.replace("-", "_")}: .word  {variables_table.table[var].offset}')

for temp in sorted(temporals_table.table, reverse=True):
  address_three_way_file.add_line_to_txt(f'   {temp.replace("-", "_")}: .word  {temporals_table.table[temp].offset}')

for instance_class in classes_table.table:
  address_three_way_file.add_line_to_txt(f'   {instance_class.replace("-", "_")}_instance: .word  {classes_table.get(instance_class).getOffset()}')

address_three_way_file.add_line_to_txt(".text")
address_three_way_file.add_line_to_txt(f'   .globl Main_main')

main_content_lines = []
found_main = False
# Strips the newline character
for line in Lines:
  if found_main and ':' not in line:
      main_content_lines.append(line)
  elif "Main-main:" in line:
      main_content_lines.append(line)
      found_main = True


for line in main_content_lines:
    new_line = return_correct_mips(variables_table, temporals_table, extracted_strings, line)
    address_three_way_file.add_line_to_txt(new_line)
# Exit program
address_three_way_file.add_line_to_txt("      li $v0, 10")
address_three_way_file.add_line_to_txt("      syscall")

found_main = 0
for line in Lines:
  new_line = return_correct_mips(variables_table, temporals_table, extracted_strings, line)

  if "Main-main:" in line:
    break

  address_three_way_file.add_line_to_txt(new_line)

file1.close()
original_three_way_file.close_txt_file()
address_three_way_file.close_txt_file()

os.remove("three_way.txt")
os.remove("intermittent_address.txt")
# print(functions_table)
# print(absolute_offset, class_table_size)
# print(variables_table)