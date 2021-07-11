from fridrich.FridrichBackend import Connection
from fridrich import bcolors
from os import system
system('color')

if __name__ == '__main__':
    from traceback import format_exc    # imports for shell

    c = Connection(debugmode='full')    # create connection instance
    #w = wiki()  # create wiki instance
    print(bcolors.OKGREEN+'initialised Connections')

    def listFuncs():
        print(bcolors.OKGREEN+'\nfunctions of Connection: '+bcolors.ENDC)  #return all functions of the two classes
        funcs = dir(Connection)
        for element in funcs:
            if not element.startswith('__'):
                print('  - '+bcolors.HEADER+element+bcolors.ENDC)

    # print('\nfunctions of wiki: ')
    # funcs = dir(wiki)
    # for element in funcs:
    #     if not element.startswith('__'):
    #         print('  - '+element)
    # print()

    listFuncs()

    while True: # shell for debugging
        try:
            cmd = input('>> ')  # take input command as string
            if cmd:
                x = eval(cmd)   # execute the code
                print(bcolors.OKGREEN+str(x)+bcolors.ENDC)    # print it

        except Exception:   # if error occures, return it
            print(bcolors.FAIL+format_exc()+bcolors.ENDC)
