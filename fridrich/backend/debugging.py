"""
Debugging helper for backend

Author:
Nilusink
"""
from typing import Callable, Tuple, Any
from fridrich import ConsoleColors
from traceback import format_exc
import time
import os


class Debugger:
    """
    functions for advanced debugging
    """
    total_title_length: int = 60

    def __init__(self, outfile: str, file_mode: str = "a") -> None:
        """
        :param outfile: the file to save the error logs to
        :param file_mode: should be "w" or "a" (FileIO write mode)
        """
        self.__outfile = outfile
        self.__file_mode = file_mode

        # check if the directory to save in already exists
        direc = os.path.split(self.__outfile)[0]
        if not os.path.isdir(direc):
            os.mkdir(direc)

        with open(self.__outfile, file_mode) as out:
            date = time.strftime("%Y.%m.%d - %H:%M:%S")
            side1, side2 = self.__calculate_sides(self.total_title_length, len(date))

            # create "heading" every time the program restarts
            out.write(f"\n\n\n\n{'#'*self.total_title_length}\n#{' '*side1}{date}"
                      f"{' '*side2}#\n{'#'*self.total_title_length}")

        print(f"File for debugging: \"{self.__outfile}\"")

    @staticmethod
    def __calculate_sides(total_length: int, string_length: int, spaces: int | None = 2) -> Tuple[int, int]:
        """
        used for creating more readable errors

        :param total_length: the total length of the finished string
        :param string_length: the length of the string to insert
        :param spaces: the amount of spaces planned between "#" and the inserted string
        """
        if total_length - string_length - spaces % 2 == 0:
            s1 = s2 = (total_length - string_length - spaces) // 2

        else:
            s1 = (total_length - string_length - spaces) // 2
            s2 = s1 + 1

        return s1, s2

    def catch_and_write(self, raise_error: bool = False, print_traceback: bool = False) -> Callable:
        """
        (decorator)
        catch tracebacks and write them into a file

        :param raise_error: defines if the caught error should be raised (still write to file and print if enabled)
        :param print_traceback: defines if the caught error should be printed
        """
        def decorator(function: Callable) -> Callable:
            def wrapper(*args, **kwargs) -> Any:
                try:
                    return function(*args, **kwargs)

                except (Exception,):
                    title = f"ERROR IN FUNCTION \"{function.__name__}\""
                    end = f"END OF EXCEPTION"
                    h1, h2 = self.__calculate_sides(self.total_title_length, len(title))
                    e1, e2 = self.__calculate_sides(self.total_title_length, len(end))

                    trace = f"\n\n\n{h1*'#'} {title} {h2*'#'}\n\n{format_exc()}\n\n{e1*'#'} {end} {e2*'#'}\n\n\n"
                    try:
                        with open(self.__outfile, self.__file_mode) as out:
                            out.write(trace)

                        if print_traceback:
                            print(f"{ConsoleColors.FAIL}{trace}{ConsoleColors.ENDC}")

                    except NameError:
                        return

                    if raise_error:
                        raise
                    print("caught traceback")

            return wrapper
        return decorator
