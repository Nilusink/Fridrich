"""
GUI program used to manage Accounts

Author:
Nilusink
"""
from contextlib import suppress
from tkinter import messagebox
import tkinter as tk

# local imports
from fridrich.backend import Connection

secEquals: tuple = ('admin', 'bot', 'user', 'guest')    # for sorting the users


def sort_user_list(lst: list, flag='sec') -> list:
    """
    return a sorted list by "sec" | "Name" | "pwd"
    """
    def sorter(element) -> int:
        element = element[flag]
        if element in secEquals:
            return secEquals.index(element)
        return len(secEquals)

    values = sorted(sorted(lst, key=lambda x: x['Name']), key=sorter)
    return list(values)


class Window(Connection):
    """
    class for the main window
    """
    def __init__(self, host: str) -> None:
        """
        ConnectionInstance: instance of fridirch.FridrichBackend.Connection
        """
        super().__init__(host=host)
        # variable definitions
        self.userEs: list = []
        self.users: list = []
        self.onlineUsers: list = []
        self.default_pwd: str = "<set>"
        self.host = host

        # tkinter
        self.root = tk.Tk()
        self.root.title('Fridrich AdminTool')
        
        self.root.minsize(width=600, height=500)
        self.root.maxsize(width=600, height=500)

        self.root.bind('<Escape>', self._end)
        self.root.bind('<F5>', self.update)

        #   login Frame
        self.loginFrame = tk.Frame(self.root, bg='black', width=600, height=700)

        # username label and button
        tk.Label(self.loginFrame, text='Username', font="Helvetica 50 bold",
                 bg='black', fg='white').place(x=137, y=50)  # Username Label
        self.loginUsername = tk.Entry(self.loginFrame, width=20, font="Helvetica 25 bold")  # Username entry
        self.loginUsername.place(x=115, y=150)
        self.loginUsername.insert(0, 'Admin')

        tk.Label(self.loginFrame, text='Password', font="Helvetica 50 bold",
                 bg='black', fg='white').place(x=137, y=250)  # Password Label
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

        self.root.bind("<Return>", self.login)  # bind Return to log in

        # mainframe
        self.mainFrame = tk.Frame(self.root, bg='grey', width=800, height=700)

        self.refreshButton = tk.Button(self.mainFrame, text='Refresh',  # button for refreshing
                                       command=self.refresh, background='grey',
                                       fg='white', width=10,
                                       relief=tk.FLAT,
                                       font="Helvetica 15"
                                       )
        
        self.updateButton = tk.Button(self.mainFrame, text='Set',   # button for setting new usernames/passwords
                                      command=self.update, background='grey',
                                      fg='white', width=10,
                                      relief=tk.FLAT,
                                      font="Helvetica 15"
                                      )
        
        self.addButton = tk.Button(self.mainFrame, text='Add',   # button for setting new usernames/passwords
                                   command=self.add_user, background='green',
                                   fg='white', width=10,
                                   relief=tk.FLAT,
                                   font="Helvetica 15"
                                   )
        
        self.delButton = tk.Button(self.mainFrame, text='ResetLogins',   # button for setting new usernames/passwords
                                   command=self.reset_logins, background='red',
                                   fg='white', width=10,
                                   relief=tk.RAISED,
                                   font="Helvetica 15"
                                   )
        
        if self == 'CantConnect':
            messagebox.showerror('Fatal Error', 'Not Connected to Fridrich Wifi! (attempt to connect failed)')
            exit()

        elif self == 'ServerNotReachable':
            messagebox.showerror('Fatal Error', 'Cant reach Fridrich Server!')
            exit()

    def run(self) -> None:
        """
        start tkinter.root.mainloop
        """
        self.root.mainloop()

    def login(self, *_args) -> None:
        """
        try to log in with username and password
        """
        name = self.loginUsername.get()
        pwd = self.loginPassword.get()

        if not self.auth(name, pwd):
            messagebox.showerror('Error', 'Invalid Username/Password')
            return

        print(self)
        sec: str = self.get_sec_clearance()
        print(sec)
        if sec != 'admin':
            messagebox.showerror('Error', f'Account is not admin ({sec})')
            return

        self.root.bind("<Return>", tk.DISABLED)

        self.loginFrame.place_forget()
        self.mainFrame.place(x=0, y=0, anchor='nw')

        self.refresh()
    
    def refresh(self) -> None:
        """
        refresh the window
        """
        users = self.admin_get_users(wait=True)
        o_users = self.get_online_users(wait=True)
        self.send()

        self.users = sort_user_list(users.result)
        self.onlineUsers = o_users.result

        for element in self.userEs:
            with suppress(IndexError):
                element[0].place_forget()
                element[1].place_forget()
                element[2].place_forget()
                element[3].place_forget()

        self.userEs = list()
        i = int()
        for i, user in enumerate(self.users):
            self.userEs.append((
                tk.Entry(self.mainFrame, width=20, font="Helvetica 15 bold"),
                tk.Entry(self.mainFrame, width=20, font="Helvetica 15 bold"),
                tk.Entry(self.mainFrame, width=20, font="Helvetica 15 bold"),
                tk.Button(self.mainFrame, width=1, font="Helvetica 10 bold", text='-',
                          bg='red', command=lambda e=None, name=user['Name']: self.rem_user(name))
                         ))

            self.userEs[-1][0].delete(0, 'end')
            self.userEs[-1][1].delete(0, 'end')
            self.userEs[-1][2].delete(0, 'end')
            self.userEs[-1][0].insert(0, user['Name'])
            self.userEs[-1][1].insert(0, self.default_pwd)
            self.userEs[-1][2].insert(0, user['sec'] if 'sec' in user else '')
            self.userEs[-1][0].place(x=50, y=i*50+10)
            self.userEs[-1][1].place(x=300, y=i*50+10)
            self.userEs[-1][2].place(x=550, y=i*50+10)

            if user['Name'].lower() != 'admin':
                self.userEs[-1][3].place(x=10,  y=i*50+10)
            else:
                self.userEs[-1][0].config(state=tk.DISABLED)
                self.userEs[-1][2].config(state=tk.DISABLED)
        
        user_num = {user: self.onlineUsers.count(user) for user in self.onlineUsers}
        is_in = list()
        not_in = int()

        j = int()
        for j, element in enumerate(self.onlineUsers):
            if element not in is_in:
                self.userEs.append((
                    tk.Label(self.mainFrame, width=18, font="Helvetica 15 bold", text='Name:', bg='grey', fg='white'),
                    tk.Label(self.mainFrame, width=18, font="Helvetica 15 bold", text=element, bg='grey', fg='white'),
                    tk.Label(self.mainFrame, width=18, font="Helvetica 15 bold", text='Count: '+str(user_num[element]),
                             bg='grey', fg='white'),
                    tk.Button(self.mainFrame, width=3, text="X", bg="red", relief=tk.FLAT,
                              command=lambda e=None, x=element: self.kick_a_user(x))
                ))

                is_in.append(element)

                self.userEs[-1][0].place(x=50, y=(i+j+3-not_in)*50+10)
                self.userEs[-1][1].place(x=300, y=(i+j+3-not_in)*50+10)
                self.userEs[-1][2].place(x=550, y=(i+j+3-not_in)*50+10)
                self.userEs[-1][3].place(x=750, y=(i+j+3-not_in)*50+11)

            else:
                not_in += 1
                
        new_window_height = (i+j+2-not_in)*50+100
        new_window_height = new_window_height if new_window_height < 1000 else 1000
        self.root.maxsize(width=800, height=new_window_height)
        self.root.minsize(width=800, height=new_window_height)
        self.mainFrame.config(height=new_window_height)

        self.delButton.place(x=350, y=(i+2)*50+10)

        self.refreshButton.place(x=50, y=(i+1)*50)
        self.addButton.place(x=350, y=(i+1)*50)
        self.updateButton.place(x=650, y=(i+1)*50)

        self.root.update()
    
    def update(self, *_args) -> None:
        """
        update the variables
        """
        for i in range(len(self.userEs)):
            try:
                name = self.userEs[i][0].get()
                pwd = self.userEs[i][1].get()
                sec = self.userEs[i][2].get()

                o_name = self.users[i]['Name']
                o_pwd = self.users[i]['pwd']
                o_sec = self.users[i]['sec'] if 'sec' in self.users[i] else ''

                try:
                    if name != o_name and name:
                        self.admin_set_username(o_name, name, wait=True)
                    
                    if pwd != o_pwd and pwd and pwd != self.default_pwd:
                        self.admin_set_password(name, pwd, wait=True)
                    
                    if sec != o_sec and sec:
                        self.admin_set_security(name, sec, wait=True)

                    with suppress(ValueError):
                        self.send()

                except NameError:
                    messagebox.showerror('Error', 'Name already exists')

            except AttributeError:
                break
        self.refresh()

    def rem_user(self, user: str) -> None:
        """
        remove user
        """
        self.admin_remove_user(user)
        self.update()

    def add_user(self) -> None:
        """
        add a new user
        """
        self.update()
        try:
            self.admin_add_user('new_user', 'new_password', 'None')
            self.update()

        except NameError:
            messagebox.showerror('Error', f'User with name "{""}" already exists')

    def reset_logins(self, _event=None) -> None:
        """
        reset all logins
        """
        global w
        ans = messagebox.askyesno('Confirm', 'Clear all users (logout)')
        if ans:
            with suppress(ConnectionAbortedError):
                self.admin_reset_logins()
                self.end(revive=True)

            w.root.destroy()
            w = Window(host=self.host)

    def kick_a_user(self, username: str) -> None:
        """
        kick one user
        """
        print(f"kicking {username}")
        self.kick_user(username, wait=False)
        self.update()

    def _end(self, *_args) -> None:
        """
        end connection to fridrich and destroy the tkinter.root
        """
        try:
            self.root.destroy()

        except (Exception,):
            return


if __name__ == '__main__':
    with Window(host='server.fridrich.xyz') as w:
        w.run()
