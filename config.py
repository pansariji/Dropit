import os

# Window Geometry (Compact 2:3 Handheld Terminal Format)
WINDOW_WIDTH = 460
WINDOW_HEIGHT = 690

# Typography Tokens
FONT_DISPLAY = "Space Grotesk"
FONT_MONO = "JetBrains Mono"

# Neo-Brutalist Core Design Tokens
BRUTAL_BG = "#F4F4EE"              # Warm canvas with industrial punch
BRUTAL_SURFACE = "#FFFFFF"         # Pure paper white for cards and bays
BRUTAL_CARD = "#FAF9F5"            # Clean card foundation
BRUTAL_BORDER = "#000000"          # Solid ink-black border
BRUTAL_TEXT = "#000000"            # Solid ink-black primary typography
BRUTAL_MUTED = "#6B7280"           # Muted technical descriptor color
BRUTAL_YELLOW = "#FFE600"          # Electric Hazard Yellow (Primary CTA & highlights)
BRUTAL_GREEN = "#00F090"           # Neo Mint Green (Connected, online, success)
BRUTAL_GREEN_LIGHT = "#D1FAE5"     # Soft Mint background badge
BRUTAL_BLUE = "#2563EB"            # Electric Cobalt (Network sockets, links)
BRUTAL_CYAN = "#58E1FF"            # High-impact Cyan tile background
BRUTAL_RED = "#FF5555"             # Safety Red (Close button, destructive alerts)
BRUTAL_RED_LIGHT = "#FFA5A5"       # Cancel button fill

# Theme Token Dictionaries
THEME_LIGHT = {
    "bg": BRUTAL_BG,
    "card": BRUTAL_SURFACE,
    "card_alt": BRUTAL_CARD,
    "border": BRUTAL_BORDER,          # #000000
    "shadow": "#000000",              # Solid ink-black 3D shadow
    "text": BRUTAL_TEXT,              # #000000
    "muted": BRUTAL_MUTED,
    "green": BRUTAL_GREEN,
    "green_hover": "#00D680",
    "green_light": BRUTAL_GREEN_LIGHT,
    "yellow": BRUTAL_YELLOW,
    "blue": BRUTAL_BLUE,
    "cyan": BRUTAL_CYAN,
    "red": BRUTAL_RED,
    "red_light": BRUTAL_RED_LIGHT,
    "btn_primary_bg": BRUTAL_YELLOW,
    "btn_primary_fg": "#000000",
    "btn_primary_border": "#000000",
    "btn_primary_shadow": "#000000",
    "btn_secondary_bg": "#FFFFFF",
    "btn_secondary_fg": "#000000",
    "btn_secondary_border": "#000000",
    "btn_secondary_shadow": "#000000",
    "status_bg": BRUTAL_GREEN_LIGHT,
    "status_fg": "#000000",
    "status_border": "#000000",
    "pin_bg": BRUTAL_SURFACE,
    "pin_border": "#000000",
    "pin_shadow": "#000000",
    "pin_fg": "#000000",
    "qr_shadow": "#000000",
}

THEME_DARK = {
    "bg": "#0D0D12",                  # Deep Cyberpunk Midnight Obsidian
    "card": "#171720",                # Elevated Titanium Slate surface
    "card_alt": "#1E1E2A",            # Inset / Secondary contrast surface
    "border": "#323246",              # Refined metallic slate structural border
    "shadow": "#000000",              # Deep grounded shadow for cards
    "text": "#FFFFFF",                # Crisp bright white typography
    "muted": "#94A3B8",               # Slate muted technical descriptor
    "green": "#00F090",               # Radiant Neo Mint Green
    "green_hover": "#00D680",
    "green_light": "#0F2E22",         # Sleek dark emerald status pill fill
    "yellow": "#FFE600",              # High-Voltage Hazard Yellow
    "blue": "#38BDF8",                # Electric Sky Blue
    "cyan": "#00E5FF",                # Electric Cyan
    "red": "#FF4B4B",                 # Vibrant Safety Red
    "red_light": "#2D1216",           # Dark crimson badge fill
    "btn_primary_bg": "#FFE600",
    "btn_primary_fg": "#000000",
    "btn_primary_border": "#000000",
    "btn_primary_shadow": "#00E5FF",  # High-voltage Electric Cyan 3D shadow!
    "btn_secondary_bg": "#FFFFFF",    # Pure White secondary button with maximum contrast!
    "btn_secondary_fg": "#000000",
    "btn_secondary_border": "#000000",
    "btn_secondary_shadow": "#00F090",# Neo Mint 3D shadow!
    "status_bg": "#0F2E22",
    "status_fg": "#00F090",
    "status_border": "#00F090",
    "pin_bg": "#1E1E2A",
    "pin_border": "#FFE600",          # Glowing Electric Yellow cypher PIN boxes!
    "pin_shadow": "#FFE600",
    "pin_fg": "#FFE600",
    "qr_shadow": "#00F090",           # Neo Mint QR frame shadow
}

# Backward Compatibility Constants
COLOR_BG = THEME_LIGHT["bg"]
COLOR_CARD = THEME_LIGHT["card"]
COLOR_CARD_ALT = THEME_LIGHT["card_alt"]
COLOR_BORDER = THEME_LIGHT["border"]
COLOR_TEXT_PRIMARY = THEME_LIGHT["text"]
COLOR_TEXT_MUTED = THEME_LIGHT["muted"]
COLOR_GREEN = THEME_LIGHT["green"]
COLOR_GREEN_HOVER = THEME_LIGHT["green_hover"]

# Networking Protocol Constants
DEFAULT_UDP_PORT = 50025    # Port for UDP broadcast discovery
DEFAULT_P2P_PORT = 50026    # Default starting port for TCP peer transfers
DEFAULT_WEB_PORT = 8080     # Default starting port for mobile web sharing
CHUNK_SIZE_P2P = 262144     # High-throughput buffer chunk size for P2P transfers (256 KB)
CHUNK_SIZE_WEB = 262144     # High-throughput buffer chunk size for HTTP transfers (256 KB)
TCP_SOCKET_BUFFER_SIZE = 2097152  # 2 MB socket send/receive buffer to prevent TCP window starvation
DISK_BUFFER_SIZE = 1048576        # 1 MB disk I/O buffer to decouple physical disk commits from socket reads

# Application Metadata and Default Storage
APP_TITLE = "DropIt"
APP_VERSION = "2.2.0"
APP_MOTTO = "FAST • SECURE • ZERO-CLOUD"
WINDOW_GEOMETRY = f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"

def get_system_downloads_dir() -> str:
    """
    Resolves the official native Downloads directory for the current operating system
    (Windows, macOS, or Linux), respecting user-customized Shell Folders on Windows
    and XDG user-dirs on Linux, with fallback to ~/Downloads.
    """
    import sys
    # Windows User Shell Folders check
    if os.name == 'nt':
        try:
            import winreg
            sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders'
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                # {374DE290-123F-4565-9164-39C4925E467B} is standard Windows KnownFolder GUID for Downloads
                for guid in ['{374DE290-123F-4565-9164-39C4925E467B}', '{7D83EE9B-2244-4E70-B1F5-54E382E3E8C1}']:
                    try:
                        val, _ = winreg.QueryValueEx(key, guid)
                        expanded = os.path.normpath(os.path.expandvars(val))
                        if os.path.exists(expanded):
                            return expanded
                    except FileNotFoundError:
                        continue
        except Exception:
            pass

    # Linux XDG user-dirs check
    if sys.platform.startswith('linux'):
        try:
            config_file = os.path.expanduser('~/.config/user-dirs.dirs')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('XDG_DOWNLOAD_DIR'):
                            val = line.split('=', 1)[1].strip().strip('"')
                            val = val.replace('$HOME', os.path.expanduser('~'))
                            if os.path.exists(val):
                                return os.path.normpath(val)
        except Exception:
            pass

    # Standard universal fallback: ~/Downloads across Windows, macOS, and Linux
    default_path = os.path.normpath(os.path.join(os.path.expanduser('~'), 'Downloads'))
    os.makedirs(default_path, exist_ok=True)
    return default_path

DOWNLOADS_DIR = get_system_downloads_dir()
