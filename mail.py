import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from drive_utils import upload_to_drive
from datetime import datetime

def send_email(frame_path, video_path):
    sender_email = 'labentrynotifications@gmail.com'
    password = 'rlno gqqs wxba kidu'
    receiver_email = 'jagbsn@g.clemson.edu'

    subject = 'Emergency Lab Security Event!'
    
    # Upload video to Drive and get link
    # Get current timestamp and create new filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    drive_filename = f'motion_{timestamp}.mp4'
    video_link = upload_to_drive(video_path, '1wE92BP8zZa--b8JTge4tSm2-sKy3s5_S', drive_filename)  # Added filename parameter
    
    # Modify body to include the Drive link
    body = ('Motion has been detected!\n\n'
            'Evidence below:\n'
            f'Video clip can be viewed here: {video_link if video_link else "Upload failed"}\n\n')

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Attach only the frame
    try:
        with open(frame_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={frame_path}')
        msg.attach(part)
    except Exception as e:
        print(f"Failed to attach frame: {e}")

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
        print("Email with frame and video link sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
