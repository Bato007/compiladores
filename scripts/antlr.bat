@echo off
del /s *.class
del /s *.java
del /s *.tokens
del /s *.interp

cd ./grammar

antlr Yalp.g4 Constants.g4
javac *.java
grun Yalp r -gui

cd ..