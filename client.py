import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading

# server connection settings

HOST = "18.219.247.150"
PORT = 8080

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ChatApp")
        self.root.resizable(False, False)

        # color palette
        self.bg        = "#0f0f0f"
        self.surface   = "#1a1a1a"
        self.border    = "#2a2a2a"
        self.accent    = "#00e5a0"
        self.text      = "#e8e8e8"
        self.muted     = "#555555"
        self.bubble_me = "#003d2a"
        self.bubble_them = "#1e1e1e"

        self.root.configure(bg=self.bg)

        self.sock = None
        self.username = ""

        # start on the login screen
        self.show_login()

    # login screen

    def show_login(self):
        self.clear_window()
        self.root.geometry("420x520")

        frame = tk.Frame(self.root, bg=self.bg)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # title
        tk.Label(frame, text="●  ChatApp", font=("Courier", 22, "bold"),
                 bg=self.bg, fg=self.accent).pack(pady=(0, 4))
        tk.Label(frame, text="sign in to continue", font=("Courier", 10),
                 bg=self.bg, fg=self.muted).pack(pady=(0, 36))

        # username field
        tk.Label(frame, text="USERNAME", font=("Courier", 9, "bold"),
                 bg=self.bg, fg=self.muted).pack(anchor="w")
        self.login_user = tk.Entry(frame, width=32, font=("Courier", 12),
                                   bg=self.surface, fg=self.text,
                                   insertbackground=self.accent,
                                   relief="flat", bd=8,
                                   highlightthickness=1,
                                   highlightbackground=self.border,
                                   highlightcolor=self.accent)
        self.login_user.pack(pady=(4, 18), ipady=6)
        self.login_user.focus()

        # password field
        tk.Label(frame, text="PASSWORD", font=("Courier", 9, "bold"),
                 bg=self.bg, fg=self.muted).pack(anchor="w")
        self.login_pass = tk.Entry(frame, width=32, font=("Courier", 12),
                                   bg=self.surface, fg=self.text,
                                   insertbackground=self.accent,
                                   relief="flat", bd=8, show="●",
                                   highlightthickness=1,
                                   highlightbackground=self.border,
                                   highlightcolor=self.accent)
        self.login_pass.pack(pady=(4, 30), ipady=6)

        # bind enter key to login
        self.login_pass.bind("<Return>", lambda e: self.do_login())
        self.login_user.bind("<Return>", lambda e: self.login_pass.focus())

        # login button
        btn = tk.Button(frame, text="CONNECT  →", font=("Courier", 11, "bold"),
                        bg=self.accent, fg="#000000", relief="flat",
                        activebackground="#00c988", activeforeground="#000000",
                        cursor="hand2", bd=0,
                        command=self.do_login)
        btn.pack(fill="x", ipady=10)

        # status label for errors
        self.login_status = tk.Label(frame, text="", font=("Courier", 9),
                                     bg=self.bg, fg="#ff5555")
        self.login_status.pack(pady=(12, 0))

    def do_login(self):
        username = self.login_user.get().strip()
        password = self.login_pass.get().strip()

        if not username or not password:
            self.login_status.config(text="username and password required")
            return

        # try to connect to the server
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
        except Exception as e:
            self.login_status.config(text=f"could not connect to server")
            self.sock = None
            return

        # send login credentials to server
        # format aswell
        try:
            self.sock.sendall(f"LOGIN {username} {password}\n".encode())
            response = self.sock.recv(1024).decode().strip()
        except Exception:
            self.login_status.config(text="server error, try again")
            return

        if response == "OK":
            self.username = username
            self.show_chat()
        else:
            self.login_status.config(text="invalid credentials")
            self.sock.close()
            self.sock = None

    # chat 

    def show_chat(self):
        self.clear_window()
        self.root.geometry("700x560")

        # top bar
        topbar = tk.Frame(self.root, bg=self.surface, height=52)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        tk.Label(topbar, text="● ChatApp", font=("Courier", 13, "bold"),
                 bg=self.surface, fg=self.accent).pack(side="left", padx=20)
        tk.Label(topbar, text=f"signed in as  {self.username}",
                 font=("Courier", 9), bg=self.surface, fg=self.muted).pack(side="left")

        tk.Button(topbar, text="disconnect", font=("Courier", 9),
                  bg=self.surface, fg=self.muted, relief="flat",
                  activebackground=self.surface, activeforeground="#ff5555",
                  cursor="hand2", bd=0,
                  command=self.disconnect).pack(side="right", padx=20)

        # message area
        self.msg_area = scrolledtext.ScrolledText(
            self.root, state="disabled", wrap="word",
            font=("Courier", 11), bg=self.bg, fg=self.text,
            relief="flat", bd=0, padx=16, pady=12,
            insertbackground=self.accent,
            selectbackground=self.accent,
        )
        self.msg_area.pack(fill="both", expand=True, padx=0, pady=0)

        # configure text tags for message bubbles
        self.msg_area.tag_config("me",
            foreground=self.accent, lmargin1=80, lmargin2=80)
        self.msg_area.tag_config("them",
            foreground=self.text, lmargin1=12, lmargin2=12)
        self.msg_area.tag_config("system",
            foreground=self.muted, justify="center")

        # input bar at the bottom
        input_frame = tk.Frame(self.root, bg=self.surface, height=60)
        input_frame.pack(fill="x", side="bottom")
        input_frame.pack_propagate(False)

        self.msg_input = tk.Entry(input_frame, font=("Courier", 12),
                                  bg=self.border, fg=self.text,
                                  insertbackground=self.accent,
                                  relief="flat", bd=0)
        self.msg_input.pack(side="left", fill="both", expand=True,
                            padx=(16, 8), pady=14, ipady=4)
        self.msg_input.bind("<Return>", lambda e: self.send_message())
        self.msg_input.focus()

        send_btn = tk.Button(input_frame, text="send  →",
                             font=("Courier", 10, "bold"),
                             bg=self.accent, fg="#000000",
                             activebackground="#00c988",
                             relief="flat", bd=0, cursor="hand2",
                             command=self.send_message)
        send_btn.pack(side="right", padx=(0, 16), pady=14, ipadx=14, ipady=4)

        self.append_message("connected to server", tag="system")

        # start background thread to listen for incoming messages
        t = threading.Thread(target=self.receive_loop, daemon=True)
        t.start()

    def append_message(self, text, tag="them"):
        self.msg_area.config(state="normal")
        self.msg_area.insert("end", text + "\n", tag)
        self.msg_area.config(state="disabled")
        self.msg_area.see("end")

    def send_message(self):
        msg = self.msg_input.get().strip()
        if not msg or not self.sock:
            return
        try:
            self.sock.sendall(f"MSG {msg}\n".encode())
            self.append_message(f"you:  {msg}", tag="me")
            self.msg_input.delete(0, "end")
        except Exception:
            self.append_message("failed to send message", tag="system")

    def receive_loop(self):
        # runs in a background thread like listens for messages from the server
        buffer = ""
        while True:
            try:
                data = self.sock.recv(4096).decode()
                if not data:
                    break
                buffer += data
                # messages are newline delimited
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        # schedule UI update on the main thread
                        self.root.after(0, self.append_message, line, "them")
            except Exception:
                break
        self.root.after(0, self.append_message, "disconnected from server", "system")

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.show_login()

    # utility

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
