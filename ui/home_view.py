import os
import flet as ft
import config
from utils import get_resource_path, make_tactile

class HomeView(ft.Container):
    """
    DropIt Neo-Brutalist Home View.
    Faithfully implements the Stitch 'DropIt Flet Desktop - Home' specification:
    - 40px Brutalist Title Bar with [ ONLINE // P2P ] Status Pill
    - Theme Switcher & Window Controls
    - Massive DROPIT Display Typography & Motto Badge
    - Punchy Heavy-Bordered CTAs with Offset Shadows ('SEND PAYLOAD' & 'RECEIVE PAYLOAD')
    - Industrial Telemetry Footer
    """
    def __init__(self, page: ft.Page, on_nav_receive, on_nav_send, on_toggle_theme):
        super().__init__(expand=True)
        self.page_ref = page
        self.on_nav_receive = on_nav_receive
        self.on_nav_send = on_nav_send
        self.on_toggle_theme = on_toggle_theme

        self.is_dark = page.theme_mode == ft.ThemeMode.DARK
        self.tokens = config.THEME_DARK if self.is_dark else config.THEME_LIGHT

        self.logo_path = get_resource_path(os.path.join("assets", "logo.png"))
        self.build_ui()

    def build_ui(self):
        tokens = self.tokens

        # ---------------------------------------------------------
        # 1. Brutalist Window Titlebar (40px)
        # ---------------------------------------------------------
        title_icon = ft.Image(
            src=self.logo_path,
            width=26,
            height=26,
            fit=ft.BoxFit.CONTAIN
        ) if os.path.exists(self.logo_path) else ft.Text(
            "D",
            size=14,
            weight=ft.FontWeight.W_900,
            font_family=config.FONT_DISPLAY,
            color=tokens["yellow"]
        )

        title_text = ft.Text(
            "DROPIT",
            size=14,
            weight=ft.FontWeight.W_900,
            font_family=config.FONT_DISPLAY,
            color=tokens["text"],
            style=ft.TextStyle(letter_spacing=1.0)
        )

        status_pill = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=7,
                        height=7,
                        border_radius=4,
                        bgcolor=tokens["green"],
                        border=ft.Border.all(1, tokens["status_border"])
                    ),
                    ft.Text(
                        "[ ONLINE // P2P ]",
                        size=9,
                        weight=ft.FontWeight.BOLD,
                        font_family=config.FONT_MONO,
                        color=tokens["status_fg"]
                    )
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=tokens["status_bg"],
            border=ft.Border.all(1.5, tokens["status_border"]),
            padding=ft.Padding(left=6, top=2, right=6, bottom=2),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["status_border"] if self.is_dark else "#000000", offset=ft.Offset(2, 2))
        )

        theme_icon = ft.Icons.LIGHT_MODE_OUTLINED if self.is_dark else ft.Icons.DARK_MODE_OUTLINED
        theme_btn = make_tactile(
            ft.Container(
                content=ft.Icon(theme_icon, size=16, color=tokens["text"]),
                width=28,
                height=28,
                bgcolor=tokens["card"],
                border=ft.Border.all(2, tokens["border"]),
                alignment=ft.Alignment.CENTER,
                tooltip="Toggle Light/Dark Theme",
            ),
            on_click_handler=lambda e: self.on_toggle_theme(),
            idle_shadow_x=2,
            idle_shadow_y=2,
            shadow_color=tokens["shadow"]
        )

        titlebar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[title_icon, title_text, status_pill],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    theme_btn
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=tokens["card_alt"],
            border=ft.Border(bottom=ft.BorderSide(2.5, tokens["border"])),
            padding=ft.Padding(left=14, top=6, right=14, bottom=6),
            height=44
        )

        # ---------------------------------------------------------
        # 2. Hero Section (Logo, Giant Display Title, Motto, Subtitle)
        # ---------------------------------------------------------
        if os.path.exists(self.logo_path):
            logo_widget = ft.Image(
                src=self.logo_path,
                width=160,
                height=160,
                fit=ft.BoxFit.CONTAIN
            )
        else:
            logo_widget = ft.Container(
                content=ft.Icon(ft.Icons.ELECTRIC_BOLT_ROUNDED, size=68, color="#000000"),
                width=140,
                height=140,
                bgcolor=tokens["yellow"],
                border=ft.Border.all(3, tokens["border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(3, 3)),
                alignment=ft.Alignment.CENTER
            )

        hero_title = ft.Text(
            "DROPIT",
            size=38,
            weight=ft.FontWeight.W_900,
            font_family=config.FONT_DISPLAY,
            color=tokens["text"],
            text_align=ft.TextAlign.CENTER,
            style=ft.TextStyle(letter_spacing=-1.0)
        )

        motto_border_col = tokens["green"] if self.is_dark else tokens["border"]
        motto_shadow_col = tokens["green"] if self.is_dark else tokens["shadow"]
        motto_text_col = tokens["green"] if self.is_dark else tokens["text"]
        motto_bg_col = tokens["card"] if self.is_dark else tokens["green_light"]

        motto_badge = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=8,
                        height=8,
                        border_radius=4,
                        bgcolor=tokens["green"],
                        border=ft.Border.all(1, motto_border_col)
                    ),
                    ft.Text(
                        config.APP_MOTTO,
                        size=10,
                        weight=ft.FontWeight.BOLD,
                        font_family=config.FONT_MONO,
                        color=motto_text_col,
                        style=ft.TextStyle(letter_spacing=1.0)
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            ),
            bgcolor=motto_bg_col,
            border=ft.Border.all(1.5 if self.is_dark else 2, motto_border_col),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=motto_shadow_col, offset=ft.Offset(2, 2)),
            padding=ft.Padding(left=12, top=4, right=12, bottom=4)
        )

        subtitle_text = ft.Text(
            "Ultra-fast local peer-to-peer file sharing.\nNo internet required.",
            size=13,
            weight=ft.FontWeight.W_500,
            font_family=config.FONT_DISPLAY,
            color=tokens["muted"],
            text_align=ft.TextAlign.CENTER
        )

        hero_section = ft.Column(
            controls=[
                logo_widget,
                ft.Container(height=4),
                hero_title,
                ft.Container(height=2),
                motto_badge,
                ft.Container(height=8),
                subtitle_text
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4
        )

        # ---------------------------------------------------------
        # 3. Massive Tactile Action Buttons
        # ---------------------------------------------------------
        # SEND PAYLOAD CTA - Electric Hazard Yellow with Black border and Cyan 3D shadow
        send_btn = make_tactile(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.BOLT_ROUNDED, size=24, color="#000000"),
                                ft.Text(
                                    "SEND PAYLOAD",
                                    size=15,
                                    weight=ft.FontWeight.W_900,
                                    font_family=config.FONT_DISPLAY,
                                    color="#000000",
                                    style=ft.TextStyle(letter_spacing=0.5)
                                )
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        ft.Container(
                            content=ft.Text(
                                "TX // OUT",
                                size=9,
                                weight=ft.FontWeight.BOLD,
                                font_family=config.FONT_MONO,
                                color="#FFFFFF"
                            ),
                            bgcolor="#000000",
                            padding=ft.Padding(left=6, top=3, right=6, bottom=3),
                            border=ft.Border.all(1, tokens["yellow"] if self.is_dark else "#000000")
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                bgcolor=tokens["btn_primary_bg"],
                border=ft.Border.all(3, tokens["btn_primary_border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["btn_primary_shadow"], offset=ft.Offset(4, 4)),
                padding=ft.Padding(left=16, top=10, right=16, bottom=10),
                height=58,
            ),
            on_click_handler=lambda e: self.on_nav_send(),
            idle_shadow_x=4,
            idle_shadow_y=4,
            shadow_color=tokens["btn_primary_shadow"]
        )

        # RECEIVE PAYLOAD CTA - Pure White with Black border and Neo Mint 3D shadow
        receive_btn = make_tactile(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.MOVE_TO_INBOX_ROUNDED, size=22, color=tokens["blue"]),
                                ft.Text(
                                    "RECEIVE PAYLOAD",
                                    size=15,
                                    weight=ft.FontWeight.W_900,
                                    font_family=config.FONT_DISPLAY,
                                    color=tokens["btn_secondary_fg"],
                                    style=ft.TextStyle(letter_spacing=0.5)
                                )
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        ft.Container(
                            content=ft.Text(
                                "RX // IN",
                                size=9,
                                weight=ft.FontWeight.BOLD,
                                font_family=config.FONT_MONO,
                                color="#FFFFFF"
                            ),
                            bgcolor="#000000",
                            padding=ft.Padding(left=6, top=3, right=6, bottom=3),
                            border=ft.Border.all(1.5, "#000000")
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                bgcolor=tokens["btn_secondary_bg"],
                border=ft.Border.all(3, tokens["btn_secondary_border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["btn_secondary_shadow"], offset=ft.Offset(4, 4)),
                padding=ft.Padding(left=16, top=10, right=16, bottom=10),
                height=58,
            ),
            on_click_handler=lambda e: self.on_nav_receive(),
            idle_shadow_x=4,
            idle_shadow_y=4,
            shadow_color=tokens["btn_secondary_shadow"]
        )

        buttons_container = ft.Column(
            controls=[send_btn, receive_btn],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH
        )

        # ---------------------------------------------------------
        # 4. Footer Specification Box
        # ---------------------------------------------------------
        footer_badge = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(f"v{config.APP_VERSION}", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"]),
                    ft.Text("•", size=9, color=tokens["muted"]),
                    ft.Text("DROPIT", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"]),
                    ft.Text("•", size=9, color=tokens["muted"]),
                    ft.Container(
                        content=ft.Text("ZERO-CLOUD P2P", size=8, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color="#000000"),
                        bgcolor=tokens["yellow"],
                        padding=ft.Padding(left=4, top=1, right=4, bottom=1),
                        border=ft.Border.all(1, tokens["border"])
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            ),
            bgcolor=tokens["card"],
            border=ft.Border.all(2, tokens["border"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(2, 2)),
            padding=ft.Padding(left=10, top=5, right=10, bottom=5)
        )

        # Main Layout Assembly
        self.bgcolor = tokens["bg"]
        self.padding = 0
        self.content = ft.Column(
            controls=[
                titlebar,
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(content=hero_section, expand=True, alignment=ft.Alignment.CENTER),
                            buttons_container,
                            ft.Container(height=10),
                            ft.Container(content=footer_badge, alignment=ft.Alignment.CENTER),
                            ft.Container(height=4)
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True
                    ),
                    padding=ft.Padding(left=20, top=12, right=20, bottom=12),
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        )

    def dispose(self):
        pass
