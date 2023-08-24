import tkinter as tk
import re
import os
import subprocess
from tkinter import filedialog
from PIL import Image, ImageTk

cool_reserved_words = [
    'if', 'else', 'fi', 'while', 'for', 'break', 'continue',
    'class', 'function', 'return', 'var', 'const',
    'true', 'false', 'null', 'this', 'new',
    'int', 'float', 'string', 'bool',
    'import', 'from', 'as', 'package',
    'try', 'catch', 'finally', 'throw',
    'public', 'private', 'protected', 'isvoid',
    'static', 'final', 'abstract', 'virtual', 'inherits'
    # Add more reserved words here
]

def execute_code():
    output_text.delete("1.0", "end")  # Clear previous output
    try:
        with open(f'{os.getcwd()}/src/programs/class.txt', "w") as file:
            file.write(text_widget.get("1.0", "end-1c"))

        result = subprocess.run(['python', f'{os.getcwd()}/src/main.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output_text.insert("end", result.stdout + result.stderr)
    except Exception as e:
        output_text.insert("end", f"Error: {e}\n")

def upload_file():
    file_path = filedialog.askopenfilename()  # No filetypes specified
    if file_path:
        with open(file_path, "r") as file:
            content = file.read()
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", content)
            highlight_syntax()

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
root.title("Cool Debugger")


# Create a frame to group the text widget and play button
frame = tk.Frame(root, bg="#272822")
frame.pack(fill="both", expand=True)


# Create an "Upload File" button
upload_button = tk.Button(frame, text="Upload File", command=upload_file)
upload_button.pack(side="left", padx=10, pady=10)

# Create a button to execute the code
# Load a play button icon image
play_image = Image.open(f'{os.getcwd()}/src/assets/play.png')
play_image = play_image.resize((30, 30))  # Adjust the size as needed
play_icon = ImageTk.PhotoImage(play_image)

# Create a label with the play icon in the top right corner
play_button = tk.Label(frame, image=play_icon, bg="#272822")
play_button.pack(anchor="ne", padx=10, pady=10)

# Bind the click event of the play button to execute_code function
play_button.bind("<Button-1>", lambda event: execute_code())


# Create a text widget with dark mode style
text_widget = tk.Text(root, bg="#272822", fg="#f8f8f2", insertbackground="#f8f8f2")
text_widget.pack()

# Create a text widget for displaying terminal name
terminal_text = tk.Text(root, height=1, bg="#161613", foreground="#F8F8F2", insertbackground="#F8F8F2")
terminal_text.insert("end", "TERMINAL\n")
terminal_text.pack()
terminal_text.configure(state="disabled")

# Create a text widget for displaying output
output_text = tk.Text(root, height=10, bg="#161613", foreground="#F8F8F2", insertbackground="#F8F8F2")
output_text.pack()


# Configure a tag for syntax highlighting
text_widget.tag_configure("reserved_word", foreground="#f92672")
text_widget.tag_configure("upper_case", foreground="#9effff")
text_widget.tag_configure("function", foreground="#a6e22e")
text_widget.tag_configure("arrow", foreground="#ffd761")


# Bind events to highlight syntax
text_widget.bind("<KeyRelease>", highlight_syntax)

# Start the main event loop
root.mainloop()
