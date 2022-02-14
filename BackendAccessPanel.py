"""
basically just a python prompt with a connection
already initialized (c)

Author:
Nilusink
"""
from traceback import format_exc
from sys import platform
import socket
import os

from fridrich.backend import Connection
from fridrich import ConsoleColors

if platform == "win32":
    os.system("color")  # only for windows

if __name__ == '__main__':
    with Connection(host="0.0.0.0") as c:
        while True:
            hostname: str = input(ConsoleColors.ENDC+"host: ")
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
            funcs = dir(Connection)
            for element in funcs:
                if not element.endswith('__'):
                    print('  - '+ConsoleColors.HEADER+element+ConsoleColors.ENDC)

        list_funcs()

        ###########################################################
        #                         Console                         #
        ###########################################################
        cmd: str
        while True:  # shell for debugging
            try:
                cmd = input('>> ')  # take input command as string
                if cmd == "help":
                    list_funcs()
                    continue

                elif cmd:
                    if "\\n" in cmd:
                        raise RuntimeError("No multiline commands allowed")

                    print(ConsoleColors.OKGREEN + str(eval(compile(cmd, "backend_command", "eval"))) + ConsoleColors.ENDC)    # execute the code and print the result

                else:
                    print(end="\r")

            except SystemExit:
                print(ConsoleColors.WARNING+"\nClosing connection...")
                break

            except SyntaxError:   # if error occurs, try to execute the command with exec and if that fails again, return the error
                trace = format_exc()
                try:
                    exec(compile(cmd, "backend_command", "exec"))

                except (Exception,):
                    print(trace)
                    continue

            except (Exception,):
                print(format_exc())
                continue

    print(ConsoleColors.OKGREEN+"Closed, good bye!\n"+ConsoleColors.ENDC)