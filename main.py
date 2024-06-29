from manager import conda_manager
import tkinter as tk

if __name__ == "__main__":
    root = tk.Tk()
    app = conda_manager.CondaManagerApp(root)
    root.mainloop()


