from copy import deepcopy
from time import time

class List:
    def RemoveAll(lst:list, value): # remove all values from list
        return list(filter(lambda a: a!=value, lst))

    def FromMatrix(lst:list, index:int):    # make list from matrix (just return all elements of the matrix (2D))
        for element in lst:
            yield element[index]
    
    def closest(number:float, lst:list):    # check wich element in list is closest to given number
        cl = 0
        for element in lst:
            if abs(element-number)<abs(cl-number):
                cl = element
        return cl

    def singles(lst:list): # removes all clones from list
        return list(set(lst))   # also sorts it
    
    def getInnerDictValues(lst:list, Index): # when given ([{'a':5}, {'b':3}, {'a':2, 'b':3}], 'a') returns (5, 2)
        out = list()
        for element in lst:
            if Index in element:
                out.append(element[Index])
        return out
class Dict:
    def Indexes(dictionary:dict):   # returns the indexes of the dictionary
        return list(dictionary)

    def Values(dictionary:dict):    # returns the values of the dictionary
        for element in dictionary:
            yield dictionary[element]

    def inverse(dictionary:dict):   # inverses the dicitonary (so values become indexes and opposite)
        x = dict()
        for element in dictionary:
            x[dictionary[element]] = element
        return x
    
    def sort(dictionary:dict):
        return {Index:dictionary[Index] for Index in sorted(list(dictionary))}

class const:
    def __init__(self, val):
        self.value = deepcopy(val) # create deepcopy of list (cause python is strange and source lists are dependent on it's cloned lists)
    
    def __repr__(self):
        return str(self.value)

    def get(self):
        return deepcopy(self.value)    # return value with an extra deep copy
    
    def len(self):
        return len(self.value)  # return lenght of list (cause why not?)

def arange(*args):  # basically like numpy.arange (range with float as steps) but with roundet output
    def_args = [0.0, None, 1.0]
    if len(args)==1:    # if only one argument is given, map it to element 1
        def_args[1] = args[0]
    else:
        for i in range(len(args)):  # else exchange each element with its corresponding new value
            def_args[i] = args[i]

    x = def_args[0] # set start position of x
    while x<def_args[1]:
        yield float(round(x, len(str(def_args[2]).split('.')[1]))) # return x (roundet based on how many decimals the step variable has)
        x+=def_args[2]  # add step to x

def inverse(value): # inverse a bool or int (or technically also a str) object
	t = type(value) # type for final convertion
	val = bool(value)   # bool value so we don't need to handle every single variable type
	if val==False:  # inverse
		val=True
	else:
		val=False
	return t(val)   # return converted value

def timeit(func):   # decorator for timing functions
    def wrapper(*args, **kw):
        start = time()
        x = func(*args, **kw)
        print(f'took: {start-time()}')
        return x
        
    return wrapper

if __name__ == '__main__':
    from traceback import format_exc

    # mylist = [[1, 2], [1, 2], [1, 2]]
    # print(list(ListFromMatrix(mylist, 0)))
    # print(list(ListFromMatrix(mylist, 1)))

    # mydict = {'Name':'John', 'Age':52, 'Gender':'Male'}
    # print(list(DictIndexes(mydict)))

    #mylist = [12, 15, None, 30, 10, 29, None]
    #print(List.RemoveAll(mylist, None))

    #print(list(arange(1, 5)))

    while True:
        try:
            com = input('>> ')
            exec(com)
            
        except:
            print(format_exc())