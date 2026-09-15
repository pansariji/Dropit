import os
import flet as ft

import config
from utils import get_resource_path
from ui import HomeView, ReceiveView, SendView

class DropItApp:
    """
    Main Flet Application & Navigation Controller for DropIt.
    Enforces a calibrated desktop terminal window (460x690, exact 2:3 ratio), handles view switching,
    Google Fonts typography, light/dark mode state, and window lifecycle.
    """
    def __init__(self, page: ft.Page):
        self.page = page

        # Configure Flet Window Properties (460x690 Brutalist Desktop Terminal)
        self.page.window.visible = False
        self.page.title = config.APP_TITLE
        self.page.window.width = config.WINDOW_WIDTH
        self.page.window.height = config.WINDOW_HEIGHT
        self.page.window.min_width = config.WINDOW_WIDTH
        self.page.window.min_height = config.WINDOW_HEIGHT
        self.page.window.max_width = config.WINDOW_WIDTH
        self.page.window.max_height = config.WINDOW_HEIGHT
        self.page.window.resizable = False
        self.page.window.alignment = ft.Alignment.CENTER

        # Set Window Icon
        icon_path = get_resource_path(os.path.join("assets", "logo.ico"))
        if os.path.exists(icon_path):
            try:
                self.page.window.icon = icon_path
            except Exception:
                pass

        # Configure Typography (Space Grotesk & JetBrains Mono)
        self.page.fonts = {
            "Space Grotesk": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700;800&display=swap",
            "JetBrains Mono": "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&display=swap",
        }
        self.page.theme = ft.Theme(font_family="Space Grotesk")

        # Theme & Layout Alignment Initialization
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.spacing = 0
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.vertical_alignment = ft.MainAxisAlignment.START

        # Pre-register Flet FilePicker service so it is mounted and immediately available
        self.file_picker = ft.FilePicker()
        self.page.services.append(self.file_picker)

        # Setup Native Drop Overlay for Windows explorer drag & drop across the entire app
        from utils import NativeDropOverlay
        self.native_overlay = NativeDropOverlay(
            target_title=config.APP_TITLE,
            on_drop=self.handle_native_drop,
            on_click=self.handle_overlay_click
        )
        self.native_overlay.start()

        self.current_view_name = "home"
        self.current_view = None

        self.page.on_keyboard_event = self.handle_keyboard_event

        # Check command line arguments for dropped file/folder paths (Windows, macOS, Linux drag onto app icon)
        import sys
        initial_payload = None
        if len(sys.argv) > 1:
            potential_path = sys.argv[1].strip('"').strip("'")
            if os.path.exists(potential_path):
                initial_payload = potential_path

        if initial_payload:
            self.show_send(initial_payload=initial_payload)
        else:
            self.show_home()

        self.page.window.visible = True
        self.page.update()

    def handle_native_drop(self, files):
        if not files or len(files) == 0:
            return
        payload = files[0]
        loop = getattr(self.page, "loop", None)
        if not loop:
            try:
                import asyncio
                loop = asyncio.get_running_loop()
            except Exception:
                loop = None

        def _dispatch():
            if self.current_view_name != "send":
                self.show_send(initial_payload=payload)
            else:
                if hasattr(self.current_view, "stage_path"):
                    self.current_view.stage_path(payload)

        if loop and loop.is_running():
            loop.call_soon_threadsafe(_dispatch)
        else:
            _dispatch()

    def handle_overlay_click(self):
        if self.current_view_name == "send" and hasattr(self.current_view, "pick_file"):
            if not getattr(self.current_view, "selected_path", None):
                loop = getattr(self.page, "loop", None)
                if not loop:
                    try:
                        import asyncio
                        loop = asyncio.get_running_loop()
                    except Exception:
                        loop = None
                if loop and loop.is_running():
                    import asyncio
                    asyncio.run_coroutine_threadsafe(self.current_view.pick_file(), loop)

    def handle_keyboard_event(self, e: ft.KeyboardEvent):
        # Support Ctrl+V on Windows/Linux and Cmd+V on macOS
        if (e.ctrl or e.meta) and e.key.lower() == "v":
            if self.current_view_name == "send" and hasattr(self.current_view, "paste_from_clipboard"):
                self.current_view.paste_from_clipboard()
            elif self.current_view_name == "home":
                self.show_send()
                if hasattr(self.current_view, "paste_from_clipboard"):
                    self.current_view.paste_from_clipboard()

    def show_home(self):
        """Displays the Neo-Brutalist Home Welcome View."""
        if self.current_view and hasattr(self.current_view, "dispose"):
            self.current_view.dispose()
        self.current_view_name = "home"
        if hasattr(self, "native_overlay") and self.native_overlay:
            self.native_overlay.configure_geometry(rel_x=16, rel_y=60, rel_w_offset=-32, height=230)
            self.native_overlay.set_visible(True)
        self.current_view = HomeView(
            page=self.page,
            on_nav_receive=self.show_receive,
            on_nav_send=self.show_send,
            on_toggle_theme=self.toggle_theme
        )
        self.page.bgcolor = self.current_view.tokens["bg"]
        self.page.controls.clear()
        self.page.add(self.current_view)
        self.page.update()

    def show_receive(self):
        """Displays the Neo-Brutalist Receive View."""
        if self.current_view and hasattr(self.current_view, "dispose"):
            self.current_view.dispose()
        self.current_view_name = "receive"
        if hasattr(self, "native_overlay") and self.native_overlay:
            self.native_overlay.set_visible(False)
        self.current_view = ReceiveView(
            page=self.page,
            on_back=self.show_home
        )
        self.page.bgcolor = self.current_view.tokens["bg"]
        self.page.controls.clear()
        self.page.add(self.current_view)
        self.page.update()

    def show_send(self, initial_payload: str = None):
        """Displays the Neo-Brutalist Send View."""
        if self.current_view and hasattr(self.current_view, "dispose"):
            self.current_view.dispose()
        self.current_view_name = "send"
        if hasattr(self, "native_overlay") and self.native_overlay:
            self.native_overlay.configure_geometry(rel_x=16, rel_y=96, rel_w_offset=-32, height=85)
            self.native_overlay.set_visible(True if not initial_payload else False)
        self.current_view = SendView(
            page=self.page,
            on_back=self.show_home,
            initial_path=initial_payload,
            native_overlay=getattr(self, "native_overlay", None)
        )
        self.page.bgcolor = self.current_view.tokens["bg"]
        self.page.controls.clear()
        self.page.add(self.current_view)
        self.page.update()

    def toggle_theme(self):
        """Toggles between Light Mode (Brutalist Paper) and Dark Mode (Obsidian)."""
        if self.page.theme_mode == ft.ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.DARK
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT

        # Re-render current view with new theme tokens
        if self.current_view_name == "home":
            self.show_home()
        elif self.current_view_name == "receive":
            self.show_receive()
        elif self.current_view_name == "send":
            self.show_send()

def main(page: ft.Page):
    DropItApp(page)

if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP_HIDDEN)
