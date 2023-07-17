@echo off
del /s *.class
del /s *.java
del /s *.tokens
del /s *.interp

Java -jar D:/Javalib/antlr-4.13.0-complete.jar Tokens.g4
javac Tokens*.java
grun Tokens r -gui