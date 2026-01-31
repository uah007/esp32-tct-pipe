import tkinter as tk
from gui import App
from config import WIN_X, WIN_Y, WIN_W, WIN_H

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
