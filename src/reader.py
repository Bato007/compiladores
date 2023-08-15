import os

def resolveLibrary():
  # Get the libraries
  library_path = os.path.join(os.getcwd(), 'src/library')
  concatenated_text = ''

  # Iterate through files in the folder
  for filename in os.listdir(library_path):
    if not filename.endswith('.txt'): continue

    file_path = os.path.join(library_path, filename)
    with open(file_path, 'r', encoding='utf-8') as file:
      file_contents = file.read()
      concatenated_text += file_contents + '\n\n'
  return concatenated_text

def resolveFile(file_name):
  full_path = os.getcwd() + '/src/programs/' + file_name
  try:
    with open(full_path, 'r') as file:
      return file.read()
  except FileNotFoundError:
    print(f"File not found: {file_name}")
    exit(-1)
  except IOError:
    print(f"Error reading the file: {file_name}")
    exit(-1)

def resolveEntryPoint(file_name):
  return resolveLibrary() + resolveFile(file_name)