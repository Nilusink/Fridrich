from contextlib import suppress
from tkinter import messagebox
from os import popen, system
from socket import gaierror
import tkinter as tk

# local imports
from fridrich.backend import Connection

secEquals = ('admin', 'bot', 'user', 'guest')    # for sorting the users


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


def get_wifi_name() -> str:
    """
    return the name of the wifi currently connected to
    """
    ret = popen('Netsh WLAN show interfaces').readlines()
    wifiDict = dict()
    for element in ret:
        tmp = element.split(':')
        if len(tmp) > 1:
            wifiDict[tmp[0].lstrip().rstrip()] = ':'.join(tmp[1::]).lstrip().rstrip().replace('\n', '')
    
    # if not wifiDict['SSID'] == 'Fridrich':
    #     print('Not Connected to Fridrich')
    #     print(f'Current Wifi: "{wifiDict["SSID"]}"')
    
    return wifiDict['SSID']


def try_connect_wifi(wifi_name: str) -> bool:
    """
    try to connect to the given wifi
    """
    ret = system(f'netsh wlan connect {wifi_name}')

    if ret == 1:
        return False
    return True


class Window:
    """
    class for the main window
    """
    def __init__(self, connection_instance: Connection) -> None:
        """
        ConnectionInstance: instance of fridirch.FridrichBackend.Connection
        """
        # variable definitions
        self.userEs = list()
        self.users = list()
        self.onlineUsers = list()

        # tkinter
        self.c = connection_instance  # setup root
        self.root = tk.Tk()
        self.root.title('Fridrich AdminTool')
        
        self.root.minsize(width=600, height=500)
        self.root.maxsize(width=600, height=500)

        self.root.bind('<Escape>', self.end)    # bin esc to exit
        self.root.bind('<F5>', self.update)

        #   login Frame
        self.loginFrame = tk.Frame(self.root, bg='black', width=600, height=700)

        # username label and button
        tk.Label(self.loginFrame, text='Username', font="Helvetica 50 bold", bg='black', fg='white').place(x=137, y=50)  # Username Label
        self.loginUsername = tk.Entry(self.loginFrame, width=20, font="Helvetica 25 bold")  # Username entry
        self.loginUsername.place(x=115, y=150)
        self.loginUsername.insert(0, 'admin')

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
        
        if self.c == 'CantConnect':
            messagebox.showerror('Fatal Error', 'Not Connected to Fridrich Wifi! (attempt to connect failed)')
            exit()

        elif self.c == 'ServerNotReachable':
            messagebox.showerror('Fatal Error', 'Cant reach Fridrich Server!')
            exit()

    def run(self) -> None:
        """
        start tkinter.root.mainloop
        """
        self.root.mainloop()

    def login(self, *args) -> None:
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
        self.users = sort_user_list(c.admin_get_users())
        self.onlineUsers = c.get_online_users()

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
            self.userEs[-1][1].insert(0, user['pwd'])
            self.userEs[-1][2].insert(0, user['sec'] if 'sec' in user else '')
            self.userEs[-1][0].place(x=50, y=i*50+10)
            self.userEs[-1][1].place(x=300, y=i*50+10)
            self.userEs[-1][2].place(x=550, y=i*50+10)

            if user['Name'] != 'admin':
                self.userEs[-1][3].place(x=10,  y=i*50+10)
            else:
                self.userEs[-1][0].config(state=tk.DISABLED)
                self.userEs[-1][2].config(state=tk.DISABLED)
        
        UserNum = {user: self.onlineUsers.count(user) for user in self.onlineUsers}
        isIn = list()
        notIn = int()

        j = int()
        for j, element in enumerate(self.onlineUsers):
            if element not in isIn:
                self.userEs.append((
                    tk.Label(self.mainFrame, width=18, font="Helvetica 15 bold", text='Name:', bg='grey', fg='white'),
                    tk.Label(self.mainFrame, width=18, font="Helvetica 15 bold", text=element, bg='grey', fg='white'),
                    tk.Label(self.mainFrame, width=18, font="Helvetica 15 bold", text='Count: '+str(UserNum[element]), bg='grey', fg='white')
                ))

                isIn.append(element)

                self.userEs[-1][0].place(x=50, y=(i+j+3-notIn)*50+10)
                self.userEs[-1][1].place(x=300, y=(i+j+3-notIn)*50+10)
                self.userEs[-1][2].place(x=550, y=(i+j+3-notIn)*50+10)
            else:
                notIn += 1
                
        newWindowHeight = (i+j+2-notIn)*50+100
        newWindowHeight = newWindowHeight if newWindowHeight < 1000 else 1000
        self.root.maxsize(width=800, height=newWindowHeight)
        self.root.minsize(width=800, height=newWindowHeight)
        self.mainFrame.config(height=newWindowHeight)

        self.delButton.place(x=350, y=(i+2)*50+10)

        self.refreshButton.place(x=50, y=(i+1)*50)
        self.addButton.place(x=350, y=(i+1)*50)
        self.updateButton.place(x=650, y=(i+1)*50)

        self.root.update()
    
    def update(self, *args) -> None:
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
                    if name != o_name:
                        self.c.admin_ser_username(o_name, name)
                    
                    if pwd != o_pwd:
                        self.c.admin_set_password(name, pwd)
                    
                    if sec != o_sec:
                        self.c.admin_set_security(name, sec)
                except NameError:
                    messagebox.showerror('Error', 'Name already exists')
            except AttributeError:
                break
        self.refresh()

    def rem_user(self, user: str) -> None:
        """
        remove user
        """
        self.c.admin_remove_user(user)
        self.update()

    def add_user(self) -> None:
        """
        add a new user
        """
        self.update()
        try:
            self.c.admin_add_user('', '', '')
            self.update()

        except NameError:
            messagebox.showerror('Error', f'User with name "{""}" already exists')

    @staticmethod
    def reset_logins(event=None) -> None:
        """
        reset all logins
        """
        global w, c
        ans = messagebox.askyesno('Confirm', 'Clear all users (logout)')
        if ans:
            with suppress(ConnectionAbortedError):
                c.admin_reset_logins()
            w.root.destroy()
            w = Window(c)

    def end(self, *args) -> None:
        """
        end connection to fridrich and destroy the tkinter.root
        """
        del args
        self.c.end()
        self.root.destroy()


if __name__ == '__main__':
    try:
        c = Connection(host='fridrich')
    except gaierror:    # if connection issue
        WifiName = get_wifi_name()    # get wifi name
        if not WifiName == 'Fridrich':  # if not connected to "Fridrich" wifi
            resp = try_connect_wifi('Fridrich')   # try to connect
            if resp:    # if connected Successfully
                try:
                    c = Connection()
                except gaierror:    # if can't reach again
                    c = 'ServerNotReachable'
            else:   # if cant connect to Fridrich
                c = 'CantConnect'
        else:   # if Wifi is "Fridrich" but Still Can't Connect
            c = 'ServerNotReachable'

    w = Window(c)
    w.run()
    exit()
