// Define a grammar called Hello
grammar Tokens;

RESERVED_CLASS : 'class' | 'CLASS' ;
RESERVED_ELSE : 'else' | 'ELSE' ;
RESERVED_IF : 'if' | 'IF' ;
RESERVED_FI : 'fi' | 'FI' ;
RESERVED_IN : 'in' | 'IN' ;
RESERVED_INHERITS : 'inherits' | 'INHERITS' ;
RESERVED_LOOP : 'loop' | 'LOOP' ;
RESERVED_POOL : 'pool' | 'POOL' ;
RESERVED_THEN : 'then' | 'THEN' ;
RESERVED_WHILE : 'while' | 'WHILE' ;
RESERVED_NEW : 'new' | 'NEW' ;
RESERVED_LET : 'let' | 'LET' ;

RESERVED_TRUE : 'true' ;
RESERVED_FALSE : 'false' ;
RESERVED_SELF : 'self' ;
RESERVED_SELF_TYPE : 'SELF_TYPE' ;

// OPERATORS
OPERATOR_DOT : '.' ;
OPERATOR_AT : '@' ;
OPERATOR_TILDE : '~' ;
RESERVED_ISVOID : 'isvoid' | 'ISVOID' ;
OPERATOR_MULTIPLY : '*' ;
OPERATOR_DIVIDE : '/' ;
OPERATOR_PLUS : '+' ;
OPERATOR_MINUS : '-' ;
OPERATOR_LESS_EQUAL : '<=' ;
OPERATOR_LESS : '<' ;
OPERATOR_EQUALS : '=' ;
RESERVED_NOT : 'not' | 'NOT' ;
OPERATOR_ASSIGNMENT : '<-' ;

WS : (' ' | '\t' | '\r' | '\n')+ -> skip ;

LOWER_CASE : [a-z] ;
UPPER_CASE : [A-Z] ;

INTEGER : [0-9]+ ;

QUOTE : '"' ;
BASE_STRING : (UPPER_CASE | LOWER_CASE | INTEGER) ;
BACK_SLASH : '\\' ;
ESCAPE_SEQUENCES : BACK_SLASH (['"\\/bfnrt])*;
STRING : QUOTE (~["\r\n] | BASE_STRING | ESCAPE_SEQUENCES | WS)* QUOTE ;

LEFT_KEY : '{' ;
RIGHT_KEY : '}' ;
LEFT_PARENTESIS : '(' ;
RIGHT_PARENTESIS : ')' ;
COLON : ':' ;
SEMI_COLON : ';' ;

COMMA : ',' ;

CLASS_ID : UPPER_CASE (LOWER_CASE | UPPER_CASE | INTEGER)* ;
OBJ_ID : LOWER_CASE (LOWER_CASE | UPPER_CASE | INTEGER)* ;

expr_params : expr (COMMA expr)*;
expr : 
  // variable <- expr
  OBJ_ID OPERATOR_ASSIGNMENT expr
  // expr [@CLASS_ID].OBJ_ID([expr params])
  expr (OPERATOR_AT CLASS_ID)? OPERATOR_DOT OBJ_ID LEFT_PARENTESIS (expr_params)? RIGHT_PARENTESIS
  // variable([expr params])
  | OBJ_ID LEFT_PARENTESIS (expr_params)? RIGHT_PARENTESIS
  // if expr then expr else expr fi
  | RESERVED_IF expr RESERVED_THEN expr RESERVED_ELSE expr RESERVED_FI
  // while expr loop expr pool
  | RESERVED_WHILE expr RESERVED_LOOP expr RESERVED_POOL
  // { (expr;)+ }
  | LEFT_KEY (expr SEMI_COLON)+ RIGHT_KEY
  // let OBJ_ID : TYPE_ID [ <- expr ] (, OBJ_ID : CLASS_ID [<- expr])* in expr
  | RESERVED_LET OBJ_ID COLON CLASS_ID (OPERATOR_ASSIGNMENT expr)? (COMMA OBJ_ID COLON CLASS_ID (OPERATOR_ASSIGNMENT expr)?)* RESERVED_IN expr
  // new Date
  | RESERVED_NEW CLASS_ID
  // isvoid expr
  | RESERVED_ISVOID expr
  // expr * expr
  | expr OPERATOR_MULTIPLY expr
  // expr / expr
  | expr OPERATOR_DIVIDE expr
  // expr + expr
  | expr OPERATOR_PLUS expr
  // expr - expr
  | expr OPERATOR_MINUS expr
  // ~expr
  | OPERATOR_TILDE expr
  // expr = expr
  | expr OPERATOR_LESS expr
  // expr <= expr
  | expr OPERATOR_LESS_EQUAL expr
  // expr = expr
  | expr OPERATOR_EQUALS expr
  // not expr
  | RESERVED_NOT expr
  // ( expr )
  | LEFT_PARENTESIS expr RIGHT_PARENTESIS
  // object
  | OBJ_ID
  // 1
  | INTEGER
  // example string
  | STRING
  // true
  | RESERVED_TRUE
  // false
  | RESERVED_FALSE ;

formal : OBJ_ID COLON CLASS_ID ;
feature : 
  OBJ_ID LEFT_PARENTESIS (formal (COMMA formal)*)? RIGHT_PARENTESIS COLON CLASS_ID LEFT_KEY (feature SEMI_COLON)* RIGHT_KEY
  | OBJ_ID (OPERATOR_ASSIGNMENT expr)? ;
r_class : RESERVED_CLASS CLASS_ID (RESERVED_INHERITS CLASS_ID)? LEFT_KEY feature SEMI_COLON RIGHT_KEY ;
program : (r_class SEMI_COLON)+ ;

r  : program ;