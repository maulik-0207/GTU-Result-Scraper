"""
GTU Results Scraper
Author: @maulik-0207 (Github Username)
Date: 28/01/2026
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import pandas as pd
from PIL import Image, ImageTk
import io
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class GTUResultsScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GTU Results Scraper")
        self.root.geometry("800x750")
        self.root.resizable(False, False)
        
        # Variables
        self.result_type_var = tk.StringVar(value="Regular")
        self.exam_var = tk.StringVar()
        self.enrollment_var = tk.StringVar()
        self.num_students_var = tk.StringVar()
        self.filename_var = tk.StringVar(value="gtu_results.xlsx")
        self.captcha_var = tk.StringVar()
        
        # Driver and state
        self.driver = None
        self.exam_options = []
        self.captcha_image_label = None
        self.is_scraping = False
        self.current_enrollment = ""
        self.captcha_submitted = False
        
        # Setup UI
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the main UI components"""
        # Configure colors
        bg_color = "#f0f4f8"
        header_color = "#1e3a8a"
        accent_color = "#3b82f6"
        button_color = "#2563eb"
        button_hover = "#1d4ed8"
        
        self.root.configure(bg=bg_color)
        
        # Header
        header_frame = tk.Frame(self.root, bg=header_color, height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="GTU Results Scraper",
            font=("Segoe UI", 20, "bold"),
            bg=header_color,
            fg="white"
        )
        title_label.pack(pady=15)
        
        # Main container
        main_frame = tk.Frame(self.root, bg=bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=15)
        
        # Form fields
        self.create_form_fields(main_frame, bg_color, accent_color)
        
        # Captcha section
        self.create_captcha_section(main_frame, bg_color, accent_color)
        
        # Progress section
        self.create_progress_section(main_frame, bg_color)
        
        # Scrape button
        self.create_scrape_button(main_frame, button_color, button_hover)
        
        # Log area
        self.create_log_area(main_frame, bg_color)
        
    def create_form_fields(self, parent, bg_color, accent_color):
        """Create all form input fields"""
        form_frame = tk.Frame(parent, bg=bg_color)
        form_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Result Type Dropdown
        self.create_field(
            form_frame, "Result Type:", 0,
            widget_type="dropdown",
            values=["Regular", "Archive"],
            variable=self.result_type_var,
            command=self.on_result_type_change,
            bg_color=bg_color
        )
        
        # Exam Selection Dropdown
        self.exam_dropdown = self.create_field(
            form_frame, "Exam Selection:", 1,
            widget_type="dropdown",
            values=[],
            variable=self.exam_var,
            bg_color=bg_color
        )
        
        # Load Exams Button
        load_btn = tk.Button(
            form_frame,
            text="Load Exams",
            command=self.load_exam_options,
            bg=accent_color,
            fg="white",
            font=("Segoe UI", 9),
            cursor="hand2",
            relief=tk.FLAT,
            padx=10,
            pady=2
        )
        load_btn.grid(row=1, column=2, padx=(10, 0), sticky="w")
        
        # Starting Enrollment Number
        self.create_field(
            form_frame, "Starting Enrollment (12 digits):", 2,
            widget_type="entry",
            variable=self.enrollment_var,
            bg_color=bg_color
        )
        
        # Number of Students
        self.create_field(
            form_frame, "Number of Students:", 3,
            widget_type="entry",
            variable=self.num_students_var,
            bg_color=bg_color
        )
        
        # Output Filename
        self.create_field(
            form_frame, "Output Filename:", 4,
            widget_type="entry",
            variable=self.filename_var,
            bg_color=bg_color
        )
        
    def create_field(self, parent, label_text, row, widget_type="entry", 
                     values=None, variable=None, command=None, bg_color="#f0f4f8"):
        """Helper to create form fields"""
        label = tk.Label(
            parent,
            text=label_text,
            font=("Segoe UI", 10),
            bg=bg_color,
            anchor="w"
        )
        label.grid(row=row, column=0, sticky="w", pady=6)
        
        if widget_type == "dropdown":
            widget = ttk.Combobox(
                parent,
                textvariable=variable,
                values=values if values else [],
                state="readonly",
                font=("Segoe UI", 10),
                width=50
            )
            if command:
                widget.bind("<<ComboboxSelected>>", lambda e: command())
        else:  # entry
            widget = tk.Entry(
                parent,
                textvariable=variable,
                font=("Segoe UI", 10),
                width=33,
                relief=tk.SOLID,
                borderwidth=1
            )
        
        widget.grid(row=row, column=1, sticky="w", pady=6, padx=(10, 0))
        return widget
        
    def create_captcha_section(self, parent, bg_color, accent_color):
        """Create captcha display and input section"""
        captcha_frame = tk.LabelFrame(
            parent,
            text="Captcha Verification",
            font=("Segoe UI", 12, "bold"),
            bg=bg_color,
            fg="#1e3a8a",
            relief=tk.GROOVE,
            borderwidth=2
        )
        captcha_frame.pack(fill=tk.X, pady=8)
        
        # Fixed-size container for captcha image (pixel-accurate)
        captcha_container = tk.Frame(
            captcha_frame,
            width=190,
            height=65,
            bg="white",
            relief=tk.SUNKEN,
            borderwidth=2
        )
        captcha_container.pack(pady=6, padx=10)
        captcha_container.pack_propagate(False)  # Prevent resizing
        
        # Captcha image label inside container
        self.captcha_image_label = tk.Label(
            captcha_container,
            text="Captcha will appear here",
            bg="white",
            font=("Segoe UI", 10),
            fg="#64748b"
        )
        self.captcha_image_label.pack(expand=True)
        
        # Captcha input
        input_frame = tk.Frame(captcha_frame, bg=bg_color)
        input_frame.pack(pady=(0, 10))
        
        tk.Label(
            input_frame,
            text="Enter Captcha:",
            font=("Segoe UI", 11),
            bg=bg_color
        ).pack(side=tk.LEFT, padx=(10, 5))
        
        self.captcha_entry = tk.Entry(
            input_frame,
            textvariable=self.captcha_var,
            font=("Segoe UI", 12),
            width=20,
            relief=tk.SOLID,
            borderwidth=1
        )
        self.captcha_entry.pack(side=tk.LEFT, padx=5)
        
        # Submit captcha button
        self.captcha_submit_btn = tk.Button(
            input_frame,
            text="Submit Captcha",
            command=self.submit_captcha,
            bg=accent_color,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            padx=15,
            pady=5,
            state=tk.DISABLED
        )
        self.captcha_submit_btn.pack(side=tk.LEFT, padx=5)
        
    def create_progress_section(self, parent, bg_color):
        """Create progress bar section"""
        progress_frame = tk.Frame(parent, bg=bg_color)
        progress_frame.pack(fill=tk.X, pady=8)
        
        tk.Label(
            progress_frame,
            text="Progress:",
            font=("Segoe UI", 11),
            bg=bg_color
        ).pack(anchor="w")
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=740,
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="0 / 0 students processed | Current: None",
            font=("Segoe UI", 9),
            bg=bg_color,
            fg="#64748b"
        )
        self.progress_label.pack(anchor="w")
        
        # Configure progress bar style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor='#e2e8f0',
            background='#3b82f6',
            borderwidth=0,
            thickness=18
        )
        
    def create_scrape_button(self, parent, button_color, button_hover):
        """Create the main scrape button"""
        self.scrape_btn = tk.Button(
            parent,
            text="Start Scraping",
            command=self.start_scraping,
            bg=button_color,
            fg="white",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
            relief=tk.FLAT,
            padx=30,
            pady=8,
            activebackground=button_hover,
            activeforeground="white"
        )
        self.scrape_btn.pack(pady=8)
        
        # Hover effects
        self.scrape_btn.bind("<Enter>", lambda e: self.scrape_btn.config(bg=button_hover))
        self.scrape_btn.bind("<Leave>", lambda e: self.scrape_btn.config(bg=button_color))
        
    def create_log_area(self, parent, bg_color):
        """Create log/status text area"""
        log_frame = tk.LabelFrame(
            parent,
            text="Status Log",
            font=("Segoe UI", 11, "bold"),
            bg=bg_color,
            fg="#1e3a8a"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=6,
            font=("Consolas", 9),
            bg="#1e293b",
            fg="#e2e8f0",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def log(self, message):
        """Add message to log area"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def on_result_type_change(self):
        """Handle result type dropdown change"""
        self.exam_var.set("")
        self.exam_dropdown['values'] = []
        self.log(f"Result type changed to: {self.result_type_var.get()}")
        
    def load_exam_options(self):
        """Load exam options from website"""
        self.log("Loading exam options from website...")
        threading.Thread(target=self._load_exam_options_thread, daemon=True).start()
        
    def _load_exam_options_thread(self):
        """Thread to load exam options"""
        try:
            # Initialize driver if not exists
            if not self.driver:
                options = ChromeOptions()
                options.add_argument("--window-size=960,1080")
                options.add_argument("--window-position=-2000,0")  # Move window off-screen
                options.add_argument("--disable-gpu")
                self.driver = webdriver.Chrome(options=options)
            
            # Navigate to appropriate URL
            if self.result_type_var.get() == "Archive":
                self.driver.get("https://www.gturesults.in/Default.aspx?ext=archive")
            else:
                self.driver.get("https://www.gturesults.in/")
            
            # Wait for dropdown to load
            wait = WebDriverWait(self.driver, 10)
            exam_dropdown = wait.until(
                EC.presence_of_element_located((By.ID, "ddlbatch"))
            )
            
            # Get options
            select = Select(exam_dropdown)
            options = [(opt.get_attribute("value"), opt.text) for opt in select.options if opt.get_attribute("value")]
            
            self.exam_options = options
            option_texts = [f"{text} ({value})" for value, text in options]
            
            # Update dropdown in main thread
            self.root.after(0, lambda: self.exam_dropdown.config(values=option_texts))
            self.root.after(0, lambda: self.log(f"Loaded {len(options)} exam options"))
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Error loading exams: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load exam options: {str(e)}"))
            
    def validate_form(self):
        """Validate all form inputs"""
        if not self.exam_var.get():
            messagebox.showerror("Validation Error", "Please select an exam")
            return False
            
        enrollment = self.enrollment_var.get().strip()
        if len(enrollment) != 12 or not enrollment.isdigit():
            messagebox.showerror("Validation Error", "Enrollment number must be exactly 12 digits")
            return False
            
        try:
            num_students = int(self.num_students_var.get())
            if num_students <= 0:
                raise ValueError()
        except:
            messagebox.showerror("Validation Error", "Number of students must be a positive integer")
            return False
            
        filename = self.filename_var.get().strip()
        if not filename.endswith('.xlsx'):
            messagebox.showerror("Validation Error", "Filename must end with .xlsx")
            return False
            
        return True
        
    def start_scraping(self):
        """Start the scraping process"""
        if not self.validate_form():
            return
            
        if self.is_scraping:
            messagebox.showwarning("Warning", "Scraping is already in progress")
            return
            
        self.is_scraping = True
        self.scrape_btn.config(state=tk.DISABLED, text="Scraping...")
        self.log_text.delete(1.0, tk.END)
        self.log("Starting scraping process...")
        
        # Start scraping in separate thread
        threading.Thread(target=self.scrape_results, daemon=True).start()
        
    def scrape_results(self):
        """Main scraping logic"""
        try:
            # Initialize driver if needed
            if not self.driver:
                self.root.after(0, lambda: self.log("Initializing browser..."))
                options = ChromeOptions()
                options.add_argument("--window-size=960,1080")
                options.add_argument("--window-position=-2000,0")  # Move window off-screen
                options.add_argument("--disable-gpu")
                self.driver = webdriver.Chrome(options=options)
                
                # Navigate and select exam
                if self.result_type_var.get() == "Archive":
                    self.driver.get("https://www.gturesults.in/Default.aspx?ext=archive")
                else:
                    self.driver.get("https://www.gturesults.in/")
            
            # Select exam
            exam_selection = self.driver.find_element(By.ID, "ddlbatch")
            dropdown = Select(exam_selection)
            
            # Extract value from selected option
            selected = self.exam_var.get()
            exam_value = selected.split("(")[-1].rstrip(")")
            dropdown.select_by_value(exam_value)
            
            self.root.after(0, lambda: self.log(f"Selected exam: {selected}"))
            
            # Parse enrollment number
            enrollment_start = self.enrollment_var.get()
            num_students = int(self.num_students_var.get())
            
            # Calculate enrollment range
            fixed_part = enrollment_start[:9]  # First 9 digits
            start_num = int(enrollment_start[9:])  # Last 3 digits
            end_num = start_num + num_students - 1
            
            # Setup progress
            total = num_students
            self.root.after(0, lambda: self.progress_bar.config(maximum=total))
            
            # Scraping loop
            for i, enroll_num in enumerate(range(start_num, end_num + 1)):
                # Build enrollment number
                build_enroll = fixed_part + str(enroll_num).zfill(3)
                self.current_enrollment = build_enroll
                
                self.root.after(0, lambda e=build_enroll, idx=i+1, tot=total: self.log(f"\n[{idx}/{tot}] Processing enrollment: {e}"))
                
                # Fill enrollment number
                enroll_no = self.driver.find_element(By.ID, "txtenroll")
                enroll_no.clear()
                enroll_no.send_keys(build_enroll)
                
                # Fill password
                ps = self.driver.find_element(By.ID, "txtpassword")
                ps.clear()
                ps.send_keys("123456789")
                
                # Get and display captcha
                self.captcha_submitted = False
                self.root.after(0, self.display_captcha)
                
                # Wait for captcha submission
                while not self.captcha_submitted:
                    threading.Event().wait(0.1)
                
                # Submit form
                btn = self.driver.find_element(By.ID, "btnSearch")
                btn.send_keys(Keys.ENTER)
                
                # Wait for results
                try:
                    wait = WebDriverWait(self.driver, 15)
                    wait.until(
                        EC.any_of(
                            EC.presence_of_element_located((By.ID, "lblCGPA")),
                            EC.presence_of_element_located((By.ID, "lblmsg"))
                        )
                    )
                except Exception:
                    self.root.after(0, lambda e=build_enroll: self.log(f"Timeout for {e}"))
                    continue
                
                # Check for errors
                if self.driver.find_elements(By.ID, "lblmsg"):
                    msg = self.driver.find_element(By.ID, "lblmsg").text.strip()
                    if "Data not available" in msg or "Incorrect captcha" in msg:
                        self.root.after(0, lambda e=build_enroll, m=msg: self.log(f"Error for {e}: {m}"))
                        continue
                
                # Scrape data
                try:
                    name = self.driver.find_element(By.ID, "lblName").text.strip()
                    enrollment_number = self.driver.find_element(By.ID, "lblExam").text.strip()
                    current_sem_back = self.driver.find_element(By.ID, "lblCUPBack").text.strip()
                    total_back = self.driver.find_element(By.ID, "lblTotalBack").text.strip()
                    spi = self.driver.find_element(By.ID, "lblSPI").text.strip()
                    cpi = self.driver.find_element(By.ID, "lblCPI").text.strip()
                    cgpa = self.driver.find_element(By.ID, "lblCGPA").text.strip()
                    
                    # Save to Excel
                    self.save_to_excel(name, enrollment_number, current_sem_back, 
                                     total_back, spi, cpi, cgpa)
                    
                    self.root.after(0, lambda n=name, e=enrollment_number: self.log(f"✓ Saved to Excel: {n} ({e})"))
                    
                except Exception as e:
                    self.root.after(0, lambda err=str(e): self.log(f"Error scraping data: {err}"))
                
                # Update progress
                progress = i + 1
                self.root.after(0, lambda p=progress, t=total, e=build_enroll: self.update_progress(p, t, e))
            
            # Add summary
            self.add_summary()
            
            self.root.after(0, lambda: self.log("\n✓ Scraping completed successfully!"))
            self.root.after(0, lambda: messagebox.showinfo("Success", "Scraping completed!"))
            
        except Exception as e:
            self.root.after(0, lambda err=str(e): self.log(f"\n✗ Error: {err}"))
            self.root.after(0, lambda err=str(e): messagebox.showerror("Error", f"Scraping failed: {err}"))
            
        finally:
            self.is_scraping = False
            self.root.after(0, lambda: self.scrape_btn.config(state=tk.NORMAL, text="Start Scraping"))
            self.root.after(0, self.reset_form)
    
    def reset_form(self):
        """Reset all form fields after scraping completes"""
        # Clear input fields
        self.enrollment_var.set("")
        self.num_students_var.set("")
        self.filename_var.set("gtu_results.xlsx")
        self.captcha_var.set("")
        
        # Reset captcha display
        self.captcha_image_label.config(image="", text="Captcha will appear here")
        self.captcha_image_label.image = None
        self.captcha_submit_btn.config(state=tk.DISABLED)
        
        # Reset progress
        self.progress_bar['value'] = 0
        self.progress_label.config(text="0 / 0 students processed | Current: None")
        self.current_enrollment = ""
        
        self.log("\n--- Form reset. Ready for new scraping session ---\n")
            
    def display_captcha(self):
        """Display captcha image from website using base64 extraction"""
        try:
            self.captcha_submit_btn.config(state=tk.NORMAL)
            self.captcha_var.set("")
            self.captcha_entry.focus()
            
            # Get captcha image element
            captcha_element = self.driver.find_element(By.ID, "imgCaptcha")
            
            # Extract Base64 directly from the browser using JavaScript
            import base64
            
            # Execute JavaScript to convert image to base64
            base64_data = self.driver.execute_script("""
                const img = arguments[0];
                const canvas = document.createElement('canvas');
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                return canvas.toDataURL('image/png').split(',')[1];
            """, captcha_element)
            
            # Decode base64 to bytes
            captcha_bytes = base64.b64decode(base64_data)
            
            # Open image from bytes
            image = Image.open(io.BytesIO(captcha_bytes))
            
            # Scale up the image for better visibility (120x40 -> 144x48)
            scale_factor = 1.2  # 1.2x scaling - minimal but readable
            new_size = (
                int(image.size[0] * scale_factor),
                int(image.size[1] * scale_factor)
            )
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage for Tkinter
            photo = ImageTk.PhotoImage(image)
            
            # Update label with image
            self.captcha_image_label.config(image=photo, text="")
            self.captcha_image_label.image = photo  # Keep reference to prevent garbage collection
            
            self.log(f"✓ Captcha loaded for enrollment: {self.current_enrollment}")
            
        except Exception as e:
            self.log(f"✗ Error displaying captcha: {str(e)}")
            self.captcha_image_label.config(text="Captcha load failed - check browser")
            
    def submit_captcha(self):
        """Submit captcha value"""
        captcha_value = self.captcha_var.get().strip()
        if not captcha_value:
            messagebox.showwarning("Warning", "Please enter captcha")
            return
            
        try:
            captcha_field = self.driver.find_element(By.ID, "CodeNumberTextBox")
            captcha_field.clear()
            captcha_field.send_keys(captcha_value)
            
            self.captcha_submitted = True
            self.captcha_submit_btn.config(state=tk.DISABLED)
            self.log(f"Captcha submitted: {captcha_value}")
            
        except Exception as e:
            self.log(f"Error submitting captcha: {str(e)}")
            
    def save_to_excel(self, name, enrollment_number, current_sem_back, 
                     total_back, spi, cpi, cgpa):
        """Save result data to Excel file"""
        file_path = self.filename_var.get()
        
        if not os.path.exists(file_path):
            result_data = {
                'Name': [name],
                'Enrollment_No': [str(enrollment_number)],
                'Current_Sem_Back': [current_sem_back],
                'Total_Back': [total_back],
                'SPI': [spi],
                'CPI': [cpi],
                'CGPA': [cgpa]
            }
            data = pd.DataFrame(result_data)
        else:
            data = pd.read_excel(file_path)
            data["Enrollment_No"] = data["Enrollment_No"].astype(str)
            result_data = {
                'Name': name,
                'Enrollment_No': str(enrollment_number),
                'Current_Sem_Back': current_sem_back,
                'Total_Back': total_back,
                'SPI': spi,
                'CPI': cpi,
                'CGPA': cgpa
            }
            data.loc[len(data)] = result_data
            
        data.to_excel(file_path, index=False)
        
    def add_summary(self):
        """Add summary statistics to Excel"""
        file_path = self.filename_var.get()
        if os.path.exists(file_path):
            df = pd.read_excel(file_path, dtype={"Enrollment_No": str})
            for col in ["SPI", "CPI", "CGPA", "Current_Sem_Back", "Total_Back"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            
            summary_rows = [
                {
                    'Name': "MAX",
                    'Enrollment_No': " - ",
                    'Current_Sem_Back': df["Current_Sem_Back"].max(),
                    'Total_Back': df["Total_Back"].max(),
                    'SPI': df["SPI"].max(),
                    'CPI': df["CPI"].max(),
                    'CGPA': df["CGPA"].max()
                },
                {
                    'Name': "MIN",
                    'Enrollment_No': " - ",
                    'Current_Sem_Back': df["Current_Sem_Back"].min(),
                    'Total_Back': df["Total_Back"].min(),
                    'SPI': df["SPI"].min(),
                    'CPI': df["CPI"].min(),
                    'CGPA': df["CGPA"].min()
                },
                {
                    'Name': "AVG",
                    'Enrollment_No': " - ",
                    'Current_Sem_Back': round(df["Current_Sem_Back"].mean(), 2),
                    'Total_Back': round(df["Total_Back"].mean(), 2),
                    'SPI': round(df["SPI"].mean(), 2),
                    'CPI': round(df["CPI"].mean(), 2),
                    'CGPA': round(df["CGPA"].mean(), 2)
                },
                {
                    'Name': "Total Failed Students",
                    'Enrollment_No': " - ",
                    'Current_Sem_Back': df[df["Current_Sem_Back"] > 0].shape[0],
                    'Total_Back': 0,
                    'SPI': 0,
                    'CPI': 0,
                    'CGPA': 0
                }
            ]
            
            for row in summary_rows:
                df.loc[len(df)] = row
            
            df.to_excel(file_path, index=False)
            self.log("Summary statistics added to Excel")
            
    def update_progress(self, current, total, enrollment="None"):
        """Update progress bar"""
        self.progress_bar['value'] = current
        self.progress_label.config(text=f"{current} / {total} students processed | Current: {enrollment}")
        
    def on_closing(self):
        """Handle window closing"""
        if self.driver:
            self.driver.quit()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = GTUResultsScraperGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
