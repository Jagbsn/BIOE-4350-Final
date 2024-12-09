import tkinter as tk
from tkinter import ttk, Scale
import cv2
import imutils
import threading
import pygame
import socket
import asyncio
import os
from datetime import datetime
import mail
import bot
from PIL import Image, ImageTk
import sys
import subprocess
import pkg_resources
import json

# Global variables
sensitivity = 10000
sensitivity_label = None
sensitivity_slider = None
video_resolution = (640, 480)
schedule_times = {"arm": 21, "disarm": 7}
root = None
tab_control = None
camera_label = None
style = None
resolution_width_entry = None
resolution_height_entry = None
arm_time_entry = None
disarm_time_entry = None
current_camera = 0
available_cameras = []
show_motion = False  # New global variable for motion highlighting
preview_mode = False  # New global variable for motion preview mode
last_motion_time = None

# Alarm related globals
alarm_mode = False
alarm = False
alarm_counter = 0
manual_override = False
running = True
recording = False
video_frames = []

# Socket settings
HOST = '127.0.0.1'
PORT = 65432

# File paths
frame_path = "motion_frame.jpg"
video_path = "motion_clip.avi"

# Initialize pygame for alarm sound
pygame.init()
pygame.mixer.init()

# Add at the top of your file with other imports
import os
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"  # Suppress OpenCV error messages

def save_settings():
    """Save current settings to settings.json"""
    settings = {
        "video_resolution": list(video_resolution),
        "sensitivity": sensitivity,
        "schedule_times": schedule_times,
        "current_camera": current_camera,
        "show_motion": show_motion,
        "preview_mode": preview_mode
    }
    
    try:
        with open('settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
        print("Settings saved successfully")
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_settings():
    """Load settings from settings.json"""
    global video_resolution, sensitivity, schedule_times, current_camera, show_motion, preview_mode
    
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
            
        # Update global variables
        video_resolution = tuple(settings.get('video_resolution', (640, 480)))
        sensitivity = settings.get('sensitivity', 10000)
        schedule_times = settings.get('schedule_times', {"arm": 21, "disarm": 7})
        current_camera = settings.get('current_camera', 0)
        show_motion = settings.get('show_motion', False)
        preview_mode = settings.get('preview_mode', False)
        
        print("Settings loaded successfully")
    except FileNotFoundError:
        print("No settings file found, using defaults")
    except Exception as e:
        print(f"Error loading settings: {e}")

def check_dependencies():
    """Check and install required dependencies"""
    # Packages that are part of standard library and don't need installation
    STANDARD_LIBRARY = {
        # main.py standard libraries
        'tkinter', 'asyncio', 'json', 'datetime', 'threading', 'socket', 'os', 'sys', 'subprocess',
        
        # mail.py standard libraries
        'smtplib', 'email',
        
        # Other standard libraries
        'pkg_resources'
    }

    # Package name mappings (pip name -> import name)
    PACKAGE_MAPPINGS = {
        'opencv-python': 'cv2',
        'pillow': 'PIL',
        'discord.py': 'discord',
        'google-api-python-client': 'googleapiclient',
        'google-auth': 'google.auth',
        'google-auth-httplib2': 'google_auth_httplib2',
        'google-auth-oauthlib': 'google_auth_oauthlib'
    }

    # Define required packages with their versions
    REQUIRED_PACKAGES = [
        # main.py requirements
        'opencv-python>=4.5.0',
        'imutils>=0.5.4',
        'pygame>=2.0.0',
        'pillow>=8.0.0',
        
        # bot.py requirements
        'discord.py>=2.0.0',
        
        # drive_utils.py requirements (also used by mail.py)
        'google-api-python-client>=2.0.0',
        'google-auth>=2.0.0',
        'google-auth-httplib2>=0.1.0',
        'google-auth-oauthlib>=0.5.0'
    ]

    def get_package_import_name(package):
        """Get the import name for a package"""
        base_name = package.split('>=')[0].lower()
        return PACKAGE_MAPPINGS.get(base_name, base_name.replace('-', '_'))

    def is_package_installed(package_name):
        """Check if a package is installed"""
        try:
            pkg_resources.get_distribution(package_name.split('>=')[0])
            return True
        except pkg_resources.DistributionNotFound:
            return False

    def install_package(package):
        try:
            if not is_package_installed(package):
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"Successfully installed {package}")
            else:
                print(f"Package already installed: {package}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing {package}: {e}")
            return False

    try:
        # Check each package
        print("Checking dependencies...")
        missing_packages = []

        for requirement in REQUIRED_PACKAGES:
            if is_package_installed(requirement):
                print(f"✓ {requirement}")
            elif requirement.split('>=')[0].lower() in STANDARD_LIBRARY:
                print(f"✓ {requirement} (standard library)")
            else:
                print(f"✗ Missing: {requirement}")
                missing_packages.append(requirement)

        # Only install if there are missing packages
        if missing_packages:
            print("\nInstalling missing packages...")
            for package in missing_packages:
                if not install_package(package):
                    print(f"Failed to install {package}. Please install it manually.")
                    sys.exit(1)
            print("All missing packages installed successfully!")
        else:
            print("\nAll required packages are already installed!")

    except Exception as e:
        print(f"Error checking dependencies: {e}")
        sys.exit(1)

def beep_alarm():
    """Play alarm sound"""
    pygame.mixer.music.load("alarm.mp3")
    pygame.mixer.music.play()

def activate_alarm():
    """Activate the alarm system"""
    global alarm_mode, manual_override, start_frame
    try:
        # Capture and process the initial frame
        _, frame = cap.read()
        if frame is not None:
            # Resize frame to a consistent size
            frame = imutils.resize(frame, width=500)
            # Convert to grayscale and blur
            start_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            start_frame = cv2.GaussianBlur(start_frame, (5, 5), 0)
            
            alarm_mode = True
            manual_override = True
            print("System Armed!")
        else:
            print("Error: Could not capture initial frame")
    except Exception as e:
        print(f"Error arming system: {e}")

def deactivate_alarm():
    """Deactivate the alarm system"""
    global alarm_mode, alarm, manual_override, alarm_counter
    alarm_mode = False
    alarm = False
    alarm_counter = 0
    manual_override = True
    pygame.mixer.music.stop()  # Stop the alarm sound
    print("System Disarmed!")

def reset_alarm():
    """Reset the alarm system"""
    global alarm, alarm_counter
    alarm = False
    alarm_counter = 0
    pygame.mixer.music.stop()  # Stop the alarm sound
    print("Alarm has been reset!")

def quit_program():
    """Safely quit the program"""
    global running
    running = False
    
    # Close OpenCV windows and release camera
    cv2.destroyAllWindows()
    if cap.isOpened():
        cap.release()
    
    # Stop the Discord bot
    try:
        asyncio.run_coroutine_threadsafe(bot.client.close(), bot.client.loop)
    except Exception as e:
        print(f"Error closing Discord bot: {e}")
    
    # Close the GUI
    root.quit()
    root.destroy()
    
    print("Quitting the program!")
    os._exit(0)  # Force exit if needed

def calculate_max_pixels():
    """Calculate total pixels in current camera resolution"""
    try:
        _, frame = cap.read()
        if frame is not None:
            height, width = frame.shape[:2]
            return width * height
    except Exception as e:
        print(f"Error calculating pixels: {e}")
    return 500 * 500

def update_sensitivity(value):
    """Update sensitivity when slider is moved"""
    global sensitivity
    sensitivity = int(float(value))
    if sensitivity_label:
        sensitivity_label.config(text=f"Pixels Needed to Trigger Alarm: {sensitivity}")

def update_resolution_settings(resolution_str):
    """Update settings specifically when resolution changes"""
    global video_resolution, sensitivity, sensitivity_slider
    try:
        # Parse resolution (format is like "1920x1080 (1080p)")
        resolution = resolution_str.split()[0]  # Get "1920x1080" part
        width, height = map(int, resolution.split('x'))  # Split by 'x' to get width and height
        video_resolution = (width, height)
        
        # Calculate and set new sensitivity to 5% of total pixels
        total_pixels = width * height
        sensitivity = int(total_pixels * 0.05)  # 5% of total pixels
        
        # Update sensitivity slider range and value
        if sensitivity_slider:
            sensitivity_slider.config(from_=total_pixels)  # Update maximum value
            sensitivity_slider.set(sensitivity)
        if sensitivity_label:
            sensitivity_label.config(text=f"Pixels Needed to Trigger Alarm: {sensitivity}")
            
    except ValueError as e:
        print(f"Error updating resolution settings: {e}")

def update_settings():
    """Update all settings and save them"""
    global video_resolution, schedule_times, sensitivity, current_camera, show_motion, preview_mode
    try:
        # Update schedule times
        schedule_times["arm"] = int(arm_time_entry.get())
        schedule_times["disarm"] = int(disarm_time_entry.get())
        
        # Save all current settings
        save_settings()
        
        print("Settings updated and saved successfully")
    except ValueError:
        print("Invalid input. Please enter valid numbers.")

def save_video(frames, output_path):
    """Save recorded frames as video"""
    if frames:
        height, width = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_path, fourcc, 20.0, (width, height))
        for frame in frames:
            out.write(frame)
        out.release()
        print(f"Video saved at {output_path}")

def update_frame():
    """Update camera feed and check for motion"""
    global start_frame, alarm, alarm_counter, recording, video_frames, last_motion_time

    if not running:
        return

    try:
        _, frame = cap.read()
        if frame is None:
            print("Error: Could not capture frame")
            return
            
        # Resize frame to a consistent size
        frame = imutils.resize(frame, width=500)

        # Process frame for motion detection (both alarm and preview modes)
        if (alarm_mode or preview_mode) and start_frame is not None:
            frame_bw = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_bw = cv2.GaussianBlur(frame_bw, (5, 5), 0)
            
            if frame_bw.shape == start_frame.shape:
                difference = cv2.absdiff(start_frame, frame_bw)
                threshold = cv2.threshold(difference, 25, 255, cv2.THRESH_BINARY)[1]
                start_frame = frame_bw

                motion_detected = threshold.sum() > sensitivity
                current_time = datetime.now()

                if motion_detected:
                    # Update the last motion time
                    last_motion_time = current_time
                    
                    # Only increment alarm counter if in alarm mode
                    if alarm_mode:
                        alarm_counter += 1
                        if alarm_counter > 20:
                            if not alarm:
                                alarm = True
                                cv2.imwrite(frame_path, frame)
                                recording = True
                                video_frames.clear()
                                threading.Thread(target=beep_alarm).start()
                                # Send Discord notification immediately when motion is detected
                                try:
                                    asyncio.run_coroutine_threadsafe(
                                        bot.send_alert_to_discord(), bot.client.loop
                                    )
                                    print("Discord notification sent successfully")
                                except Exception as e:
                                    print(f"Error sending Discord notification: {e}")
                    
                    # Show motion highlight in either mode if enabled
                    if show_motion or preview_mode:
                        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        for contour in contours:
                            if cv2.contourArea(contour) > 500:
                                (x, y, w, h) = cv2.boundingRect(contour)
                                color = (0, 255, 0) if not preview_mode else (255, 0, 0)
                                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                else:
                    if alarm_counter > 0 and alarm_mode:
                        alarm_counter -= 1

                if recording:
                    video_frames.append(frame)
                    
                    # Check if we should stop recording
                    if not motion_detected and last_motion_time is not None:
                        time_since_motion = (current_time - last_motion_time).total_seconds()
                        if time_since_motion >= 1.0:  #after motion time buffer
                            save_video(video_frames, video_path)
                            recording = False
                            last_motion_time = None
                            print(f"Sending email with video: link to video and first motion frame.")
                            threading.Thread(target=mail.send_email, args=(frame_path, video_path)).start()

        # Update the GUI with the current frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        camera_label.imgtk = imgtk
        camera_label.configure(image=imgtk)

        root.after(30, update_frame)

    except Exception as e:
        print(f"Error in update_frame: {e}")

# Then define your GUI setup functions
def setup_settings_tab():
    global sensitivity_label, resolution_combo, arm_time_entry, disarm_time_entry, sensitivity_slider
    
    # Settings Tab
    tab_settings = ttk.Frame(tab_control, style="Dark.TFrame")
    tab_control.add(tab_settings, text="Settings")

    # Configure styles
    style.configure("Dark.TLabel", background="#1e1e1e", foreground="white", font=("Arial", 10))
    style.configure("Dark.TFrame", background="#1e1e1e")
    style.configure("Dark.TButton", background="#333333", foreground="white", font=("Arial", 10))
    
    # Configure Combobox style for better readability
    style.map('TCombobox',
        fieldbackground=[('readonly', '#333333')],
        background=[('readonly', '#333333')],
        foreground=[('readonly', 'white')]
    )
    
    # Option menu style (dropdown list)
    root.option_add('*TCombobox*Listbox.background', '#333333')
    root.option_add('*TCombobox*Listbox.foreground', 'white')
    root.option_add('*TCombobox*Listbox.selectBackground', '#1e1e1e')
    root.option_add('*TCombobox*Listbox.selectForeground', 'white')

    # Add these style configurations after the existing style configurations
    style.configure("Dark.TEntry",
        fieldbackground="#333333",
        foreground="white",
        insertcolor="white",  # cursor color
        borderwidth=1,
        relief="solid"
    )

    style.configure("Dark.TCheckbutton",
        background="#1e1e1e",
        foreground="white"
    )
    
    style.map("Dark.TCheckbutton",
        background=[('active', '#1e1e1e')],
        foreground=[('active', 'white')]
    )

    # Create a main frame with padding
    main_frame = ttk.Frame(tab_settings, style="Dark.TFrame", padding="20")
    main_frame.pack(fill="both", expand=True)

    # Camera selector section
    camera_frame = ttk.Frame(main_frame, style="Dark.TFrame")
    camera_frame.pack(fill="x", pady=(0, 20))

    # Create a frame for the label and refresh button
    camera_header_frame = ttk.Frame(camera_frame, style="Dark.TFrame")
    camera_header_frame.pack(fill="x", pady=5)

    ttk.Label(
        camera_header_frame, 
        text="Select Camera:", 
        style="Dark.TLabel"
    ).pack(side="left", padx=5)

    # Add refresh button with more visible styling
    ttk.Button(
        camera_header_frame,
        text="Refresh Cameras",  # Changed from icon to text for better visibility
        style="Dark.TButton",
        command=refresh_cameras,
        width=15  # Set a fixed width
    ).pack(side="right", padx=5)

    # Create and populate the combobox
    global camera_combo
    camera_combo = ttk.Combobox(
        camera_frame, 
        state="readonly",
        style="Dark.TCombobox"
    )
    
    # Use the already detected cameras
    camera_options = [f"{i} (Camera {i})" for i in available_cameras]
    camera_combo['values'] = camera_options
    
    # Set current camera as selected
    try:
        current_index = available_cameras.index(current_camera)
        camera_combo.current(current_index)
    except ValueError:
        if camera_options:
            camera_combo.current(0)
    
    camera_combo.pack(fill="x", pady=5, padx=5)
    camera_combo.bind('<<ComboboxSelected>>', change_camera)

    # Sensitivity section
    sensitivity_frame = ttk.Frame(main_frame, style="Dark.TFrame")
    sensitivity_frame.pack(fill="x", pady=(0, 20))

    ttk.Label(
        sensitivity_frame, 
        text="Motion Detection Sensitivity:", 
        style="Dark.TLabel"
    ).pack(anchor="w")

    # Create a frame for the slider and labels
    slider_frame = ttk.Frame(sensitivity_frame, style="Dark.TFrame")
    slider_frame.pack(fill="x", pady=5)

    # High sensitivity label (right side)
    ttk.Label(
        slider_frame, 
        text="High", 
        style="Dark.TLabel"
    ).pack(side="right")

    # Low sensitivity label (left side)
    ttk.Label(
        slider_frame, 
        text="Low", 
        style="Dark.TLabel"
    ).pack(side="left")

    max_pixels = calculate_max_pixels()
    sensitivity_slider = Scale(
        slider_frame,
        from_=max_pixels,    # High value (low sensitivity) on left
        to=20,               # Low value (high sensitivity) on right
        orient='horizontal',
        length=300,
        bg="#1e1e1e",
        fg="white",
        troughcolor="#333333",
        highlightthickness=0,
        showvalue=0,      # Hide the numbers
        command=update_sensitivity
    )
    sensitivity_slider.set(sensitivity)
    sensitivity_slider.pack(fill="x", padx=40)  # Add padding to make room for labels

    sensitivity_label = ttk.Label(
        sensitivity_frame, 
        text=f"Pixels needed to trigger alarm: {sensitivity}", 
        style="Dark.TLabel"
    )
    sensitivity_label.pack(anchor="w")

    # Resolution section with horizontal layout
    resolution_frame = ttk.Frame(main_frame, style="Dark.TFrame")
    resolution_frame.pack(fill="x", pady=(0, 20), padx=5, anchor="w")

    # Header and dropdown in the same row
    ttk.Label(
        resolution_frame, 
        text="Resolution:",
        style="Dark.TLabel"
    ).pack(side="left", padx=(0, 10))

    # Define common resolutions
    resolutions = [
        "640x480 (480p)",
        "1280x720 (720p)",
        "1920x1080 (1080p)",
        "2560x1440 (1440p)"
    ]

    # Create and populate the resolution combobox
    resolution_combo = ttk.Combobox(
        resolution_frame,
        values=resolutions,
        state="readonly",
        width=20  # Adjust width as needed
    )
    resolution_combo.pack(side="left")

    # Set default value based on current resolution
    current_res = f"{video_resolution[0]}x{video_resolution[1]}"
    for res in resolutions:
        if current_res in res:
            resolution_combo.set(res)
            break

    # Schedule section
    schedule_frame = ttk.Frame(main_frame, style="Dark.TFrame")
    schedule_frame.pack(fill="x", pady=20)

    ttk.Label(
        schedule_frame, 
        text="Schedule Settings:", 
        style="Dark.TLabel"
    ).pack(anchor="w")

    # Arm time
    arm_frame = ttk.Frame(schedule_frame, style="Dark.TFrame")
    arm_frame.pack(fill="x", pady=5)
    
    ttk.Label(
        arm_frame, 
        text="Arm Time (24h):", 
        style="Dark.TLabel"
    ).pack(side="left")
    
    arm_time_entry = ttk.Entry(
        arm_frame,
        width=10,
        style="Dark.TEntry"
    )
    arm_time_entry.pack(side="left", padx=10)
    arm_time_entry.insert(0, str(schedule_times["arm"]))

    # Disarm time
    disarm_frame = ttk.Frame(schedule_frame, style="Dark.TFrame")
    disarm_frame.pack(fill="x", pady=5)
    
    ttk.Label(
        disarm_frame, 
        text="Disarm Time (24h):", 
        style="Dark.TLabel"
    ).pack(side="left")
    
    disarm_time_entry = ttk.Entry(
        disarm_frame,
        width=10,
        style="Dark.TEntry"
    )
    disarm_time_entry.pack(side="left", padx=10)
    disarm_time_entry.insert(0, str(schedule_times["disarm"]))

    # Motion highlight toggle
    highlight_frame = ttk.Frame(main_frame, style="Dark.TFrame")
    highlight_frame.pack(fill="x", pady=20)
    
    ttk.Label(
        highlight_frame,
        text="Motion Detection Highlight:",
        style="Dark.TLabel"
    ).pack(side="left")
    
    highlight_var = tk.BooleanVar(value=show_motion)
    highlight_toggle = ttk.Checkbutton(
        highlight_frame,
        variable=highlight_var,
        command=lambda: toggle_motion_highlight(highlight_var.get()),
        style="Dark.TCheckbutton"
    )
    highlight_toggle.pack(side="left", padx=10)

    # Motion preview toggle
    preview_frame = ttk.Frame(main_frame, style="Dark.TFrame")
    preview_frame.pack(fill="x", pady=10)
    
    ttk.Label(
        preview_frame,
        text="Motion Detection Preview:",
        style="Dark.TLabel"
    ).pack(side="left")
    
    preview_var = tk.BooleanVar(value=preview_mode)
    preview_toggle = ttk.Checkbutton(
        preview_frame,
        variable=preview_var,
        command=lambda: toggle_preview_mode(preview_var.get()),
        style="Dark.TCheckbutton"
    )
    preview_toggle.pack(side="left", padx=10)

    # Update button
    ttk.Button(
        main_frame, 
        text="Save Settings",  # Change button text to "Save Settings"
        style="Dark.TButton", 
        command=update_settings
    ).pack(pady=20)

    # In setup_settings_tab where resolution_combo is created:
    resolution_combo.bind('<<ComboboxSelected>>', 
        lambda event: update_resolution_settings(resolution_combo.get()))

    return tab_settings

def initialize_gui():
    global root, tab_control, camera_label, style
    
    root = tk.Tk()
    root.title("Motion Detection System")
    root.configure(bg="#1e1e1e")
    root.protocol("WM_DELETE_WINDOW", quit_program)
    
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Dark.TFrame", background="#1e1e1e")
    style.configure("Dark.TButton", background="#333333", foreground="#ffffff", font=("Arial", 12), padding=10)
    
    tab_control = ttk.Notebook(root)
    
    # Setup camera tab
    tab_camera = ttk.Frame(tab_control, style="Dark.TFrame")
    tab_control.add(tab_camera, text="Camera Feed")
    
    # Create a container frame for camera and buttons
    camera_container = ttk.Frame(tab_camera, style="Dark.TFrame")
    camera_container.pack(expand=True, fill="both")
    
    # Camera label now packed in container
    camera_label = tk.Label(camera_container, bg="#1e1e1e")
    camera_label.pack(expand=True, fill="both")
    
    # Button frame now packed directly after camera with some padding
    button_frame = ttk.Frame(camera_container, style="Dark.TFrame")
    button_frame.pack(pady=20)  # Add padding above and below buttons
    
    # Add camera tab buttons
    ttk.Button(button_frame, text="Arm System", style="Dark.TButton", command=activate_alarm).pack(side="left", padx=10)
    ttk.Button(button_frame, text="Disarm System", style="Dark.TButton", command=deactivate_alarm).pack(side="left", padx=10)
    ttk.Button(button_frame, text="Reset Alarm", style="Dark.TButton", command=reset_alarm).pack(side="left", padx=10)
    ttk.Button(button_frame, text="Quit", style="Dark.TButton", command=quit_program).pack(side="left", padx=10)
    
    # Setup settings tab
    setup_settings_tab()
    
    tab_control.pack(expand=1, fill="both")

# Add this function to detect available cameras
def get_available_cameras():
    """Detect all available cameras"""
    global available_cameras
    available_cameras = []
    
    # Suppress stderr temporarily to hide error messages
    with open(os.devnull, 'w') as devnull:
        old_stderr = os.dup(2)
        os.dup2(devnull.fileno(), 2)
        
        # Check indices 0-9 (10 possible cameras)
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        available_cameras.append(i)
                cap.release()
            except:
                continue
                
        # Restore stderr
        os.dup2(old_stderr, 2)
    
    # Single message about camera count
    print(f"Found {len(available_cameras)} camera(s)")
    return available_cameras

# Add this function to handle camera changes
def change_camera(event):
    """Switch to selected camera"""
    global cap, current_camera
    selected = camera_combo.get()
    new_camera = int(selected.split()[0])  # Get the camera index
    if new_camera != current_camera:
        current_camera = new_camera
        cap.release()
        cap = cv2.VideoCapture(current_camera)
        print(f"Switched to camera {current_camera}")

# Before initializing the GUI
def initialize_camera():
    global cap, current_camera
    cameras = get_available_cameras()
    if cameras:
        current_camera = cameras[0]
        cap = cv2.VideoCapture(current_camera)
        return True
    return False

def start_discord_bot():
    """Start the Discord bot in a separate thread"""
    bot_thread = threading.Thread(target=bot.run_bot)
    bot_thread.start()

async def handle_client(reader, writer):
    """Handle incoming socket connections"""
    try:
        data = await reader.read(1024)
        message = data.decode().strip()
        addr = writer.get_extra_info('peername')
        print(f"Received {message} from {addr}")
        
        # Handle different commands
        if message == "status":
            current_time = datetime.now()
            current_hour = current_time.hour
            
            # Determine next schedule change
            if current_hour < schedule_times['arm']:
                next_time = schedule_times['arm']
                next_action = "arm"
            elif current_hour < schedule_times['disarm']:
                next_time = schedule_times['disarm']
                next_action = "disarm"
            else:
                next_time = schedule_times['arm']
                next_action = "arm"
            
            response = f"System Status:\n"
            response += f"Current Time: {current_time.strftime('%H:%M:%S')}\n"
            response += f"System is: {'Armed' if alarm_mode else 'Disarmed'}\n"
            response += f"Manual Override: {'Yes' if manual_override else 'No'}\n"
            response += f"Next Schedule Change: {next_time}:00 ({next_action})"
            
        elif message == "schedule":
            response = f"Schedule Settings:\n"
            response += f"Arm Time: {schedule_times['arm']}:00\n"
            response += f"Disarm Time: {schedule_times['disarm']}:00"
        elif message == "alarm on":
            activate_alarm()
            response = "Alarm activated"
        elif message == "alarm off":
            deactivate_alarm()
            response = "Alarm deactivated"
        elif message == "alarm reset":
            reset_alarm()
            response = "Alarm reset"
        else:
            response = "Unknown command"
            
        writer.write(response.encode())
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        
    except Exception as e:
        print(f"Error handling client: {e}")

async def start_server():
    """Start the socket server"""
    try:
        server = await asyncio.start_server(
            handle_client, HOST, PORT
        )
        addr = server.sockets[0].getsockname()
        print(f'Socket server running on {addr}')
        
        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"Error starting server: {e}")

# Add new function to handle toggle
def toggle_motion_highlight(value):
    """Toggle motion detection highlight"""
    global show_motion
    show_motion = value
    save_settings()

# Add new function for preview mode toggle
def toggle_preview_mode(value):
    """Toggle motion detection preview mode"""
    global preview_mode, alarm_mode, start_frame
    preview_mode = value
    if preview_mode:
        # Store current alarm state and disable alarm
        global stored_alarm_state
        stored_alarm_state = alarm_mode
        alarm_mode = False
        
        # Initialize start_frame for preview mode
        try:
            _, frame = cap.read()
            if frame is not None:
                frame = imutils.resize(frame, width=500)
                start_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                start_frame = cv2.GaussianBlur(start_frame, (5, 5), 0)
            else:
                print("Error: Could not capture initial frame for preview mode")
        except Exception as e:
            print(f"Error initializing preview mode: {e}")
    else:
        # Restore previous alarm state
        alarm_mode = stored_alarm_state
    save_settings()

def refresh_cameras():
    """Refresh the list of available cameras"""
    global available_cameras, camera_combo
    try:
        # Store current camera selection
        current_selection = camera_combo.get() if camera_combo.get() else "0 (Camera 0)"
        
        # Get new camera list
        new_cameras = []
        with open(os.devnull, 'w') as devnull:
            old_stderr = os.dup(2)
            os.dup2(devnull.fileno(), 2)
            
            # Check indices 0-9 (10 possible cameras)
            for i in range(10):
                if i == current_camera:  # Skip current camera to avoid disruption
                    new_cameras.append(i)
                    continue
                    
                try:
                    temp_cap = cv2.VideoCapture(i)
                    if temp_cap.isOpened():
                        ret, _ = temp_cap.read()
                        if ret:
                            new_cameras.append(i)
                    temp_cap.release()
                except:
                    continue
                    
            # Restore stderr
            os.dup2(old_stderr, 2)
        
        # Update available cameras
        available_cameras = new_cameras
        
        # Update combobox values
        camera_options = [f"{i} (Camera {i})" for i in available_cameras]
        camera_combo['values'] = camera_options
        
        # Try to maintain previous selection if possible
        if current_selection in camera_options:
            camera_combo.set(current_selection)
        elif camera_options:
            camera_combo.set(camera_options[0])
            
        print(f"Found {len(available_cameras)} camera(s)")
        
    except Exception as e:
        print(f"Error refreshing cameras: {e}")

# Then initialize GUI and start main loop
if __name__ == "__main__":
    check_dependencies()  # Ensure dependencies are installed
    load_settings()  # Load saved settings
    if initialize_camera():
        start_discord_bot()
        initialize_gui()
        update_frame()
        
        # Start socket server in a separate thread
        server_thread = threading.Thread(
            target=lambda: asyncio.run(start_server())
        )
        server_thread.daemon = True
        server_thread.start()
        
        root.mainloop()
    else:
        print("No cameras found!")
