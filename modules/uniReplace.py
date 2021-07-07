tReplace = [('ö', 'oe'), ('ä', 'ae'), ('ü', 'ue')]
for element in tReplace:
    tReplace.append((element[0].upper(), element[1].upper()))

def encode(string:str):
    for element in tReplace:
        string.replace(element[0], element[1])
    return string

def decode(string:str):
    for element in tReplace:
        string.replace(element[1], element[0])
    return string