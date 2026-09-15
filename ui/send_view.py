import flet as ft
import os
import time
import asyncio
import config
import logging

logger = logging.getLogger("dropit")
from utils import get_local_ip, format_size, generate_qr_image, pil_to_b64, make_tactile, get_resource_path
from p2p.client import Sender
from web.server import WebSender
from ui.transfer_view import TransferView

class SendView(ft.Container):
    """
    DropIt Neo-Brutalist Send View.
    Implements the Stitch 'DropIt Flet Desktop - Send Payload' specification:
    - 44px Titlebar with [ ONLINE // P2P ] Status
    - Header with Channel 01 Tag and Back Navigation
    - Dual Action Staging: Select File / Select Folder & Drag-and-Drop Target
    - Staged Payload Card with Cyan File Tile, Monospace Size Badge & Dismiss Button
    - Segmented Mode Switcher: PC Transfer vs Mobile Transfer
    - High-Contrast Input Fields with 0/4 Passcode Counter
    - Massive Punchy Yellow 'SEND NOW' CTA with Offset Shadow
    - Seamless Transition to Unified TransferView
    """
    def __init__(self, page: ft.Page, on_back, initial_path: str = None, native_overlay=None):
        super().__init__(expand=True)
        self.page_ref = page
        self.on_back = on_back

        self.logo_path = get_resource_path(os.path.join("assets", "logo.png"))
        self.is_dark = page.theme_mode == ft.ThemeMode.DARK
        self.tokens = config.THEME_DARK if self.is_dark else config.THEME_LIGHT

        # File selection state
        self.selected_path = None
        self.selected_name = None
        self.selected_size_str = "--"
        self.is_folder = False

        # Transfer mode state
        self.active_mode = "pc"  # "pc" or "mobile"

        # P2P & Web Sender instances
        self.p2p_sender = None
        self.web_sender = None
        self.active_transfer_view = None

        # Metrics state
        self.transfer_state = "idle"  # "idle", "transferring", "completed", "error"
        self.status_text_val = "Ready for staging"
        self.progress_percent = 0.0
        self.cur_speed_val = "--"
        self.avg_speed_val = "--"
        self.peak_speed_val = "--"
        self.size_info_val = "--"
        self.eta_val = "--"
        self.elapsed_val = "--"

        # Rate-limiting and asyncio loop
        self._last_ui_update = 0.0
        self.main_loop = getattr(page, "loop", None)
        if not self.main_loop:
            try:
                self.main_loop = asyncio.get_running_loop()
            except Exception:
                self.main_loop = None

        # Setup Flet FilePicker service
        existing_picker = next((s for s in self.page_ref.services if isinstance(s, ft.FilePicker)), None)
        if existing_picker:
            self.file_picker = existing_picker
        else:
            self.file_picker = ft.FilePicker()
            self.page_ref.services.append(self.file_picker)

        # Setup Native Drop Overlay for Windows explorer drag & drop
        if native_overlay is not None:
            self.native_overlay = native_overlay
        else:
            from utils import NativeDropOverlay
            self.native_overlay = NativeDropOverlay(
                target_title=config.APP_TITLE,
                on_drop=self._on_native_drop,
                on_click=self._on_native_click,
                rel_x=16,
                rel_y=96,
                rel_w_offset=-32,
                height=85
            )
            self.native_overlay.start()

        self.build_ui()
        if initial_path and os.path.exists(initial_path):
            self.stage_path(initial_path)

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
        # 2. View Header (Back Button, Title, Channel Badge)
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

        view_title = ft.Text("SEND PAYLOAD", size=20, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"])

        channel_badge = ft.Container(
            content=ft.Text("CH-01", size=10, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"]),
            bgcolor=tokens["card"],
            border=ft.Border.all(1.5, tokens["border"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(2, 2)),
            padding=ft.Padding(left=8, top=3, right=8, bottom=3)
        )

        header_row = ft.Row(
            controls=[
                ft.Row(controls=[back_btn, view_title], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                channel_badge
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------
        # 3. Direct Browse & Paste Actions
        # ---------------------------------------------------------
        self.btn_browse_payload = make_tactile(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.ATTACH_FILE_ROUNDED, size=13, color="#000000"),
                        ft.Text("BROWSE PAYLOAD", size=10, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color="#000000")
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4
                ),
                bgcolor=tokens["btn_primary_bg"],
                border=ft.Border.all(2, tokens["btn_primary_border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["btn_primary_shadow"], offset=ft.Offset(2, 2)),
                padding=ft.Padding(left=10, top=6, right=10, bottom=6),
            ),
            on_click_handler=self.pick_file,
            idle_shadow_x=2,
            idle_shadow_y=2,
            shadow_color=tokens["btn_primary_shadow"]
        )

        self.btn_browse_folder = make_tactile(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.FOLDER_ROUNDED, size=13, color=tokens["btn_secondary_fg"]),
                        ft.Text("BROWSE FOLDER", size=10, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["btn_secondary_fg"])
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4
                ),
                bgcolor=tokens["btn_secondary_bg"],
                border=ft.Border.all(2, tokens["btn_secondary_border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["btn_secondary_shadow"], offset=ft.Offset(2, 2)),
                padding=ft.Padding(left=10, top=6, right=10, bottom=6),
            ),
            on_click_handler=self.pick_folder,
            idle_shadow_x=2,
            idle_shadow_y=2,
            shadow_color=tokens["btn_secondary_shadow"]
        )

        self.btn_paste_payload = make_tactile(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CONTENT_PASTE_ROUNDED, size=13, color=tokens["btn_secondary_fg"]),
                        ft.Text("PASTE", size=10, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["btn_secondary_fg"])
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4
                ),
                bgcolor=tokens["btn_secondary_bg"],
                border=ft.Border.all(2, tokens["btn_secondary_border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["btn_secondary_shadow"], offset=ft.Offset(2, 2)),
                padding=ft.Padding(left=10, top=6, right=10, bottom=6),
            ),
            on_click_handler=self.paste_from_clipboard,
            idle_shadow_x=2,
            idle_shadow_y=2,
            shadow_color=tokens["btn_secondary_shadow"]
        )

        self.browse_actions_row = ft.Row(
            controls=[self.btn_browse_payload, self.btn_browse_folder, self.btn_paste_payload],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6
        )

        # ---------------------------------------------------------
        # 4. Staged Payload Card / Drop Zone
        # ---------------------------------------------------------
        self.staged_payload_container = ft.Container(
            bgcolor=tokens["card_alt"],
            border=ft.Border.all(2.5, tokens["border"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(3, 3)),
            padding=ft.Padding(left=12, top=12, right=12, bottom=12),
            alignment=ft.Alignment.CENTER,
            on_click=self.pick_file
        )

        self.drop_zone = ft.DragTarget(
            group="drop_files",
            content=self.staged_payload_container,
            on_accept=self.handle_drag_drop
        )

        # ---------------------------------------------------------
        # 5. Segmented Mode Switcher (PC Transfer vs Mobile Transfer)
        # ---------------------------------------------------------
        self.tab_pc = make_tactile(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.COMPUTER_ROUNDED, size=15),
                        ft.Text("PC TRANSFER", size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5
                ),
                padding=ft.Padding(left=8, top=6, right=8, bottom=6),
                expand=True,
            ),
            on_click_handler=lambda e: self.switch_mode("pc"),
            idle_shadow_x=2,
            idle_shadow_y=2,
            shadow_color=tokens["shadow"]
        )

        self.tab_mobile = make_tactile(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.PHONE_ANDROID_ROUNDED, size=15),
                        ft.Text("MOBILE TRANSFER", size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5
                ),
                padding=ft.Padding(left=8, top=6, right=8, bottom=6),
                expand=True,
            ),
            on_click_handler=lambda e: self.switch_mode("mobile"),
            idle_shadow_x=2,
            idle_shadow_y=2,
            shadow_color=tokens["shadow"]
        )

        self.mode_switcher = ft.Container(
            content=ft.Row(controls=[self.tab_pc, self.tab_mobile], spacing=4),
            bgcolor=tokens["card"],
            border=ft.Border.all(2, tokens["border"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(2, 2)),
            padding=2
        )

        # ---------------------------------------------------------
        # 6. Mode Parameters Container (PC Inputs vs Mobile QR)
        # ---------------------------------------------------------
        self.options_container = ft.Container(
            border=ft.Border.all(2.5, tokens["border"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(4, 4)),
            bgcolor=tokens["card"],
            padding=10,
            alignment=ft.Alignment.CENTER
        )

        # PC Transfer Controls
        self.counter_badge = ft.Container(
            content=ft.Text("0/4", size=10, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"]),
            bgcolor=tokens["card_alt"],
            border=ft.Border.all(1, tokens["border"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(1.5, 1.5)),
            padding=ft.Padding(left=6, top=1, right=6, bottom=1)
        )

        self.passcode_input = ft.TextField(
            hint_text="4-DIGIT CODE",
            text_size=13,
            max_length=4,
            text_align=ft.TextAlign.CENTER,
            border_radius=0,
            border_color=tokens["border"],
            focused_border_color=tokens["border"],
            bgcolor=tokens["card_alt"],
            hint_style=ft.TextStyle(font_family=config.FONT_MONO, size=12, weight=ft.FontWeight.BOLD, letter_spacing=1.0, color=tokens["muted"]),
            text_style=ft.TextStyle(font_family=config.FONT_MONO, weight=ft.FontWeight.BOLD, letter_spacing=2.0, color=tokens["text"]),
            counter=ft.Container(),
            content_padding=ft.Padding(left=8, top=8, right=8, bottom=8),
            dense=True,
            on_change=self.on_passcode_change
        )

        self.ip_input = ft.TextField(
            hint_text="192.168.1.xxx (auto-discover)",
            text_size=11,
            text_align=ft.TextAlign.CENTER,
            border_radius=0,
            border_color=tokens["border"],
            focused_border_color=tokens["border"],
            bgcolor=tokens["card_alt"],
            text_style=ft.TextStyle(font_family=config.FONT_MONO, weight=ft.FontWeight.BOLD, color=tokens["text"]),
            content_padding=ft.Padding(left=8, top=8, right=8, bottom=8),
            dense=True
        )

        self.send_cta_btn = make_tactile(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.SEND_ROUNDED, size=16, color="#000000"),
                        ft.Text("SEND NOW", size=13, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color="#000000", style=ft.TextStyle(letter_spacing=1.0))
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8
                ),
                bgcolor=tokens["btn_primary_bg"],
                border=ft.Border.all(3, tokens["btn_primary_border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["btn_primary_shadow"], offset=ft.Offset(4, 4)),
                height=44,
            ),
            on_click_handler=self.start_p2p_send,
            idle_shadow_x=4,
            idle_shadow_y=4,
            shadow_color=tokens["btn_primary_shadow"]
        )

        # Initial Renders
        self.update_selected_item_ui()
        self.update_mode_tabs_ui()
        self.update_options_container_ui()

        # ---------------------------------------------------------
        # 7. Status Banner & Footer
        # ---------------------------------------------------------
        self.status_banner = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(width=6, height=6, bgcolor=tokens["green"], border=ft.Border.all(1, tokens["border"])),
                    ft.Text(self.status_text_val, size=10, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["muted"], overflow=ft.TextOverflow.ELLIPSIS)
                ],
                spacing=6,
                alignment=ft.MainAxisAlignment.START
            ),
            padding=ft.Padding(left=4, top=1, right=4, bottom=1)
        )

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
            padding=ft.Padding(left=10, top=4, right=10, bottom=4)
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
                            self.drop_zone,
                            self.browse_actions_row,
                            self.mode_switcher,
                            self.options_container,
                            self.status_banner,
                            ft.Container(expand=True),
                            ft.Container(content=footer_badge, alignment=ft.Alignment.CENTER),
                            ft.Container(height=2)
                        ],
                        spacing=8,
                        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        expand=True
                    ),
                    padding=ft.Padding(left=16, top=8, right=16, bottom=8),
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        )

    # -------------------------------------------------------------
    # UI State Helpers
    # -------------------------------------------------------------
    def on_passcode_change(self, e):
        tokens = self.tokens
        val = self.passcode_input.value or ""
        length = len(val)
        self.counter_badge.content.value = f"{length}/4"
        if length == 4:
            self.counter_badge.bgcolor = tokens["green"]
        else:
            self.counter_badge.bgcolor = tokens["card_alt"]
        try:
            self.counter_badge.update()
        except Exception:
            pass

    def update_selected_item_ui(self):
        tokens = self.tokens
        if not self.selected_path:
            self.browse_actions_row.visible = True
            self.staged_payload_container.bgcolor = tokens["card_alt"]
            self.staged_payload_container.padding = ft.Padding(left=12, top=14, right=12, bottom=14)
            self.staged_payload_container.on_click = self.pick_file
            self.staged_payload_container.content = ft.Column(
                controls=[
                    ft.Icon(ft.Icons.CLOUD_UPLOAD_ROUNDED, size=28, color="#000000"),
                    ft.Text("DRAG & DROP PAYLOAD OR FOLDER HERE", size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"], text_align=ft.TextAlign.CENTER),
                    ft.Text("Or click anywhere in this zone to browse files", size=9, font_family=config.FONT_DISPLAY, color=tokens["muted"], text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=3
            )
        else:
            self.browse_actions_row.visible = False
            self.staged_payload_container.on_click = None
            self.staged_payload_container.bgcolor = tokens["card"]
            self.staged_payload_container.padding = 12
            item_icon = ft.Icons.FOLDER_ROUNDED if self.is_folder else ft.Icons.INSERT_DRIVE_FILE_ROUNDED
            ext_str = "DIR" if self.is_folder else (os.path.splitext(self.selected_name)[1].replace(".", "").upper() or "PAYLOAD")

            remove_btn = make_tactile(
                ft.Container(
                    content=ft.Text("✕", size=13, weight=ft.FontWeight.W_900, font_family=config.FONT_MONO, color="#000000"),
                    width=30,
                    height=30,
                    bgcolor=tokens["card"],
                    border=ft.Border.all(2, "#000000"),
                    shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color="#000000", offset=ft.Offset(2, 2)),
                    alignment=ft.Alignment.CENTER,
                    tooltip="Remove selection",
                ),
                on_click_handler=self.clear_selection,
                idle_shadow_x=2,
                idle_shadow_y=2
            )

            self.staged_payload_container.content = ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(item_icon, size=22, color="#000000"),
                        width=42,
                        height=42,
                        bgcolor=tokens["cyan"],
                        border=ft.Border.all(2, "#000000"),
                        shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color="#000000", offset=ft.Offset(2, 2)),
                        alignment=ft.Alignment.CENTER
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(self.selected_name, size=12, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"], overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(f"[ {self.selected_size_str} // {ext_str} ]", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color="#FFFFFF"),
                                        bgcolor="#000000",
                                        padding=ft.Padding(left=5, top=1, right=5, bottom=1)
                                    ),
                                    ft.Text("STAGED", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"])
                                ],
                                spacing=5
                            )
                        ],
                        spacing=3,
                        expand=True
                    ),
                    remove_btn
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )

        try:
            self.browse_actions_row.update()
        except Exception:
            pass

        try:
            self.staged_payload_container.update()
        except Exception:
            pass

    def update_mode_tabs_ui(self):
        tokens = self.tokens
        active_border = tokens["btn_primary_border"]
        active_shadow_col = tokens["btn_primary_shadow"]

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

    def update_options_container_ui(self):
        tokens = self.tokens
        if self.active_mode == "pc":
            self.options_container.content = ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(width=6, height=6, bgcolor=tokens["yellow"]),
                            ft.Text("RECEIVER PASSCODE", size=10, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"]),
                            self.counter_badge
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6
                    ),
                    self.passcode_input,
                    ft.Container(height=1),
                    ft.Row(
                        controls=[
                            ft.Container(width=6, height=6, bgcolor=tokens["yellow"]),
                            ft.Text("RECEIVER IP ADDRESS (OPTIONAL)", size=10, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"])
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6
                    ),
                    self.ip_input,
                    ft.Container(height=2),
                    self.send_cta_btn
                ],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                spacing=6
            )
        else:
            # Mobile Transfer Mode
            if not self.selected_path:
                self.options_container.content = ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.QR_CODE_2_ROUNDED, size=34, color=tokens["muted"]),
                        ft.Text("STAGE A PAYLOAD OR FOLDER ABOVE", size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"], text_align=ft.TextAlign.CENTER),
                        ft.Text("A QR code will generate for instant mobile phone download.", size=9, font_family=config.FONT_DISPLAY, color=tokens["muted"], text_align=ft.TextAlign.CENTER)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4
                )
            else:
                if not self.web_sender:
                    self.web_sender = WebSender(
                        shared_path=self.selected_path,
                        port=config.DEFAULT_WEB_PORT,
                        on_status_callback=self.on_status,
                        on_progress_callback=self.on_progress,
                        on_complete_callback=self.on_complete
                    )
                    self.web_sender.start()

                url = self.web_sender.url

                qr_img = generate_qr_image(url, fg_color="#000000", bg_color="#FFFFFF")
                qr_b64 = pil_to_b64(qr_img)
                qr_widget = ft.Image(src=f"data:image/png;base64,{qr_b64}", width=120, height=120, fit=ft.BoxFit.CONTAIN) if qr_b64 else ft.Container()

                server_card = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.WIFI_TETHERING_ROUNDED, size=18, color="#000000"),
                                width=30,
                                height=30,
                                bgcolor=tokens["green"],
                                border=ft.Border.all(1.5, tokens["border"]),
                                alignment=ft.Alignment.CENTER
                            ),
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text("LOCAL SERVER ACTIVE", size=9, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"]),
                                            ft.Container(
                                                content=ft.Text("PORT 8080", size=8, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color="#000000"),
                                                bgcolor=tokens["yellow"],
                                                border=ft.Border.all(1, tokens["border"]),
                                                padding=ft.Padding(left=4, top=1, right=4, bottom=1)
                                            )
                                        ],
                                        spacing=5,
                                        alignment=ft.MainAxisAlignment.CENTER
                                    ),
                                    ft.Text(url, size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"], text_align=ft.TextAlign.CENTER)
                                ],
                                spacing=1,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                expand=True
                            )
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    bgcolor=tokens["card_alt"],
                    border=ft.Border.all(1.5, tokens["border"]),
                    padding=6,
                    alignment=ft.Alignment.CENTER
                )

                qr_box = ft.Container(
                    content=qr_widget,
                    width=165,
                    height=165,
                    bgcolor="#FFFFFF",
                    border=ft.Border.all(2.5, "#000000"),
                    shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens.get("qr_shadow", "#000000"), offset=ft.Offset(3, 3)),
                    padding=8,
                    alignment=ft.Alignment.CENTER
                )

                folder_note = ft.Container(
                    content=ft.Text("[ AUTO-ZIP ARCHIVE STREAM ACTIVE ]", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color="#000000"),
                    bgcolor=tokens["yellow"],
                    border=ft.Border.all(1, tokens["border"]),
                    padding=ft.Padding(left=6, top=2, right=6, bottom=2)
                ) if self.is_folder else ft.Container()

                self.options_container.content = ft.Column(
                    controls=[
                        server_card,
                        ft.Row(
                            controls=[qr_box],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        folder_note,
                        ft.Text("Scan with phone camera to download directly in browser.", size=10, font_family=config.FONT_DISPLAY, color=tokens["muted"], text_align=ft.TextAlign.CENTER)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8
                )

        try:
            self.options_container.update()
        except Exception:
            pass

    # -------------------------------------------------------------
    # Event Handlers & Core Networking Logic
    # -------------------------------------------------------------
    def dispose(self):
        if hasattr(self, "native_overlay") and self.native_overlay:
            try:
                self.native_overlay.stop()
            except Exception:
                pass
        self.stop_senders()

    def handle_back(self, e=None):
        self.dispose()
        self.on_back()

    def _on_native_drop(self, files):
        if files and len(files) > 0:
            first_path = files[0]
            if self.main_loop:
                self.main_loop.call_soon_threadsafe(self.stage_path, first_path)
            else:
                self.stage_path(first_path)

    def _on_native_click(self):
        if not self.selected_path:
            if self.main_loop:
                asyncio.run_coroutine_threadsafe(self.pick_file(), self.main_loop)

    def stage_path(self, path: str):
        if not path or not os.path.exists(path):
            return
        self.selected_path = path
        self.is_folder = os.path.isdir(path)
        self.selected_name = os.path.basename(path.rstrip("\\/")) or ("Directory" if self.is_folder else "File")

        # Temporarily hide native overlay so staged item card buttons remain responsive
        if hasattr(self, "native_overlay") and self.native_overlay:
            self.native_overlay.set_visible(False)

        self.status_text_val = f"STAGED: {self.selected_name}"
        self.status_banner.content.controls[1].value = self.status_text_val
        try:
            self.status_banner.update()
        except Exception:
            pass

        if self.is_folder:
            self.selected_size_str = "Calculating..."
            self.update_selected_item_ui()

            async def _calc():
                total_size = await asyncio.to_thread(self._calc_folder_size, path)
                self.selected_size_str = format_size(total_size) if total_size > 0 else "--"
                self.update_selected_item_ui()
                if self.active_mode == "mobile":
                    self.restart_web_sender()
                else:
                    self.update_options_container_ui()

            if self.main_loop:
                asyncio.run_coroutine_threadsafe(_calc(), self.main_loop)
            else:
                total_size = self._calc_folder_size(path)
                self.selected_size_str = format_size(total_size) if total_size > 0 else "--"
                self.update_selected_item_ui()
                if self.active_mode == "mobile":
                    self.restart_web_sender()
                else:
                    self.update_options_container_ui()
        else:
            try:
                self.selected_size_str = format_size(os.path.getsize(path))
            except Exception:
                self.selected_size_str = "--"
            self.update_selected_item_ui()
            if self.active_mode == "mobile":
                self.restart_web_sender()
            else:
                self.update_options_container_ui()

    async def pick_file(self, e=None):
        from utils import open_native_file_picker
        picked_path = None
        try:
            res = await self.file_picker.pick_files(
                dialog_title="Select Payload to Send",
                allow_multiple=False
            )
            if res and len(res) > 0:
                item = res[0]
                if hasattr(item, "path") and item.path:
                    picked_path = item.path
        except Exception as ex:
            logger.debug(f"[SendView] pick_file service error: {ex}, falling back to native OS picker")
            picked_path = await asyncio.to_thread(open_native_file_picker, "Select Payload to Send", False)

        if picked_path and os.path.exists(picked_path):
            self.stage_path(picked_path)

    async def pick_folder(self, e=None):
        from utils import open_native_file_picker
        folder_path = None
        try:
            res = await self.file_picker.get_directory_path(
                dialog_title="Select Directory to Send"
            )
            if res and isinstance(res, str):
                folder_path = res
        except Exception as ex:
            logger.debug(f"[SendView] pick_folder service error: {ex}, falling back to native OS picker")
            folder_path = await asyncio.to_thread(open_native_file_picker, "Select Directory to Send", True)

        if folder_path and os.path.exists(folder_path):
            self.stage_path(folder_path)

    def paste_from_clipboard(self, e=None):
        from utils import get_clipboard_files
        files = get_clipboard_files()
        if files and len(files) > 0:
            self.stage_path(files[0])
            self.status_text_val = f"STAGED FROM CLIPBOARD: {os.path.basename(files[0])}"
            self.status_banner.content.controls[1].value = self.status_text_val
            try:
                self.status_banner.update()
            except Exception:
                pass
        else:
            self.status_text_val = "NO PAYLOAD DETECTED ON CLIPBOARD (COPY FIRST)"
            self.status_banner.content.controls[1].value = self.status_text_val
            try:
                self.status_banner.update()
            except Exception:
                pass

    def _calc_folder_size(self, path):
        total = 0
        try:
            for root, dirs, files in os.walk(path):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except Exception:
            pass
        return total

    async def handle_drag_drop(self, e):
        path = getattr(e, "data", None) or getattr(e, "src_id", None)
        if path and isinstance(path, str):
            clean_path = path.strip('"').strip("'")
            if os.path.exists(clean_path):
                self.stage_path(clean_path)

    def clear_selection(self, e=None):
        self.selected_path = None
        self.selected_name = None
        self.selected_size_str = "--"
        self.is_folder = False
        self.stop_senders()
        self.transfer_state = "idle"
        self.status_text_val = "Ready for staging"
        if hasattr(self, "native_overlay") and self.native_overlay:
            self.native_overlay.set_visible(True)
        self.update_selected_item_ui()
        self.update_options_container_ui()
        self.status_banner.content.controls[1].value = self.status_text_val
        try:
            self.status_banner.update()
        except Exception:
            pass

    def switch_mode(self, mode):
        if self.active_mode == mode:
            return
        self.active_mode = mode
        self.stop_senders()
        self.update_mode_tabs_ui()
        self.update_options_container_ui()
        try:
            self.mode_switcher.update()
        except Exception:
            pass

    def restart_web_sender(self):
        self.stop_senders()
        self.update_options_container_ui()

    def start_p2p_send(self, e):
        if not self.selected_path:
            self.status_text_val = "Please select a payload or folder first"
            self.status_banner.content.controls[1].value = self.status_text_val
            try:
                self.status_banner.update()
            except Exception:
                pass
            return

        passcode = self.passcode_input.value.strip() if self.passcode_input.value else ""
        if not passcode or len(passcode) != 4 or not passcode.isdigit():
            self.status_text_val = "Please enter a valid 4-digit passcode"
            self.status_banner.content.controls[1].value = self.status_text_val
            try:
                self.status_banner.update()
            except Exception:
                pass
            return

        target_ip = self.ip_input.value.strip() if self.ip_input.value else None

        self.stop_senders()
        self.transfer_state = "transferring"
        self.progress_percent = 0.0

        # Immediately transition to TransferView upon initiating send
        self.ensure_transfer_view()

        self.p2p_sender = Sender(
            on_status_callback=self.on_status,
            on_progress_callback=self.on_progress,
            on_complete_callback=self.on_complete
        )
        self.p2p_sender.discover_and_send(self.selected_path, passcode, target_ip)

    def stop_senders(self):
        if self.p2p_sender:
            self.p2p_sender.cancel()
            self.p2p_sender = None
        if self.web_sender:
            self.web_sender.stop()
            self.web_sender = None

    def handle_pause_toggle(self, is_paused: bool):
        if is_paused:
            if self.p2p_sender:
                self.p2p_sender.pause()
            if self.web_sender:
                self.web_sender.pause()
        else:
            if self.p2p_sender:
                self.p2p_sender.resume()
            if self.web_sender:
                self.web_sender.resume()

    def ensure_transfer_view(self):
        if self.active_transfer_view is None:
            target_str = "Sending to Mobile Device..." if self.active_mode == "mobile" else "Sending to PC..."
            self.active_transfer_view = TransferView(
                page=self.page_ref,
                mode="send",
                title_text=target_str,
                item_name=self.selected_name or "Selected Item",
                item_size_str=self.selected_size_str or "--",
                is_folder=self.is_folder,
                on_cancel=self.reset_to_send_view,
                on_done=self.reset_to_send_view,
                on_pause_toggle=self.handle_pause_toggle
            )
            self.content = self.active_transfer_view
            self._schedule_ui_update()

    def reset_to_send_view(self, e=None):
        self.stop_senders()
        self.active_transfer_view = None
        self.transfer_state = "idle"
        self.selected_path = None
        self.selected_name = None
        self.selected_size_str = "--"
        self.is_folder = False
        self.build_ui()
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
        if self.active_transfer_view:
            self.active_transfer_view.on_status(msg)
        else:
            self.status_banner.content.controls[1].value = msg
            self._schedule_ui_update()

    def on_progress(self, percent, cur_speed, avg_speed, peak_speed, size_info, eta_str="--", elapsed_str="--"):
        if self.active_transfer_view is None:
            self.ensure_transfer_view()

        if self.active_transfer_view:
            self.active_transfer_view.on_progress(percent, cur_speed, avg_speed, peak_speed, size_info, eta_str, elapsed_str)

    def on_complete(self, success, details=None):
        if self.active_transfer_view is None:
            self.ensure_transfer_view()

        if self.active_transfer_view:
            self.active_transfer_view.on_complete(success, details)
        else:
            self.transfer_state = "completed" if success else "error"
            self.status_text_val = "Transfer Complete!" if success else "Transfer Failed"
            self.status_banner.content.controls[1].value = self.status_text_val
            self._schedule_ui_update()
