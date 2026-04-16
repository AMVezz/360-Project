import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading

# server info (this is the server we connect to)
HOST = "18.219.247.150"
PORT = 8080

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ChatApp")
        self.root.resizable(False, False)

        # just setting up colors to make the UI look cleaner
        self.bg        = "#0f0f0f"
        self.surface   = "#1a1a1a"
        self.border    = "#2a2a2a"
        self.accent    = "#00e5a0"
        self.text      = "#e8e8e8"
        self.muted     = "#555555"
        self.bubble_me = "#003d2a"
        self.bubble_them = "#1e1e1e"

        self.root.configure(bg=self.bg)

        # this will hold the socket connection and username later
        self.sock = None
        self.username = ""

        # when the app starts, go straight to login screen
        self.show_login()

    # login screen

    def show_login(self):
        self.clear_window()
        self.root.geometry("420x520")

        # center everything on screen
        frame = tk.Frame(self.root, bg=self.bg)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # title + subtitle
        tk.Label(frame, text="●  ChatApp", font=("Courier", 22, "bold"),
                 bg=self.bg, fg=self.accent).pack(pady=(0, 4))
        tk.Label(frame, text="sign in to continue", font=("Courier", 10),
                 bg=self.bg, fg=self.muted).pack(pady=(0, 36))

        # username input
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

        # password input (hidden text)
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

        # pressing enter makes it easier to log in
        self.login_pass.bind("<Return>", lambda e: self.do_login())
        self.login_user.bind("<Return>", lambda e: self.login_pass.focus())

        # login button
        tk.Button(frame, text="CONNECT  →", font=("Courier", 11, "bold"),
                  bg=self.accent, fg="#000000",
                  command=self.do_login).pack(fill="x", ipady=10)

        # where error messages show up
        self.login_status = tk.Label(frame, text="", font=("Courier", 9),
                                     bg=self.bg, fg="#ff5555")
        self.login_status.pack(pady=(12, 0))

    def do_login(self):
        # grab what the user typed
        username = self.login_user.get().strip()
        password = self.login_pass.get().strip()

        # simple check so empty fields don't go through
        if not username or not password:
            self.login_status.config(text="username and password required")
            return

        # try connecting to the server
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
        except Exception:
            self.login_status.config(text="could not connect to server")
            self.sock = None
            return

        # send login info to server and wait for response
        try:
            self.sock.sendall(f"LOGIN {username} {password}\n".encode())
            response = self.sock.recv(1024).decode().strip()
        except Exception:
            self.login_status.config(text="server error, try again")
            return

        # if login works, go to chat screen
        if response == "OK":
            self.username = username
            self.show_chat()
        else:
            self.login_status.config(text="invalid credentials")
            self.sock.close()
            self.sock = None

    # chat screen

    def show_chat(self):
        self.clear_window()
        self.root.geometry("700x560")

        # top section with app name and user
        topbar = tk.Frame(self.root, bg=self.surface, height=52)
        topbar.pack(fill="x")

        tk.Label(topbar, text="● ChatApp", bg=self.surface, fg=self.accent).pack(side="left", padx=20)
        tk.Label(topbar, text=f"signed in as {self.username}",
                 bg=self.surface, fg=self.muted).pack(side="left")

        # disconnect button
        tk.Button(topbar, text="disconnect", command=self.disconnect).pack(side="right", padx=20)

        # main chat area (read only)
        self.msg_area = scrolledtext.ScrolledText(
            self.root, state="disabled", wrap="word",
            bg=self.bg, fg=self.text
        )
        self.msg_area.pack(fill="both", expand=True)

        # different styles for messages
        self.msg_area.tag_config("me", foreground=self.accent)
        self.msg_area.tag_config("them", foreground=self.text)
        self.msg_area.tag_config("system", foreground=self.muted)

        # bottom input area
        input_frame = tk.Frame(self.root, bg=self.surface)
        input_frame.pack(fill="x")

        self.msg_input = tk.Entry(input_frame)
        self.msg_input.pack(side="left", fill="both", expand=True)
        self.msg_input.bind("<Return>", lambda e: self.send_message())

        tk.Button(input_frame, text="send", command=self.send_message).pack(side="right")

        self.append_message("connected to server", tag="system")

        # start listening for messages in background
        threading.Thread(target=self.receive_loop, daemon=True).start()

    def append_message(self, text, tag="them"):
        # temporarily enable text box so we can insert text
        self.msg_area.config(state="normal")
        self.msg_area.insert("end", text + "\n", tag)
        self.msg_area.config(state="disabled")
        self.msg_area.see("end")

    def send_message(self):
        msg = self.msg_input.get().strip()
        if not msg or not self.sock:
            return

        try:
            # send message to server
            self.sock.sendall(f"MSG {msg}\n".encode())

            # show it in our own chat immediately
            self.append_message(f"you: {msg}", tag="me")
            self.msg_input.delete(0, "end")
        except Exception:
            self.append_message("failed to send message", tag="system")

    def receive_loop(self):
        # this runs forever in the background waiting for messages
        buffer = ""
        while True:
            try:
                data = self.sock.recv(4096).decode()
                if not data:
                    break

                buffer += data

                # split messages by newline
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        # update UI safely
                        self.root.after(0, self.append_message, line.strip(), "them")
            except Exception:
                break

        self.root.after(0, self.append_message, "disconnected from server", "system")

    def disconnect(self):
        # close connection and go back to login
        if self.sock:
            self.sock.close()
            self.sock = None
        self.show_login()

    def clear_window(self):
        # remove everything from window before switching screens
        for widget in self.root.winfo_children():
            widget.destroy()


# start the app
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()