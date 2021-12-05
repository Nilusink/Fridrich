"""
basically just a python prompt with a connection
already initialized (c)

Author: Nilusink
"""
from fridrich import backend
from sys import platform
from fridrich import *
import socket
import os

if platform == "win32":
    os.system("color")  # only for windows

if __name__ == '__main__':
    from traceback import format_exc    # imports for shell
    with backend.Connection(debug_mode=Off, host="0.0.0.0") as c:
        while True:
            hostname = input(ConsoleColors.ENDC+"host: ")
            try:
                c.server_ip = hostname  # assign ip / hostname
                break

            except socket.gaierror:
                print(ConsoleColors.FAIL+"Couldn't connect to Server: Getaddrinfo failed")
                input(ConsoleColors.WARNING+'to try again hit enter\n')

        print(ConsoleColors.OKGREEN+'initialised Connections')

        def list_funcs() -> None:
            """
            list all the functions of fridrich.backend.Connection
            """
            print(ConsoleColors.OKGREEN+'\nfunctions of Connection: '+ConsoleColors.ENDC)  # return all functions of the two classes
            funcs = dir(backend.Connection)
            for element in funcs:
                if not element.endswith('__'):
                    print('  - '+ConsoleColors.HEADER+element+ConsoleColors.ENDC)

        list_funcs()

        cmd = str()
        while True:  # shell for debugging
            try:
                cmd = input('>> ')  # take input command as string
                if cmd:
                    backend_access_panel_result_please_dont_name_your_variable_like_this = eval(cmd)   # execute the code
                    print(ConsoleColors.OKGREEN + str(backend_access_panel_result_please_dont_name_your_variable_like_this) + ConsoleColors.ENDC)    # print it

            except (Exception,):   # if error occurs, try to execute the command with exec and if that fails again, return both errors
                trace = format_exc()
                try:
                    exec(cmd)
                except (Exception,):
                    print(ConsoleColors.FAIL+format_exc()+ConsoleColors.ENDC)

