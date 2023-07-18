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

fragment LOWER_CASE : [a-z] ;
fragment UPPER_CASE : [A-Z] ;

INTEGER : [0-9]+ ;

QUOTE : '"' ;
fragment BASE_STRING : (UPPER_CASE | LOWER_CASE | INTEGER) ;
fragment BACK_SLASH : '\\' ;
fragment ESCAPE_SEQUENCES : BACK_SLASH (['"\\/bfnrt])*;
fragment TEXT : (~["\r\n] | BASE_STRING | ESCAPE_SEQUENCES | WS)* ;
STRING : QUOTE (BASE_STRING | ESCAPE_SEQUENCES | WS)* QUOTE ;

LEFT_KEY : '{' ;
RIGHT_KEY : '}' ;
LEFT_PARENTESIS : '(' ;
RIGHT_PARENTESIS : ')' ;

COLON : ':' ;
SEMI_COLON : ';' ;
COMMA : ',' ;

// (* expr *)
COMMENT
  : '(*' TEXT? '*)' -> skip
;

LINE_COMMENT
  : '--' ~[\r\n]* -> skip
;

ERROR :
  .*? { System.out.println("ERROR IN CODE"); }
;

CLASS_ID : UPPER_CASE (LOWER_CASE | UPPER_CASE | INTEGER)* ;
OBJ_ID : LOWER_CASE (LOWER_CASE | UPPER_CASE | INTEGER | '_' | '.')* ;

OBJ_TYPE :
  CLASS_ID
  | RESERVED_SELF_TYPE
;

expr_params : expr (COMMA expr)*;
expr :
  // expr [@CLASS_ID].OBJ_ID([expr params])
  expr (OPERATOR_AT CLASS_ID)? OPERATOR_DOT OBJ_ID LEFT_PARENTESIS (expr_params)? RIGHT_PARENTESIS
  // variable <- expr
  | OBJ_ID OPERATOR_ASSIGNMENT expr
  // variable([expr params])
  | OBJ_ID LEFT_PARENTESIS (expr_params)? RIGHT_PARENTESIS
  // if expr then expr else expr fi
  | RESERVED_IF expr RESERVED_THEN expr RESERVED_ELSE expr RESERVED_FI
  // while expr loop expr pool
  | RESERVED_WHILE expr RESERVED_LOOP expr RESERVED_POOL
  // { (expr;)+ }
  | LEFT_KEY (expr SEMI_COLON)+ RIGHT_KEY (SEMI_COLON)*
  // let OBJ_ID : TYPE_ID [ <- expr ] (, OBJ_ID : CLASS_ID [<- expr])* in expr
  | RESERVED_LET OBJ_ID COLON CLASS_ID (OPERATOR_ASSIGNMENT expr)? (COMMA OBJ_ID COLON CLASS_ID (OPERATOR_ASSIGNMENT expr)?)* RESERVED_IN expr
  // new Date
  | RESERVED_NEW CLASS_ID
  // new List.cons(1).cons(2).cons(3).cons(4).cons(5);
  | '.' (OBJ_ID) RIGHT_PARENTESIS (expr)* LEFT_PARENTESIS (SEMI_COLON)*
  // ~expr  
  | OPERATOR_TILDE expr
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
  // 1
  | INTEGER
  // example string
  | STRING
  // variable
  | OBJ_ID
  // true
  | RESERVED_TRUE
  // false
  | RESERVED_FALSE
  // self
  | RESERVED_SELF
;  

formal : 
  OBJ_ID COLON CLASS_ID
;
feature : 
  OBJ_ID LEFT_PARENTESIS (formal (COMMA formal)*)? RIGHT_PARENTESIS COLON CLASS_ID LEFT_KEY ((expr) (SEMI_COLON)*)* RIGHT_KEY
  | OBJ_ID (OPERATOR_ASSIGNMENT expr)? 
  // s : String;
  | formal
  // s : String <- "Hello"; | s : "Hello"; | | s : String;
  | OBJ_ID (COLON CLASS_ID)? OPERATOR_ASSIGNMENT expr
  | CLASS_ID LEFT_PARENTESIS expr RIGHT_PARENTESIS
;
r_class :
  RESERVED_CLASS CLASS_ID (RESERVED_INHERITS CLASS_ID)? LEFT_KEY (feature SEMI_COLON)+ RIGHT_KEY
;
program : 
  (r_class SEMI_COLON)+
;
r  :
  program
;