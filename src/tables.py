class VariableObject(object):
	def __init__(self, name, type, context, init_value=None):
		self.name = name
		self.type = type
		self.contex = context
		self.init_value = init_value
	

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

	def __str__(self):
		details = '{\n'
		for key in self.table:
			variable = self.table[key]
			details += f'  {key} : ' + '{\n'
			details += f'\tname: {variable.name}\n'
			details += f'\ttype: {variable.type}\n'
			details += f'\tcontex: {variable.contex}\n'
			details += f'\tvalue: {variable.init_value}\n'
		details += '}'
		return details

class FunctionObject(object):
	def __init__(
		self,
		name,
		context,
		num_params,
		return_type,
		param_types = []
	) -> None:
		self.name = name
		self.context = context
		self.num_params = num_params
		self.return_type = return_type
		self.param_types = param_types

class FunctionsTable(object):
	def __init__(self) -> None:
		self.table = {}
	
	def add(
		self,
		name,
		context,
		num_params,
		return_type,
		param_types
	):
		key = context + '-' + name
		if (key in self.table.keys()):
			return False

		
		variable = FunctionObject(
			name,
			context,
			num_params,
			return_type,
			param_types
		)

		self.table[key] = variable
		return True

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
