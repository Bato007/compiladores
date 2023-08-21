def compare_dicts_ignore_attribute(dict1, dict2, attribute_to_ignore):
    dict1_copy = dict1.copy()
    dict2_copy = dict2.copy()
    
    if attribute_to_ignore in dict1_copy:
        del dict1_copy[attribute_to_ignore]
    if attribute_to_ignore in dict2_copy:
        del dict2_copy[attribute_to_ignore]
    
    return dict1_copy == dict2_copy