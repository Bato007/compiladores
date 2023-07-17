@echo off
del /s *.class
del /s *.java
del /s *.tokens
del /s *.interp

antlr4 Tokens.g4
javac Tokens*.java
grun Tokens r -gui