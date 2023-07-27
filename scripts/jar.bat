@echo off
del /s *.class
del /s *.java
del /s *.tokens
del /s *.interp

Java -jar D:/Javalib/antlr-4.13.0-complete.jar Yalp.g4
javac Yalp*.java
grun Yalp r -gui

Java -jar D:/Javalib/antlr-4.13.0-complete.jar  -Dlanguage=Python3 -visitor Yalp.g4