@echo off
del /s *.class
del /s *.java
del /s *.tokens
del /s *.interp

antlr4 Yalp.g4
javac Yalp*.java
grun Yalp r -gui