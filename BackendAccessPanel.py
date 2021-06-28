from modules.FridrichBackend import Connection

if __name__ == '__main__':
    from traceback import format_exc    # imports for shell

    c = Connection(mode='debug')    # create connection instance
    #w = wiki()  # create wiki instance
    print('initialised Connections')

    print('\n\nfunctions of Connection: ')  #return all functions of the two classes
    funcs = dir(Connection)
    for element in funcs:
        if not element.startswith('__'):
            print('  - '+element)

    # print('\nfunctions of wiki: ')
    # funcs = dir(wiki)
    # for element in funcs:
    #     if not element.startswith('__'):
    #         print('  - '+element)
    # print()

    while True: # shell for debugging
        try:
            cmd = input('>> ')  # take input command as string
            x = eval(cmd)   # execute the code
            if True:   # if vlue is returned
                print(x)    # print it

        except Exception:   # if error occures, return it
            print(format_exc())