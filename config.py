import os

# Window Geometry (Fixed 2:3 Aspect Ratio)
WINDOW_WIDTH = 440
WINDOW_HEIGHT = 660

# Light Theme Tokens (Warm Cream & Black Palette)
THEME_LIGHT = {
    "bg": "#F3EFE6",
    "card": "#FAF7F0",
    "card_alt": "#EAE4D7",
    "border": "#E2DCD0",
    "text": "#1C1917",
    "muted": "#78716C",
    "green": "#15803D",
    "green_hover": "#166534",
    "btn_primary_bg": "#1C1917",
    "btn_primary_fg": "#F3EFE6",
    "btn_secondary_bg": "#FAF7F0",
    "btn_secondary_fg": "#1C1917",
}

# Dark Theme Tokens (Obsidian & Cream Palette)
THEME_DARK = {
    "bg": "#121212",
    "card": "#1E1E1E",
    "card_alt": "#2A2A2A",
    "border": "#333333",
    "text": "#F3EFE6",
    "muted": "#A8A29E",
    "green": "#22C55E",
    "green_hover": "#16A34A",
    "btn_primary_bg": "#F3EFE6",
    "btn_primary_fg": "#121212",
    "btn_secondary_bg": "#1E1E1E",
    "btn_secondary_fg": "#F3EFE6",
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
CHUNK_SIZE_P2P = 65536       # Buffer chunk size for peer-to-peer TCP transfers (64 KB)
CHUNK_SIZE_WEB = 65536       # Buffer chunk size for mobile HTTP web transfers (64 KB)

# Application Metadata and Default Storage
APP_TITLE = "DropIt"
APP_VERSION = "2.2.0"
APP_MOTTO = "FAST • SECURE • ZERO-CLOUD"
WINDOW_GEOMETRY = f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
DOWNLOADS_DIR = os.path.join(os.getcwd(), "Downloads")


