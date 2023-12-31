from utils import compare_dicts_ignore_attribute

BASE_SIZES = {
  'Int': 4,
  'Bool': 1,
  'String': 16,
}

class LoopObject(object):
	def __init__(self, _id, context, if_condition):
		self._id = _id
		self.context = context
		self.if_condition = if_condition
		self.goto = None

	def start(self, is_if=False, is_while=False):
		content = ""
		# if (is_if):
		# 	content += (f'	if {self.context}-t{self.if_condition} goto L{self._id}\n')
		# 	content += (f'	goto L{self._id + 1}\n')
		# elif (is_while): # while
		# 	content += (f'	if {self.context}-t{self.if_condition} goto L{self._id}\n')
		# 	content += (f'	goto END_L{self._id - 1}\n')
		if (self._id != 1):
			content += (f'	jr $ra\n\n')
		content += (f'	{self.context}-L{self._id}: ')

		return content

	def end(self, is_while=False):
		content = ""
		if (is_while):
			content += (f'	j {self.context}-L{self._id}\n')
		# content += (f'	END_L{self._id}')
		content += (f'	jr $ra')
		return content

	def setGoto(self, goto):
		self.goto = goto

	def __str__(self):
		if (self.goto != None):
			details += f'	if {self.context}-t{self.if_condition} goto L{self.goto}\n'
		else: # while
			details = f'	END_L{self._id}\n'
			details += f'	if {self.context}-t{self.if_condition} goto L{self._id}\n'
		return details
	
class TemporalObject(object):
	def __init__(self, _id, context, originalRule, unlabeledRule):
		self._id = _id
		self.context = context
		self.size = 0
		self.offset = 0
		self.originalRule = originalRule
		self.intermediaryRule = originalRule
		self.unlabeledRule = unlabeledRule

	def setError(self):
		self.type = 'ERROR'

	def setOffset(self, offset = 0):
		self.offset = offset

	def setReturnValue(self, newValue):
		self.intermediaryRule = newValue

	def setSize(self, size = 0):
		try:
			self.size = BASE_SIZES[self.type]
		except:
			self.size = size

	def setRule(self, rule, content, _id):
		name = f'{self.context}-t{_id}'
		if (content != None):
			intermediaryRule = rule.replace(content, name)
			# print("			rule", rule)
			# print("			originalRule", self.originalRule)
			# print("			intermediaryRule", intermediaryRule)
			self.intermediaryRule = intermediaryRule

		return self.intermediaryRule
	
	def getSize(self):
		return self.size
	
	def three_way_print(self, tab="     	"):
		return (f'{tab}t{self._id} = {self.intermediaryRule}')
	
	def move_address(self, 
					current_id, 
					labeledOperandText,
					tab="     	"):
		
		return f'{tab}la $a0, {labeledOperandText}\n{tab}lw $t{current_id}, {labeledOperandText}($a0)'

	def three_way_print_context(self, 
							 context, 
							 labeled_tree,
							 current_id=-1,
							 tab="     	"):
		
		text = ""
		has_integer = False
		next_label = 0
		operator = labeled_tree.pop(1)
		for i in range(len(labeled_tree)):
			if not labeled_tree[i].isdigit():
				labeled_tree[i] = f'${labeled_tree[i]}'
			else:
				has_integer = True
		
		if (operator == "+"):
			if (has_integer):
				text += f'{tab}addi $t{self._id}, {labeled_tree[0]}, {labeled_tree[1]}\n'
				text += f'{tab}sw $t{self._id}, {context}-t{self._id}($gp)'
			
			else:
				text += f'{tab}add $t1, $t1, $t0\n'

		elif (operator == "/"):
			try:
				labeled_tree[1] = int(labeled_tree[1])
				text += f'{tab}li $t0, {labeled_tree[1]}\n'
				labeled_tree[1] = "$t0"
			except:
				pass
			text += f'{tab}div {labeled_tree[0]}, {labeled_tree[1]}\n'
			text += f'{tab}mflo $t{self._id}\n'
		
			text += f'{tab}sw $t{self._id}, {context}-t{self._id}($gp)'
		elif (operator == "*"):
			try:
				labeled_tree[0] = int(labeled_tree[0])
				text += f'{tab}li $t0, {labeled_tree[0]}\n'
				text += f'{tab}mult $t0, {labeled_tree[1]}\n'
			except:
				text += f'{tab}mult {labeled_tree[0]}, {labeled_tree[1]}\n'
			text += f'{tab}mfhi $t{self._id}\n' # 32 most significant bits
		
			text += f'{tab}sw $t{self._id}, {context}-t{self._id}($gp)'
		elif (operator == "-"):
			text += f'{tab}sub $t{self._id}, {labeled_tree[0]}, {labeled_tree[1]}\n'
			text += f'{tab}sw $t{self._id}, {context}-t{self._id}($gp)'
		elif (operator == "="):
			try:
				labeled_tree[1] = int(labeled_tree[1])
				text += f'{tab}li $t0, {labeled_tree[1]}\n'
			except:
				pass
			try:
				labeled_tree[0] = int(labeled_tree[0])
				text += f'{tab}li $t0, {labeled_tree[0]}\n'
				labeled_tree[0] = "$t0"
			except:
				pass

			text += f'{tab}beq {labeled_tree[0]}, $t0, {context}-L{current_id}\n'
			text += f'{tab}j {context}-L{current_id+1}\n'
		else:
			text += f'{tab}{context}-t{self._id} = {self.intermediaryRule}'


		return text

	def __str__(self):
		details = '{\n'
		details += f'  id: {self._id}\n'
		details += f'  context: {self.context}\n'
		details += f'  size: {self.size}\n'
		details += f'  offset: {self.offset}\n'
		details += f'  intermediaryRule: {self.intermediaryRule}\n'
		details += f'  originalRule: {self.originalRule}\n'
		details += f'  unlabeledRule: {self.unlabeledRule}\n'
		details += '}'
		return details

class TemporalsTable(object):
	def __init__(self) -> None:
		self.table = {}
	
	def add(
		self,
		_id,
		context,
		originalRule,
		unlabeledRule=None
	):
		key = f'{context}-t{_id}'
		if key in self.table.keys():
			self.table.pop(key)

		temporal = TemporalObject(
			_id,
			context,
			originalRule,
			unlabeledRule
		)

		self.table[key] = temporal
		return temporal

	def contains(self, temporal_context, _id):
		key = f'{temporal_context}-t{_id}'
		if key in self.table.keys():
			return True
		return False
	
	def get(
		self,
		temporal_context,
		_id
	):
		key = f'{temporal_context}-t{_id}'
		if not self.contains(temporal_context, _id):
			return None
		return self.table.get(key).originalRule
	
	def getByKey(
		self,
		key,
	):
		return self.table.get(key)

	def __str__(self):
		details = '{\n'
		for key in self.table:
			variable = self.table[key]
			details += f'  {key} : ' + '{\n'
			details += f'    name: t-{variable._id}\n'
			details += f'    context: {variable.context}\n'
			details += f'    size: {variable.size}\n'
			details += f'    offset: {variable.offset}\n'
		details += '}'
		return details

class VariableObject(object):
	def __init__(self, name, type, context, init_value=None):
		self.name = name
		self.type = type + ''
		self.context = context
		self.init_value = init_value
		self.size = 0
		self.offset = 0
		self.absoluteOffset = -1

	def setError(self):
		self.type = 'ERROR'

	def setOffset(self, offset = 0):
		self.offset = offset

	def setAbsoluteOffset(self, absoluteOffset = 0):
		self.absoluteOffset = absoluteOffset

	def setSize(self, size = 0):
		try:
			self.size = BASE_SIZES[self.type]
		except:
			self.size = size

	def getSize(self):
		return self.size

	def __str__(self):
		details = '{\n'
		details += f'  name: {self.name}\n'
		details += f'  type: {self.type}\n'
		details += f'  context: {self.context}\n'
		details += f'  value: {self.init_value}\n'
		details += f'  size: {self.size}\n'
		details += f'  offset: {self.offset}\n'
		details += '}'
		return details

class VariablesTable(object):
	def __init__(self) -> None:
		self.table = {}
	
	def add(
		self,
		name,
		type,
		context,
		init_value = None
	):
		key = context + '-' + name
		if key in self.table.keys():
			return False
		
		if init_value is None:
			if type == 'Int':
				init_value = 0
			elif type == 'Bool':
				init_value = 'false'
			elif type == 'String':
				init_value = ''

		variable = VariableObject(
			name,
			type,
			context,
			init_value
		)

		self.table[key] = variable
		return True

	def contains(self, var_name, var_context):
		key = var_context + '-' + var_name
		if key in self.table.keys():
			return True
		return False
	
	def get(
		self,
		var_name,
		var_context
	):
		key = var_context + '-' + var_name
		if not self.contains(var_name, var_context):
			return None
		return self.table.get(key)

	def __str__(self):
		details = '{\n'
		for key in self.table:
			variable = self.table[key]
			details += f'  {key} : ' + '{\n'
			details += f'    name: {variable.name}\n'
			details += f'    type: {variable.type}\n'
			details += f'    context: {variable.context}\n'
			details += f'    value: {variable.init_value}\n'
			details += f'    size: {variable.size}\n'
			details += f'    offset: {variable.offset}\n'
			details += f'    absoluteOffset: {variable.absoluteOffset}\n'
		details += '}'
		return details

class FunctionObject(object):

	def getReturnSize(self, return_type):
		if (return_type == 'String'):
			return BASE_SIZES['String']
		elif (return_type == 'Bool'):
			return BASE_SIZES['Bool']
		elif (return_type == 'Int'):
			return BASE_SIZES['Int']
		else:
			return 8

	def __init__(
		self,
		name,
		context,
		return_type='Void',
		num_params=0,
	) -> None:
		self.name = name
		self.is_inherited = False
		self.context = context
		self.num_params = num_params
		self.return_type = return_type
		self.param_types = []
		self.param_names = []

		self.return_size = self.getReturnSize(return_type)
		self.absolute_return_offset = 0

		self.let_num = 0
		self.size = self.getReturnSize(return_type)
		self.current_offset = self.getReturnSize(return_type)

	def getSize(self):
		return self.size
	
	def getContext(self):
		return self.context

	def addLet(self):
		self.let_num += 1

	def addParam(self, param_name, param_type, param_size = 0):
		self.param_types.append(param_type)
		self.param_names.append(param_name)
		self.size += param_size

	def addToSize(self, size = 0):
		self.size += size

	def updateOffset(self, offset):
		self.current_offset = offset

	def set_return_type(self, return_type):
		self.return_type = return_type

	def set_absolute_return_offset(self, offset):
		self.absolute_return_offset = offset

	def set_is_inherited(self):
		self.is_inherited = True

	def __str__(self):
		details = '{\n'
		details += f'  name: {self.name}\n'
		details += f'  context: {self.context}\n'
		details += f'  return_type: {self.return_type}\n'
		details += f'  num_params: {self.num_params}\n'
		details += f'  param_types: {self.param_types}\n'
		details += f'  param_names: {self.param_names}\n'
		details += f'  is_inherited: {self.is_inherited}\n'
		details += f'  size: {self.size}\n'
		details += f'  return_size: {self.return_size}\n'
		details += f'  absolute_return_offset: {self.absolute_return_offset}\n'
		details += f'  let_num: {self.let_num}\n'
		details += f'  current_offset: {self.current_offset}\n'
		details += '}'
		return details

class FunctionsTable(object):
	def __init__(self) -> None:
		self.table = {}

	def add(
		self,
		fun_name,
		class_name,
		return_type=None,
		num_params=0
	):
		key = class_name + '-' + fun_name
		if key in self.table.keys():
			function = self.table[key]
			
			if function.is_inherited and function.return_type == return_type and function.num_params == num_params:
				pass
			else:
				return False

		variable = FunctionObject(
			fun_name,
			class_name,
			return_type,
			num_params
		)

		self.table[key] = variable
		return True

	def contains(self, fun_name, fun_class):
		key = fun_class + '-' + fun_name
		if key in self.table.keys():
			return True
		return False
	
	def get(
		self,
		fun_name,
		class_name
	):
		key = class_name + '-' + fun_name
		if key not in self.table.keys():
			return None
		return self.table.get(key)

	def function_exists_with_name(self, searched_name):
		for key in self.table.keys():
			possible_name = key.split("-")[1]
			if possible_name == searched_name:
				return True
	
	def inheritFunctions(
		self,
		parent_class,
		inherited_class
	):
		inner_table = {}
		for key in self.table.keys():
			possible_from_class = key.split("-")[0]
			if possible_from_class == parent_class:
				parent_method = self.table.get(key)
				inherited_key = f'{inherited_class}-{",".join(key.split("-")[1:])}'
				
				if inherited_key in self.table.keys():
					# Check if the signature is the same and keep the child's method
					child_method = self.table[inherited_key]

					if not compare_dicts_ignore_attribute(parent_method, child_method, "context"):
						return False
				else:
					# Add the method
					inner_table[inherited_key] = parent_method

		for key in inner_table:
			current_funct = inner_table[key]
			current_funct.set_is_inherited()
			self.table[key] = current_funct

		return True

	def __str__(self):
		details = '{\n'
		for key in self.table:
			fun_obj = self.table[key]
			details += f'  {key} : ' + '{\n'
			details += f'    name: {fun_obj.name}\n'
			details += f'    context: {fun_obj.context}\n'
			details += f'    return_type: {fun_obj.return_type}\n'
			details += f'    num_params: {fun_obj.num_params}\n'
			details += f'    param_types: {fun_obj.param_types}\n'
			details += f'    param_names: {fun_obj.param_names}\n'
			details += f'    is_inherited: {fun_obj.is_inherited}\n'
			details += f'    size: {fun_obj.size}\n'
			details += f'    return_size: {fun_obj.return_size}\n'
			details += f'    absolute_return_offset: {fun_obj.absolute_return_offset}\n'
			details += f'    let_num: {fun_obj.let_num}\n'
			details += f'    current_offset: {fun_obj.current_offset}\n'
		details += '}'
		return details

class ClassObject(object):
	def __init__(self, name, parent='Object') -> None:
		self.name = name
		self.parent = parent
		self.current_offset = 0
		self.variables = []
		self.functions = []
	
	def getParent(self):
		return self.parent

	def getOffset(self):
		return self.current_offset

	def getSize(self):
		return self.current_offset

	def addVariable(self, var_name):
		self.variables.append(var_name)

	def addFunction(self, fun_name):
		self.functions.append(fun_name)

	def updateOffset(self, add_value):
		self.current_offset += add_value

	def __str__(self):
		details = '{\n'
		details += f'    name: {self.name}\n'
		details += f'    parent: {self.parent}\n'
		details += f'    size: {self.current_offset}\n'
		details += f'    variables: {self.variables}\n'
		details += f'    functions: {self.functions}\n'
		details += '}'
		return details

class ClassesTable(object):
	def __init__(self) -> None:
		self.table = {}
	
	def add(
		self,
		name,
		parent,
	):
		if name in self.table.keys():
			return False

		variable = ClassObject(
			name,
			parent
		)

		self.table[name] = variable
		return True

	def get(self, key):
		if key not in self.table.keys():
			return None
		return self.table[key]
	
	def contains(self, key):
		if key not in self.table.keys():
			return False
		return True

	def getSize(self, variables_table, functions_table):
		size = 0

		for key in self.table:
			class_obj = self.table[key]
			class_size = 0

			for variable in class_obj.variables:
				temp_variable = variables_table.get(variable, class_obj.name)
				class_size += temp_variable.size
			for function in class_obj.functions:
				temp_function = functions_table.get(function, class_obj.name)
				class_size += temp_function.size

			size += class_size
		return size

	def __str__(self):
		details = '{\n'
		for key in self.table:
			class_obj = self.table[key]
			details += f'  {key} : ' + '{\n'
			details += f'    name: {class_obj.name}\n'
			details += f'    parent: {class_obj.parent}\n'
			details += f'    size: {class_obj.current_offset}\n'
			details += f'    variables: {class_obj.variables}\n'
			details += f'    functions: {class_obj.functions}\n'
		details += '}'
		return details