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
  'Bool-OPERATOR_PLUS-Bool': 'Int',
  'Bool-OPERATOR_MINUS-Bool': 'Int',
  'Bool-OPERATOR_DIVIDE-Bool': 'Int',
  'Bool-OPERATOR_MULTIPLY-Bool': 'Int',
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

POINTER_SIZE = 8

uninherable = ['Bool', 'Int', 'String']
unoverloading = ['Object', 'IO', 'Bool', 'Int', 'String']