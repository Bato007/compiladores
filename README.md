Run the following commands:

```
antlr <filename>.g4 | Java -jar D:/Javalib/antlr-4.13.0-complete.jar <filename>.g4
javac <filename>*.java
grun <filename> r -gui
```
```
./run.bat
```

Then do CTRL + Z + ENTER, then the image will show

To generate python files use the following comand
```
antlr -Dlanguage=Python3 -visitor <filename>.g4
```
