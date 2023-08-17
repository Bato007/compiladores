class VariableObject(object):
	def __init__(self, name, type, context, init_value=None):
		self.name = name
		self.type = type
		self.context = context
		self.init_value = init_value
	
	def __str__(self):
		details = '{\n'
		details += f'  name: {self.name}\n'
		details += f'  type: {self.type}\n'
		details += f'  context: {self.context}\n'
		details += f'  value: {self.init_value}\n'
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
		if (key in self.table.keys()):
			return False
		
		if (init_value == None):
			if (type == 'Int'):
				init_value = 0
			elif (type == 'Bool'):
				init_value = 'false'
			elif (type == 'String'):
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
		if (key in self.table.keys()):
			return True
		return False
	
	def get(
		self,
		var_name,
		var_context
	):
		key = var_context + '-' + var_name
		if (not self.contains(var_name, var_context)): return None

		return self.table.get(key)

	def __str__(self):
		details = '{\n'
		for key in self.table:
			variable = self.table[key]
			details += f'  {key} : ' + '{\n'
			details += f'\tname: {variable.name}\n'
			details += f'\ttype: {variable.type}\n'
			details += f'\tcontext: {variable.context}\n'
			details += f'\tvalue: {variable.init_value}\n'
		details += '}'
		return details

class FunctionObject(object):
	def __init__(
		self,
		name,
		context,
		return_type = 'Void',
		num_params = 0,
	) -> None:
		self.name = name
		self.context = context
		self.num_params = num_params
		self.return_type = return_type
		self.param_types = []
		self.param_names = []

	def addParam(self, param_name, param_type):
		self.param_types.append(param_type)
		self.param_names.append(param_name)
		self.num_params = self.num_params + 1
	
	def __str__(self):
		details = '{\n'
		details += f'  name: {self.name}\n'
		details += f'  context: {self.context}\n'
		details += f'  return_type: {self.return_type}\n'
		details += f'  num_params: {self.num_params}\n'
		details += f'  param_types: {self.param_types}\n'
		details += f'  param_names: {self.param_names}\n'
		details += '}'
		return details

class FunctionsTable(object):
	def __init__(self) -> None:
		self.table = {}

	def add(
		self,
		fun_name,
		class_name,
		return_type,
	):
		key = class_name + '-' + fun_name
		if (key in self.table.keys()):
			return False

		variable = FunctionObject(
			fun_name,
			class_name,
			return_type,
		)

		self.table[key] = variable
		return True
	
	def get(
		self,
		fun_name,
		class_name
	):
		key = class_name + '-' + fun_name
		if (key not in self.table.keys()):
			return None
		return self.table.get(key)

class ClassObject(object):
	def __init__(self, name, parent = 'Object') -> None:
		self.name = name
		self.parent = parent
	
	def getParent(self):
		return self.parent

class ClassesTable(object):
	def __init__(self) -> None:
		self.table = {}
	
	def add(
		self,
		name,
		parent,
	):
		if (name in self.table.keys()):
			return False

		variable = ClassObject(
			name,
			parent
		)

		self.table[name] = variable
		return True

	def get(self, key):
		if (key not in self.table.keys()):
			return None
		return self.table[key]
	
	def contains(self, key):
		if (key not in self.table.keys()):
			return False
		return True
