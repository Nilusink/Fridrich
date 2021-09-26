#! C:\users\Niclas\AppData\local\programs\Python\Python310\python.exe
from concurrent.futures import ThreadPoolExecutor
from fridrich.backend import Connection
from fridrich.new_types import FileVar
from tkinter import filedialog
from tkinter import ttk
from fridrich import *
import tkinter as tk
import json


def bytes_to(value_in_bytes: float, rnd: int | None = ...) -> str:
    """
    :param value_in_bytes: the value in bytes to convert
    :param rnd: number of digits to round to
    :return: formatted string
    """
    sizes = ["bytes", "KB", "MB", "GB", "TB"]
    now = int()
    while len(str(value_in_bytes).split('.')[0]) > 3:
        value_in_bytes /= 1024
        now += 1

    if rnd is not ...:
        value_in_bytes = round(value_in_bytes, rnd)

    return f"{value_in_bytes} {sizes[now]}"


def split_string(string: str, length: int, separator: str | None = " ") -> list:
    """
    :param string: input string
    :param length: max length to split a string
    :param separator: where to split the string
    :return: list with elements
    """
    parts = string.split(separator)
    out = list()
    now = str()
    for element in parts:
        element = element.strip()
        if len(now) > length:
            raise ValueError(f"cannot separate string at part {now} (too long)")

        elif len(now)+len(element)+1 > length:
            out.append(now)
            now = element
        else:
            now += separator+element
    out.append(now)
    return out


class VerticalScrolledFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!

    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling
    """
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        # create a canvas object and a vertical scrollbar for scrolling it
        v_scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        v_scrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                           yscrollcommand=v_scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        v_scrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(_event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(_event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)


class Window:
    """
    main window of the Program
    """
    def __init__(self) -> None:
        """
        initialise the window
        :return: None
        """
        self.info_line_length = 40
        try:
            temp = open("data/AppStore.config", 'r')
        except FileNotFoundError:
            temp = {}
        self.settings = FileVar(json.load(temp), "data/AppStore.config")

        self.root = tk.Tk()
        self.root.configure(bg="gray")
        self.root.title("Fridrich AppStore")
        self.root.minsize(width=1500, height=500)
        self.root.bind("<Escape>", self.end)
        self.root.protocol("WM_DELETE_WINDOW", self.end)
        self.root.bind("<Configure>", self.resize)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        self.c = Connection()
        self.c.auth("Hurensohn3", "13102502")
        if not self.c:
            raise AuthError("Not Authenticated")
        self.side_menu = tk.Canvas(self.root, bg="black", width=300)
        self.downloading_name = self.side_menu.create_text(10, self.root.winfo_height()-80, text="Downloading: ", anchor=tk.NW, fill="white")
        self.pb = ttk.Progressbar(
            self.side_menu,
            orient='horizontal',
            mode='determinate',
            length=280
        )
        self.side_menu.grid(row=0, column=0, sticky=tk.NSEW)

        self.app_canvas = VerticalScrolledFrame(self.root)
        self.app_canvas.grid(row=0, column=1, columnspan=2, sticky=tk.NSEW)

        self.app_info = tk.Canvas(self.root, bg="white", width=400)
        self.info = self.app_info.create_text(10, 10, anchor=tk.NW, font="Helvetica 15")
        self.du_button = tk.Button(self.app_info, text="Download", bg="green", font="Helvetica 30 bold", relief=tk.FLAT)
        self.app_info.grid(row=0, column=3, sticky=tk.NSEW)

        self.apps_items = list()

        self.update_apps()

    def resize(self, _event=None) -> None:
        """
        configure the placement of some things
        """
        self.pb.place_forget()
        self.pb.place(x=10, y=self.root.winfo_height()-30, anchor=tk.NW)
        self.side_menu.coords(self.downloading_name, 10, self.root.winfo_height()-80)

    def run(self) -> None:
        """
        run the mainloop
        """
        self.root.mainloop()

    def end(self, _event: tk.Event | None = ...) -> None:
        """
        call to end connection with server and close window
        :param _event: so it can be called by tkinter events
        :return: None
        """
        self.c.end()
        self.root.destroy()

    def update_apps(self) -> None:
        """
        update the app-list / versions
        """
        for element in self.apps_items:
            element.grid_forget()

        i = 0
        for app in self.c.get_apps():
            tmp = tk.Canvas(self.app_canvas.interior, bg="gray25", height=80)
            tmp.create_text(20, 20, text=f'{app["name"]}', fill="white", font="Helvetica 30 bold", anchor=tk.NW)
            tmp.bind("<Button-1>", lambda _e: self.select_app(app["name"]))
            tmp.pack(fill=tk.BOTH)
            self.apps_items.append(tmp)

            i += 1

    def upload_app(self) -> None:
        """
        upload an app to the appstore
        """

    def download_app(self, app_name, directory: str | None = ...) -> None:
        """
        download a app from the server
        :param app_name: the app to download
        :param directory: if given, doesn't ask for directory to download
        """
        self.du_button["bg"] = "grey"
        self.du_button["state"] = "disabled"
        app = {app["name"]: app for app in self.c.get_apps()}[app_name]

        if directory is ...:
            directory = filedialog.askdirectory()
        ex = ThreadPoolExecutor(max_workers=1)
        x = ex.submit(self.c.download_app, app_name, directory)

        while x.running():
            self.pb["value"] = int(self.c.download_progress*100)
            self.side_menu.itemconfig(self.downloading_name, text="Downloading:\n"+self.c.download_program)
            self.root.update()
        self.pb["value"] = 0
        self.side_menu.itemconfig(self.downloading_name, text="Downloading:")

        temp = self.settings["installed_programs"]
        temp[app_name] = {
            "version": app["version"],
            "path": directory+'/'
        }
        self.settings["installed_programs"] = temp
        self.select_app(app_name)

    def select_app(self, app_name) -> None:
        """
        :param app_name: the name of the app to be selected
        """
        installed_apps = self.settings["installed_programs"]
        app = {app["name"]: app for app in self.c.get_apps()}[app_name]

        app_version = None
        if app["name"] in installed_apps:
            app_version = installed_apps[app["name"]]["version"]

        newline = '\n'
        info_string = f"""Version:
{app['version']}{newline+newline+"Installed:"+newline+app_version if app_version else ""}

Size:
{bytes_to(app['size'], 2)}

Files:
{newline.join(app['files'])}

Info:
{newline.join(split_string(app["info"], self.info_line_length)).lstrip(" ")}
"""
        lines = info_string.count("\n")
        self.app_info.itemconfig(self.info, text=info_string)
        self.du_button["state"] = "normal"
        self.du_button["bg"] = "green"
        self.du_button["text"] = "Download"
        self.du_button["command"] = lambda _e=None: self.download_app(app_name)

        if app_version and app_version != app["version"]:
            self.du_button["text"] = "Update"
            self.du_button["command"] = lambda _e=None: self.download_app(app_name, directory=installed_apps[app["name"]]["path"])

        elif app_version and app_version == app["version"]:
            self.du_button["text"] = "Newest"
            self.du_button["bg"] = "grey"
            self.du_button["state"] = "disabled"

        self.du_button.place(x=80, y=lines*25, anchor=tk.NW)


def main() -> None:
    """
    main program
    """
    w = Window()
    w.run()


if __name__ == '__main__':
    main()
