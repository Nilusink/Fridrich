"""
basically just a python prompt with a connection
already initialized (c)

Author: Nilusink
"""
from sys import platform
import socket
import os

from fridrich.backend import Connection
from fridrich import ConsoleColors

if platform == "win32":
    os.system("color")  # only for windows

if __name__ == '__main__':
    from traceback import format_exc    # imports for shell
    with Connection(host="0.0.0.0") as c:
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
            funcs = dir(Connection)
            for element in funcs:
                if not element.endswith('__'):
                    print('  - '+ConsoleColors.HEADER+element+ConsoleColors.ENDC)

        list_funcs()

        cmd = str()
        while True:  # shell for debugging
            try:
                cmd = input('>> ')  # take input command as string
                if cmd:
                    if "\\n" in cmd:
                        raise RuntimeError("No multiline commands allowed")
                    backend_access_panel_result_please_dont_name_your_variable_like_this = eval(compile(cmd, "backend_command", "eval"))   # execute the code
                    print(ConsoleColors.OKGREEN + str(backend_access_panel_result_please_dont_name_your_variable_like_this) + ConsoleColors.ENDC)    # print it

            except SyntaxError:   # if error occurs, try to execute the command with exec and if that fails again, return the error
                trace = format_exc()
                try:
                    exec(compile(cmd, "backend_command", "exec"))

                except (Exception,):
                    continue

            except (Exception,):
                continue
