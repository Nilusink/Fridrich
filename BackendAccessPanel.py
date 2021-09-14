from fridrich.backend import Connection
from fridrich import bcolors
from socket import gaierror
from os import system
system('color')

if __name__ == '__main__':
    from traceback import format_exc    # imports for shell
    while True:
        try:
            c = Connection(debugmode='normal', host='fridrich')    # create connection instance
            break

        except gaierror:
            print(bcolors.FAIL+"Couldn't connect to Server: Getaddrinfo failed")
            input(bcolors.WARNING+'to try again hit enter\n')

    #w = wiki()  # create wiki instance
    print(bcolors.OKGREEN+'initialised Connections')

    def listFuncs() -> None:
        "list all the functions of fridrich.backend.Connection"
        print(bcolors.OKGREEN+'\nfunctions of Connection: '+bcolors.ENDC)  #return all functions of the two classes
        funcs = dir(Connection)
        for element in funcs:
            if not element.endswith('__'):
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

        except Exception:   # if error occures, try to execute the command with exec and if that failes again, return both errors
            trace = format_exc()
            try:
                exec(cmd)
            except Exception:
                print(bcolors.FAIL+format_exc()+bcolors.ENDC)
