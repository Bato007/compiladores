@echo off
@REM del /s *.class
@REM del /s *.java
@REM del /s *.tokens
@REM del /s *.interp

antlr Yalp.g4
javac Yalp*.java
grun Yalp r -gui