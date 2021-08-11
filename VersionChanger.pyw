import tkinter as tk

# local imports
from fridrich.FridrichBackend import Connection

class window:
    def __init__(self, ConnectionInstance:Connection) -> None:
        "create a new window"
        # variable definitions
        self.userEs = list()

        # tkinter
        self.c = ConnectionInstance
        self.root = tk.Tk()
        self.root.title('Fridrich Version Changer')
        
        self.root.minsize(width=600, height=150)
        self.root.maxsize(width=600, height=150)

        self.root.bind('<Escape>', self.end)

        # mainframe
        self.mainFrame = tk.Frame(self.root, bg='grey', width=600, height=700)

        self.refreshButton = tk.Button(self.mainFrame, text='Refresh', 
                                        command=self.refresh, background='grey', 
                                        fg='white', width=10, 
                                        relief=tk.FLAT, 
                                        font = "Helvetica 15"
                                        )
        self.refreshButton.place(x=100, y=100)
        
        self.updateButton = tk.Button(self.mainFrame, text='Set', 
                                        command=self.update, background='grey', 
                                        fg='white', width=10, 
                                        relief=tk.FLAT, 
                                        font = "Helvetica 15"
                                        )
        
        self.updateButton.place(x=400, y=100)
        
        self.versionEntry = tk.Entry(self.mainFrame,
                                    width=30,
                                    font = "Helvetica 15"
                                    )
        self.versionEntry.place(x=160, y=30)
        
        self.mainFrame.place(x=0, y=0, anchor='nw')

        self.login()

    def run(self) -> None:
        "start the tkinter.root.mainloop"
        self.root.mainloop()

    def login(self, *args) -> None:
        "login"
        if not self.c.auth('Lukas', 'Hurenficker'):
            exit()

        self.refresh()
    
    def refresh(self) -> None:
        "refresh vesion and enter it into the entry"
        self.version = c.getVersion()
        self.versionEntry.delete(0, 'end')
        self.versionEntry.insert(0, self.version)
        
    
    def update(self) -> None:
        "update"
        nv = self.versionEntry.get()
        if self.version!=nv:
            c.setVersion(nv)

    def end(self, *args) -> None:
        "end the connection and close the window"
        self.c.end()

if __name__ == '__main__':
    w = window(Connection())
    w.run()
    w.end()
