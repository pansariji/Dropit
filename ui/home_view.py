import flet as ft
import config
from utils import get_resource_path

class HomeView(ft.Container):
    """
    Minimalistic Welcome View for DropIt.
    Displays app branding, icon asset, 3-keyword motto, Send/Receive action buttons,
    and dark mode toggle.
    """
    def __init__(self, page: ft.Page, on_nav_receive, on_nav_send, on_toggle_theme):
        super().__init__(expand=True)
        self.page_ref = page
        self.on_nav_receive = on_nav_receive
        self.on_nav_send = on_nav_send
        self.on_toggle_theme = on_toggle_theme

        # Determine theme tokens
        self.is_dark = page.theme_mode == ft.ThemeMode.DARK
        self.tokens = config.THEME_DARK if self.is_dark else config.THEME_LIGHT

        self.logo_path = get_resource_path("assets/logo.png")

        self.build_ui()

    def build_ui(self):
        tokens = self.tokens

        # Header Row with App Status & Dark/Light Theme Toggle
        theme_icon = ft.Icons.LIGHT_MODE_OUTLINED if self.is_dark else ft.Icons.DARK_MODE_OUTLINED
        theme_tooltip = "Switch to Light Mode" if self.is_dark else "Switch to Dark Mode"

        theme_btn = ft.IconButton(
            icon=theme_icon,
            icon_size=22,
            icon_color=tokens["text"],
            tooltip=theme_tooltip,
            on_click=lambda e: self.on_toggle_theme()
        )

        header_row = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(
                            width=8,
                            height=8,
                            border_radius=4,
                            bgcolor=tokens["green"]
                        ),
                        ft.Text(
                            "Local Network Ready",
                            size=12,
                            weight=ft.FontWeight.W_500,
                            color=tokens["muted"]
                        )
                    ],
                    spacing=6
                ),
                theme_btn
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # Branding Header: Logo Image & App Title
        logo_image = ft.Image(
            src=self.logo_path,
            width=110,
            height=110,
            fit=ft.BoxFit.CONTAIN
        )

        app_title = ft.Text(
            config.APP_TITLE,
            size=34,
            weight=ft.FontWeight.BOLD,
            color=tokens["text"],
            text_align=ft.TextAlign.CENTER
        )

        # 3-Keyword Motto Badge Container
        motto_badge = ft.Container(
            content=ft.Text(
                config.APP_MOTTO,
                size=11,
                weight=ft.FontWeight.W_700,
                color=tokens["green"],
                style=ft.TextStyle(letter_spacing=1.2),
                text_align=ft.TextAlign.CENTER
            ),
            bgcolor=ft.Colors.with_opacity(0.12, tokens["green"]),
            border_radius=20,
            padding=ft.Padding(left=16, top=6, right=16, bottom=6),
            alignment=ft.Alignment.CENTER
        )

        sub_description = ft.Text(
            "Ultra-fast local peer-to-peer file sharing.\nNo internet required.",
            size=13,
            color=tokens["muted"],
            text_align=ft.TextAlign.CENTER
        )

        branding_card = ft.Container(
            content=ft.Column(
                controls=[
                    logo_image,
                    ft.Container(height=6),
                    app_title,
                    ft.Container(height=4),
                    motto_badge,
                    ft.Container(height=8),
                    sub_description
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4
            ),
            padding=ft.Padding(left=16, top=20, right=16, bottom=20),
            alignment=ft.Alignment.CENTER
        )

        # Action Buttons Container (Receive & Send)
        receive_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FILE_DOWNLOAD_ROUNDED, size=20, color=tokens["btn_secondary_fg"]),
                    ft.Text("Receive", size=16, weight=ft.FontWeight.W_600, color=tokens["btn_secondary_fg"])
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8
            ),
            style=ft.ButtonStyle(
                color=tokens["btn_secondary_fg"],
                bgcolor=tokens["card"],
                side=ft.BorderSide(1, tokens["border"]),
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.Padding(left=0, top=18, right=0, bottom=18)
            ),
            on_click=lambda e: self.on_nav_receive(),
            expand=True
        )

        send_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SEND_ROUNDED, size=20, color=tokens["btn_primary_fg"]),
                    ft.Text("Send", size=16, weight=ft.FontWeight.W_600, color=tokens["btn_primary_fg"])
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8
            ),
            style=ft.ButtonStyle(
                color=tokens["btn_primary_fg"],
                bgcolor=tokens["btn_primary_bg"],
                shape=ft.RoundedRectangleBorder(radius=12),
                padding=ft.Padding(left=0, top=18, right=0, bottom=18)
            ),
            on_click=lambda e: self.on_nav_send(),
            expand=True
        )

        buttons_column = ft.Column(
            controls=[
                send_button,
                receive_button
            ],
            spacing=12,
            alignment=ft.MainAxisAlignment.CENTER
        )

        # Footer Version Label
        footer_text = ft.Text(
            f"v{config.APP_VERSION} • DropIt Flet",
            size=11,
            color=tokens["muted"],
            text_align=ft.TextAlign.CENTER
        )

        # Main View Layout Container
        self.bgcolor = tokens["bg"]
        self.padding = ft.Padding(left=20, top=16, right=20, bottom=16)
        self.content = ft.Column(
            controls=[
                header_row,
                ft.Container(
                    content=branding_card,
                    expand=True,
                    alignment=ft.Alignment.CENTER
                ),
                buttons_column,
                ft.Container(height=10),
                footer_text
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
