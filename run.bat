set arg1=%1

if %arg1% == 4 (
  antlr4 Tokens.g4
) else (
  Java -jar D:/Javalib/antlr-4.13.0-complete.jar Tokens.g4
)
javac Tokens*.java
grun Tokens r -gui