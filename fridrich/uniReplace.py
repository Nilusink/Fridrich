tReplace = list()
for element in [('ö', 'oe'), ('ä', 'ae'), ('ü', 'ue')]:
    tReplace.append((element[0].upper(), element[1].upper()))
tReplace += [('ö', 'oe'), ('ä', 'ae'), ('ü', 'ue')]

def encode(string:str):
    for element in tReplace:
        string.replace(element[0], element[1])
    return string

def decode(string:str):
    for element in tReplace:
        string.replace(element[1], element[0])
    return string