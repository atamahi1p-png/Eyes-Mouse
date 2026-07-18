import cv2
import mediapipe as mp
import pyautogui
import tkinter as tk
import threading
import time
from tkinter import messagebox

# -----------------------------
# 🔐 Default Login Credentials
# -----------------------------
DEFAULT_EMAIL = "mahi@gmail.com"
DEFAULT_PASS = "1234"

# -----------------------------
# 👁 Eyes Mouse Function (runs in background thread)
# -----------------------------
def eyes_mouse():
    # try opening camera
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        # schedule error popup on main thread
        root.after(0, lambda: messagebox.showerror("Camera Error", "Cannot open camera."))
        return

    # set resolution (optional)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    mp_face_mesh = mp.solutions.face_mesh
    # use context manager for proper resource cleanup
    with mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as face_mesh:

        screen_w, screen_h = pyautogui.size()
        prev_x, prev_y = 0, 0
        smoothing = 5.0
        blink_threshold = 0.03
        blink_cooldown = 1.0
        last_blink = time.time()

        while True:
            ret, frame = cam.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            frame_h, frame_w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            output = face_mesh.process(rgb_frame)
            landmark_points = output.multi_face_landmarks

            if landmark_points:
                landmarks = landmark_points[0].landmark

                # track right-eye landmarks (using refined indices)
                # Using landmarks[474:478] as in your original code (right eye region)
                for idx, landmark in enumerate(landmarks[474:478]):
                    x = int(landmark.x * frame_w)
                    y = int(landmark.y * frame_h)
                    cv2.circle(frame, (x, y), 3, (0, 255, 0), -1)

                    # use the 2nd point as cursor anchor (as before)
                    if idx == 1:
                        screen_x = screen_w * landmark.x
                        screen_y = screen_h * landmark.y

                        # smoothing to reduce jitter
                        screen_x = prev_x + (screen_x - prev_x) / smoothing
                        screen_y = prev_y + (screen_y - prev_y) / smoothing

                        try:
                            pyautogui.moveTo(screen_x, screen_y)
                        except Exception:
                            # ignore pyautogui exceptions (e.g., fail-safe)
                            pass

                        prev_x, prev_y = screen_x, screen_y

                # Blink detection (left eye sample points)
                # using indices 145 and 159 (as in your original code)
                left_top = landmarks[145]
                left_bottom = landmarks[159]

                # draw the points for debug
                lx = int(left_top.x * frame_w)
                ly = int(left_top.y * frame_h)
                rx = int(left_bottom.x * frame_w)
                ry = int(left_bottom.y * frame_h)
                cv2.circle(frame, (lx, ly), 3, (0, 255, 255), -1)
                cv2.circle(frame, (rx, ry), 3, (0, 255, 255), -1)

                eye_ratio = left_top.y - left_bottom.y

                if eye_ratio < blink_threshold and (time.time() - last_blink) > blink_cooldown:
                    try:
                        pyautogui.click()
                    except Exception:
                        pass
                    last_blink = time.time()

            cv2.imshow('👁 Eye Controlled Mouse (press q to quit)', frame)

            # quit if user presses 'q' OR if main tkinter window was destroyed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            if not root.winfo_exists():
                # main window closed, break loop
                break

    cam.release()
    cv2.destroyAllWindows()

    # schedule the thank-you window on the main thread (safe)
    try:
        root.after(0, show_thank_you)
    except Exception:
        pass


# -----------------------------
# 🎉 Dynamic Welcome Page
# -----------------------------
def type_text(label, text, delay=80):
    def inner():
        label.config(text="")
        for i in range(len(text) + 1):
            label.config(text=text[:i])
            label.update()
            time.sleep(delay / 1000)
    threading.Thread(target=inner, daemon=True).start()


def start_eyes_mouse_thread():
    # start eyes_mouse in a daemon thread so it stops when main program exits
    t = threading.Thread(target=eyes_mouse, daemon=True)
    t.start()


def show_welcome():
    welcome = tk.Toplevel(root)
    welcome.title("Welcome")
    welcome.geometry("700x400")
    welcome.configure(bg="#1E1E2F")

    tk.Label(welcome, text="👁 Eyes Mouse For People With Mobility Challenges 👁",
             font=("Arial", 22, "bold"),
             bg="#1E1E2F", fg="white").pack(pady=25)

    status_label = tk.Label(welcome, text="", font=("Arial", 16),
                            bg="#1E1E2F", fg="white")
    status_label.pack(pady=15)

    type_text(status_label, "Initializing system... Please wait", 60)

    progress = tk.Canvas(welcome, width=500, height=25, bg="white")
    progress.pack(pady=30)

    def fill_progress(i=0):
        if i <= 500:
            progress.delete("bar")
            progress.create_rectangle(0, 0, i, 25, fill="green", tags="bar")
            welcome.after(8, lambda: fill_progress(i + 1))
        else:
            welcome.destroy()
            start_eyes_mouse_thread()

    fill_progress()


# -----------------------------
# 🙏 Thank You Page
# -----------------------------
def show_thank_you():
    # ensure root exists
    if not root.winfo_exists():
        return
    thank = tk.Toplevel(root)
    thank.title("Thank You")
    thank.geometry("600x300")
    thank.configure(bg="#1E1E2F")

    tk.Label(thank, text="🎯 Thank You for Using Eyes Mouse!",
             font=("Arial", 22, "bold"),
             bg="#1E1E2F", fg="white").pack(pady=40)

    tk.Label(thank, text="Project by Team Shariar💻",
             font=("Arial", 16),
             bg="#1E1E2F", fg="white").pack()

    tk.Button(thank, text="Exit", font=("Arial", 16, "bold"),
              bg="red", fg="white",
              command=root.destroy).pack(pady=25)


# -----------------------------
# 🚀 Start Button Action in Main Window
# -----------------------------
def start_program():
    start_button.config(state=tk.DISABLED)
    show_welcome()


# -----------------------------
# 🔐 Desktop-size Login Window (Email Login)
# -----------------------------
def show_login():
    login = tk.Tk()
    login.title("Login")
    login.geometry("800x500")  # Desktop size
    login.configure(bg="#1E1E2F")

    # Center the window on screen (approx)
    try:
        screen_w = login.winfo_screenwidth()
        screen_h = login.winfo_screenheight()
        x = int((screen_w / 2) - (800 / 2))
        y = int((screen_h / 2) - (500 / 2))
        login.geometry(f"800x500+{x}+{y}")
    except Exception:
        pass

    tk.Label(login, text="🔐 User Login", font=("Arial", 28, "bold"),
             bg="#1E1E2F", fg="white").pack(pady=30)

    # Email Label + Entry
    tk.Label(login, text="Email Address:", font=("Arial", 16),
             bg="#1E1E2F", fg="white").pack(pady=(10, 0))
    email_entry = tk.Entry(login, font=("Arial", 16), width=35)
    email_entry.pack(pady=8)

    # Password Label + Entry
    tk.Label(login, text="Password:", font=("Arial", 16),
             bg="#1E1E2F", fg="white").pack(pady=(10, 0))
    password_entry = tk.Entry(login, font=("Arial", 16), width=35, show="*")
    password_entry.pack(pady=8)

    # Show/hide password checkbox
    def toggle_password():
        if password_entry.cget('show') == '':
            password_entry.config(show='*')
            toggle_btn.config(text="Show")
        else:
            password_entry.config(show='')
            toggle_btn.config(text="Hide")

    toggle_btn = tk.Button(login, text="Show", font=("Arial", 10), command=toggle_password)
    toggle_btn.pack(pady=(0, 5))

    def check_login():
        email = email_entry.get().strip()
        pwd = password_entry.get()

        if email == DEFAULT_EMAIL and pwd == DEFAULT_PASS:
            messagebox.showinfo("Success", "Login Successful!")
            login.destroy()
            # open main window
            show_main_window()
        else:
            messagebox.showerror("Error", "Invalid Email or Password")

    # Login Button
    tk.Button(login, text="Login", font=("Arial", 18, "bold"),
              bg="green", fg="white", width=18,
              command=check_login).pack(pady=18)

    # Optional info label
    tk.Label(login, text=f"Default Email: {DEFAULT_EMAIL}  |  Default Pass: {DEFAULT_PASS}",
             font=("Arial", 10), bg="#1E1E2F", fg="lightgrey").pack(side="bottom", pady=12)

    login.mainloop()


# -----------------------------
# 🪟 Main Tkinter Window (Launched after successful login)
# -----------------------------
def show_main_window():
    global root, start_button
    root = tk.Tk()
    root.title("Eyes Mouse Controller")
    root.geometry("800x450")
    root.configure(bg="#1E1E2F")

    # Center the main window
    try:
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = int((screen_w / 2) - (800 / 2))
        y = int((screen_h / 2) - (450 / 2))
        root.geometry(f"800x450+{x}+{y}")
    except Exception:
        pass

    tk.Label(root, text="👁 Eyes Mouse For People With Mobility Challenges 👁",
             font=("Arial", 22, "bold"),
             bg="#1E1E2F", fg="white").pack(pady=30)

    tk.Label(root, text="Project by Team Shariar💻",
             font=("Arial", 16),
             bg="#1E1E2F", fg="white").pack()

    start_button = tk.Button(root, text="Let's Open", font=("Arial", 20, "bold"),
                             bg="green", fg="white", command=start_program)
    start_button.pack(pady=25)

    exit_button = tk.Button(root, text="EXIT", font=("Arial", 16, "bold"),
                            bg="red", fg="white", command=root.destroy)
    exit_button.pack(pady=10)

    tk.Label(root, text="(When camera window opens: press 'q' to quit the eye-mouse)",
             font=("Arial", 12),
             bg="#1E1E2F", fg="white").pack(pady=12)

    root.mainloop()


# -----------------------------------
# 🔥 START PROGRAM → OPEN LOGIN PAGE
# -----------------------------------
if __name__ == "__main__":
    show_login()
