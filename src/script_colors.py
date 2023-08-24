import tkinter as tk
import re

cool_reserved_words = [
    'if', 'else', 'fi', 'while', 'for', 'break', 'continue',
    'class', 'function', 'return', 'var', 'const',
    'true', 'false', 'null', 'this', 'new',
    'int', 'float', 'string', 'bool',
    'import', 'from', 'as', 'package',
    'try', 'catch', 'finally', 'throw',
    'public', 'private', 'protected', 
    'static', 'final', 'abstract', 'virtual', 'inherits'
    # Add more reserved words here
]

def highlight_syntax(event=None):
    text = text_widget.get("1.0", "end-1c")
    text_widget.tag_remove("highlight", "1.0", "end")
    
    reserved_words_pattern = r'\b(?:' + '|'.join(re.escape(word) for word in cool_reserved_words) + r')\b'
    # Define regular expression patterns and corresponding colors
    patterns = [
        (reserved_words_pattern, 'reserved_word'),
        (r'\b[A-Z][a-zA-Z0-9_]*\b', 'upper_case'),
        ( r'(\w+)\s*(?=:|\(\))', 'function'),
        (r'<-', 'arrow')
    ]


    lines = text.splitlines()

    line_numb = 1
    for line in lines:
        for pattern, tag in patterns:
            for match in re.finditer(pattern, line):
                start = match.start(0)
                end = match.end(0)
                
                # Find the line number for the start of the match
                text_widget.tag_add(tag, f"{line_numb}.{start}", f"{line_numb}.{end}")
        line_numb += 1
# Create the main themed window
root = tk.Tk()
root.title("Script")

# Create a text widget with dark mode style
text_widget = tk.Text(root, bg="#272822", fg="#f8f8f2", insertbackground="#f8f8f2")
text_widget.pack()

# Configure a tag for syntax highlighting
text_widget.tag_configure("reserved_word", foreground="#f92672")
text_widget.tag_configure("upper_case", foreground="#9effff")
text_widget.tag_configure("function", foreground="#a6e22e")
text_widget.tag_configure("arrow", foreground="#ffd761")


# Bind events to highlight syntax
text_widget.bind("<KeyRelease>", highlight_syntax)

# Start the main event loop
root.mainloop()
