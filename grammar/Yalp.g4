grammar Yalp;

CLASS : 'class' | 'CLASS' ;
ELSE : 'else' | 'ELSE' ;
IF : 'if' | 'IF' ;
FI : 'fi' | 'FI' ;
IN : 'in' | 'IN' ;
INHERITS : 'inherits' | 'INHERITS' ;
LOOP : 'loop' | 'LOOP' ;
POOL : 'pool' | 'POOL' ;
THEN : 'then' | 'THEN' ;
WHILE : 'while' | 'WHILE' ;
NEW : 'new' | 'NEW' ;
LET : 'let' | 'LET' ;

Bool : 'true' | 'false' ;
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

fragment LOWER_CASE : [a-z] ;
fragment UPPER_CASE : [A-Z] ;

Int : [0-9]+ ;

QUOTE : '"' ;
fragment BASE_STRING : (UPPER_CASE | LOWER_CASE | Int) ;
fragment BACK_SLASH : '\\' ;
fragment ESCAPE_SEQUENCES : BACK_SLASH (['"\\/bfnrt])*;
fragment TEXT : (~["\r\n] | BASE_STRING | ESCAPE_SEQUENCES | WS)* ;

String : QUOTE (BASE_STRING | ESCAPE_SEQUENCES | WS)* QUOTE ;

LEFT_KEY : '{' ;
RIGHT_KEY : '}' ;
LEFT_PARENTESIS : '(' ;
RIGHT_PARENTESIS : ')' ;

COLON : ':' ;
SEMI_COLON : ';' ;
COMMA : ',' ;

// (* expr *)
WS : (' ' | '\t' | '\r' | '\n')+ -> skip ;

COMMENT
  : '(*' TEXT? '*)' -> skip
;

LINE_COMMENT
  : '--' ~[\r\n]* -> skip
;

ERROR :
  .*?
;
  
CLASS_ID : UPPER_CASE (LOWER_CASE | UPPER_CASE | Int)* ;
OBJ_ID : LOWER_CASE (LOWER_CASE | UPPER_CASE | Int | '_')* ;

type :
  CLASS_ID
  | RESERVED_SELF_TYPE
;

expr :
  // expr [@CLASS_ID].OBJ_ID([expr params])
  expr (OPERATOR_AT CLASS_ID)? OPERATOR_DOT OBJ_ID 
    LEFT_PARENTESIS (expr (COMMA expr)*)? RIGHT_PARENTESIS                      # functionCall
  // variable([expr params])
  | OBJ_ID LEFT_PARENTESIS (expr (COMMA expr)*)? RIGHT_PARENTESIS               # localFunCall
  // if expr then expr else expr fi
  | IF expr THEN expr ELSE expr FI                                              # ifTense
  // while expr loop expr pool
  | WHILE expr LOOP expr POOL                                                   # loopTense
  // { (expr;)+ }
  | LEFT_KEY (expr SEMI_COLON)+ RIGHT_KEY                                       # instructions
  // let OBJ_ID : TYPE_ID [ <- expr ] (, OBJ_ID : CLASS_ID [<- expr])* in expr
  | LET OBJ_ID COLON CLASS_ID (OPERATOR_ASSIGNMENT expr)? 
    (COMMA OBJ_ID COLON CLASS_ID (OPERATOR_ASSIGNMENT expr)?)* IN expr          # letTense
  // new Date
  | NEW CLASS_ID                                                                # objCreation
  // ~expr  
  | OPERATOR_TILDE expr                                                         # arithmetical
  // isvoid expr
  | RESERVED_ISVOID expr                                                        # isVoidExpr
  // expr * expr
  | expr OPERATOR_MULTIPLY expr                                                 # arithmetical
  // expr / expr
  | expr OPERATOR_DIVIDE expr                                                   # arithmetical
  // expr + exprx
  | expr OPERATOR_PLUS expr                                                     # arithmetical
  // expr - expr
  | expr OPERATOR_MINUS expr                                                    # arithmetical
  // expr < expr
  | expr OPERATOR_LESS expr                                                     # logical
  // expr <= expr
  | expr OPERATOR_LESS_EQUAL expr                                               # logical
  // expr = expr
  | expr OPERATOR_EQUALS expr                                                   # logical
  // not expr
  | RESERVED_NOT expr                                                           # logical
  // variable <- expr
  | OBJ_ID OPERATOR_ASSIGNMENT expr                                             # assignment
  // ( expr )
  | LEFT_PARENTESIS expr RIGHT_PARENTESIS                                       # parentesis
  // variable
  | OBJ_ID                                                                      # objectId
  // self
  | RESERVED_SELF                                                               # self
  // 1
  | Int                                                                         # int
  // example string
  | String                                                                      # string
  // true / false
  | Bool                                                                        # boolean
;  

formal : 
  OBJ_ID COLON CLASS_ID
;

var_declarations :
  // s : String <- "Hello"; | s <- "Hello"; | s : String;
  OBJ_ID COLON type (OPERATOR_ASSIGNMENT expr)? 
;

feature : 
  // fun(...) { expr }
  OBJ_ID LEFT_PARENTESIS (formal (COMMA formal)*)? 
    RIGHT_PARENTESIS COLON type 
    LEFT_KEY expr RIGHT_KEY                             # funDeclaration
  | var_declarations                                    # varDeclarations                
;   
r_class :
  CLASS CLASS_ID (INHERITS CLASS_ID)? 
    LEFT_KEY (feature SEMI_COLON)* RIGHT_KEY
;
program : 
  (r_class SEMI_COLON)+
;
r  :
  program
;