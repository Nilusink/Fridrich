from contextlib import suppress
from tkinter import messagebox
from socket import gaierror
import tkinter as tk
from os import popen, system

# local imports
from modules.FridrichBackend import Connection

secEquals = {'admin':0, 'user':1, 'guest':2, 'other':3}    # for sorting the users

def sortUserList(lst:list, flag='sec'):
    values = sorted(lst, key=lambda element: secEquals[element[flag]] if element[flag] in secEquals else secEquals['other'])
    return list(values)

def getWifiName():
    ret = popen('Netsh WLAN show interfaces').readlines()
    wifiDict = dict()
    for element in ret:
        tmp = element.split(':')
        if len(tmp)>1:
            wifiDict[tmp[0].lstrip().rstrip()] = ':'.join(tmp[1::]).lstrip().rstrip().replace('\n', '')
    
    # if not wifiDict['SSID'] == 'Fridrich':
    #     print('Not Connected to Fridrich')
    #     print(f'Current Wifi: "{wifiDict["SSID"]}"')
    
    return wifiDict['SSID']

def tryConnectWifi(wifiName):
    ret = system(f'netsh wlan connect {wifiName}')

    if ret==1:
        return False
    return True

class window:
    def __init__(self, ConnectionInstance):
        # variable definitions
        self.userEs = list()

        # tkinter
        self.c = ConnectionInstance # setup root
        self.root = tk.Tk()
        self.root.title('Fridrich AdminTool')
        
        self.root.minsize(width=600, height=500)
        self.root.maxsize(width=600, height=500)

        self.root.bind('<Escape>', self.end)    # bin esc to exit
        self.root.bind('<F5>', self.update)

        #   login Frame
        self.loginFrame = tk.Frame(self.root, bg='black', width=600, height=700)

        # username label and button
        tk.Label(self.loginFrame, text='Username', font = "Helvetica 50 bold", bg='black', fg='white').place(x=137, y=50)  # Username Label
        self.loginUsername = tk.Entry(self.loginFrame, width=20, font = "Helvetica 25 bold")  # Username entry
        self.loginUsername.place(x=115, y=150)
        self.loginUsername.insert(0, 'admin')

        tk.Label(self.loginFrame, text='Password', font = "Helvetica 50 bold", bg='black', fg='white').place(x=137, y=250)  # Password Label
        self.loginPassword = tk.Entry(self.loginFrame, width=20, font = "Helvetica 25 bold", show='*')  # Password entry
        self.loginPassword.place(x=115, y=350)

        self.loginButton = tk.Button(self.loginFrame,   # button for login
                                    text='login', bg='grey5', 
                                    fg='white', relief=tk.FLAT,
                                    command=self.login,
                                    font = "Helvetica 30"
                                    )
        self.loginButton.place(x=230, y=400)

        self.loginFrame.place(x=0, y=0, anchor='nw')

        self.root.bind("<Return>", self.login)  # bind Return to login

        # mainframe
        self.mainFrame = tk.Frame(self.root, bg='grey', width=800, height=700)

        self.refreshButton = tk.Button(self.mainFrame, text='Refresh', # button for refreshing
                                        command=self.refresh, background='grey', 
                                        fg='white', width=10, 
                                        relief=tk.FLAT, 
                                        font = "Helvetica 15"
                                        )
        
        self.updateButton = tk.Button(self.mainFrame, text='Set',   # button for setting new usernames/passwords
                                        command=self.update, background='grey', 
                                        fg='white', width=10, 
                                        relief=tk.FLAT, 
                                        font = "Helvetica 15"
                                        )
        
        self.addButton = tk.Button(self.mainFrame, text='Add',   # button for setting new usernames/passwords
                                        command=self.addUser, background='green', 
                                        fg='white', width=10, 
                                        relief=tk.FLAT, 
                                        font = "Helvetica 15"
                                        )
        
        self.delButton = tk.Button(self.mainFrame, text='ResetLogins',   # button for setting new usernames/passwords
                                        command=self.resetLogins, background='red', 
                                        fg='white', width=10, 
                                        relief=tk.RAISED, 
                                        font = "Helvetica 15"
                                        )
        
        if ConnectionInstance == 'CantConnect':
            messagebox.showerror('Fatal Error', 'Not Connected to Fridrich Wifi! (attempt to connect failed)')
            exit()

        elif ConnectionInstance == 'ServerNotReachable':
            messagebox.showerror('Fatal Error', 'Cant reach Fridrich Server!')
            exit()

    def run(self):
        self.root.mainloop()

    def login(self, *args):
        name = self.loginUsername.get()
        pwd = self.loginPassword.get()

        if not self.c.auth(name, pwd):
            messagebox.showerror('Error', 'Invalid Username/Password')
            return

        sec = self.c.getSecClearance()
        if sec != 'admin':
            messagebox.showerror('Error', f'Account is not admin ({sec})')
            return

        self.root.bind("<Return>", tk.DISABLED)

        self.loginFrame.place_forget()
        self.mainFrame.place(x=0, y=0, anchor='nw')

        self.refresh()
    
    def refresh(self):
        self.users = sortUserList(c.AdminGetUsers())
        self.onlineUsers = c.getOnlineUsers()

        for element in self.userEs:
            with suppress(IndexError):
                element[0].place_forget()
                element[1].place_forget()
                element[2].place_forget()
                element[3].place_forget()
        
        self.userEs = list()
        
        for i, user in enumerate(self.users):
            self.userEs.append((
                tk.Entry(self.mainFrame, width=20, font = "Helvetica 15 bold"), 
                tk.Entry(self.mainFrame, width=20, font = "Helvetica 15 bold"),
                tk.Entry(self.mainFrame, width=20, font = "Helvetica 15 bold"),
                tk.Button(self.mainFrame, width=1, font = "Helvetica 10 bold", text = '-', 
                    bg = 'red', command = lambda e=None, name=user['Name']: self.remUser(name))
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
        
        for j, element in enumerate(self.onlineUsers):
            self.userEs.append((
                tk.Label(self.mainFrame, width=18, font = "Helvetica 15 bold", text='Name:', bg='grey', fg='white'),
                tk.Label(self.mainFrame, width=18, font = "Helvetica 15 bold", text=element, bg='grey', fg='white')
            ))

            self.userEs[-1][0].place(x=50, y=(i+j+2)*50+10)
            self.userEs[-1][1].place(x=300, y=(i+j+2)*50+10)
                
            


        newWindowHeight = (i+j+2)*50+100
        newWindowHeight = newWindowHeight if newWindowHeight<1000 else 1000
        self.root.maxsize(width=800, height=newWindowHeight)
        self.root.minsize(width=800, height=newWindowHeight)
        self.mainFrame.config(height=newWindowHeight)

        self.delButton.place(x=350, y=(i+j+1)*50+100)

        self.refreshButton.place(x=50, y=(i+1)*50)
        self.addButton.place(x=350, y=(i+1)*50)
        self.updateButton.place(x=650, y=(i+1)*50)

        self.root.update()
    
    def update(self, *args):
        for i in range(len(self.userEs)):
            try:
                name = self.userEs[i][0].get()
                pwd = self.userEs[i][1].get()
                sec = self.userEs[i][2].get()

                oname = self.users[i]['Name']
                opwd = self.users[i]['pwd']
                osec = self.users[i]['sec'] if 'sec' in self.users[i] else ''
        
                try:
                    if name!=oname:
                        self.c.AdminSetUsername(oname, name)
                    
                    if pwd!=opwd:
                        self.c.AdminSetPassword(name, pwd)
                    
                    if sec!=osec:
                        self.c.AdminSetSecurity(name, sec)
                except NameError:
                    messagebox.showerror('Error', 'Name already exists')
            except AttributeError:
                break
        self.refresh()

    def remUser(self, user):
        self.c.AdminRemoveUser(user)
        self.update()

    def addUser(self):
        self.update()
        try:
            self.c.AdminAddUser('', '', '')
            self.update()

        except Exception:
            messagebox.showerror('Error', f'User with name "{""}" already exists')

    def resetLogins(self, event=None):
        global w, c
        ans = messagebox.askyesno('Confirm', 'Clear all users (logout)')
        if ans:
            c.AdminResetLogins()
            c.AuthKey = None
            w.root.destroy()
            w = window(c)


    def end(self, *args):
        self.c.end()
        exit()

if __name__ == '__main__':
    try:
        c = Connection()
    except gaierror:    # if connection issue
        WifiName = getWifiName()    # get wifi name
        if not WifiName == 'Fridrich':  # if not connected to "Fridich" wifi
            resp = tryConnectWifi('Fridrich')   # try to connect
            if resp:    # if connected Sucessfully
                try:
                    c = Connection()
                except gaierror:    # if can't reach again
                    c = 'ServerNotReachable'
            else:   # if cant connect to Fridrich
                c = 'CantConnect'
        else:   # if Wifi is "Fridrich" but Still Can't Connect
            c = 'ServerNotReachable'

    w = window(c)
    w.run()
    w.end()
