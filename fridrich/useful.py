from types import GeneratorType
from copy import deepcopy
from typing import Any
from time import time

class List:
    "list functions"
    def RemoveAll(lst:list, value) -> list:
        "remove all values from list"
        return list(filter(lambda a: a!=value, lst))

    def FromMatrix(lst:list, index:int) -> GeneratorType:
        "make list from matrix (just return all elements of the matrix (2D))"
        for element in lst:
            yield element[index]
    
    def AllFromMatrix(lst:list) -> GeneratorType:
        """
        yield all elements of all lists in parent list
        
        works with lists and tuples ONLY - no dicts
        """
        tmp = str(lst).strip().replace('[', '').replace(']', '').replace('(', '').replace(')', '')
        print(tmp)
        while ',,' in tmp:
            tmp = tmp.replace(',,', ',')
        lst = tmp.split(',')
        for element in lst:
            yield (eval(element))
    
    def closest(number:float, lst:list) -> float:
        "check wich element in list is closest to given number"
        cl = 0
        for element in lst:
            if abs(element-number)<abs(cl-number):
                cl = element
        return cl

    def singles(lst:list) -> list:
        """
        removes all clones from list
        
        also sorts it
        """
        return list(set(lst))
    
    def getInnerDictValues(lst:list, Index) -> list:
        "when given ([{'a':5}, {'b':3}, {'a':2, 'b':3}], 'a') returns (5, 2)"
        out = list()
        for element in lst:
            if Index in element:
                out.append(element[Index])
        return out

class Dict:
    "dictionary functions"
    def Indexes(dictionary:dict) -> list:
        "returns the indexes of the dictionary"
        return list(dictionary)

    def Values(dictionary:dict) -> GeneratorType:
        "returns the values of the dictionary"
        for element in dictionary:
            yield dictionary[element]

    def inverse(dictionary:dict) -> dict:
        "inverses the dicitonary (so values become indexes and opposite)"
        x = dict()
        for element in dictionary:
            x[dictionary[element]] = element
        return x
    
    def sort(dictionary:dict, key=sorted) -> dict:
        "sort dicitonarys by indexes"
        return {Index:dictionary[Index] for Index in key(list(dictionary))}

class const:
    def __init__(self, val:Any) -> None:
        """
        create deepcopy of list (cause python is strange and source lists are dependent on it's cloned lists)
        
        also works with other variable types
        """
        self.value = deepcopy(val)
    
    def __repr__(self) -> str:
        return str(self.value)

    def get(self):
        "return value with an extra deep copy"
        return deepcopy(self.value)
    
    def len(self) -> int:
        "return lenght of list (cause why not?)"
        return len(self.value)

def arange(*args) -> GeneratorType:
    "basically like numpy.arange (range with float as steps) but with roundet output"
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

def inverse(value:bool|int|str) -> bool|int|str:
    "inverse a bool or int (or technically also a str) object"
    t = type(value) # type for final convertion
    val = bool(value)   # bool value so we don't need to handle every single variable type
    if val==False:  # inverse
        val=True
    else:
        val=False
	return t(val)   # return converted value

def timeit(func:function) -> function:
    "decorator for timing functions"
    def wrapper(*args, **kw) -> Any:
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