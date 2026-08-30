import sys
import socket
import random
import os
import config

def get_resource_path(relative_path):
    """
    Resolves the absolute path to bundled resource assets.
    Handles standard development environment paths as well as PyInstaller frozen sys._MEIPASS paths.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_local_ip():
    """
    Determines the local IP address of the active network interface.
    Creates a temporary datagram socket toward a public IP range to resolve
    the primary network interface IP without transmitting actual network data.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        pass

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return '127.0.0.1'

def generate_passcode():
    """
    Generates a random 4-digit numeric passcode formatted as a zero-padded string.
    Used for pairing laptop-to-laptop transfers.
    """
    return f"{random.randint(0, 9999):04d}"

def format_size(size_in_bytes):
    """
    Converts a byte count into a formatted human-readable string (B, KB, MB, GB, TB).
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} PB"

def format_time(seconds):
    """
    Formats seconds into a human-readable duration (e.g. 12s, 01m 23s, 02h 05m).
    """
    if seconds is None or seconds < 0 or seconds == float('inf'):
        return "--"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    secs = seconds % 60
    if minutes < 60:
        return f"{minutes:02d}m {secs:02d}s"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}h {mins:02d}m"

def pil_to_b64(pil_img):
    """
    Converts a PIL Image object into a base64 encoded PNG string for Flet Image controls.
    """
    if not pil_img:
        return ""
    import io
    import base64
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def generate_qr_image(url, fg_color=config.COLOR_TEXT_PRIMARY, bg_color=config.COLOR_CARD):
    """
    Generates a PIL Image containing a QR code for mobile browser connections.
    """
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fg_color, back_color=bg_color)
        return img.convert('RGB')
    except Exception as e:
        print(f"Failed to generate QR code image: {e}")
        return None


