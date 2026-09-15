import sys
import socket
import random
import os
import config
from config import get_system_downloads_dir
import logging

logger = logging.getLogger("dropit")

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
            box_size=8,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color=fg_color, back_color=bg_color)
        return img.convert('RGB')
    except Exception as e:
        logger.error(f"Failed to generate QR code image: {e}")
        return None

def open_file_location(path: str):
    """
    Opens the containing directory or selects the file in the native OS file manager
    (Windows Explorer, macOS Finder, or Linux file manager).
    """
    import subprocess
    if not path:
        path = config.DOWNLOADS_DIR
    if not os.path.exists(path):
        path = config.DOWNLOADS_DIR
        os.makedirs(path, exist_ok=True)

    try:
        norm_path = os.path.normpath(path)
        if os.name == 'nt':
            if os.path.isfile(norm_path):
                subprocess.Popen(['explorer', f'/select,{norm_path}'])
            else:
                os.startfile(norm_path)
        elif sys.platform == 'darwin':
            cmd = ['open', '-R', norm_path] if os.path.isfile(norm_path) else ['open', norm_path]
            subprocess.Popen(cmd)
        else:
            folder = os.path.dirname(norm_path) if os.path.isfile(norm_path) else norm_path
            subprocess.Popen(['xdg-open', folder])
    except Exception as e:
        logger.error(f"Failed to open file location: {e}")

def make_tactile(
    container,
    on_click_handler=None,
    idle_shadow_x: float = 3.0,
    idle_shadow_y: float = 3.0,
    press_shadow_x: float = 1.0,
    press_shadow_y: float = 1.0,
    duration_ms: int = 50,
    shadow_color: str = None
):
    """
    Applies an authentic Neo-Brutalist 3D mechanical press animation to a Container button.
    On click, the hard box shadow collapses from (idle_shadow_x, idle_shadow_y) to
    (press_shadow_x, press_shadow_y) while translating down-right, simulating a physical
    tactile depression into the canvas, then springs back up and executes the callback.
    Preserves theme-specific shadow color (#000000 in light, #FFFFFF in dark mode).
    Guarantees restoration of idle position even under rapid clicking, thread switching,
    or exception conditions, preventing the button from ever getting visually stuck.
    """
    import asyncio
    import inspect
    import flet as ft

    resolved_shadow_color = shadow_color or (container.shadow.color if (container.shadow and container.shadow.color) else "#000000")

    container.animate = ft.Animation(duration=duration_ms, curve=ft.AnimationCurve.EASE_OUT)
    container.animate_offset = ft.Animation(duration=duration_ms, curve=ft.AnimationCurve.EASE_OUT)
    container.mouse_cursor = ft.MouseCursor.CLICK
    container.shadow = ft.BoxShadow(spread_radius=0, blur_radius=0, color=resolved_shadow_color, offset=ft.Offset(idle_shadow_x, idle_shadow_y))
    container.offset = ft.Offset(0, 0)

    is_animating = False

    async def _animated_click(e):
        nonlocal is_animating
        if is_animating:
            return
        is_animating = True
        try:
            had_shadow = container.shadow is not None
            active_color = container.shadow.color if (had_shadow and container.shadow.color) else resolved_shadow_color

            # 1. Depress button visually
            if had_shadow:
                container.shadow = ft.BoxShadow(spread_radius=0, blur_radius=0, color=active_color, offset=ft.Offset(press_shadow_x, press_shadow_y))
            container.offset = ft.Offset(0.007, 0.018)
            try:
                container.update()
            except Exception:
                pass

            # 2. Brief tactile depression duration
            await asyncio.sleep(duration_ms / 1000.0)

            # 3. Restore idle position
            spring_color = container.shadow.color if (container.shadow and container.shadow.color) else active_color
            if had_shadow:
                container.shadow = ft.BoxShadow(spread_radius=0, blur_radius=0, color=spring_color, offset=ft.Offset(idle_shadow_x, idle_shadow_y))
            container.offset = ft.Offset(0, 0)
            try:
                container.update()
            except Exception:
                pass
        finally:
            # Guarantees idle position restoration and unlocks animation state
            container.offset = ft.Offset(0, 0)
            is_animating = False

        # 4. Execute click handler directly on Flet's event loop
        if on_click_handler:
            try:
                sig = inspect.signature(on_click_handler)
                has_params = len(sig.parameters) > 0
            except Exception:
                has_params = True

            try:
                if has_params:
                    res = on_click_handler(e)
                else:
                    res = on_click_handler()

                if asyncio.iscoroutine(res):
                    await res
            except Exception as ex:
                logger.debug(f"[make_tactile] Click handler error: {ex}")

    container.on_click = _animated_click
    return container

def optimize_tcp_socket(sock):
    """
    Applies high-throughput TCP streaming optimizations to a socket:
    1. TCP_NODELAY: Disables Nagle's algorithm to eliminate 40ms-200ms Delayed-ACK stalls.
    2. SO_SNDBUF & SO_RCVBUF: Configures enlarged 2 MB buffers to maximize TCP window scale
       and prevent sender/receiver pipeline starvation over LAN and high-speed Wi-Fi.
    Gracefully handles platform-specific buffer clamping and closed sockets.
    """
    if not sock:
        return sock
    import socket
    # 1. Disable Nagle's algorithm for continuous pipelining without Delayed-ACK stalls
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except Exception:
        pass

    # 2. Enlarge socket send and receive buffers to prevent TCP window collapse
    target_buf = getattr(config, 'TCP_SOCKET_BUFFER_SIZE', 2097152)
    for opt in (socket.SO_SNDBUF, socket.SO_RCVBUF):
        try:
            sock.setsockopt(socket.SOL_SOCKET, opt, target_buf)
        except Exception:
            try:
                sock.setsockopt(socket.SOL_SOCKET, opt, 524288)
            except Exception:
                pass

    return sock


class TransferMetricsTracker:
    """
    Performance calculator tracking elapsed time, current speed, average speed,
    peak speed, size strings, and dynamic ETA.
    
    Features:
    - Adaptive Exponential Moving Average (EMA) and rolling window smoothing:
      Eliminates erratic speed jitter (e.g. jumping between 70 KB/s and 40 MB/s due to 100ms
      sampling aliasing) while preserving rapid response to true bandwidth shifts.
    - True peak speed tracking filtered against micro-slice division artifacts.
    - Pause & resume support with elapsed time discounting and delta preservation.
    """
    def __init__(self, ema_alpha=0.25):
        self.ema_alpha = ema_alpha
        self.reset()

    def reset(self):
        import time
        self.start_time = time.time()
        self.peak_bytes_sec = 0.0
        self.smoothed_bytes_sec = None
        self.last_update_time = self.start_time
        self.last_bytes = 0
        self.total_paused_time = 0.0
        self.pause_start_time = None
        self.sample_history = []

    def pause(self):
        import time
        if self.pause_start_time is None:
            self.pause_start_time = time.time()

    def resume(self):
        import time
        now = time.time()
        if self.pause_start_time is not None:
            self.total_paused_time += max(0.0, now - self.pause_start_time)
            self.pause_start_time = None
        self.last_update_time = now

    def update(self, current_bytes, total_bytes, delta_time=None, bytes_diff=None):
        import time
        import math
        now = time.time()
        if not hasattr(self, 'start_time') or self.start_time is None:
            self.reset()

        total_paused = getattr(self, 'total_paused_time', 0.0)
        total_elapsed = max(now - self.start_time - total_paused, 0.001)

        if delta_time is None or delta_time <= 0:
            delta_time = max(now - self.last_update_time, 0.001)
        if bytes_diff is None:
            bytes_diff = max(current_bytes - self.last_bytes, 0)

        # Raw instantaneous rate
        raw_bytes_sec = (bytes_diff / delta_time) if delta_time > 0 else 0.0

        # Update rolling sample history (keep last 1.2 seconds of samples)
        if not hasattr(self, 'sample_history'):
            self.sample_history = []
        self.sample_history.append((now, current_bytes))
        cutoff = now - 1.2
        while len(self.sample_history) > 1 and self.sample_history[0][0] < cutoff:
            self.sample_history.pop(0)

        # Calculate rolling window rate if at least 2 samples spanning >= 0.2s exist
        if len(self.sample_history) >= 2:
            oldest_time, oldest_bytes = self.sample_history[0]
            window_time = now - oldest_time
            if window_time >= 0.2:
                window_bytes_sec = max(current_bytes - oldest_bytes, 0) / window_time
            else:
                window_bytes_sec = raw_bytes_sec
        else:
            window_bytes_sec = raw_bytes_sec

        # Apply Exponential Moving Average (EMA)
        if self.smoothed_bytes_sec is None or self.smoothed_bytes_sec <= 0:
            self.smoothed_bytes_sec = window_bytes_sec
        else:
            alpha = getattr(self, 'ema_alpha', 0.25)
            adjusted_alpha = min(1.0, max(alpha, 1.0 - math.exp(-delta_time / 0.4)))
            self.smoothed_bytes_sec = (adjusted_alpha * window_bytes_sec) + ((1.0 - adjusted_alpha) * self.smoothed_bytes_sec)

        cur_bytes_sec = self.smoothed_bytes_sec
        avg_bytes_sec = (current_bytes / total_elapsed) if total_elapsed > 0 else 0.0

        # Peak speed tracking (filtered against startup spikes)
        if cur_bytes_sec > self.peak_bytes_sec and total_elapsed > 0.3:
            self.peak_bytes_sec = cur_bytes_sec

        self.last_update_time = now
        self.last_bytes = current_bytes

        percent = (current_bytes / total_bytes * 100) if total_bytes > 0 else 100.0
        cur_speed_str = f"{format_size(cur_bytes_sec)}/s"
        avg_speed_str = f"{format_size(avg_bytes_sec)}/s"
        peak_speed_str = f"{format_size(self.peak_bytes_sec)}/s"
        size_info_str = f"{format_size(current_bytes)} / {format_size(total_bytes)}"

        remaining_bytes = max(0, total_bytes - current_bytes)
        eta_sec = (remaining_bytes / cur_bytes_sec) if cur_bytes_sec > 0 else None
        eta_str = format_time(eta_sec)
        elapsed_str = format_time(total_elapsed)

        return {
            "percent": percent,
            "cur_speed_str": cur_speed_str,
            "avg_speed_str": avg_speed_str,
            "peak_speed_str": peak_speed_str,
            "size_info_str": size_info_str,
            "eta_str": eta_str,
            "elapsed_str": elapsed_str,
            "cur_bytes_sec": cur_bytes_sec,
            "avg_bytes_sec": avg_bytes_sec,
        }

    def get_final_metrics(self, total_bytes):
        import time
        now = time.time()
        total_paused = getattr(self, 'total_paused_time', 0.0)
        total_elapsed = max(now - (self.start_time or now) - total_paused, 0.001)
        avg_bytes_sec = (total_bytes / total_elapsed) if total_elapsed > 0 else 0.0
        peak = max(self.peak_bytes_sec, avg_bytes_sec)
        return {
            "percent": 100.0,
            "cur_speed_str": "0 B/s",
            "avg_speed_str": f"{format_size(avg_bytes_sec)}/s",
            "peak_speed_str": f"{format_size(peak)}/s",
            "size_info_str": f"{format_size(total_bytes)} / {format_size(total_bytes)}",
            "eta_str": "0s",
            "elapsed_str": format_time(total_elapsed),
        }

def open_native_file_picker(title="Select Payload to Send", is_folder=False):
    """
    Universal native file & directory picker for Windows, macOS, and Linux.
    - macOS: Invokes Cocoa NSOpenPanel via osascript with zero external dependencies.
    - Linux: Uses zenity (GNOME) or kdialog (KDE), falling back to tkinter.filedialog.
    - Windows & Fallback: Uses tkinter.filedialog.
    """
    try:
        # 1. macOS: Native AppleScript Cocoa NSOpenPanel
        if sys.platform == "darwin":
            import subprocess
            prompt = title.replace('"', '\\"')
            if is_folder:
                cmd = ["osascript", "-e", f'POSIX path of (choose folder with prompt "{prompt}")']
            else:
                cmd = ["osascript", "-e", f'POSIX path of (choose file with prompt "{prompt}")']
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0 and proc.stdout.strip():
                p = proc.stdout.strip()
                if os.path.exists(p):
                    return p
            return None

        # 2. Linux: zenity or kdialog
        elif sys.platform.startswith("linux"):
            import shutil
            import subprocess
            if shutil.which("zenity"):
                cmd = ["zenity", "--file-selection", f"--title={title}"]
                if is_folder:
                    cmd.append("--directory")
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode == 0 and proc.stdout.strip():
                    p = proc.stdout.strip()
                    if os.path.exists(p):
                        return p
            elif shutil.which("kdialog"):
                cmd = ["kdialog", "--getexistingdirectory" if is_folder else "--getopenfilename"]
                proc = subprocess.run(cmd, capture_output=True, text=True)
                if proc.returncode == 0 and proc.stdout.strip():
                    p = proc.stdout.strip()
                    if os.path.exists(p):
                        return p

        # 3. Windows and universal fallback: Tkinter
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        if is_folder:
            path = filedialog.askdirectory(title=title)
        else:
            path = filedialog.askopenfilename(title=title)
        root.destroy()
        if path and os.path.exists(path):
            return os.path.normpath(path)
        return None
    except Exception as e:
        logger.debug(f"[open_native_file_picker] error: {e}")
        return None

def get_clipboard_files() -> list[str]:
    """
    Cross-platform clipboard payload reader for Windows, macOS, and Linux.
    Retrieves files/folders copied from Windows Explorer, macOS Finder, or Linux File Managers.
    """
    # 1. Windows: Win32 CF_HDROP & Unicode Text
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            shell32 = ctypes.windll.shell32
            kernel32 = ctypes.windll.kernel32

            user32.GetClipboardData.argtypes = [wintypes.UINT]
            user32.GetClipboardData.restype = wintypes.HANDLE
            kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]

            CF_HDROP = 15
            CF_UNICODETEXT = 13

            if not user32.OpenClipboard(None):
                return []

            try:
                hdrop = user32.GetClipboardData(CF_HDROP)
                if hdrop:
                    count = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
                    files = []
                    for i in range(count):
                        length = shell32.DragQueryFileW(hdrop, i, None, 0)
                        buff = ctypes.create_unicode_buffer(length + 1)
                        shell32.DragQueryFileW(hdrop, i, buff, length + 1)
                        if os.path.exists(buff.value):
                            files.append(buff.value)
                    if files:
                        return files

                htext = user32.GetClipboardData(CF_UNICODETEXT)
                if htext:
                    ptr = kernel32.GlobalLock(htext)
                    if ptr:
                        try:
                            text_val = ctypes.wstring_at(ptr).strip().strip('"').strip("'")
                            if text_val and os.path.exists(text_val):
                                return [text_val]
                        finally:
                            kernel32.GlobalUnlock(htext)
            finally:
                user32.CloseClipboard()
        except Exception:
            pass

    # 2. macOS: Finder Pasteboard via AppleScript
    elif sys.platform == "darwin":
        try:
            import subprocess
            import urllib.parse
            script = '''
            try
                set cb to (the clipboard as «class furl»)
                return POSIX path of cb
            on error
                try
                    return (the clipboard as text)
                end try
            end try
            '''
            proc = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            if proc.returncode == 0:
                raw = proc.stdout.strip()
                lines = [l.strip() for l in raw.splitlines() if l.strip()]
                results = []
                for l in lines:
                    if l.startswith("file://"):
                        l = urllib.parse.unquote(urllib.parse.urlparse(l).path)
                    if os.path.exists(l):
                        results.append(l)
                if results:
                    return results
        except Exception:
            pass

    # 3. Linux: xclip / wl-paste for text/uri-list
    elif sys.platform.startswith("linux"):
        import shutil
        import subprocess
        import urllib.parse
        tools = []
        if shutil.which("wl-paste"):
            tools.append(["wl-paste", "-t", "text/uri-list"])
        if shutil.which("xclip"):
            tools.append(["xclip", "-selection", "clipboard", "-t", "text/uri-list", "-o"])

        for cmd in tools:
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                if proc.returncode == 0 and proc.stdout.strip():
                    results = []
                    for line in proc.stdout.splitlines():
                        line = line.strip()
                        if line.startswith("file://"):
                            path = urllib.parse.unquote(urllib.parse.urlparse(line).path)
                            if os.path.exists(path):
                                results.append(path)
                    if results:
                        return results
            except Exception:
                continue

    # 4. Universal Fallback: Tkinter Clipboard
    try:
        import tkinter as tk
        import urllib.parse
        root = tk.Tk()
        root.withdraw()
        clip_text = root.clipboard_get()
        root.destroy()
        if clip_text:
            lines = [l.strip() for l in clip_text.splitlines() if l.strip()]
            results = []
            for l in lines:
                if l.startswith("file://"):
                    l = urllib.parse.unquote(urllib.parse.urlparse(l).path)
                l = l.strip('"').strip("'")
                if os.path.exists(l):
                    results.append(l)
            if results:
                return results
    except Exception:
        pass

    return []

class NativeDropOverlay:
    """
    Desktop Drop Zone Overlay.
    - Windows: Creates a transparent Win32 layered popup window registered for DragAcceptFiles (WM_DROPFILES),
      owned by the DropIt target window (hWndParent=target_hwnd) and positioned at HWND_TOP in the Z-order.
    - macOS & Linux: Safe cross-platform handler that manages overlay lifecycle cleanly.
    """
    def __init__(self, target_title="DropIt", on_drop=None, on_click=None, rel_x=16, rel_y=96, rel_w_offset=-32, height=85):
        self.target_title = target_title
        self.on_drop = on_drop
        self.on_click = on_click
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.rel_w_offset = rel_w_offset
        self.height = height
        self.hwnd = None
        self.target_hwnd = None
        self.running = False
        self.is_visible = True
        self.thread = None

    def configure_geometry(self, rel_x, rel_y, rel_w_offset, height):
        self.rel_x = rel_x
        self.rel_y = rel_y
        self.rel_w_offset = rel_w_offset
        self.height = height

    def start(self):
        self.running = True
        if sys.platform == "win32":
            import threading
            self.thread = threading.Thread(target=self._run_win32, daemon=True)
            self.thread.start()

    def set_visible(self, visible: bool):
        self.is_visible = visible
        if sys.platform == "win32" and self.hwnd:
            try:
                import ctypes
                user32 = ctypes.windll.user32
                if user32.IsWindow(self.hwnd):
                    user32.ShowWindow(self.hwnd, 5 if visible else 0)
            except Exception:
                pass

    def stop(self):
        self.running = False

    def _find_target_hwnd(self):
        if sys.platform != "win32":
            return None
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32

        # 1. Direct search by title
        found = user32.FindWindowW(None, self.target_title)
        if found:
            return found

        # 2. Search by Flutter Window Class
        flutter_hwnd = user32.FindWindowW("FLUTTER_RUNNER_WIN32_WINDOW", None)
        if flutter_hwnd:
            return flutter_hwnd

        # 3. Desktop enumeration fallback
        hdesk = user32.OpenInputDesktop(0, False, 0x0100)
        def cb(hwnd, lp):
            nonlocal found
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                if buff.value == self.target_title:
                    found = hwnd
                    return False
            return True
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        if hdesk:
            user32.EnumDesktopWindows(hdesk, WNDENUMPROC(cb), 0)
            user32.CloseDesktop(hdesk)

        return found

    def _run_win32(self):
        import ctypes
        from ctypes import wintypes
        import time

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        shell32 = ctypes.windll.shell32

        # Explicit 64-bit argument and return types
        user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.DefWindowProcW.restype = ctypes.c_ssize_t
        user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
        user32.SetWindowPos.restype = wintypes.BOOL
        user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.ShowWindow.restype = wintypes.BOOL
        user32.SetLayeredWindowAttributes.argtypes = [wintypes.HWND, wintypes.COLORREF, wintypes.BYTE, wintypes.DWORD]
        user32.SetLayeredWindowAttributes.restype = wintypes.BOOL
        user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
        user32.ClientToScreen.restype = wintypes.BOOL
        user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        user32.GetClientRect.restype = wintypes.BOOL
        user32.IsWindow.argtypes = [wintypes.HWND]
        user32.IsWindow.restype = wintypes.BOOL
        user32.IsIconic.argtypes = [wintypes.HWND]
        user32.IsIconic.restype = wintypes.BOOL
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL

        shell32.DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]
        shell32.DragQueryFileW.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
        shell32.DragQueryFileW.restype = wintypes.UINT
        shell32.DragFinish.argtypes = [wintypes.HANDLE]

        WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

        def _wnd_proc(hwnd, msg, wp, lp):
            if msg == 0x0233:  # WM_DROPFILES
                hdrop = wp
                count = shell32.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)
                files = []
                for i in range(count):
                    length = shell32.DragQueryFileW(hdrop, i, None, 0)
                    buff = ctypes.create_unicode_buffer(length + 1)
                    shell32.DragQueryFileW(hdrop, i, buff, length + 1)
                    files.append(buff.value)
                shell32.DragFinish(hdrop)
                if self.on_drop and files:
                    self.on_drop(files)
                return 0
            elif msg == 0x0202:  # WM_LBUTTONUP
                if self.on_click:
                    self.on_click()
                return 0
            elif msg == 0x0002:  # WM_DESTROY
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, msg, wp, lp)

        class WNDCLASSEXW(ctypes.Structure):
            _fields_ = [
                ('cbSize', wintypes.UINT),
                ('style', wintypes.UINT),
                ('lpfnWndProc', WNDPROC),
                ('cbClsExtra', ctypes.c_int),
                ('cbWndExtra', ctypes.c_int),
                ('hInstance', wintypes.HINSTANCE),
                ('hIcon', wintypes.HICON),
                ('hCursor', wintypes.HICON),
                ('hbrBackground', wintypes.HBRUSH),
                ('lpszMenuName', wintypes.LPCWSTR),
                ('lpszClassName', wintypes.LPCWSTR),
                ('hIconSm', wintypes.HICON)
            ]

        self._p_wndproc = WNDPROC(_wnd_proc)
        wclass = WNDCLASSEXW()
        wclass.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wclass.style = 0
        wclass.lpfnWndProc = self._p_wndproc
        wclass.hInstance = kernel32.GetModuleHandleW(None)
        wclass.lpszClassName = "DropItNativeOverlayClass"
        user32.RegisterClassExW(ctypes.byref(wclass))

        while self.running and not self.target_hwnd:
            self.target_hwnd = self._find_target_hwnd()
            if not self.target_hwnd:
                time.sleep(0.05)

        if not self.running or not self.target_hwnd:
            return

        WS_POPUP = 0x80000000
        WS_VISIBLE = 0x10000000
        WS_EX_TOOLWINDOW = 0x00000080
        WS_EX_LAYERED = 0x00080000
        LWA_ALPHA = 0x00000002

        # Create overlay as an owned popup window of target_hwnd
        self.hwnd = user32.CreateWindowExW(
            WS_EX_TOOLWINDOW | WS_EX_LAYERED,
            "DropItNativeOverlayClass",
            "DropTarget",
            WS_POPUP | (WS_VISIBLE if self.is_visible else 0),
            0, 0, 10, 10,
            self.target_hwnd, 0, kernel32.GetModuleHandleW(None), 0
        )
        if not self.hwnd:
            return

        user32.SetLayeredWindowAttributes(self.hwnd, 0, 1, LWA_ALPHA)
        shell32.DragAcceptFiles(self.hwnd, True)

        msg = wintypes.MSG()
        last_pos = None
        HWND_TOP = 0

        while self.running:
            if self.target_hwnd and user32.IsWindow(self.target_hwnd):
                if not self.is_visible or user32.IsIconic(self.target_hwnd) or not user32.IsWindowVisible(self.target_hwnd):
                    user32.ShowWindow(self.hwnd, 0)
                else:
                    pt = wintypes.POINT(0, 0)
                    user32.ClientToScreen(self.target_hwnd, ctypes.byref(pt))
                    client_rect = wintypes.RECT()
                    user32.GetClientRect(self.target_hwnd, ctypes.byref(client_rect))
                    client_w = client_rect.right - client_rect.left

                    x = pt.x + self.rel_x
                    y = pt.y + self.rel_y
                    w = max(client_w + self.rel_w_offset, 50)
                    h = self.height

                    curr_pos = (x, y, w, h)
                    if curr_pos != last_pos:
                        # HWND_TOP keeps the overlay in front of target_hwnd
                        user32.SetWindowPos(self.hwnd, HWND_TOP, x, y, w, h, 0x0040 | 0x0010)
                        last_pos = curr_pos
                    else:
                        user32.ShowWindow(self.hwnd, 5 if self.is_visible else 0)
            else:
                self.target_hwnd = self._find_target_hwnd()

            while user32.PeekMessageW(ctypes.byref(msg), self.hwnd, 0, 0, 1):
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))

            time.sleep(0.02)

        if self.hwnd:
            user32.DestroyWindow(self.hwnd)
