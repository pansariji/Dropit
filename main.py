import os
import flet as ft

import config
from utils import get_resource_path
from ui import HomeView, ReceiveView, SendView

class DropItApp:
    """
    Main Flet Application & Navigation Controller for DropIt.
    Enforces a fixed 2:3 aspect ratio window (440x660), handles view switching,
    light/dark mode state, and window lifecycle.
    """
    def __init__(self, page: ft.Page):
        self.page = page

        # Configure Flet Window Properties (2:3 Aspect Ratio)
        self.page.title = config.APP_TITLE
        self.page.window.width = config.WINDOW_WIDTH
        self.page.window.height = config.WINDOW_HEIGHT
        self.page.window.min_width = config.WINDOW_WIDTH
        self.page.window.min_height = config.WINDOW_HEIGHT
        self.page.window.max_width = config.WINDOW_WIDTH
        self.page.window.resizable = False
        self.page.window.alignment = ft.Alignment.CENTER

        # Set Window Icon
        icon_path = get_resource_path(os.path.join("assets", "logo.ico"))
        if os.path.exists(icon_path):
            try:
                self.page.window.icon = icon_path
            except Exception:
                pass

        # Theme & Layout Alignment Initialization
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        self.page.spacing = 0
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER

        self.current_view_name = "home"
        self.current_view = None

        self.show_home()

    def show_home(self):
        """Displays the Minimalistic Home Welcome View."""
        self.current_view_name = "home"
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
        """Displays the Receive View."""
        self.current_view_name = "receive"
        self.current_view = ReceiveView(
            page=self.page,
            on_back=self.show_home
        )
        self.page.bgcolor = self.current_view.tokens["bg"]
        self.page.controls.clear()
        self.page.add(self.current_view)
        self.page.update()

    def show_send(self):
        """Displays the Send View."""
        self.current_view_name = "send"
        self.current_view = SendView(
            page=self.page,
            on_back=self.show_home
        )
        self.page.bgcolor = self.current_view.tokens["bg"]
        self.page.controls.clear()
        self.page.add(self.current_view)
        self.page.update()

    def toggle_theme(self):
        """Toggles between Light Mode (Cream/Black) and Dark Mode (Obsidian/Cream)."""
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
    ft.run(main)
