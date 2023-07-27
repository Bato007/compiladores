@echo off

rem Delete .class files
if exist './src/grammar/*.class' (
    del /s './src/grammar/*.class'
) else (
    echo No .class files found.
)

rem Delete .java files
if exist './src/grammar/*.java' (
    del /s './src/grammar/*.java'
) else (
    echo No .java files found.
)

rem Delete .tokens files
if exist './src/grammar/*.java' (
    del /s './src/grammar/*.java'
) else (
    echo No .tokens files found.
)

rem Delete .interp files
if exist './src/grammar/*.interp' (
    del /s './src/grammar/*.interp'
) else (
    echo No .interp files found.
)

antlr -Dlanguage=Python3 -visitor -o ./src ./grammar/*.g4
