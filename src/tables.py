from utils import compare_dicts_ignore_attribute

BASE_SIZES = {
  'Int': 4,
  'Bool': 1,
  'String': 16,
}

class TemporalObject(object):
	def __init__(self, _id, context, originalRule):
		self._id = _id
		self.context = context
		self.size = 0
		self.offset = 0
		self.originalRule = originalRule
		self.intermediaryRule = originalRule

	def setError(self):
		self.type = 'ERROR'

	def setOffset(self, offset = 0):
		self.offset = offset

	def setSize(self, size = 0):
		try:
			self.size = BASE_SIZES[self.type]
		except:
			self.size = size

	def setRule(self, rule, content, _id):
		name = f't{_id}'
		if (content != None):
			intermediaryRule = rule.replace(content, name)
			# print("			rule", rule)
			# print("			originalRule", self.originalRule)
			# print("			intermediaryRule", intermediaryRule)
			self.intermediaryRule = intermediaryRule

		return self.intermediaryRule
	
	def getSize(self):
		return self.size
	
	def three_way_print(self):
		print(f'		t{self._id} = {self.intermediaryRule}')

	def __str__(self):
		details = '{\n'
		details += f'  id: {self._id}\n'
		details += f'  context: {self.context}\n'
		details += f'  size: {self.size}\n'
		details += f'  offset: {self.offset}\n'
		details += f'  intermediaryRule: {self.intermediaryRule}\n'
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
	):
		key = f'{context}-t{_id}'
		if key in self.table.keys():
			return False

		temporal = TemporalObject(
			_id,
			context,
			originalRule
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
		return self.table.get(key)

	def __str__(self):
		details = '{\n'
		for key in self.table:
			variable = self.table[key]
			details += f'  {key} : ' + '{\n'
			details += f'    name: t-{variable._id}\n'
			details += f'    context: {variable.context}\n'
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

	def setError(self):
		self.type = 'ERROR'

	def setOffset(self, offset = 0):
		self.offset = offset

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
		details += '}'
		return details

class FunctionObject(object):
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
		self.let_num = 0
		self.size = 0
		self.current_offset = 0

	def getSize(self):
		return self.size

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