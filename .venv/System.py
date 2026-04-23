import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, simpledialog, filedialog, Toplevel
from PIL import Image, ImageTk
import json, os

FILE = "data.json"
ACCOUNTS_FILE = "accounts.json"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

current_user = None
is_admin = False
selected_image = None


# ================= DATA =================
def load_data():
    try:
        with open(FILE, "r") as f:
            data = json.load(f)

        if isinstance(data.get("about"), str):
            data["about"] = [{
                "user": "system",
                "message": data["about"],
                "likes": [],
                "comments": []
            }]

        return data

    except:
        return {
            "announcements": [],
            "news": [],
            "reminders": [],
            "about": []
        }


def save_data(d):
    with open(FILE, "w") as f:
        json.dump(d, f, indent=4)


# ================= ACCOUNTS =================
def load_accounts():
    try:
        with open(ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"students": {}, "pending": {}}


def save_accounts(d):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(d, f, indent=4)


# ================= ROOT =================
root = tb.Window(themename="flatly")
root.title("GNHS System")
root.geometry("900x700")


# ================= HEADER =================
header = tb.Frame(root)
header.pack(fill="x")

canvas_header = tb.Canvas(header, height=120, highlightthickness=0)
canvas_header.pack(fill="x")

try:
    cover = Image.open("images/cover.png").resize((1100,120))
    cover = ImageTk.PhotoImage(cover)
    canvas_header.create_image(0,0,anchor="nw",image=cover)
    canvas_header.cover = cover
except:
    canvas_header.configure(bg="#111827")

try:
    logo = Image.open("images/logo.png").resize((100,100))
    logo = ImageTk.PhotoImage(logo)
    canvas_header.create_image(15,60,anchor="w",image=logo)
    canvas_header.logo = logo
except:
    pass


# ================= HEADER TITLE (LEFT SIDE FIXED) =================
canvas_header.create_text(
    130, 35,
    text="GNHS ANNOUNCEMENT SYSTEM",
    fill="white",
    font=("Segoe UI", 16, "bold"),
    anchor="w"
)


user_text = canvas_header.create_text(
    150,70,
    text="Not logged in",
    fill="white",
    font=("Segoe UI",10),
    anchor="w"
)


def refresh_header():
    canvas_header.itemconfig(
        user_text,
        text=current_user if current_user else "Not logged in"
    )


# ================= MAIN =================
main = tb.Frame(root)
main.pack(fill="both", expand=True)

sidebar = tb.Frame(main, width=230)
sidebar.pack(side="left", fill="y")

canvas = tb.Canvas(main)
scrollbar = tb.Scrollbar(main, command=canvas.yview)

feed = tb.Frame(canvas)

feed.bind("<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0,0), window=feed, anchor="n")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")


def scroll(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", scroll)


# ================= LIKE =================
def like_post(cat, idx):
    data = load_data()
    post = data[cat][idx]
    post.setdefault("likes", [])

    if current_user not in post["likes"]:
        post["likes"].append(current_user)

    save_data(data)
    show(cat)


# ================= COMMENT =================
def comment_post(cat, idx):
    msg = simpledialog.askstring("Comment", "Write comment:")
    if not msg:
        return

    data = load_data()
    post = data[cat][idx]
    post.setdefault("comments", [])

    post["comments"].append({
        "text": f"{current_user}: {msg}",
        "replies": []
    })

    save_data(data)
    show(cat)

def reply_comment(cat, post_idx, comment_idx):
    msg = simpledialog.askstring("Reply", "Write reply:")
    if not msg:
        return

    data = load_data()
    post = data[cat][post_idx]

    # ensure structure exists
    if "comments" not in post:
        post["comments"] = []

    if "replies" not in post["comments"][comment_idx]:
        post["comments"][comment_idx] = {
            "text": post["comments"][comment_idx],
            "replies": []
        }

    post["comments"][comment_idx]["replies"].append(f"{current_user}: {msg}")

    save_data(data)
    show(cat)


# ================= FEED =================
def post_card(post, cat, idx):
    card = tb.Frame(feed, bootstyle="light", padding=15)
    card.pack(pady=10, padx=20, fill="x")

    tb.Label(card,
             text=post["user"],
             font=("Segoe UI",11,"bold")).pack(anchor="w")

    tb.Label(card,
             text=post["message"],
             wraplength=700).pack(anchor="w", pady=5)

    if post.get("image") and os.path.exists(post["image"]):
        try:
            img = Image.open(post["image"]).resize((500,300))
            img = ImageTk.PhotoImage(img)

            lbl = tb.Label(card, image=img)
            lbl.image = img
            lbl.pack(pady=5)
        except:
            pass

    btn = tb.Frame(card)
    btn.pack(anchor="w")

    tb.Button(btn,
              text=f"👍 {len(post.get('likes', []))}",
              bootstyle="secondary",
              command=lambda c=cat,i=idx: like_post(c,i)).pack(side="left", padx=5)

    tb.Button(btn,
              text="💬 Comment",
              bootstyle="info",
              command=lambda c=cat,i=idx: comment_post(c,i)).pack(side="left")

    for ci, c in enumerate(post.get("comments", [])):

        # handle OLD + NEW comment format safely
        if isinstance(c, str):
            comment_text = c
            replies = []
        else:
            comment_text = c.get("text", "")
            replies = c.get("replies", [])

        tb.Label(card, text=comment_text, foreground="gray").pack(anchor="w")

        tb.Button(
            card,
            text="↪ Reply",
            bootstyle="link",
            command=lambda cidx=ci, ccat=cat, pidx=idx: reply_comment(ccat, pidx, cidx)
        ).pack(anchor="w")

        for r in replies:
            tb.Label(card, text="   ↳ " + r, foreground="darkgray").pack(anchor="w")

    tb.Separator(card).pack(fill="x", pady=10)


def show(cat):
    for w in feed.winfo_children():
        w.destroy()

    data = load_data()

    tb.Label(feed,
             text=cat.upper(),
             font=("Segoe UI",18,"bold")).pack(pady=10)

    for i, post in enumerate(data.get(cat, [])):
        post_card(post, cat, i)


# ================= LOGOUT =================
def logout():
    global current_user, is_admin
    current_user = None
    is_admin = False
    build_home()
    refresh_header()


# ================= POST =================
def open_post(category):
    global selected_image

    win = Toplevel(root)
    win.title(f"Post {category}")
    win.geometry("420x360")

    text = tb.Text(win, height=6)
    text.pack(fill="x", padx=10)

    img_label = tb.Label(win, text="No image selected", foreground="gray")
    img_label.pack(pady=5)

    def add_photo():
        global selected_image
        selected_image = filedialog.askopenfilename()
        if selected_image:
            img_label.config(text=os.path.basename(selected_image))

    def post():
        msg = text.get("1.0","end").strip()
        if not msg:
            return

        data = load_data()
        data[category].append({
            "user": "admin",
            "message": msg,
            "image": selected_image,
            "likes": [],
            "comments": []
        })

        save_data(data)
        win.destroy()
        show(category)

    tb.Button(win, text="🖼 Add Photo",
              bootstyle="warning",
              command=add_photo).pack()

    tb.Button(win, text="📤 Post",
              bootstyle="success",
              command=post).pack()


# ================= APPROVAL INBOX =================
def open_inbox():
    win = Toplevel(root)
    win.title("Approval Inbox")
    win.geometry("500x500")

    canvas = tb.Canvas(win)
    scroll = tb.Scrollbar(win, command=canvas.yview)

    frame = tb.Frame(canvas)

    frame.bind("<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0,0), window=frame, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)

    canvas.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    data = load_accounts()

    for user in list(data["pending"].keys()):
        box = tb.Frame(frame, padding=10)
        box.pack(fill="x", pady=5)

        tb.Label(box, text=user, font=("bold")).pack(anchor="w")

        def approve(u=user):
            acc = load_accounts()
            acc["students"][u] = acc["pending"].pop(u)
            save_accounts(acc)
            open_inbox()

        def reject(u=user):
            acc = load_accounts()
            acc["pending"].pop(u, None)
            save_accounts(acc)
            open_inbox()

        tb.Button(box, text="Approve", bootstyle="success",
                  command=approve).pack(side="left")

        tb.Button(box, text="Reject", bootstyle="danger",
                  command=reject).pack(side="left")


# ================= REGISTER =================
def register():
    u = simpledialog.askstring("Register", "Username")
    p = simpledialog.askstring("Register", "Password", show="*")

    if not u or not p:
        return

    data = load_accounts()
    data["pending"][u] = {"password": p}
    save_accounts(data)

    messagebox.showinfo("Sent", "Request sent to admin")


# ================= ADMIN UI =================
def build_admin():
    for w in sidebar.winfo_children():
        w.destroy()

    refresh_header()

    tb.Label(sidebar, text="ADMIN PANEL", font=("bold",12)).pack(pady=10)

    tb.Button(sidebar, text="📢 Announcements",
              bootstyle="primary",
              command=lambda: show("announcements")).pack(fill="x")

    tb.Button(sidebar, text="📰 News",
              bootstyle="info",
              command=lambda: show("news")).pack(fill="x")

    tb.Button(sidebar, text="📌 Reminders",
              bootstyle="success",
              command=lambda: show("reminders")).pack(fill="x")

    tb.Button(sidebar, text="ℹ About",
              bootstyle="secondary",
              command=lambda: show("about")).pack(fill="x")

    tb.Button(sidebar, text="➕ Post Announcement",
              bootstyle="primary",
              command=lambda: open_post("announcements")).pack(fill="x")

    tb.Button(sidebar, text="➕ Post News",
              bootstyle="info",
              command=lambda: open_post("news")).pack(fill="x")

    tb.Button(sidebar, text="➕ Post Reminder",
              bootstyle="success",
              command=lambda: open_post("reminders")).pack(fill="x")

    tb.Button(sidebar, text="➕ Post About",
              bootstyle="secondary",
              command=lambda: open_post("about")).pack(fill="x")

    tb.Button(sidebar, text="📥 Approval Inbox",
              bootstyle="warning",
              command=open_inbox).pack(fill="x")

    tb.Button(sidebar, text="🚪 Logout",
              bootstyle="danger",
              command=logout).pack(fill="x", pady=10)


# ================= USER UI =================
def build_user():
    for w in sidebar.winfo_children():
        w.destroy()

    refresh_header()

    tb.Label(sidebar, text="HOME", font=("bold",12)).pack(pady=10)

    tb.Button(sidebar, text="🏠 Feed",
              bootstyle="primary",
              command=lambda: show("announcements")).pack(fill="x")

    tb.Button(sidebar, text="📰 News",
              bootstyle="info",
              command=lambda: show("news")).pack(fill="x")

    tb.Button(sidebar, text="📌 Reminders",
              bootstyle="success",
              command=lambda: show("reminders")).pack(fill="x")

    tb.Button(sidebar, text="ℹ About",
              bootstyle="secondary",
              command=lambda: show("about")).pack(fill="x")

    tb.Button(sidebar, text="📝 Register",
              bootstyle="warning",
              command=register).pack(fill="x")

    tb.Button(sidebar, text="🚪 Logout",
              bootstyle="danger",
              command=logout).pack(fill="x", pady=10)


# ================= LOGIN =================
def login():
    global current_user, is_admin

    u = simpledialog.askstring("Login", "Username")
    p = simpledialog.askstring("Login", "Password", show="*")

    acc = load_accounts()

    if u in acc["students"] and acc["students"][u]["password"] == p:
        current_user = u
        is_admin = False
        build_user()
        show("announcements")
        refresh_header()
    else:
        messagebox.showerror("Error", "Not approved or invalid")


def admin_login():
    global current_user, is_admin

    u = simpledialog.askstring("Admin", "Username")
    p = simpledialog.askstring("Admin", "Password", show="*")

    if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
        current_user = "admin"
        is_admin = True
        build_admin()
        show("announcements")
        refresh_header()

def open_saved_accounts():
    win = Toplevel(root)
    win.title("Saved Accounts")
    win.geometry("300x400")

    frame = tb.Frame(win)
    frame.pack(fill="both", expand=True)

    data = load_accounts()

    if not data["students"]:
        tb.Label(frame, text="No approved accounts yet").pack()
        return

    tb.Label(frame, text="Click account to login", font=("bold", 12)).pack(pady=10)

    for user in data["students"].keys():
        def quick_login(u=user):
            global current_user, is_admin
            current_user = u
            is_admin = False
            build_user()
            show("announcements")
            refresh_header()
            win.destroy()

        tb.Button(
            frame,
            text=user,
            bootstyle="success",
            command=quick_login
        ).pack(fill="x", padx=10, pady=5)

# ================= HOME =================
def build_home():
    for w in sidebar.winfo_children():
        w.destroy()

    refresh_header()

    # clear main feed area (so only login shows)
    for w in feed.winfo_children():
        w.destroy()

    # center container in full window
    center = tb.Frame(feed)
    center.pack(expand=True)

    box = tb.Frame(center, padding=30)
    box.pack(expand=True)

    tb.Label(box,
             text="WELCOME",
             font=("Segoe UI", 18, "bold")).pack(pady=10)

    tb.Button(box,
              text="👤 Login",
              bootstyle="primary",
              width=25,
              command=login).pack(pady=8)

    tb.Button(box,
              text="👑 Admin Login",
              bootstyle="warning",
              width=25,
              command=admin_login).pack(pady=8)

    tb.Button(box,
              text="📝 Register",
              bootstyle="success",
              width=25,
              command=register).pack(pady=8)

    tb.Button(box,
              text="💾 Saved Accounts",
              bootstyle="info",
              width=25,
              command=open_saved_accounts).pack(pady=8)

build_home()
root.mainloop()