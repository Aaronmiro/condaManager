import tkinter as tk
import subprocess
import threading
import queue
from tkinter import ttk
from tkinter import messagebox, scrolledtext, filedialog


class CondaManagerApp:
    def __init__(self, root):
        self.base_command_list = ["powershell", "-ExecutionPolicy", "ByPass"]
        self.base_torch_3_10 = "base_torch_3.10"
        self.file_path = ""

        self.root = root
        self.root.title("Conda Manager")

        #  self.output_queue = queue.Queue() 创建一个线程安全的队列，用于存储命令输出。
        self.output_queue = queue.Queue()

        self.use_torch = tk.IntVar()
        self.load_req = tk.IntVar()

        self.create_widgets()

    def create_widgets(self):
        # Create a frame for environment management
        env_frame = tk.LabelFrame(self.root, text="Environment Management", padx=10, pady=10)
        env_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Create widgets for environment management
        tk.Label(env_frame, text="Environment Name:").grid(row=0, column=0, padx=5, pady=5)

        self.env_name_entry = tk.Entry(env_frame)
        self.env_name_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(env_frame, text="Python Version:").grid(row=0, column=2, padx=5, pady=5)

        self.combo = ttk.Combobox(env_frame, values=["", "3.7.6", "3.8", "3.9", "3.10", "3.10.11", "3.11.7"])
        self.combo.current(0)  # 设置默认选项为第一个
        self.combo.grid(row=0, column=3, padx=5, pady=5)

        tk.Button(env_frame, text="Create Environment", command=self.create_env).grid(row=1, column=0, columnspan=1,
                                                                                      padx=5, pady=5)
        tk.Button(env_frame, text="Remove Environment", command=self.delete_env).grid(row=2, column=0, columnspan=1,
                                                                                      padx=5, pady=5)
        tk.Button(env_frame, text="List Environments", command=self.list_envs).grid(row=3, column=0, columnspan=1,
                                                                                    padx=5, pady=5)

        tk.Checkbutton(env_frame, text="Torch GPU", variable=self.use_torch).grid(row=1, column=2, padx=5, pady=5)
        tk.Checkbutton(env_frame, text="pip requirement", variable=self.load_req, command=self.select_file).grid(row=1,
                                                                                                                 column=3,
                                                                                                                 padx=5,
                                                                                                                 pady=5)


        tk.Label(env_frame, text="Pip Install:").grid(row=2, column=1, padx=5, pady=5)
        self.pip_install_entry = tk.Entry(env_frame)
        self.pip_install_entry.grid(row=2, column=2, padx=5, pady=5)
        tk.Button(env_frame, text="install", command=self.pip_install).grid(row=2, column=3, columnspan=1,
                                                                            padx=5, pady=5)

        tk.Button(env_frame, text="Start Jupyter Lab", command=self.start_jupyter).grid(row=3, column=2, columnspan=1,
                                                                            padx=5, pady=5)

        tk.Button(env_frame, text="Install To Jupyter Lab", command=self.install_to_jupyter).grid(row=3, column=3, columnspan=1,
                                                                                        padx=5, pady=5)
        # Create a frame for output
        output_frame = tk.LabelFrame(self.root, text="Output", padx=10, pady=10)
        output_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Create a scrolled text widget for output
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, width=80, height=15)
        self.output_text.grid(row=0, column=0, padx=5, pady=5)

        self.update_output()

    def run_conda_command(self, command):
        # enqueue_output 函数负责将子进程的输出行写入队列。
        def enqueue_output(process, queue):
            for line in iter(process.stdout.readline, ''):
                queue.put(line)
            process.stdout.close()

        base_command = f"& 'D:\miniconda3\shell\condabin\conda-hook.ps1'; {command}"
        target_command = self.base_command_list + ["-Command", base_command]

        # subprocess.Popen 以非阻塞方式运行 PowerShell 命令，并使用一个线程将输出行写入队列。
        process = subprocess.Popen(target_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                        bufsize=1)
        process.daemon = True

        thread = threading.Thread(target=enqueue_output, args=(process, self.output_queue))
        thread.daemon = True
        thread.start()

    # update_output 方法每 100 毫秒检查一次队列是否有新输出，并将其插入 ScrolledText 小部件。
    def update_output(self):
        while not self.output_queue.empty():
            line = self.output_queue.get_nowait()
            # print(line)
            self.output_text.insert(tk.END, line)
            self.output_text.see(tk.END)

        # self.root.after(100, self.update_output) 设置一个定时器，以便定期调用 update_output 方法。
        self.root.after(100, self.update_output)

    def create_env(self):
        env_name = self.env_name_entry.get().strip()
        python_version = self.combo.get()

        if env_name and python_version:
            command = f"conda create -n {env_name} -y "

            if self.use_torch.get():
                command += f"--clone base_torch_{python_version};"
            else:
                command += f"python={python_version};"
            if self.load_req.get():
                command += f"conda activate {env_name}; pip install -r {self.file_path}"
            # print(command)
            self.run_conda_command(command)  # 旧环境名

        else:
            messagebox.showwarning("Input Error", "Please enter a valid environment name or Python Version.")

    def delete_env(self):
        env_name = self.env_name_entry.get().strip()
        if env_name:
            self.run_conda_command(f"conda remove -n {env_name} --all -y")
            # self.output_text.insert(tk.END, output + "\n")
        else:
            messagebox.showwarning("Input Error", "Please enter a valid environment name.")

    def list_envs(self):
        self.run_conda_command("conda env list")

    def pip_install(self):
        env_name = self.env_name_entry.get().strip()
        pip_package_name = self.pip_install_entry.get().strip()
        if env_name != "" and pip_package_name != "":
            self.run_conda_command(f"conda deactivate; conda activate {env_name}; pip install {pip_package_name}")
        else:
            messagebox.showwarning("Pip Install Error", "Please enter a valid environment name and pip package name.")

    def select_file(self):
        if self.load_req.get():
            # 打开文件选择对话框
            self.file_path = filedialog.askopenfilename(title="Select a File")

            if self.file_path:
                # messagebox.showinfo("File Selected", f"File selected: {file_path}")
                self.output_queue.put(f"File selected: \n{self.file_path}\n")

    def start_jupyter(self):
            self.run_conda_command(f"conda deactivate; conda activate jupyter_env; jupyter lab")


    def install_to_jupyter(self):
        env_name = self.env_name_entry.get().strip()
        if env_name != "":
            self.run_conda_command(f"conda deactivate; conda activate {env_name}; pip install ipykernel; python -m ipykernel install --user --name {env_name} --display-name {env_name}")
        else:
            messagebox.showwarning("Install To Jupyter Error", "Please enter a valid environment name")


if __name__ == "__main__":
    root = tk.Tk()
    app = CondaManagerApp(root)
    root.mainloop()
