import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import io
from datetime import datetime
import random
import cv2
import threading
import numpy as np
import requests
import csv
from io import StringIO

class QuizGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Brain Buster Quiz Game")
        
        # Set fullscreen mode
        self.root.attributes('-fullscreen', True)
        
        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Tab switching detection
        self.tab_switches = 0
        self.root.bind('<FocusOut>', self.on_focus_out)
        self.root.bind('<FocusIn>', self.on_focus_in)
        
        # Bind escape key to exit fullscreen
        self.root.bind('<Escape>', lambda e: self.toggle_fullscreen())
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        
        # Create gradient background
        self.create_gradient_background()
        
        # Motivational quotes
        self.quotes = [
            "Believe you can and you're halfway there!",
            "The only way to do great work is to love what you do.",
            "Success is not final, failure is not fatal: it is the courage to continue that counts.",
            "Your limitation—it's only your imagination.",
            "Push yourself, because no one else is going to do it for you.",
            "Great things never come from comfort zones.",
            "Dream it. Wish it. Do it.",
            "Success doesn't just find you. You have to go out and get it.",
            "The harder you work for something, the greater you'll feel when you achieve it.",
            "Dream bigger. Do bigger."
        ]
        
        # Load questions from Google Sheet
        self.all_questions = []
        self.load_questions_from_sheet()
        
        # Quiz data - will be populated with random selection
        self.questions = ()
        self.options = ()
        self.answers = ()
        self.select_random_questions()
        
        self.guesses = []
        self.skipped_questions = []
        self.score = 0
        self.question_num = 0
        
        # Eye tracking variables
        self.eye_tracking_active = False
        self.mouse_x = self.screen_width // 2
        self.mouse_y = self.screen_height // 2
        
        # Camera and face tracking
        self.camera_active = False
        self.cap = None
        self.face_cascade = None
        self.eye_cascade = None
        self.camera_frame = None
        self.face_detected = True
        self.eyes_looking_away = False
        self.looking_away_count = 0
        self.body_movement_warnings = 0
        self.last_face_position = None
        self.monitoring = False
        
        # Initialize camera
        self.init_camera()
        
        # Create UI elements
        self.create_widgets()
        self.display_question()
        self.update_datetime()
        self.start_eye_tracking()
        self.start_camera_monitoring()
    
    def load_questions_from_sheet(self):
        """Load questions from Google Sheet CSV export"""
        try:
            # Google Sheets CSV export URL
            sheet_id = "1xKbWWQ39_q6aR17uy9xZMi0HaDnt38TCflwgS2UB4Kc"
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            
            response = requests.get(csv_url, timeout=10)
            response.raise_for_status()
            
            # Parse CSV
            csv_reader = csv.DictReader(StringIO(response.text))
            
            for row in csv_reader:
                if row.get('Question') and row.get('Option A'):
                    question_data = {
                        'question': row['Question'],
                        'options': [
                            row['Option A'],
                            row['Option B'],
                            row['Option C'],
                            row['Option D']
                        ],
                        'correct_answer': row['Correct Answer'].strip()
                    }
                    self.all_questions.append(question_data)
            
            messagebox.showinfo("Success", f"Loaded {len(self.all_questions)} questions from sheet!")
            
        except Exception as e:
            messagebox.showwarning("Load Error", f"Could not load questions from sheet: {e}\nUsing default questions.")
            # Fallback to default questions
            self.all_questions = [
                {
                    'question': "How many elements are in periodic table?",
                    'options': ["116", "117", "118", "119"],
                    'correct_answer': "C"
                },
                {
                    'question': "Which is the most abundant gas in the atmosphere?",
                    'options': ["Nitrogen", "Oxygen", "CO2", "Hydrogen"],
                    'correct_answer': "A"
                },
                {
                    'question': "Which animal lays the largest eggs?",
                    'options': ["Whale", "Crocodile", "Elephant", "Ostrich"],
                    'correct_answer': "D"
                },
                {
                    'question': "How many bones are in the human body?",
                    'options': ["206", "207", "208", "204"],
                    'correct_answer': "A"
                },
                {
                    'question': "Which is the hottest planet in our solar system?",
                    'options': ["Mercury", "Venus", "Earth", "Mars"],
                    'correct_answer': "B"
                }
            ]
    
    def select_random_questions(self, num_questions=5):
        """Select random questions from loaded questions"""
        if len(self.all_questions) < num_questions:
            num_questions = len(self.all_questions)
        
        selected = random.sample(self.all_questions, num_questions)
        
        self.questions = tuple(q['question'] for q in selected)
        self.options = tuple(tuple(q['options']) for q in selected)
        
        # Map correct answers to letter format (A, B, C, D)
        self.answers = tuple(self.convert_answer_to_letter(q['correct_answer'], q['options']) for q in selected)
    
    def convert_answer_to_letter(self, correct_answer, options):
        """Convert correct answer to A, B, C, or D"""
        # If already a letter, return it
        if correct_answer in ['A', 'B', 'C', 'D']:
            return correct_answer
        
        # Otherwise, find the index of the correct answer in options
        correct_answer_clean = correct_answer.strip()
        for idx, option in enumerate(options):
            if option.strip() == correct_answer_clean:
                return chr(ord('A') + idx)
        
        # Default to A if not found
        return 'A'
    
    def init_camera(self):
        """Initialize camera and face detection"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showwarning("Camera Error", "Could not access camera. Proceeding without camera monitoring.")
                return
            
            try:
                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
                self.camera_active = True
            except Exception as e:
                messagebox.showwarning("Detection Error", f"Could not load face detection models: {e}")
                return
                
        except Exception as e:
            messagebox.showwarning("Camera Error", f"Could not initialize camera: {e}")
    
    def start_camera_monitoring(self):
        """Start camera monitoring in a separate thread"""
        if self.camera_active:
            self.monitoring = True
            self.camera_thread = threading.Thread(target=self.monitor_camera, daemon=True)
            self.camera_thread.start()
            self.update_camera_display()
    
    def monitor_camera(self):
        """Monitor camera for face and eye movements"""
        while self.monitoring and self.camera_active:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                self.face_detected = False
                self.looking_away_count += 1
                if self.looking_away_count > 30:
                    self.handle_face_not_detected()
                    self.looking_away_count = 0
            else:
                self.face_detected = True
                self.looking_away_count = 0
                
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    current_position = (x, y, w, h)
                    if self.last_face_position is not None:
                        dx = abs(x - self.last_face_position[0])
                        dy = abs(y - self.last_face_position[1])
                        dw = abs(w - self.last_face_position[2])
                        
                        if dx > 50 or dy > 50 or dw > 30:
                            self.body_movement_warnings += 1
                            if self.body_movement_warnings > 5:
                                self.handle_excessive_movement()
                                self.body_movement_warnings = 0
                    
                    self.last_face_position = current_position
                    
                    roi_gray = gray[y:y+h, x:x+w]
                    roi_color = frame[y:y+h, x:x+w]
                    eyes = self.eye_cascade.detectMultiScale(roi_gray)
                    
                    for (ex, ey, ew, eh) in eyes:
                        cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (255, 0, 0), 2)
                    
                    if len(eyes) < 2:
                        self.eyes_looking_away = True
                    else:
                        self.eyes_looking_away = False
            
            self.camera_frame = frame
    
    def handle_face_not_detected(self):
        """Handle when face is not detected"""
        if self.question_num < len(self.questions) and self.monitoring:
            self.root.after(0, lambda: messagebox.showerror(
                "Face Not Detected",
                "⚠️ FACE NOT DETECTED!\n\nYou must remain in front of the camera.\n\nQuiz terminated for security reasons."
            ))
            self.root.after(0, self.show_results_terminated)
    
    def handle_excessive_movement(self):
        """Handle excessive body movement"""
        if self.question_num < len(self.questions) and self.monitoring and not hasattr(self, '_movement_warning_shown'):
            self._movement_warning_shown = True
            self.root.after(0, lambda: messagebox.showwarning(
                "Excessive Movement",
                "⚠️ EXCESSIVE BODY MOVEMENT DETECTED!\n\nPlease remain still during the quiz.\n\nThis is your warning."
            ))
            # Reset the warning flag after 5 seconds so it can warn again if needed
            self.root.after(5000, lambda: delattr(self, '_movement_warning_shown') if hasattr(self, '_movement_warning_shown') else None)
    
    def update_camera_display(self):
        """Update camera feed display"""
        if self.camera_active and self.monitoring and self.camera_frame is not None:
            frame_rgb = cv2.cvtColor(self.camera_frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (200, 150))
            img = Image.fromarray(frame_resized)
            imgtk = ImageTk.PhotoImage(image=img)
            
            if hasattr(self, 'camera_label') and self.camera_label.winfo_exists():
                self.camera_label.imgtk = imgtk
                self.camera_label.configure(image=imgtk)
            
            if hasattr(self, 'camera_status_label') and self.camera_status_label.winfo_exists():
                if self.face_detected:
                    status_text = "✓ Face Detected"
                    status_color = "#00FF00"
                else:
                    status_text = "✗ Face Not Detected"
                    status_color = "#FF0000"
                self.camera_status_label.config(text=status_text, fg=status_color)
        
        if self.monitoring:
            self.root.after(30, self.update_camera_display)
    
    def stop_camera(self):
        """Stop camera monitoring"""
        self.monitoring = False
        self.camera_active = False
        if self.cap is not None:
            self.cap.release()
    
    def on_focus_out(self, event):
        """Detect when user switches tabs/windows - STOP QUIZ"""
        self.tab_switches += 1
        if self.question_num < len(self.questions):
            messagebox.showerror(
                "Quiz Terminated",
                f"❌ TAB SWITCH DETECTED!\n\nThe quiz has been terminated due to suspicious activity.\n\nTab switches: {self.tab_switches}\n\nPlease restart to try again."
            )
            self.show_results_terminated()
    
    def on_focus_in(self, event):
        """Detect when user returns to the quiz"""
        pass
    
    def start_eye_tracking(self):
        """Start tracking mouse movement as eye proxy"""
        self.eye_tracking_active = True
        self.root.bind('<Motion>', self.track_mouse)
        self.create_eye_follower()
    
    def track_mouse(self, event):
        """Track mouse position"""
        self.mouse_x = event.x
        self.mouse_y = event.y
    
    def create_eye_follower(self):
        """Create eyes that follow the mouse"""
        self.eye_canvas = tk.Canvas(
            self.root,
            width=120,
            height=60,
            bg='#1a1a2e',
            highlightthickness=0
        )
        self.eye_canvas.place(x=20, y=20)
        
        self.left_eye_bg = self.eye_canvas.create_oval(10, 15, 40, 45, fill='white', outline='#FFD700', width=2)
        self.left_pupil = self.eye_canvas.create_oval(20, 25, 30, 35, fill='black')
        
        self.right_eye_bg = self.eye_canvas.create_oval(50, 15, 80, 45, fill='white', outline='#FFD700', width=2)
        self.right_pupil = self.eye_canvas.create_oval(60, 25, 70, 35, fill='black')
        
        self.eye_label = tk.Label(
            self.root,
            text="👀 Watching",
            font=("Arial", 10, "bold"),
            bg='#1a1a2e',
            fg='#FFD700'
        )
        self.eye_label.place(x=25, y=85)
        
        self.update_eye_position()
    
    def update_eye_position(self):
        """Update pupil positions to follow mouse"""
        if self.eye_tracking_active and hasattr(self, 'left_pupil'):
            import math
            
            left_eye_x, left_eye_y = 25, 30
            dx_left = self.mouse_x - (20 + left_eye_x)
            dy_left = self.mouse_y - (20 + left_eye_y)
            
            angle_left = math.atan2(dy_left, dx_left)
            distance_left = min(5, math.sqrt(dx_left**2 + dy_left**2) / 50)
            
            pupil_x_left = left_eye_x + distance_left * math.cos(angle_left)
            pupil_y_left = left_eye_y + distance_left * math.sin(angle_left)
            
            self.eye_canvas.coords(
                self.left_pupil,
                pupil_x_left - 5, pupil_y_left - 5,
                pupil_x_left + 5, pupil_y_left + 5
            )
            
            right_eye_x, right_eye_y = 65, 30
            dx_right = self.mouse_x - (20 + right_eye_x)
            dy_right = self.mouse_y - (20 + right_eye_y)
            
            angle_right = math.atan2(dy_right, dx_right)
            distance_right = min(5, math.sqrt(dx_right**2 + dy_right**2) / 50)
            
            pupil_x_right = right_eye_x + distance_right * math.cos(angle_right)
            pupil_y_right = right_eye_y + distance_right * math.sin(angle_right)
            
            self.eye_canvas.coords(
                self.right_pupil,
                pupil_x_right - 5, pupil_y_right - 5,
                pupil_x_right + 5, pupil_y_right + 5
            )
            
            self.root.after(50, self.update_eye_position)
    
    def update_datetime(self):
        """Update date and time display"""
        if hasattr(self, 'datetime_label') and self.datetime_label.winfo_exists():
            now = datetime.now()
            date_str = now.strftime("%A, %B %d, %Y")
            time_str = now.strftime("%I:%M:%S %p")
            self.datetime_label.config(text=f"📅 {date_str} | ⏰ {time_str}")
            self.root.after(1000, self.update_datetime)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)
    
    def create_gradient_background(self):
        """Create a beautiful gradient background"""
        width = self.screen_width
        height = self.screen_height
        
        gradient = Image.new('RGB', (width, height), '#1a1a2e')
        draw = ImageDraw.Draw(gradient)
        
        for i in range(height):
            r = int(26 + (128 - 26) * (i / height))
            g = int(26 + (0 - 26) * (i / height))
            b = int(46 + (128 - 46) * (i / height))
            draw.rectangle([(0, i), (width, i+1)], fill=(r, g, b))
        
        self.bg_image = ImageTk.PhotoImage(gradient)
        
        self.bg_label = tk.Label(self.root, image=self.bg_image)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    
    def create_colorful_emoji(self, canvas, emoji_text, x, y, size=100):
        """Create colorful emoji with glow effect"""
        glow_colors = ['#FFD700', '#FFA500', '#FF6347', '#FF1493', '#00FFFF', '#00FF00']
        
        for i, color in enumerate(glow_colors):
            offset = (len(glow_colors) - i) * 2
            canvas.create_text(
                x, y,
                text=emoji_text,
                font=("Arial", size + offset, "bold"),
                fill=color,
                tags="emoji_glow"
            )
        
        canvas.create_text(
            x, y,
            text=emoji_text,
            font=("Arial", size, "bold"),
            fill='white',
            tags="emoji_main"
        )
    
    def create_widgets(self):
        self.datetime_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 12, "bold"),
            bg='#1a1a2e',
            fg='#00FFFF'
        )
        self.datetime_label.place(relx=0.5, rely=0.02, anchor=tk.CENTER)
        
        exit_btn = tk.Button(
            self.root,
            text="✖",
            font=("Arial", 16, "bold"),
            bg="#e74c3c",
            fg="white",
            cursor="hand2",
            command=self.root.quit,
            relief=tk.RAISED,
            bd=3,
            padx=15,
            pady=5
        )
        exit_btn.place(x=self.screen_width-70, y=20)
        
        self.tab_counter_label = tk.Label(
            self.root,
            text="⚠️ Tab Switches: 0",
            font=("Arial", 11, "bold"),
            bg='#1a1a2e',
            fg='#FF6347'
        )
        self.tab_counter_label.place(x=self.screen_width-220, y=65)
        
        if self.camera_active:
            camera_container = tk.Frame(self.root, bg='#1a1a2e')
            camera_container.place(x=self.screen_width-230, y=100)
            
            tk.Label(
                camera_container,
                text="📹 Camera Monitor",
                font=("Arial", 11, "bold"),
                bg='#1a1a2e',
                fg='#FFD700'
            ).pack()
            
            self.camera_label = tk.Label(
                camera_container,
                bg='#000000',
                width=200,
                height=150
            )
            self.camera_label.pack(pady=5)
            
            self.camera_status_label = tk.Label(
                camera_container,
                text="✓ Face Detected",
                font=("Arial", 10, "bold"),
                bg='#1a1a2e',
                fg='#00FF00'
            )
            self.camera_status_label.pack()
        
        self.emoji_canvas = tk.Canvas(
            self.root,
            width=200,
            height=150,
            bg='#1a1a2e',
            highlightthickness=0
        )
        self.emoji_canvas.place(relx=0.5, rely=0.10, anchor=tk.CENTER)
        self.create_colorful_emoji(self.emoji_canvas, "🧠", 100, 75, 80)
        
        self.title_label = tk.Label(
            self.root,
            text="BRAIN BUSTER QUIZ GAME",
            font=("Arial", 42, "bold"),
            bg='#1a1a2e',
            fg='#FFD700'
        )
        self.title_label.place(relx=0.5, rely=0.20, anchor=tk.CENTER)
        
        self.animate_title()
        
        self.quote_label = tk.Label(
            self.root,
            text=f"💭 {random.choice(self.quotes)}",
            font=("Arial", 14, "italic"),
            bg='#1a1a2e',
            fg='#FFD700',
            wraplength=800
        )
        self.quote_label.place(relx=0.5, rely=0.26, anchor=tk.CENTER)
        
        self.subtitle_label = tk.Label(
            self.root,
            text="⭐ Test Your Knowledge & Challenge Your Mind! ⭐",
            font=("Arial", 16, "italic"),
            bg='#1a1a2e',
            fg='#00FFFF'
        )
        self.subtitle_label.place(relx=0.5, rely=0.31, anchor=tk.CENTER)
        
        self.counter_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 16, "bold"),
            bg='#1a1a2e',
            fg='#00FF00'
        )
        self.counter_label.place(relx=0.5, rely=0.37, anchor=tk.CENTER)
        
        frame_width = min(900, self.screen_width - 200)
        frame_height = min(400, self.screen_height - 400)
        
        self.question_frame = tk.Frame(
            self.root, 
            bg="#16213e",
            relief=tk.RAISED,
            bd=5,
            highlightbackground="#FFD700",
            highlightthickness=3
        )
        self.question_frame.place(relx=0.5, rely=0.60, anchor=tk.CENTER, 
                                 width=frame_width, height=frame_height)
        
        self.question_label = tk.Label(
            self.question_frame,
            text="",
            font=("Arial", 18, "bold"),
            bg="#16213e",
            fg="#FFD700",
            wraplength=frame_width-100,
            justify=tk.LEFT
        )
        self.question_label.pack(pady=25, padx=30)
        
        self.selected_option = tk.StringVar()
        self.option_buttons = []
        self.option_frames = []
        
        option_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        option_letters = ['A', 'B', 'C', 'D']
        
        for i in range(4):
            # Create a frame for each option with border
            opt_frame = tk.Frame(
                self.question_frame,
                bg="#16213e",
                relief=tk.RAISED,
                bd=2,
                cursor="hand2"
            )
            opt_frame.pack(anchor=tk.W, padx=40, pady=8, fill=tk.X)
            self.option_frames.append(opt_frame)
            
            # Bind click to the frame
            opt_frame.bind("<Button-1>", lambda e, idx=i: self.select_option(idx))
            
            # Create a container for letter box and text
            inner_frame = tk.Frame(opt_frame, bg="#16213e", cursor="hand2")
            inner_frame.pack(fill=tk.X, padx=10, pady=10)
            inner_frame.bind("<Button-1>", lambda e, idx=i: self.select_option(idx))
            
            # Letter box
            letter_box = tk.Label(
                inner_frame,
                text=option_letters[i],
                font=("Arial", 16, "bold"),
                bg=option_colors[i],
                fg="white",
                width=3,
                relief=tk.RAISED,
                bd=2,
                cursor="hand2"
            )
            letter_box.pack(side=tk.LEFT, padx=10)
            letter_box.bind("<Button-1>", lambda e, idx=i: self.select_option(idx))
            
            # Radio button (hidden)
            btn = tk.Radiobutton(
                inner_frame,
                text="",
                variable=self.selected_option,
                value=option_letters[i],
                font=("Arial", 15, "bold"),
                bg="#16213e",
                fg=option_colors[i],
                selectcolor="#16213e",
                activebackground="#16213e",
                activeforeground="#FFFFFF",
                cursor="hand2",
                highlightthickness=0,
                padx=0
            )
            btn.pack(side=tk.LEFT, padx=5)
            btn.bind("<Button-1>", lambda e, idx=i: self.select_option(idx))
            
            # Option text
            text_label = tk.Label(
                inner_frame,
                text="",
                font=("Arial", 14, "bold"),
                bg="#16213e",
                fg=option_colors[i],
                wraplength=500,
                justify=tk.LEFT,
                cursor="hand2"
            )
            text_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
            text_label.bind("<Button-1>", lambda e, idx=i: self.select_option(idx))
            
            self.option_buttons.append((btn, text_label, opt_frame, letter_box))
        
        # Button frame for Submit and Skip buttons
        button_frame = tk.Frame(self.root, bg='#1a1a2e')
        button_frame.place(relx=0.5, rely=0.88, anchor=tk.CENTER)
        
        self.submit_btn = tk.Button(
            button_frame,
            text="✓ Submit Answer",
            font=("Arial", 18, "bold"),
            bg="#27ae60",
            fg="white",
            cursor="hand2",
            command=self.check_answer,
            relief=tk.RAISED,
            bd=5,
            padx=40,
            pady=15,
            activebackground="#229954"
        )
        self.submit_btn.pack(side=tk.LEFT, padx=10)
        
        # Skip button
        self.skip_btn = tk.Button(
            button_frame,
            text="⏭️ Skip Question",
            font=("Arial", 18, "bold"),
            bg="#f39c12",
            fg="white",
            cursor="hand2",
            command=self.skip_question,
            relief=tk.RAISED,
            bd=5,
            padx=40,
            pady=15,
            activebackground="#e67e22"
        )
        self.skip_btn.pack(side=tk.LEFT, padx=10)
        
        self.feedback_label = tk.Label(
            self.root,
            text="",
            font=("Arial", 16, "bold"),
            bg='#1a1a2e'
        )
        self.feedback_label.place(relx=0.5, rely=0.95, anchor=tk.CENTER)
    
    def animate_title(self):
        """Animate title with color changes"""
        colors = ['#FFD700', '#FF6347', '#00FF00', '#00FFFF', '#FF69B4', '#FFA500']
        self.color_index = 0
        
        def change_color():
            if hasattr(self, 'title_label') and self.title_label.winfo_exists():
                self.title_label.config(fg=colors[self.color_index % len(colors)])
                self.color_index += 1
                self.root.after(500, change_color)
        
        change_color()
    
    def display_question(self):
        if self.question_num < len(self.questions):
            if hasattr(self, 'tab_counter_label'):
                self.tab_counter_label.config(text=f"⚠️ Tab Switches: {self.tab_switches}")
            
            self.counter_label.config(
                text=f"📝 Question {self.question_num + 1} of {len(self.questions)} 📝"
            )
            
            self.question_label.config(text=self.questions[self.question_num])
            
            option_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
            for i in range(4):
                option_text = self.options[self.question_num][i]
                letter = chr(ord('A') + i)
                btn, text_label, opt_frame, letter_box = self.option_buttons[i]
                
                # Update text label
                text_label.config(text=option_text, fg=option_colors[i])
                
                # Reset frame appearance
                opt_frame.config(relief=tk.RAISED, bd=2, bg="#16213e")
                letter_box.config(bg=option_colors[i])
            
            self.selected_option.set("")
            self.feedback_label.config(text="")
            self.highlight_selected_option()
        else:
            self.show_results()
    
    def highlight_selected_option(self):
        """Highlight the currently selected option"""
        selected = self.selected_option.get()
        option_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        
        for i in range(4):
            btn, text_label, opt_frame, letter_box = self.option_buttons[i]
            letter = chr(ord('A') + i)
            
            if letter == selected:
                # Highlight selected option
                opt_frame.config(relief=tk.SUNKEN, bd=4, bg="#2a3a4e")
                letter_box.config(bg="#00FF00", fg="black", relief=tk.SUNKEN)
                text_label.config(fg="#00FF00")
            else:
                # Reset non-selected options
                opt_frame.config(relief=tk.RAISED, bd=2, bg="#16213e")
                letter_box.config(bg=option_colors[i], relief=tk.RAISED)
                text_label.config(fg=option_colors[i])
        
        # Check again after 100ms for continuous updating
        self.root.after(100, self.highlight_selected_option)
    
    def select_option(self, index):
        """Select an option when any part of it is clicked"""
        letter = chr(ord('A') + index)
        self.selected_option.set(letter)
    
    def skip_question(self):
        """Skip the current question"""
        self.skipped_questions.append(self.question_num + 1)
        self.guesses.append("SKIPPED")
        self.feedback_label.config(text="⏭️ Question Skipped!", fg="#FFA500")
        self.question_num += 1
        
        self.root.after(1500, self.display_question)
        self.submit_btn.config(state=tk.DISABLED)
        self.skip_btn.config(state=tk.DISABLED)
        self.root.after(1500, lambda: (self.submit_btn.config(state=tk.NORMAL), self.skip_btn.config(state=tk.NORMAL)))
    
    def check_answer(self):
        """Check if the selected answer is correct"""
        guess = self.selected_option.get()
        
        if not guess:
            messagebox.showwarning("Warning", "Please select an answer!")
            return
        
        self.guesses.append(guess)
        
        # Highlight the selected answer
        self.show_selected_answer(guess)
        
        if guess == self.answers[self.question_num]:
            self.score += 1
            self.feedback_label.config(text="✓ CORRECT! 🎉", fg="#00FF00")
            self.show_fireworks_animation()
        else:
            correct_answer = self.answers[self.question_num]
            self.feedback_label.config(
                text=f"✗ INCORRECT! 😞 Correct answer: {correct_answer}",
                fg="#FF0000"
            )
            self.show_thumbs_down_animation()
        
        self.question_num += 1
        
        self.root.after(1500, self.display_question)
        self.submit_btn.config(state=tk.DISABLED)
        self.skip_btn.config(state=tk.DISABLED)
        self.root.after(1500, lambda: (self.submit_btn.config(state=tk.NORMAL), self.skip_btn.config(state=tk.NORMAL)))
    
    def show_selected_answer(self, selected):
        """Show which answer the user selected"""
        option_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        
        for i in range(4):
            btn, text_label, opt_frame, letter_box = self.option_buttons[i]
            letter = chr(ord('A') + i)
            
            if letter == selected:
                opt_frame.config(relief=tk.SUNKEN, bd=4, bg="#2a3a4e")
                letter_box.config(bg="#00FF00", fg="black", relief=tk.SUNKEN)
                text_label.config(fg="#00FF00")
            else:
                opt_frame.config(relief=tk.RAISED, bd=2, bg="#16213e")
                letter_box.config(bg=option_colors[i], relief=tk.RAISED)
                text_label.config(fg=option_colors[i])
    
    def show_fireworks_animation(self):
        """Show colorful fireworks animation for correct answer"""
        self.fireworks = []
        colors = ['#FFD700', '#FF6347', '#00FF00', '#1E90FF', '#FF69B4', '#FFA500', 
                  '#00FFFF', '#FF1493', '#7FFF00', '#FF4500']
        
        for burst_num in range(8):
            x = 150 + (burst_num * (self.screen_width - 300) // 7)
            y = 200 + (burst_num % 2) * 100
            
            for angle in range(0, 360, 30):
                firework = tk.Label(
                    self.root,
                    text="✨",
                    font=("Arial", 25),
                    bg='#1a1a2e',
                    fg=colors[burst_num % len(colors)]
                )
                firework.place(x=x, y=y)
                self.fireworks.append(firework)
                self.animate_firework(firework, x, y, angle)
        
        self.root.after(1500, self.clear_fireworks)
    
    def animate_firework(self, firework, start_x, start_y, angle):
        """Animate individual firework particle"""
        import math
        
        distance = 0
        max_distance = 100
        
        def move():
            nonlocal distance
            if distance < max_distance:
                distance += 10
                rad = math.radians(angle)
                new_x = start_x + distance * math.cos(rad)
                new_y = start_y + distance * math.sin(rad)
                firework.place(x=new_x, y=new_y)
                
                if distance > max_distance * 0.7:
                    firework.config(font=("Arial", 18))
                
                self.root.after(30, move)
            else:
                firework.place_forget()
        
        move()
    
    def clear_fireworks(self):
        """Remove all firework elements"""
        for firework in self.fireworks:
            firework.destroy()
        self.fireworks = []
    
    def show_thumbs_down_animation(self):
        """Show animated sad emoji with thumbs down for wrong answer"""
        self.sad_emoji = tk.Label(
            self.root,
            text="😞",
            font=("Arial", 120),
            bg='#1a1a2e',
            fg='#FF6347'
        )
        self.sad_emoji.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        self.thumb_down = tk.Label(
            self.root,
            text="👎",
            font=("Arial", 100),
            bg='#1a1a2e',
            fg='#FF0000'
        )
        
        self.animate_sad_emoji()
        self.animate_thumb_gesture()
        
        self.root.after(1500, self.clear_sad_animation)
    
    def animate_sad_emoji(self):
        """Shake the sad emoji left and right"""
        positions = [0.5, 0.48, 0.5, 0.52, 0.5, 0.48, 0.5, 0.52, 0.5]
        colors = ['#FF6347', '#FF4500', '#FF1493', '#FF69B4', '#FF6347']
        
        def shake(index=0):
            if index < len(positions) and hasattr(self, 'sad_emoji'):
                self.sad_emoji.place(relx=positions[index], rely=0.5, anchor=tk.CENTER)
                if index < len(colors):
                    self.sad_emoji.config(fg=colors[index % len(colors)])
                self.root.after(80, lambda: shake(index + 1))
        
        shake()
    
    def animate_thumb_gesture(self):
        """Animate thumbs down sliding in from the side"""
        x_positions = list(range(self.screen_width, self.screen_width//2 - 150, -50))
        colors = ['#FF0000', '#FF4500', '#FF6347', '#FF1493', '#FF0000']
        
        def slide_in(index=0):
            if index < len(x_positions) and hasattr(self, 'thumb_down'):
                self.thumb_down.place(x=x_positions[index], 
                                     y=self.screen_height//2 - 50)
                
                self.thumb_down.config(fg=colors[index % len(colors)])
                
                size = 100 - (index % 3) * 8
                self.thumb_down.config(font=("Arial", size))
                
                self.root.after(60, lambda: slide_in(index + 1))
        
        slide_in()
    
    def clear_sad_animation(self):
        """Remove sad emoji animation elements"""
        if hasattr(self, 'sad_emoji'):
            self.sad_emoji.destroy()
        if hasattr(self, 'thumb_down'):
            self.thumb_down.destroy()
    
    def show_firecracker_animation(self):
        """Show intense firecracker animation on results page"""
        self.firecrackers = []
        
        for _ in range(30):
            x = random.randint(50, self.screen_width - 50)
            y = random.randint(50, self.screen_height - 50)
            
            for angle in range(0, 360, 15):
                firecracker = tk.Label(
                    self.root,
                    text=random.choice(['💥', '✨', '🎆', '🎇', '⭐']),
                    font=("Arial", random.randint(20, 40)),
                    bg='#1a1a2e',
                    fg=random.choice(['#FFD700', '#FF6347', '#00FF00', '#1E90FF', '#FF69B4', '#FFA500'])
                )
                firecracker.place(x=x, y=y)
                self.firecrackers.append(firecracker)
                self.animate_firecracker(firecracker, x, y, angle)
        
        self.root.after(5000, self.clear_firecrackers)
    
    def animate_firecracker(self, firecracker, start_x, start_y, angle):
        """Animate individual firecracker particle"""
        import math
        
        distance = 0
        max_distance = random.randint(80, 150)
        
        def explode():
            nonlocal distance
            if distance < max_distance and firecracker.winfo_exists():
                distance += random.randint(8, 15)
                rad = math.radians(angle)
                new_x = start_x + distance * math.cos(rad)
                new_y = start_y + distance * math.sin(rad)
                firecracker.place(x=new_x, y=new_y)
                
                if random.random() > 0.7:
                    size = random.randint(15, 35)
                    firecracker.config(font=("Arial", size))
                
                self.root.after(40, explode)
            else:
                if firecracker.winfo_exists():
                    firecracker.place_forget()
        
        explode()
    
    def clear_firecrackers(self):
        """Remove all firecracker elements"""
        for firecracker in self.firecrackers:
            if firecracker.winfo_exists():
                firecracker.destroy()
        self.firecrackers = []
    
    def show_clapping_cartoon(self):
        """Show animated clapping cartoon character"""
        self.cartoon_body = tk.Label(
            self.root,
            text="🙂",
            font=("Arial", 150),
            bg='#1a1a2e'
        )
        self.cartoon_body.place(relx=0.5, rely=0.15, anchor=tk.CENTER)
        
        self.left_hand = tk.Label(
            self.root,
            text="👏",
            font=("Arial", 80),
            bg='#1a1a2e'
        )
        
        self.right_hand = tk.Label(
            self.root,
            text="👏",
            font=("Arial", 80),
            bg='#1a1a2e'
        )
        
        self.confetti = []
        self.create_confetti()
        
        self.animate_clapping()
        
        self.root.after(3000, self.stop_clapping)
    
    def create_confetti(self):
        """Create colorful confetti particles"""
        confetti_emojis = ['🎉', '🎊', '✨', '⭐', '🌟', '💫']
        colors = ['#FFD700', '#FF6347', '#00FF00', '#1E90FF', '#FF69B4', '#FFA500']
        
        for i in range(30):
            x = random.randint(100, self.screen_width - 100)
            y = random.randint(0, 150)
            
            confetti = tk.Label(
                self.root,
                text=random.choice(confetti_emojis),
                font=("Arial", random.randint(20, 40)),
                bg='#1a1a2e',
                fg=random.choice(colors)
            )
            confetti.place(x=x, y=y)
            self.confetti.append(confetti)
            self.animate_confetti(confetti, x, y)
    
    def animate_confetti(self, confetti, start_x, start_y):
        """Animate confetti falling down"""
        y = start_y
        
        def fall():
            nonlocal y
            if y < self.screen_height and confetti.winfo_exists():
                y += random.randint(5, 15)
                x_offset = random.randint(-5, 5)
                confetti.place(x=start_x + x_offset, y=y)
                self.root.after(50, fall)
        
        fall()
    
    def animate_clapping(self):
        """Animate hands clapping"""
        self.clap_count = 0
        positions = [
            (0.35, 0.18, 0.65, 0.18),
            (0.48, 0.18, 0.52, 0.18),
        ]
        
        def clap():
            if self.clap_count < 12 and hasattr(self, 'left_hand') and hasattr(self, 'right_hand'):
                pos_index = self.clap_count % 2
                left_x, left_y, right_x, right_y = positions[pos_index]
                
                self.left_hand.place(relx=left_x, rely=left_y, anchor=tk.CENTER)
                self.right_hand.place(relx=right_x, rely=right_y, anchor=tk.CENTER)
                
                colors = ['#FFD700', '#FF6347', '#00FF00', '#1E90FF', '#FF69B4']
                if hasattr(self, 'cartoon_body'):
                    self.cartoon_body.config(fg=colors[self.clap_count % len(colors)])
                
                self.clap_count += 1
                self.root.after(250, clap)
        
        clap()
    
    def stop_clapping(self):
        """Remove clapping animation"""
        if hasattr(self, 'cartoon_body'):
            self.cartoon_body.destroy()
        if hasattr(self, 'left_hand'):
            self.left_hand.destroy()
        if hasattr(self, 'right_hand'):
            self.right_hand.destroy()
        
        for confetti in self.confetti:
            confetti.destroy()
        self.confetti = []
    
    def show_results_terminated(self):
        """Show results when quiz is terminated due to tab switch"""
        self.eye_tracking_active = False
        self.stop_camera()
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.create_gradient_background()
        
        results_frame = tk.Frame(self.root, bg='#1a1a2e')
        results_frame.place(relx=0.5, rely=0.50, anchor=tk.CENTER)
        
        trophy_canvas = tk.Canvas(
            results_frame,
            width=200,
            height=150,
            bg='#1a1a2e',
            highlightthickness=0
        )
        trophy_canvas.pack(pady=10)
        self.create_colorful_emoji(trophy_canvas, "⛔", 100, 75, 90)
        
        tk.Label(
            results_frame,
            text="QUIZ TERMINATED",
            font=("Arial", 42, "bold"),
            bg='#1a1a2e',
            fg='#FF0000'
        ).pack(pady=10)
        
        tk.Label(
            results_frame,
            text="❌ Tab Switch Detected ❌",
            font=("Arial", 24, "bold"),
            bg='#1a1a2e',
            fg='#FF6347'
        ).pack(pady=10)
        
        tk.Label(
            results_frame,
            text="The quiz was terminated due to suspicious activity.",
            font=("Arial", 16),
            bg='#1a1a2e',
            fg='#FFA500',
            wraplength=600
        ).pack(pady=10)
        
        questions_attempted = len(self.guesses)
        if questions_attempted > 0:
            score_percentage = int(self.score / questions_attempted * 100)
        else:
            score_percentage = 0
        
        tk.Label(
            results_frame,
            text=f"Questions Completed: {questions_attempted} / {len(self.questions)}",
            font=("Arial", 18, "bold"),
            bg='#1a1a2e',
            fg="#00FFFF"
        ).pack(pady=10)
        
        tk.Label(
            results_frame,
            text=f"Score Before Termination: {self.score} correct",
            font=("Arial", 18, "bold"),
            bg='#1a1a2e',
            fg="#FFD700"
        ).pack(pady=5)
        
        tk.Label(
            results_frame,
            text=f"⚠️ Tab Switches: {self.tab_switches}",
            font=("Arial", 20, "bold"),
            bg='#1a1a2e',
            fg="#FF0000"
        ).pack(pady=15)
        
        tk.Label(
            results_frame,
            text="⚠️ Stay focused and avoid switching tabs during the quiz! ⚠️",
            font=("Arial", 14, "italic"),
            bg='#1a1a2e',
            fg="#FF69B4",
            wraplength=700
        ).pack(pady=10)
        
        button_frame = tk.Frame(results_frame, bg='#1a1a2e')
        button_frame.pack(pady=30)
        
        tk.Button(
            button_frame,
            text="🔄 Try Again",
            font=("Arial", 18, "bold"),
            bg="#3498db",
            fg="white",
            cursor="hand2",
            command=self.restart_quiz,
            relief=tk.RAISED,
            bd=5,
            padx=50,
            pady=15,
            activebackground="#2980b9"
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="✖ Quit Game",
            font=("Arial", 18, "bold"),
            bg="#e74c3c",
            fg="white",
            cursor="hand2",
            command=self.root.quit,
            relief=tk.RAISED,
            bd=5,
            padx=50,
            pady=15,
            activebackground="#c0392b"
        ).pack(side=tk.LEFT, padx=10)
    
    def show_results(self):
        self.eye_tracking_active = False
        self.stop_camera()
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.create_gradient_background()
        
        self.show_firecracker_animation()
        self.show_clapping_cartoon()
        
        results_frame = tk.Frame(self.root, bg='#1a1a2e')
        results_frame.place(relx=0.5, rely=0.60, anchor=tk.CENTER)
        
        trophy_canvas = tk.Canvas(
            results_frame,
            width=200,
            height=150,
            bg='#1a1a2e',
            highlightthickness=0
        )
        trophy_canvas.pack(pady=10)
        self.create_colorful_emoji(trophy_canvas, "🏆", 100, 75, 90)
        
        tk.Label(
            results_frame,
            text="QUIZ RESULTS",
            font=("Arial", 38, "bold"),
            bg='#1a1a2e',
            fg='#FFD700'
        ).pack(pady=10)
        
        score_percentage = int(self.score / len(self.questions) * 100)
        
        if score_percentage >= 80:
            score_color = "#00FF00"
            emoji = "🌟"
            message = "Outstanding!"
            quote = "Excellence is not a skill, it's an attitude!"
        elif score_percentage >= 60:
            score_color = "#FFA500"
            emoji = "👍"
            message = "Good Job!"
            quote = "Good, but you can be great!"
        else:
            score_color = "#FF6347"
            emoji = "📚"
            message = "Keep Learning!"
            quote = "Every expert was once a beginner. Keep trying!"
        
        tk.Label(
            results_frame,
            text=f"{emoji} {message} {emoji}",
            font=("Arial", 22, "bold"),
            bg='#1a1a2e',
            fg=score_color
        ).pack(pady=5)
        
        tk.Label(
            results_frame,
            text=f"💭 {quote}",
            font=("Arial", 14, "italic"),
            bg='#1a1a2e',
            fg='#FFD700',
            wraplength=600
        ).pack(pady=8)
        
        tk.Label(
            results_frame,
            text=f"Your Score: {score_percentage}%",
            font=("Arial", 30, "bold"),
            bg='#1a1a2e',
            fg=score_color
        ).pack(pady=10)
        
        tk.Label(
            results_frame,
            text=f"✓ Correct: {self.score} / {len(self.questions)}",
            font=("Arial", 20),
            bg='#1a1a2e',
            fg="#00FFFF"
        ).pack(pady=10)
        
        if len(self.skipped_questions) > 0:
            tk.Label(
                results_frame,
                text=f"⏭️ Skipped: {len(self.skipped_questions)} questions",
                font=("Arial", 16),
                bg='#1a1a2e',
                fg="#FFA500"
            ).pack(pady=5)
        
        if self.tab_switches > 0:
            tk.Label(
                results_frame,
                text=f"⚠️ Tab switches detected: {self.tab_switches}",
                font=("Arial", 14, "bold"),
                bg='#1a1a2e',
                fg="#FF6347"
            ).pack(pady=5)
        
        button_frame = tk.Frame(results_frame, bg='#1a1a2e')
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="🔄 Play Again",
            font=("Arial", 18, "bold"),
            bg="#3498db",
            fg="white",
            cursor="hand2",
            command=self.restart_quiz,
            relief=tk.RAISED,
            bd=5,
            padx=50,
            pady=15,
            activebackground="#2980b9"
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="✖ Quit Game",
            font=("Arial", 18, "bold"),
            bg="#e74c3c",
            fg="white",
            cursor="hand2",
            command=self.root.quit,
            relief=tk.RAISED,
            bd=5,
            padx=50,
            pady=15,
            activebackground="#c0392b"
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Label(
            results_frame,
            text="",
            bg='#1a1a2e'
        ).pack(pady=5)
        
        def show_answers():
            answer_window = tk.Toplevel(self.root)
            answer_window.title("Answer Key")
            answer_window.geometry("600x500")
            answer_window.configure(bg="#16213e")
            
            tk.Label(
                answer_window,
                text="📊 Answer Key",
                font=("Arial", 24, "bold"),
                bg="#16213e",
                fg="#FFD700"
            ).pack(pady=20)
            
            for i in range(len(self.questions)):
                if self.guesses[i] == "SKIPPED":
                    text = f"⏭️ Q{i+1}: Skipped  |  Correct: {self.answers[i]}"
                    color = "#FFA500"
                else:
                    color = "#00FF00" if self.guesses[i] == self.answers[i] else "#FF6347"
                    icon = "✓" if self.guesses[i] == self.answers[i] else "✗"
                    text = f"{icon} Q{i+1}: Your answer: {self.guesses[i]}  |  Correct: {self.answers[i]}"
                
                tk.Label(
                    answer_window,
                    text=text,
                    font=("Arial", 14, "bold"),
                    bg="#16213e",
                    fg=color
                ).pack(pady=8)
            
            tk.Button(
                answer_window,
                text="Close",
                font=("Arial", 14, "bold"),
                bg="#e74c3c",
                fg="white",
                command=answer_window.destroy,
                padx=30,
                pady=10
            ).pack(pady=20)
        
        tk.Button(
            results_frame,
            text="📋 View Answer Key",
            font=("Arial", 16, "bold"),
            bg="#9b59b6",
            fg="white",
            cursor="hand2",
            command=show_answers,
            relief=tk.RAISED,
            bd=4,
            padx=40,
            pady=12,
            activebackground="#8e44ad"
        ).pack(pady=10)
    
    def restart_quiz(self):
        self.guesses = []
        self.skipped_questions = []
        self.score = 0
        self.question_num = 0
        self.tab_switches = 0
        self.looking_away_count = 0
        self.body_movement_warnings = 0
        self.last_face_position = None
        
        self.stop_camera()
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.init_camera()
        self.select_random_questions()
        
        self.create_gradient_background()
        
        self.create_widgets()
        self.display_question()
        self.update_datetime()
        self.start_eye_tracking()
        self.start_camera_monitoring()


if __name__ == "__main__":
    root = tk.Tk()
    app = QuizGame(root)
    
    def on_closing():
        if hasattr(app, 'cap') and app.cap is not None:
            app.stop_camera()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
    self.skip_btn.config(state=tk.DISABLED)
    self.root.after(1500, lambda: (self.submit_btn.config(state=tk.NORMAL), self.skip_btn.config(state=tk.NORMAL)))
    
    def check_answer(self):
        guess = self.selected_option.get()
        
        if not guess:
            messagebox.showwarning("Warning", "Please select an answer!")
            return
        
        self.guesses.append(guess)
        
        if guess == self.answers[self.question_num]:
            self.score += 1
            self.feedback_label.config(text="✓ CORRECT! 🎉", fg="#00FF00")
            self.show_fireworks_animation()
        else:
            correct_answer = self.answers[self.question_num]
            self.feedback_label.config(
                text=f"✗ INCORRECT! 😞 Correct answer: {correct_answer}",
                fg="#FF0000"
            )
            self.show_thumbs_down_animation()
        
        self.question_num += 1
        
        self.root.after(1500, self.display_question)
        self.submit_btn.config(state=tk.DISABLED)