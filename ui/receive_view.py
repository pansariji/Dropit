import flet as ft
import os
import time
import asyncio
import config
from utils import get_local_ip, generate_passcode, generate_qr_image, pil_to_b64, open_file_location, make_tactile, get_resource_path
from p2p.server import Receiver
from web.server import WebReceiver
from ui.transfer_view import TransferView

class ReceiveView(ft.Container):
    """
    DropIt Neo-Brutalist Receive View.
    Implements the Stitch 'DropIt Flet Desktop - Receive' specification:
    - 44px Titlebar with [ ONLINE // P2P ] Status
    - Header with RX-01 Tag and Back Navigation
    - Segmented Mode Switcher: Mobile (QR) vs PC (Passcode)
    - PC Mode: 4 Distinct High-Contrast Passcode Digit Boxes & Regenerate PIN
    - Host IP Interface Banner with Tactile 'COPY IP' Action (with 'COPIED!' feedback)
    - Diagnostic Card with Pulsing Telemetry Waveform & Socket Listener Details
    - Mobile Mode: High-Contrast QR Code Display with Direct Local URL
    - Seamless Transition to Unified TransferView
    """
    def __init__(self, page: ft.Page, on_back):
        super().__init__(expand=True)
        self.page_ref = page
        self.on_back = on_back

        self.logo_path = get_resource_path(os.path.join("assets", "logo.png"))
        self.is_dark = page.theme_mode == ft.ThemeMode.DARK
        self.tokens = config.THEME_DARK if self.is_dark else config.THEME_LIGHT

        # State Variables
        self.active_mode = "pc"  # Default to PC for instant 4-box PIN layout
        self.passcode = generate_passcode()
        self.local_ip = get_local_ip()

        # Engine instances
        self.p2p_receiver = None
        self.web_receiver = None
        self.active_transfer_view = None

        # Metrics state
        self.transfer_state = "idle"  # "idle", "transferring", "completed", "error"
        self.received_filepath = None
        self.status_text_val = "Waiting for incoming socket handshake..."
        self.progress_percent = 0.0
        self.cur_speed_val = "--"
        self.avg_speed_val = "--"
        self.peak_speed_val = "--"
        self.size_info_val = "--"
        self.eta_val = "--"
        # Item metadata tracking
        self._current_item_name = None
        self._current_size_str = "--"
        self._current_is_folder = False

        # Rate-limiting and asyncio loop
        self._last_ui_update = 0.0
        self.main_loop = getattr(page, "loop", None)
        if not self.main_loop:
            try:
                self.main_loop = asyncio.get_running_loop()
            except Exception:
                self.main_loop = None

        self.build_ui()
        self.start_mode_server()

    def build_ui(self):
        tokens = self.tokens

        # ---------------------------------------------------------
        # 1. Brutalist Titlebar (44px)
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

        title_text = ft.Text("DROPIT", size=14, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"])

        status_pill = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(width=7, height=7, border_radius=4, bgcolor=tokens["green"], border=ft.Border.all(1, tokens["border"])),
                    ft.Text("[ ONLINE // P2P ]", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"])
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=tokens["green_light"],
            border=ft.Border.all(1.5, tokens["border"]),
            padding=ft.Padding(left=6, top=2, right=6, bottom=2),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(2, 2))
        )

        titlebar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(controls=[title_icon, title_text, status_pill], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=tokens["card_alt"],
            border=ft.Border(bottom=ft.BorderSide(2.5, tokens["border"])),
            padding=ft.Padding(left=14, top=6, right=14, bottom=6),
            height=44
        )

        # ---------------------------------------------------------
        # 2. View Header (Back Button, Title, Mode Badge)
        # ---------------------------------------------------------
        back_btn = make_tactile(
            ft.Container(
                content=ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, size=18, color=tokens["text"]),
                width=36,
                height=36,
                bgcolor=tokens["card"],
                border=ft.Border.all(2, tokens["border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(2, 2)),
                alignment=ft.Alignment.CENTER,
                tooltip="Back to Home",
            ),
            on_click_handler=self.handle_back,
            idle_shadow_x=2,
            idle_shadow_y=2,
            shadow_color=tokens["shadow"]
        )

        view_title = ft.Text("RECEIVE PAYLOAD", size=20, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"])

        rx_badge = ft.Container(
            content=ft.Text("RX-01", size=10, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"]),
            bgcolor=tokens["card"],
            border=ft.Border.all(1.5, tokens["border"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(2, 2)),
            padding=ft.Padding(left=8, top=3, right=8, bottom=3)
        )

        header_row = ft.Row(
            controls=[
                ft.Row(controls=[back_btn, view_title], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                rx_badge
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------
        # 3. Segmented Mode Switcher (PC Passcode vs Mobile QR)
        # ---------------------------------------------------------
        self.tab_pc = make_tactile(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.COMPUTER_ROUNDED, size=15),
                        ft.Text("PC (PASSCODE)", size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5
                ),
                padding=ft.Padding(left=8, top=6, right=8, bottom=6),
                expand=True,
            ),
            on_click_handler=lambda e: self.switch_mode("pc"),
            idle_shadow_x=2,
            idle_shadow_y=2
        )

        self.tab_mobile = make_tactile(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.PHONE_ANDROID_ROUNDED, size=15),
                        ft.Text("MOBILE (QR)", size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5
                ),
                padding=ft.Padding(left=8, top=6, right=8, bottom=6),
                expand=True,
            ),
            on_click_handler=lambda e: self.switch_mode("mobile"),
            idle_shadow_x=2,
            idle_shadow_y=2
        )

        self.mode_switcher = ft.Container(
            content=ft.Row(controls=[self.tab_pc, self.tab_mobile], spacing=4),
            bgcolor=tokens["card"],
            border=ft.Border.all(2, tokens["border"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(2, 2)),
            padding=2
        )

        # ---------------------------------------------------------
        # 4. Dynamic Info & Parameters Container
        # ---------------------------------------------------------
        self.content_area = ft.Container(expand=True)
        self.update_mode_tabs_ui()
        self.update_content_area_ui()

        # ---------------------------------------------------------
        # 5. Diagnostic Protocol Footer
        # ---------------------------------------------------------
        protocol_meta_bar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(width=6, height=6, bgcolor=tokens["yellow"]),
                            ft.Text("CRC32 INTEGRITY CHECK", size=8, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"])
                        ],
                        spacing=4
                    ),
                    ft.Text("•", size=9, color=tokens["muted"]),
                    ft.Text("DIRECT SOCKET STREAM", size=8, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["green"])
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor=tokens["card"],
            border=ft.Border.all(2, tokens["border"]),
            padding=ft.Padding(left=10, top=4, right=10, bottom=4)
        )

        footer_meta = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("BUF:256KB", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["muted"]),
                    ft.Row(
                        controls=[
                            ft.Container(width=6, height=6, border_radius=3, bgcolor=tokens["green"]),
                            ft.Text("READY FOR STAGING", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"])
                        ],
                        spacing=4
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            bgcolor=tokens["card_alt"],
            border=ft.Border(top=ft.BorderSide(2, tokens["border"])),
            padding=ft.Padding(left=14, top=6, right=14, bottom=6),
            height=32
        )

        # Assembly
        self.bgcolor = tokens["bg"]
        self.padding = 0
        self.content = ft.Column(
            controls=[
                titlebar,
                ft.Container(
                    content=ft.Column(
                        controls=[
                            header_row,
                            self.mode_switcher,
                            self.content_area,
                            protocol_meta_bar
                        ],
                        spacing=8,
                        expand=True
                    ),
                    padding=ft.Padding(left=16, top=8, right=16, bottom=8),
                    expand=True
                ),
                footer_meta
            ],
            spacing=0,
            expand=True
        )

    # -------------------------------------------------------------
    # UI Renderers for PC and Mobile Modes
    # -------------------------------------------------------------
    def update_mode_tabs_ui(self):
        tokens = self.tokens
        active_border = "#000000"
        active_shadow_col = tokens.get("btn_primary_shadow", "#000000")

        if self.active_mode == "pc":
            self.tab_pc.bgcolor = tokens["yellow"]
            self.tab_pc.content.controls[0].color = "#000000"
            self.tab_pc.content.controls[1].color = "#000000"
            self.tab_pc.border = ft.Border.all(2, active_border)
            self.tab_pc.shadow = ft.BoxShadow(spread_radius=0, blur_radius=0, color=active_shadow_col, offset=ft.Offset(2, 2))

            self.tab_mobile.bgcolor = tokens["card"]
            self.tab_mobile.content.controls[0].color = tokens["muted"]
            self.tab_mobile.content.controls[1].color = tokens["muted"]
            self.tab_mobile.border = ft.Border.all(1.5, tokens["border"])
            self.tab_mobile.shadow = None
        else:
            self.tab_mobile.bgcolor = tokens["yellow"]
            self.tab_mobile.content.controls[0].color = "#000000"
            self.tab_mobile.content.controls[1].color = "#000000"
            self.tab_mobile.border = ft.Border.all(2, active_border)
            self.tab_mobile.shadow = ft.BoxShadow(spread_radius=0, blur_radius=0, color=active_shadow_col, offset=ft.Offset(2, 2))

            self.tab_pc.bgcolor = tokens["card"]
            self.tab_pc.content.controls[0].color = tokens["muted"]
            self.tab_pc.content.controls[1].color = tokens["muted"]
            self.tab_pc.border = ft.Border.all(1.5, tokens["border"])
            self.tab_pc.shadow = None

        try:
            self.tab_pc.update()
        except Exception:
            pass
        try:
            self.tab_mobile.update()
        except Exception:
            pass

    def update_content_area_ui(self):
        tokens = self.tokens

        if self.active_mode == "pc":
            # 4 Distinct Passcode Digit Boxes
            digit_boxes = []
            for d in str(self.passcode):
                digit_boxes.append(
                    ft.Container(
                        content=ft.Text(d, size=24, weight=ft.FontWeight.W_900, font_family=config.FONT_MONO, color=tokens["pin_fg"]),
                        width=52,
                        height=54,
                        bgcolor=tokens["pin_bg"],
                        border=ft.Border.all(2.5, tokens["pin_border"]),
                        shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["pin_shadow"], offset=ft.Offset(3, 3)),
                        alignment=ft.Alignment.CENTER
                    )
                )

            passcode_row = ft.Row(controls=digit_boxes, alignment=ft.MainAxisAlignment.CENTER, spacing=10)

            regenerate_btn = make_tactile(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.REFRESH_ROUNDED, size=14, color=tokens["muted"]),
                            ft.Text("REGENERATE SECURITY PIN", size=10, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["muted"])
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=4
                    ),
                    padding=ft.Padding(left=8, top=4, right=8, bottom=4),
                ),
                on_click_handler=self.regenerate_pin,
                idle_shadow_x=0,
                idle_shadow_y=0
            )

            pin_card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(width=6, height=6, bgcolor=tokens["yellow"]),
                                ft.Text("RECEIVER PASSCODE", size=10, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"])
                            ],
                            spacing=6
                        ),
                        ft.Container(height=2),
                        passcode_row,
                        ft.Container(height=2),
                        regenerate_btn
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=3
                ),
                bgcolor=tokens["card"],
                border=ft.Border.all(2.5, tokens["border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(4, 4)),
                padding=10
            )

            # Interface IP Readout Banner with Copy Action
            self.copy_ip_btn_text = ft.Text("COPY IP", size=10, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color="#000000")
            self.copy_ip_btn = make_tactile(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CONTENT_COPY_ROUNDED, size=14, color="#000000"),
                            self.copy_ip_btn_text
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=4
                    ),
                    bgcolor=tokens["yellow"],
                    border=ft.Border.all(2, "#000000"),
                    shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens.get("btn_primary_shadow", "#000000"), offset=ft.Offset(2, 2)),
                    padding=ft.Padding(left=10, top=5, right=10, bottom=5),
                ),
                on_click_handler=self.copy_ip_address,
                idle_shadow_x=2,
                idle_shadow_y=2,
                shadow_color=tokens.get("btn_primary_shadow", "#000000")
            )

            ip_banner = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(ft.Icons.ROUTER_ROUNDED, size=18, color=tokens["text"]),
                                    width=32,
                                    height=32,
                                    bgcolor=tokens["card_alt"],
                                    border=ft.Border.all(1.5, tokens["border"]),
                                    alignment=ft.Alignment.CENTER
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("INTERFACE // WLAN0", size=8, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["muted"]),
                                        ft.Text(self.local_ip, size=13, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"])
                                    ],
                                    spacing=1
                                )
                            ],
                            spacing=8
                        ),
                        self.copy_ip_btn
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                bgcolor=tokens["card"],
                border=ft.Border.all(2, tokens["border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(2, 2)),
                padding=ft.Padding(left=10, top=6, right=10, bottom=6)
            )

            # Diagnostic Waiting Card with Pulse Waveform
            tcp_port_str = str(self.p2p_receiver.tcp_port if (self.p2p_receiver and self.p2p_receiver.tcp_port) else config.DEFAULT_P2P_PORT)
            diag_card = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Container(width=8, height=8, border_radius=4, bgcolor=tokens["green"], border=ft.Border.all(1, tokens["border"])),
                                        ft.Text("READY TO RECEIVE PAYLOADS...", size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"])
                                    ],
                                    spacing=6
                                ),
                                ft.Container(
                                    content=ft.Text(f"PORT :{tcp_port_str}", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"]),
                                    bgcolor=tokens["card_alt"],
                                    border=ft.Border.all(1, tokens["border"]),
                                    padding=ft.Padding(left=6, top=2, right=6, bottom=2)
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Container(
                            content=ft.Text(self.status_text_val, size=10, font_family=config.FONT_MONO, color=tokens["muted"]),
                            padding=ft.Padding(left=8, top=3, right=8, bottom=3),
                            border=ft.Border(left=ft.BorderSide(2, tokens["border"]))
                        ),
                        # Visual graphic telemetry wave
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Text("RX_STBY", size=8, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["muted"]),
                                    ft.Row(
                                        controls=[
                                            ft.Container(width=3, height=8, bgcolor=tokens["green"]),
                                            ft.Container(width=3, height=4, bgcolor=tokens["border"]),
                                            ft.Container(width=3, height=12, bgcolor=tokens["green"]),
                                            ft.Container(width=3, height=6, bgcolor=tokens["border"]),
                                            ft.Container(width=3, height=9, bgcolor=tokens["green"]),
                                            ft.Container(width=3, height=5, bgcolor=tokens["border"]),
                                            ft.Container(width=3, height=11, bgcolor=tokens["green"]),
                                            ft.Container(width=3, height=4, bgcolor=tokens["border"]),
                                            ft.Container(width=3, height=14, bgcolor=tokens["green"]),
                                            ft.Container(width=3, height=6, bgcolor=tokens["border"]),
                                        ],
                                        spacing=2
                                    ),
                                    ft.Text("0.0 KB/s", size=8, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["green"])
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            bgcolor=tokens["card_alt"],
                            border=ft.Border.all(1, tokens["border"]),
                            padding=ft.Padding(left=8, top=4, right=8, bottom=4)
                        )
                    ],
                    spacing=8
                ),
                bgcolor=tokens["card"],
                border=ft.Border.all(2, tokens["border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(2, 2)),
                padding=10
            )

            self.content_area.content = ft.Column(
                controls=[
                    pin_card,
                    ip_banner,
                    diag_card
                ],
                spacing=8
            )

        else:
            # Mobile (QR) Mode
            url = f"http://{self.local_ip}:{config.DEFAULT_WEB_PORT}"
            if self.web_receiver and hasattr(self.web_receiver, 'url'):
                url = self.web_receiver.url

            qr_img = generate_qr_image(url, fg_color="#000000", bg_color="#FFFFFF")
            qr_b64 = pil_to_b64(qr_img)
            qr_widget = ft.Image(src=f"data:image/png;base64,{qr_b64}", width=190, height=190, fit=ft.BoxFit.CONTAIN) if qr_b64 else ft.Container()

            qr_box = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(width=6, height=6, bgcolor=tokens["yellow"]),
                                ft.Text("SCAN QR WITH MOBILE PHONE", size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"])
                            ],
                            spacing=6
                        ),
                        ft.Container(height=4),
                        ft.Container(
                            content=qr_widget,
                            bgcolor="#FFFFFF",
                            border=ft.Border.all(2.5, "#000000"),
                            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens.get("qr_shadow", "#000000"), offset=ft.Offset(3, 3)),
                            padding=8,
                            alignment=ft.Alignment.CENTER
                        ),
                        ft.Container(height=6),
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Text(url, size=11, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color="#000000"),
                                    make_tactile(
                                        ft.Container(
                                            content=ft.Text("COPY", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color="#FFFFFF"),
                                            bgcolor="#000000",
                                            padding=ft.Padding(left=6, top=2, right=6, bottom=2),
                                        ),
                                        on_click_handler=self.copy_url,
                                        idle_shadow_x=0,
                                        idle_shadow_y=0
                                    )
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                            ),
                            bgcolor=tokens["yellow"],
                            border=ft.Border.all(2, tokens["border"]),
                            padding=ft.Padding(left=10, top=5, right=8, bottom=5)
                        ),
                        ft.Container(height=4),
                        ft.Text("Select payloads or full folders in your mobile browser to stream directly to PC.", size=10, font_family=config.FONT_DISPLAY, color=tokens["muted"], text_align=ft.TextAlign.CENTER)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4
                ),
                bgcolor=tokens["card"],
                border=ft.Border.all(2.5, tokens["border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(4, 4)),
                padding=18
            )

            self.content_area.content = ft.Column(
                controls=[
                    qr_box
                ],
                spacing=10
            )

        try:
            self.content_area.update()
        except Exception:
            pass

    # -------------------------------------------------------------
    # User Interactions & Networking Lifecycle
    # -------------------------------------------------------------
    async def _set_clipboard_text(self, text):
        try:
            if hasattr(self.page_ref, "clipboard") and self.page_ref.clipboard:
                await self.page_ref.clipboard.set(str(text))
                return
        except Exception:
            pass
        try:
            if hasattr(self.page_ref, "set_clipboard"):
                self.page_ref.set_clipboard(str(text))
        except Exception:
            pass

    async def copy_url(self, e):
        try:
            url = self.web_receiver.url if self.web_receiver else ""
            if url:
                await self._set_clipboard_text(url)
        except Exception:
            pass

    async def copy_ip_address(self, e):
        try:
            await self._set_clipboard_text(self.local_ip)
            self.copy_ip_btn_text.value = "COPIED!"
            self.copy_ip_btn.bgcolor = self.tokens["green"]
            self.copy_ip_btn.update()

            def reset_btn():
                time.sleep(1.8)
                self.copy_ip_btn_text.value = "COPY IP"
                self.copy_ip_btn.bgcolor = self.tokens["yellow"]
                try:
                    self.copy_ip_btn.update()
                except Exception:
                    pass

            import threading
            threading.Thread(target=reset_btn, daemon=True).start()
        except Exception:
            pass

    def regenerate_pin(self, e):
        self.passcode = generate_passcode()
        self.stop_servers()
        self.start_mode_server()

    def switch_mode(self, mode):
        if self.active_mode == mode:
            return
        self.active_mode = mode
        self.stop_servers()
        self.update_mode_tabs_ui()
        self.start_mode_server()
        try:
            self.mode_switcher.update()
        except Exception:
            pass

    def start_mode_server(self):
        self.update_content_area_ui()

        if self.active_mode == "mobile":
            self.web_receiver = WebReceiver(
                port=config.DEFAULT_WEB_PORT,
                on_status_callback=self.on_status,
                on_progress_callback=self.on_progress,
                on_complete_callback=self.on_complete
            )
            self.web_receiver.start()
        else:
            self.p2p_receiver = Receiver(
                passcode=self.passcode,
                on_status_callback=self.on_status,
                on_progress_callback=self.on_progress,
                on_complete_callback=self.on_complete
            )
            self.p2p_receiver.start()

    def stop_servers(self):
        if self.p2p_receiver:
            self.p2p_receiver.stop()
            self.p2p_receiver = None
        if self.web_receiver:
            self.web_receiver.stop()
            self.web_receiver = None

    def dispose(self):
        self.stop_servers()

    def handle_back(self, e):
        self.dispose()
        self.on_back()

    def _parse_item_info(self, msg: str):
        """Extracts item name, size, and whether it is a folder from status messages."""
        name = None
        size_str = "--"
        is_folder = False

        if msg.startswith("Receiving folder:"):
            is_folder = True
            content = msg[len("Receiving folder:"):].strip()
            if "(" in content and content.endswith(")"):
                name_part, meta_part = content.rsplit("(", 1)
                name = name_part.strip()
                meta = meta_part.rstrip(")")
                size_str = meta.split(",")[0].strip()
            else:
                name = content
        elif msg.startswith("Receiving payload:") or msg.startswith("Receiving file:"):
            is_folder = False
            prefix = "Receiving payload:" if msg.startswith("Receiving payload:") else "Receiving file:"
            content = msg[len(prefix):].strip()
            if "(" in content and content.endswith(")"):
                name_part, meta_part = content.rsplit("(", 1)
                name = name_part.strip()
                size_str = meta_part.rstrip(")").strip()
            else:
                name = content
        elif msg.startswith("Receiving "):
            is_folder = False
            content = msg[len("Receiving "):].strip()
            if "(" in content and content.endswith(")"):
                name_part, meta_part = content.rsplit("(", 1)
                name = os.path.basename(name_part.strip())
                meta = meta_part.rstrip(")").strip()
                size_str = meta.split("/")[0].strip()
            else:
                name = os.path.basename(content)

        return name, size_str, is_folder

    def handle_pause_toggle(self, is_paused: bool):
        if is_paused:
            if self.p2p_receiver:
                self.p2p_receiver.pause()
            if self.web_receiver:
                self.web_receiver.pause()
        else:
            if self.p2p_receiver:
                self.p2p_receiver.resume()
            if self.web_receiver:
                self.web_receiver.resume()

    def ensure_transfer_view(self, filename="Incoming Payload", filesize="--", is_folder=False):
        if self.active_transfer_view is None:
            target_str = "Receiving from Mobile..." if self.active_mode == "mobile" else "Receiving from PC..."
            self.active_transfer_view = TransferView(
                page=self.page_ref,
                mode="receive",
                title_text=target_str,
                item_name=filename,
                item_size_str=filesize,
                is_folder=is_folder,
                on_cancel=self.reset_to_receive_view,
                on_done=self.reset_to_receive_view,
                on_pause_toggle=self.handle_pause_toggle
            )
            self.content = self.active_transfer_view
            self._schedule_ui_update()

    def reset_to_receive_view(self, e=None):
        self.stop_servers()
        self.active_transfer_view = None
        self.transfer_state = "idle"
        self._current_item_name = None
        self._current_size_str = "--"
        self._current_is_folder = False
        self.build_ui()
        self.start_mode_server()
        try:
            self.page_ref.update()
        except Exception:
            pass

    def _schedule_ui_update(self):
        def _apply_update():
            try:
                self.update()
            except Exception:
                pass
            try:
                self.page_ref.update()
            except Exception:
                pass

        loop = getattr(self.page_ref, "loop", None) or self.main_loop
        if loop is None or not loop.is_running():
            try:
                loop = asyncio.get_running_loop()
                self.main_loop = loop
            except Exception:
                loop = None

        if loop and loop.is_running():
            try:
                loop.call_soon_threadsafe(_apply_update)
                return
            except Exception:
                pass
        _apply_update()

    def on_status(self, msg):
        self.status_text_val = msg
        name, size_str, is_folder = self._parse_item_info(msg)

        # Trigger immediate automatic transition to TransferView on socket handshake or payload stream start
        if "Connected by" in msg or "Receiving" in msg or "Sender found" in msg:
            initial_name = name or self._current_item_name or "Incoming Transfer"
            initial_size = size_str if size_str != "--" else self._current_size_str
            self.ensure_transfer_view(
                filename=initial_name,
                filesize=initial_size,
                is_folder=is_folder
            )

        if name:
            self._current_item_name = name
            self._current_size_str = size_str
            self._current_is_folder = is_folder
            if self.active_transfer_view:
                self.active_transfer_view.update_item_info(name, size_str, is_folder)

        if self.active_transfer_view:
            self.active_transfer_view.on_status(msg)
        else:
            self.update_content_area_ui()

    def on_progress(self, percent, cur_speed, avg_speed, peak_speed, size_info, eta_str="--", elapsed_str="--"):
        if self.active_transfer_view is None:
            self.ensure_transfer_view(
                filename=self._current_item_name or "Incoming Payload",
                filesize=size_info or self._current_size_str or "--",
                is_folder=self._current_is_folder
            )

        if self.active_transfer_view:
            self.active_transfer_view.on_progress(percent, cur_speed, avg_speed, peak_speed, size_info, eta_str, elapsed_str)

    def on_complete(self, success, details=None):
        if self.active_transfer_view is None:
            self.ensure_transfer_view(
                filename=self._current_item_name or ("Folder" if self._current_is_folder else "Payload"),
                filesize=self._current_size_str or "--",
                is_folder=self._current_is_folder
            )

        if self.active_transfer_view:
            self.active_transfer_view.on_complete(success, details)
        else:
            self.transfer_state = "completed" if success else "error"
            self.status_text_val = "Transfer Completed!" if success else "Transfer Interrupted"
            self.update_content_area_ui()
