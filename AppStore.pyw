"""
AppStore is used to download Apps from
the Fridrich server.
The apps available are unique to
every Fridrich server, since they are
saved locally.

Author: Nilusink
"""
from concurrent.futures import ThreadPoolExecutor, Future
from time import sleep
import threading
import os

from fridrich.backend import Connection
from server.new_types import FileVar
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from fridrich import *
import tkinter as tk
import json
import sys


def bytes_to(value_in_bytes: float, rnd: int | None = ...) -> str:
    """
    :param value_in_bytes: the value in bytes to convert
    :param rnd: number of digits to round to
    :return: formatted string
    """
    sizes = ["bytes", "KB", "MB", "GB", "TB"]
    now = int()
    while value_in_bytes > 1024:
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
    def __init__(self, c: Connection) -> None:
        """
        initialise the window
        :return: None
        """
        self.c = c

        self.info_line_length = 40
        try:
            temp = open("data/AppStore.config", 'r')
        except FileNotFoundError:
            temp = {}
        self.settings = FileVar(json.load(temp), "data/AppStore.config")

        # for threads
        self.threads = ThreadPoolExecutor()

        # tkinter
        self.root = tk.Tk()
        self.root.configure(bg="gray")
        self.root.title("Fridrich AppStore")
        self.root.bind("<Escape>", self.end)
        self.root.bind("<F5>", self.update_apps)
        self.root.protocol("WM_DELETE_WINDOW", self.end)
        self.root.bind("<Configure>", self.__resize)

        self.root.minsize(width=600, height=500)
        self.root.maxsize(width=600, height=500)

        #   login Frame
        self.loginFrame = tk.Frame(self.root, bg='black', width=600, height=700)

        # username label and button
        tk.Label(self.loginFrame, text='Username', font="Helvetica 50 bold", bg='black', fg='white').place(x=137, y=50)  # Username Label
        self.loginUsername = tk.Entry(self.loginFrame, width=20, font="Helvetica 25 bold")  # Username entry
        self.loginUsername.place(x=115, y=150)

        tk.Label(self.loginFrame, text='Password', font="Helvetica 50 bold", bg='black', fg='white').place(x=137, y=250)  # Password Label
        self.loginPassword = tk.Entry(self.loginFrame, width=20, font="Helvetica 25 bold", show='*')  # Password entry
        self.loginPassword.place(x=115, y=350)

        self.loginButton = tk.Button(self.loginFrame,   # button for login
                                     text='login', bg='black',
                                     fg='white', activeforeground='green',
                                     activebackground='black',
                                     relief=tk.FLAT,
                                     command=self.login,
                                     font="Helvetica 30"
                                     )
        self.loginButton.place(x=230, y=400)

        self.loginFrame.place(x=0, y=0, anchor='nw')

        self.root.bind("<Return>", self.login)  # bind Return to login

        # main frame
        self.main_frame = tk.Frame(self.root)

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(2, weight=1)

        self.side_menu = tk.Canvas(self.main_frame, bg="black", width=300)
        self.downloading_name = self.side_menu.create_text(10, self.main_frame.winfo_height()-80, text="Downloading: ", anchor=tk.NW, fill="white")
        self.pb = ttk.Progressbar(
            self.side_menu,
            orient='horizontal',
            mode='determinate',
            length=280
        )
        self.side_menu.grid(row=0, column=0, sticky=tk.NSEW)

        self.app_canvas = VerticalScrolledFrame(self.main_frame)
        self.app_canvas.grid(row=0, column=1, columnspan=2, sticky=tk.NSEW)
        self.add_app = tk.Button(self.app_canvas.interior, bg="lightgreen", text="+", font="Helvetica 30 bold", width=10, command=self.upload_app)

        self.app_info = tk.Canvas(self.main_frame, bg="white", width=400)
        self.info = self.app_info.create_text(10, 10, anchor=tk.NW, font="Helvetica 15")
        self.info_buttons = tk.Canvas(self.app_info)
        self.info_buttons.columnconfigure(0, weight=1)
        self.info_buttons.columnconfigure(1, weight=1)
        self.du_button = tk.Button(self.info_buttons, text="Download", bg="green", font="Helvetica 30 bold", relief=tk.FLAT)
        self.mod_button = tk.Button(self.info_buttons, text="Modify", bg="yellow", font="Helvetica 30 bold", relief=tk.FLAT)
        self.du_button.grid(column=0, row=0, sticky=tk.SW)
        self.app_info.grid(row=0, column=3, sticky=tk.NSEW)

        self.apps_items = list()

        self.u_height = 450
        self.u_width = 800

        self.window = tk.Toplevel()
        self.window.title("AppCreator")
        self.window.minsize(width=self.u_width, height=self.u_height)
        self.window.maxsize(width=self.u_width, height=self.u_height)
        self.window.protocol("WM_DELETE_WINDOW", self.__new_app_reset)
        self.window.bind("<Escape>", self.__new_app_reset)

        self.window.withdraw()
        self.root.focus_set()

        # create app
        # meta info
        self.app_name_frame = tk.Canvas(self.window, width=self.u_width, height=self.u_height, bg="grey20", bd=0, highlightthickness=0, relief=tk.RIDGE)
        self.app_name_frame.pack()

        tk.Button(self.app_name_frame, text="Cancel", font="Helvetica 15 bold", bg="grey20", fg="red", relief=tk.FLAT, command=self.__new_app_reset).place(x=00, y=self.u_height, anchor=tk.SW)
        tk.Button(self.app_name_frame, text="Next", font="Helvetica 15 bold", bg="grey20", fg="green", relief=tk.FLAT, command=self.__new_app_iter).place(x=self.u_width, y=self.u_height, anchor=tk.SE)

        tk.Label(self.app_name_frame, text="Add a new App", font=("Segoe Print", 50), bg="grey20", fg="white").place(x=self.u_width/2, y=60, anchor=tk.CENTER)

        self.new_app_info_label = tk.Label(self.app_name_frame, font=("Ink Free", 30), bg="grey20", fg="white", justify=tk.LEFT)
        self.new_app_info_label.place(x=30, y=100, anchor=tk.NW)

        self.new_app_entry_title = tk.Label(self.app_name_frame, text="Name", font="Helvetica 30 bold", bg="grey20", fg="white")
        self.new_app_entry_title.place(x=(self.u_width/2)-180, y=(self.u_height/2)-25, anchor=tk.CENTER)

        self.new_app_entry = ttk.Entry(self.app_name_frame, font=("Ink Free", 30), width=20)
        self.new_app_entry.place(x=self.u_width/2, y=(self.u_height/2)+25, anchor=tk.CENTER)

        self.new_app_text = tk.Text(self.app_name_frame, font=("Ink Free", 20), width=40, height=5)

        self.new_app_entry.bind("<Return>", self.__new_app_iter)

        # file info
        self.files_window = tk.Canvas(self.window, width=self.u_width, height=self.u_height, bg="grey20", bd=0, highlightthickness=0, relief=tk.RIDGE)

        tk.Label(self.files_window, text="Add a new App", font=("Segoe Print", 50), bg="grey20", fg="white").place(x=self.u_width/2, y=60, anchor=tk.CENTER)

        tk.Button(self.files_window, text="Cancel", font="Helvetica 15 bold", bg="grey20", fg="red", relief=tk.FLAT, command=self.__new_app_reset).place(x=00, y=self.u_height, anchor=tk.SW)
        tk.Button(self.files_window, text="Done", font="Helvetica 15 bold", bg="grey20", fg="green", relief=tk.FLAT, command=self.__new_app_iter).place(x=self.u_width, y=self.u_height, anchor=tk.SE)

        tk.Button(self.files_window, text="Select Files", font="Helvetica 20 bold", bg="grey20", fg="white", relief=tk.FLAT, command=self.__select_new_app_files).place(x=self.u_width/2, y=150, anchor=tk.CENTER)

        self.upload_files = tk.Label(self.files_window, font=("Ink Free", 30), bg="grey20", fg="white")
        self.upload_files.place(x=self.u_width/2, y=250, anchor=tk.CENTER)

        # configure app
        self.configure_window = tk.Canvas(self.window, width=self.u_width, height=self.u_height, bg="grey20", bd=0, highlightthickness=0, relief=tk.RIDGE)

        tk.Label(self.configure_window, text="Configure App", font=("Segoe Print", 50), bg="grey20", fg="white").place(x=self.u_width/2, y=60, anchor=tk.CENTER)

        tk.Button(self.configure_window, text="Cancel", font="Helvetica 15 bold", bg="grey20", fg="red", relief=tk.FLAT, command=self.__new_app_reset).place(x=00, y=self.u_height, anchor=tk.SW)
        tk.Button(self.configure_window, text="Done", font="Helvetica 15 bold", bg="grey20", fg="green", relief=tk.FLAT, command=self.__done_configure).place(x=self.u_width, y=self.u_height, anchor=tk.SE)

        tk.Label(self.configure_window, text="Name", font="Helvetica 20", bg="grey20", fg="white").place(x=30, y=150, anchor=tk.W)
        self.config_name_entry = ttk.Entry(self.configure_window, font=("Ink Free", 30), width=25)
        self.config_name_entry.place(x=self.u_width/2+50, y=150, anchor=tk.CENTER)

        tk.Label(self.configure_window, text="Version", font="Helvetica 20", bg="grey20", fg="white").place(x=30, y=200, anchor=tk.W)
        self.config_version_entry = ttk.Entry(self.configure_window, font=("Ink Free", 30), width=25)
        self.config_version_entry.place(x=self.u_width/2+50, y=200, anchor=tk.CENTER)

        tk.Label(self.configure_window, text="Info", font="Helvetica 20", bg="grey20", fg="white").place(x=30, y=260, anchor=tk.W)
        self.config_info_text = tk.Text(self.configure_window, font=("Ink Free", 30), width=25, height=3)
        self.config_info_text.place(x=self.u_width/2+50, y=240, anchor=tk.N)

        # Configure Files
        self.configure_files = tk.Canvas(self.window, width=self.u_width, height=self.u_height, bg="grey20", bd=0, highlightthickness=0, relief=tk.RIDGE)

        tk.Label(self.configure_files, text="Configure App", font=("Segoe Print", 50), bg="grey20", fg="white").place(x=self.u_width/2, y=60, anchor=tk.CENTER)

        tk.Button(self.configure_files, text="Cancel", font="Helvetica 15 bold", bg="grey20", fg="red", relief=tk.FLAT, command=self.__new_app_reset).place(x=00, y=self.u_height, anchor=tk.SW)
        tk.Button(self.configure_files, text="Done", font="Helvetica 15 bold", bg="grey20", fg="green", relief=tk.FLAT, command=self.__done_configure).place(x=self.u_width, y=self.u_height, anchor=tk.SE)

        tk.Button(self.configure_files, text="Select Files", font="Helvetica 20 bold", bg="grey20", fg="white", relief=tk.FLAT, command=self.__configure_open_files).place(x=self.u_width/2, y=150, anchor=tk.CENTER)

        self.configure_app_files = tk.Canvas(self.configure_files, bg="red")
        self.configure_app_files.place(x=self.u_width/2, y=200, anchor=tk.N)

        # new app
        self.__app_name = str()
        self.__app_version = None
        self.__app_info = None
        self.__upload_files = tuple()

        self.__app_done = False

        # configure app
        self.__configuring = dict()
        self.__selected_files = False
        self.__update_files = list()

        # for updating progressbar
        self.ud = self.up_down_updater = self.update_update(thread=True, loop=True)

    def login(self, *_args) -> None:
        """
        try to login with username and password
        """
        name = self.loginUsername.get()
        pwd = self.loginPassword.get()

        if not self.c.auth(name, pwd):
            messagebox.showerror('Error', 'Invalid Username/Password')
            return

        print(self.c)
        sec = self.c.get_sec_clearance()
        print(sec)
        if sec != 'user':
            messagebox.showerror('Error', f'Account is not user ({sec})')
            return

        self.root.bind("<Return>", tk.DISABLED)

        self.root.minsize(width=1500, height=500)
        self.root.maxsize(width=60000, height=60000)  # "disable" the maxsize
        self.loginFrame.place_forget()
        self.main_frame.pack(expand=1, fill=tk.BOTH)

        self.update_apps()

    def __resize(self, _event=None) -> None:
        """
        configure the placement of some things
        """
        self.pb.place_forget()
        self.pb.place(x=10, y=self.main_frame.winfo_height()-30, anchor=tk.NW)
        self.side_menu.coords(self.downloading_name, 10, self.main_frame.winfo_height()-80)

    def __new_app_iter(self, _event=None) -> None:
        """
        iter names and stuff
        """
        if not self.__app_name:
            tmp = self.new_app_entry.get()
            if len(tmp) <= 2:
                messagebox.showinfo("Info", "App name must at least be 3 Charters")
                return
            self.__app_name = tmp
            self.new_app_entry.delete(0, tk.END)
            self.new_app_info_label["text"] = f"App Name: {tmp}"
            self.new_app_entry_title["text"] = "Version"

        elif self.__app_version is None:
            tmp = self.new_app_entry.get()
            self.__app_version = tmp
            self.new_app_entry.delete(0, tk.END)
            self.new_app_info_label["text"] += f"\nApp Version: {tmp}"
            self.new_app_entry_title["text"] = "Info"
            self.new_app_entry.place_forget()
            self.new_app_text.place(x=self.u_width/2, y=(self.u_height/2)+120, anchor=tk.CENTER)
            self.new_app_entry_title.place(x=(self.u_width/2)-250, y=(self.u_height/2)+10, anchor=tk.CENTER)

        elif self.__app_info is None:
            tmp = self.new_app_text.get("1.0", tk.END)
            self.__app_info = tmp
            self.new_app_entry_title.place_forget()
            self.new_app_text.place_forget()
            self.new_app_info_label["text"] += "\nInfo:\n"+'\n'.join(split_string(tmp, 30))

        elif not self.__app_done:
            self.app_name_frame.pack_forget()
            self.files_window.pack()
            self.__app_done = True

        else:
            self.threads.submit(self.c.create_app, app_name=self.__app_name, app_version=self.__app_version, app_info=self.__app_info, files=self.__upload_files)
            self.__new_app_reset()

    def __select_new_app_files(self, _event=None) -> None:
        """
        Select the files that should be uploaded to the appstore
        """
        self.__upload_files = filedialog.askopenfilenames(parent=self.window, title="Choose Archives to upload", filetypes=[('Archives', '*.zip')])
        self.upload_files["text"] = "\n".join([file.split("/")[-1] for file in self.__upload_files])

    def __new_app_reset(self, _event=None) -> None:
        """
        reset all variables for App Configurer
        """
        self.__app_name = str()
        self.__app_version = str()
        self.__app_info = str()
        self.__upload_files = tuple()

        self.__app_done = False
        self.__selected_files = False

        self.new_app_entry.delete(0, tk.END)
        self.new_app_text.delete("1.0", tk.END)

        self.new_app_info_label["text"] = str()
        self.new_app_entry_title["text"] = "Name"

        self.mod_button["state"] = tk.NORMAL
        self.add_app["state"] = tk.NORMAL

        self.__configuring = dict()

        self.new_app_text.place_forget()
        self.new_app_entry.place(x=self.u_width/2, y=(self.u_height/2)+25, anchor=tk.CENTER)

        self.files_window.pack_forget()
        self.configure_window.pack_forget()
        self.configure_files.pack_forget()
        self.app_name_frame.pack()
        self.window.withdraw()

        self.add_app["state"] = tk.NORMAL

    def __done_configure(self, _event=None) -> None:
        """
        called by a button when done configuring
        """
        if not self.__selected_files:
            self.__app_name = self.config_name_entry.get()
            self.__app_version = self.config_version_entry.get()
            self.__app_info = self.config_info_text.get(0.0, tk.END).rstrip("\n")
            self.configure_window.pack_forget()
            self.configure_files.pack()
            self.__update_files = [{"name": file, "tag": "keep", "dir": None} for file in self.__configuring["files"]]
            self.__selected_files = True
            self.update_files_list()
            return

        self.c.modify_app(self.__configuring["name"], self.__app_name, self.__app_version, self.__app_info,
                          files=[file["dir"] for file in self.__update_files if file["tag"] in ("new", "overwrite")],
                          to_delete=[file["name"] for file in self.__update_files if file["tag"] == "delete"])

        self.mod_button["state"] = tk.NORMAL
        self.__new_app_reset()
        self.update_apps()
        self.select_app("")

    def __remove_open_file(self, element: dict) -> None:
        """
        removes a file if its new or else keeps in dict but with "remove"
        :param element: the element to remove
        """
        match element["tag"]:
            case "new":
                self.__update_files.remove(element)
                self.update_files_list()
                return
            case "delete":
                element["tag"] = "keep"
            case "overwrite":
                element["tag"] = "keep"
            case "keep":
                element["tag"] = "delete"
            case _:
                raise ValueError(f"invalid tag for file: {element['tag']}")

        index = self.__update_files.index(element)
        self.__update_files[index] = element
        self.update_files_list()

    def __configure_open_files(self) -> None:
        """
        open files
        """
        files = list(filedialog.askopenfilenames(parent=self.window, title="Choose Archives to upload", filetypes=[('Archives', '*.zip')]))
        filenames = [file.split("/")[-1] for file in files]

        for file in self.__update_files:  # check if file is already in list
            if file["name"] in filenames:
                f_index = filenames.index(file["name"])
                file["tag"] = "overwrite"
                file["dir"] = files[f_index]

                filenames.pop(f_index)
                files.pop(f_index)
            else:
                print(file["name"], filenames)

        for element in files:  # if not append as new element
            self.__update_files.append({
                "name": filenames[files.index(element)],
                "tag": "new",
                "dir": element
            })
        self.update_files_list()

    def update_files_list(self) -> None:
        """
        update the files list when configuring app
        """
        for element in self.configure_app_files.winfo_children():
            element.grid_forget()

        for file in self.__update_files:
            curr_row = self.__update_files.index(file)
            tk.Label(self.configure_app_files, text=file["name"], font=("Ink Free", 20), bg="grey20", fg="white").grid(row=curr_row, column=0, sticky=tk.NSEW)
            match file["tag"]:
                case "keep":
                    tmp = tk.Button(self.configure_app_files, text="keep", font=("Ink Free", 20), bg="grey20", fg="white", relief=tk.FLAT)
                case "overwrite":
                    tmp = tk.Button(self.configure_app_files, text="overwrite", font=("Ink Free", 20), bg="grey20", fg="yellow", relief=tk.FLAT)
                case "new":
                    tmp = tk.Button(self.configure_app_files, text="new", font=("Ink Free", 20), bg="grey20", fg="green", relief=tk.FLAT)
                case "delete":
                    tmp = tk.Button(self.configure_app_files, text="delete", font=("Ink Free", 20), bg="grey20", fg="red", relief=tk.FLAT)
                case _:
                    raise ValueError(f"Invalid tag: {file['tag']}")

            tmp["command"] = lambda _e=None: self.__remove_open_file(file)
            tmp.grid(row=curr_row, column=1, sticky=tk.NSEW)

    def configure_app(self, app: dict) -> None:
        """
        Configure an app
        :param app: a dictionary with all app info (c.get_results())
        :return: Nothing
        """
        self.__configuring = app

        self.window.deiconify()
        self.mod_button["state"] = tk.DISABLED
        self.add_app["state"] = tk.DISABLED
        self.app_name_frame.pack_forget()
        self.configure_window.pack()

        self.config_name_entry.delete(0, tk.END)
        self.config_version_entry.delete(0, tk.END)
        self.config_info_text.delete(0.0, tk.END)
        self.config_name_entry.insert(0, app["name"])
        self.config_version_entry.insert(0, app["version"])
        self.config_info_text.insert(0.0, app["info"].lstrip(" ").replace("\\\\n", "\n"))

        self.__resize()

    def update_update(self, _event=None, thread: bool | None = False, loop: bool | None = False) -> Future | None:
        """
        update the download/upload progressbar and label
        :param _event: trash variable if called by tkinter events
        :param thread: if true runs as thread
        :param loop: if true runs in a endless loop
        """
        if thread:
            return self.threads.submit(self.update_update, thread=False, loop=loop)
        self.pb["value"] = int(self.c.load_progress*100)
        self.side_menu.itemconfig(self.downloading_name, text=self.c.load_state+"\n"+self.c.load_program)

        while loop:
            self.pb["value"] = int(self.c.load_progress*100)
            self.side_menu.itemconfig(self.downloading_name, text=self.c.load_state+"\n"+self.c.load_program)
            sleep(.1)

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
        self.threads.shutdown(wait=False)
        self.c.end()
        self.root.destroy()
        if len(threading.enumerate()) > 1:
            os.kill(os.getpid(), 9)  # if threads are running, terminate the process
        sys.exit(0)

    def update_apps(self, _event=None) -> None:
        """
        update the app-list / versions
        """
        for element in self.app_canvas.interior.winfo_children():
            element.pack_forget()

        i = 0
        for app in self.c.get_apps():
            tmp = tk.Canvas(self.app_canvas.interior, bg="gray25", height=80)
            tmp.create_text(20, 20, text=f'{app["name"]}', fill="white", font="Helvetica 30 bold", anchor=tk.NW)
            tmp.bind("<Button-1>", lambda _e, n=app["name"]: self.select_app(n))
            tmp.pack(fill=tk.BOTH)
            self.apps_items.append(tmp)

            i += 1

        self.add_app.pack()

    def upload_app(self, _event=None) -> None:
        """
        upload an app to the appstore
        """
        self.window.deiconify()
        self.add_app["state"] = tk.DISABLED
        self.mod_button["state"] = tk.DISABLED
        self.__resize()

    def download_app(self, app_name, directory: str | None = ...) -> None:
        """
        download a app from the server
        :param app_name: the app to download
        :param directory: if given, doesn't ask for directory to download
        """
        self.du_button["bg"] = "grey"
        self.du_button["state"] = "disabled"
        apps = self.c.get_apps()
        app = {app["name"]: app for app in apps}[app_name]

        if directory is ...:
            directory = filedialog.askdirectory()
        self.threads.submit(self.c.download_app, app_name, directory)

        temp = self.settings["installed_programs"]
        temp[app_name] = {
            "version": app["version"],
            "path": directory+'/'
        }
        self.settings["installed_programs"] = temp
        self.select_app(app_name, apps)

    def select_app(self, app_name, apps: list | None = ...) -> None:
        """
        :param app_name: the name of the app to be selected
        :param apps: give alternative apps
        """
        if app_name == "":
            self.app_info.itemconfig(self.info, text="")
            self.info_buttons.place_forget()
            return

        installed_apps = self.settings["installed_programs"]
        if apps is ...:
            apps = self.c.get_apps()
        app = {app["name"]: app for app in apps}[app_name]

        app_version = None
        if app["name"] in installed_apps:
            app_version = installed_apps[app["name"]]["version"]

        newline = '\n'
        rep = ("\\\\n", "\n")
        info_string = f"""Version:
{app['version']}{newline+newline+"Installed:"+newline+app_version if app_version else ""}

Size:
{bytes_to(app['size'], 2)}

Files:
{newline.join(app['files'])}

Info:
{newline.join(split_string(app["info"], self.info_line_length)).lstrip(" ").replace(*rep)}

by {app["publisher"]}
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

        if self.c.username == app["publisher"]:
            self.mod_button["command"] = lambda _e=None: self.configure_app(app)
            self.mod_button.grid(column=1, row=0, sticky=tk.SW)
        else:
            self.mod_button.grid_forget()

        self.info_buttons.place(x=200, y=lines*25, anchor=tk.N)


def main() -> None:
    """
    main program
    """
    c = Connection(debug_mode=Off, host="192.168.10.15")
    w = Window(c)
    w.run()


if __name__ == '__main__':
    main()
