def compare_dicts_ignore_attribute(dict1, dict2, attribute_to_ignore):
    dict1_copy = dict1.copy()
    dict2_copy = dict2.copy()
    
    if attribute_to_ignore in dict1_copy:
        del dict1_copy[attribute_to_ignore]
    if attribute_to_ignore in dict2_copy:
        del dict2_copy[attribute_to_ignore]
    
    return dict1_copy == dict2_copy

def return_correct_mips(variables_table, temporals_table, extracted_strings, line):
  new_line = line
  for var in variables_table.table:
    if (var in line):
      try:
        offset = variables_table.table[var].offset
        if ("la" in new_line):
          pass
        elif ("lw" in new_line or "sw" in new_line):
          new_line = new_line.replace(var, f'{offset}')
        else:
          new_line = new_line.replace(var, f'GP[{offset}]')
      except:
        pass
  
  for temp in sorted(temporals_table.table, reverse=True):
    if (temp in line):
      if (temporals_table.getByKey(temp) != None): 
        if ("la" in new_line):
          pass
        elif ("lw" in new_line or "sw" in new_line):
          new_line = new_line.replace(temp, f'{temporals_table.getByKey(temp).offset}')
        else:
          new_line = new_line.replace(temp, f'GP[{temporals_table.getByKey(temp).offset}]')

  for extracted_string in extracted_strings:
    value = extracted_strings[extracted_string]
    if (value in line):
      new_line = new_line.replace(value, extracted_string)

  new_line = new_line.replace("-", "_").rstrip()
  return new_line