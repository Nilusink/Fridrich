from time import sleep
import tkinter as tk

# local imports
from modules.FridrichBackend import Connection

class window:
    def __init__(self, ConnectionInstance):
        # variable definitions
        self.userEs = list()

        # tkinter
        self.c = ConnectionInstance # setup root
        self.root = tk.Tk()
        self.root.title('Fridrich AdminTool')
        
        self.root.minsize(width=600, height=700)
        self.root.maxsize(width=600, height=700)

        self.root.bind('<Escape>', self.end)    # bin esc to exit

        #   login Frame
        self.loginFrame = tk.Frame(self.root, bg='black', width=600, height=700)

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
        
        self.login()

    def run(self):
        self.root.mainloop()

    def login(self, *args):
        pwd = self.loginPassword.get()

        if not self.c.auth('admin', 'Nic13.10.25#0213'):
            return

        self.root.bind("<Return>", tk.DISABLED)

        self.loginFrame.place_forget()
        self.mainFrame.place(x=0, y=0, anchor='nw')

        self.refresh()
    
    def refresh(self):
        self.users = c.AdminGetUsers()

        for element in self.userEs:
            element[0].place_forget()
            element[1].place_forget()
        
        self.userEs = list()
        
        for i, user in enumerate(self.users):
            self.userEs.append((
                tk.Entry(self.mainFrame, width=20, font = "Helvetica 15 bold"), 
                tk.Entry(self.mainFrame, width=20, font = "Helvetica 15 bold"),
                tk.Entry(self.mainFrame, width=20, font = "Helvetica 15 bold")
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
        
        newWindowHeight = i*50+100
        self.root.maxsize(width=800, height=newWindowHeight)
        self.root.minsize(width=800, height=newWindowHeight)
        self.mainFrame.config(height=newWindowHeight)

        self.refreshButton.place(x=50, y=newWindowHeight-50)
        self.updateButton.place(x=650, y=newWindowHeight-50)

        self.root.update()
    
    def update(self):
        for i in range(len(self.userEs)):
            name = self.userEs[i][0].get()
            pwd = self.userEs[i][1].get()
            sec = self.userEs[i][2].get()

            oname = self.users[i]['Name']
            opwd = self.users[i]['pwd']
            osec = self.users[i]['sec'] if 'sec' in self.users[i] else ''
    
            if name!=oname:
                self.c.AdminSetUsername(oname, name)
            
            if pwd!=opwd:
                self.c.AdminSetPassword(name, pwd)
            
            if sec!=osec:
                self.c.AdminSetSecurity(name, sec)

        self.refresh()

    def end(self, *args):
        self.c.end()
        exit()

if __name__ == '__main__':
    c = Connection()

    w = window(c)
    w.run()
    w.end()
