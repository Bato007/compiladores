class CreateFile(object):
    def __init__(self, file_name) -> None:
        # Create a new text file and leave it open
        self.file_name = file_name
        self.file = open(file_name, 'w')
        pass

    # Function to add a line to the text file
    def add_line_to_txt(self, new_line):
        self.file.write(new_line + '\n')  # Add a newline character to separate lines

    # Function to close the text file
    def close_txt_file(self):
        self.file.close()
