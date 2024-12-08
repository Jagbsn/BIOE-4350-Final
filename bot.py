import discord
from discord.ext import commands
import datetime
import asyncio
import os
from main import alarm_mode, schedule_times

TOKEN = 'MTMwNjY5NTkzODYwNTA1NjExMQ.GYcekm.heDxQoOUB4nJNCk8O9RovBzftkazPJjvlL24m4'
YOUR_CHANNEL_ID = 1306695137216430093
HOST = '127.0.0.1'
PORT = 65432

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True

# Use commands.Bot but handle messages without a prefix
client = commands.Bot(command_prefix='', intents=intents)

@client.event
async def on_ready():
    """Called when the bot successfully connects to Discord"""
    print(f'\nDiscord Bot "{client.user}" is now operational!')
    print(f'Connected to {len(client.guilds)} server(s)')
    print('-' * 50)

async def send_command(command):
    """Send a command to main.py via socket and return the response."""
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
        writer.write(command.encode())
        await writer.drain()
        
        # Wait for response with timeout
        response = await asyncio.wait_for(reader.read(1024), timeout=5.0)
        response_text = response.decode()
        
        writer.close()
        await writer.wait_closed()
        return response_text
    except Exception as e:
        print(f"Error sending command: {e}")
        return f"Error: {str(e)}"

async def send_alert_to_discord():
    """Sends an alert message with the motion frame to Discord when motion is detected."""
    try:
        await client.wait_until_ready()
        channel = client.get_channel(YOUR_CHANNEL_ID)
        if channel:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            embed = discord.Embed(
                title="⚠️ Motion Detected!",
                description=f"Motion was detected at {current_time}",
                color=discord.Color.red()
            )
            
            # Add the motion frame
            frame_path = "motion_frame.jpg"
            if os.path.exists(frame_path):
                file = discord.File(frame_path, filename="motion.jpg")
                embed.set_image(url="attachment://motion.jpg")
                await channel.send(file=file, embed=embed)
            else:
                await channel.send(embed=embed)
                
            print("Alert sent to Discord successfully.")
        else:
            print(f"Could not find channel with ID: {YOUR_CHANNEL_ID}")
    except Exception as e:
        print(f"Error sending Discord alert: {e}")

async def send_motion_frame_to_discord():
    """Sends the last motion frame to Discord."""
    try:
        channel = client.get_channel(YOUR_CHANNEL_ID)
        frame_path = "motion_frame.jpg"
        
        if not os.path.exists(frame_path):
            await channel.send("No motion frame available!")
            return
            
        with open(frame_path, "rb") as frame_file:
            await channel.send("Last detected motion:", file=discord.File(frame_file))
    except Exception as e:
        print(f"Error sending motion frame: {e}")
        await channel.send(f"Error sending motion frame: {str(e)}")

async def send_url_to_discord():
    """Sends the video drive URL to Discord."""
    try:
        channel = client.get_channel(YOUR_CHANNEL_ID)
        # Replace with your actual video drive URL
        url = "https://drive.google.com/drive/folders/1wE92BP8zZa--b8JTge4tSm2-sKy3s5_S?usp=sharing"
        await channel.send(f"Video Drive URL: {url}")
    except Exception as e:
        print(f"Error sending URL: {e}")
        await channel.send(f"Error sending URL: {str(e)}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    command = message.content.lower()
    if command == "arm":
        await send_command("alarm on")
        await message.channel.send("Alarm system activated!")
    elif command == "disarm":
        await send_command("alarm off")
        await message.channel.send("Alarm system deactivated!")
    elif command == "reset":
        await send_command("alarm reset")
        await message.channel.send("Alarm system reset!")
    elif command == "status":
        try:
            status = await send_command("status")
            await message.channel.send(f"```{status}```")
        except Exception as e:
            print(f"Error in status command: {e}")
            await message.channel.send("Error retrieving status information.")
    elif command == "schedule":
        try:
            schedule = await send_command("schedule")
            await message.channel.send(f"```{schedule}```")
        except Exception as e:
            print(f"Error in schedule command: {e}")
            await message.channel.send("Error retrieving schedule information.")
    elif command == "last":
        await send_motion_frame_to_discord()
    elif command == "link":
        await send_url_to_discord()
    elif command == "help":
        help_text = (
            "Available commands:\n"
            "`arm` - Activate the alarm system\n"
            "`disarm` - Deactivate the alarm system\n"
            "`reset` - Reset the alarm system\n"
            "`status` - Current status of the alarm system\n"
            "`schedule` - Arming and disarming schedule\n"
            "`last` - Sends the last frame of detected motion\n"
            "`link` - Sends the URL of the video drive\n"
            "`help` - Sends command list\n"
        )
        await message.channel.send(help_text)
    elif command == "test alert":  # For testing the alert function
        await send_alert_to_discord()

def run_bot():
    """Initialize and run the Discord bot"""
    print("\nAttempting to log in to Discord...")
    try:
        client.run(TOKEN)
    except discord.errors.LoginFailure:
        print("Error: Invalid Discord token. Please check your token.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
