from utils import compare_dicts_ignore_attribute

class VariableObject(object):
	def __init__(self, name, type, context, init_value=None):
		self.name = name
		self.type = type
		self.context = context
		self.init_value = init_value

	def setError(self):
		self.type = 'ERROR'
	
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
		self.is_inherited = False
		self.context = context
		self.num_params = num_params
		self.return_type = return_type
		self.param_types = []
		self.param_names = []

	def addParam(self, param_name, param_type):
		self.param_types.append(param_type)
		self.param_names.append(param_name)

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
		details += '}'
		return details

class FunctionsTable(object):
	def __init__(self) -> None:
		self.table = {}

	def add(
		self,
		fun_name,
		class_name,
		return_type = None,
    	num_params = 0
	):
		key = class_name + '-' + fun_name
		if (key in self.table.keys()):
			function = self.table[key]
			
			if (function.is_inherited and function.return_type == return_type and function.num_params == num_params):
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
		if (key in self.table.keys()):
			return True
		return False
	
	def get(
		self,
		fun_name,
		class_name
	):
		key = class_name + '-' + fun_name
		if (key not in self.table.keys()):
			return None
		return self.table.get(key)

	
	def inheritFunctions(
		self,
		parent_class,
		inherited_class
	):
		inner_table = {}
		for key in self.table.keys():
			possible_from_class = key.split("-")[0]
			if (possible_from_class == parent_class):
				parent_method = self.table.get(key)
				inherited_key = f'{inherited_class}-{",".join(key.split("-")[1:])}'
				
				if (inherited_key in self.table.keys()):
					# Se revisa que la firma sea la misma y se deja el metodo del hijo
					child_method = self.table[inherited_key]

					if (not compare_dicts_ignore_attribute(parent_method, child_method, "context")):
						return False
				else:
					# Agreegamos el metodo
					inner_table[inherited_key] = parent_method

		for key in inner_table:
			current_funct = inner_table[key]
			current_funct.set_is_inherited()
			self.table[key] = current_funct

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
