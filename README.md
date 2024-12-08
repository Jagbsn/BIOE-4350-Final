# Motion Detection Security System

A Python-based security system that uses computer vision for motion detection, with Discord notifications, email alerts, and Google Drive video storage.

## Features

- Real-time motion detection with adjustable sensitivity
- Live camera feed with motion highlighting
- Automatic video recording when motion is detected
- Email notifications with snapshots and video clips
- Discord bot integration for remote monitoring and control
- Google Drive integration for video storage
- Scheduled arming/disarming
- Multiple camera support
- Settings persistence between sessions

## Prerequisites

- Python 3.8 or higher
- A webcam or USB camera
- Google Drive API credentials (`drive.json`)
- Discord bot token
- Gmail account for sending notifications

## Installation

1. Clone the repository:

2. Set up credentials:
   - Place your Google Drive API credentials in `drive.json`
   - Update Discord bot token in `Bot_test.py`
   - Update email credentials in `Mail_Test.py`

## Usage

1. Run the main program:

2. Main Interface:
   - **Camera Feed Tab**: Shows live camera feed and main controls
   - **Settings Tab**: Configure system parameters

3. Camera Feed Controls:
   - **Arm System**: Start motion detection
   - **Disarm System**: Stop motion detection
   - **Reset Alarm**: Clear current alarm state
   - **Quit**: Safely exit the program

4. Settings Options:
   - Camera selection and refresh
   - Motion detection sensitivity
   - Video resolution
   - Scheduling (24-hour format)
   - Motion highlighting toggle
   - Preview mode

5. Discord Commands:
   - `arm`: Activate the alarm system
   - `disarm`: Deactivate the alarm system
   - `reset`: Reset the alarm system
   - `status`: Check current system status
   - `schedule`: View arming schedule
   - `last`: View last motion detection frame
   - `link`: Get video drive link
   - `help`: List available commands

## Configuration

### Settings.json
The system saves settings in `settings.json`, including:
- Video resolution
- Sensitivity level
- Schedule times
- Camera selection
- Motion highlight preferences

### Email Notifications
Emails include:
- Snapshot of detected motion
- Link to recorded video clip
- Timestamp of the event

### Discord Integration
The Discord bot provides:
- Real-time notifications
- Remote control capabilities
- Access to motion detection images
- System status monitoring

## Troubleshooting

1. Camera Issues:
   - Use the "Refresh Cameras" button to detect new cameras
   - Ensure camera isn't being used by other applications

2. Discord Bot:
   - Verify bot token is correct
   - Ensure bot has necessary permissions

3. Email Notifications:
   - Check Gmail credentials
   - Allow less secure app access if needed

4. Motion Detection:
   - Adjust sensitivity using the slider
   - Use preview mode to test detection

## Notes

- The system requires continuous internet connection for Discord and email features
- Video clips are automatically uploaded to Google Drive
- Settings are saved to the settings.json file automatically when using the "Save Settings" button
- The system can be scheduled to arm/disarm at specific times
