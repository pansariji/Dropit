import flet as ft
import os
import time
import asyncio
import config
import logging

logger = logging.getLogger("dropit")
from utils import get_resource_path, format_size, open_file_location, make_tactile

class TransferView(ft.Container):
    """
    DropIt Neo-Brutalist Active Transfer View.
    Implements the Stitch 'DropIt Flet Desktop - Active Transfer' specification:
    - 44px Titlebar with [ BROADCASTING // PORT ] Status Pill
    - Screen Header with Back Action and LIVE Telemetry Tag
    - Staged Payload Card with Yellow Tile & Metadata
    - Connected Target Device Alert Box with Green Accent
    - Hero Telemetry HUD: Giant 64px Monospace Percentage, Heavy Neo-Brutalist Progress Bar,
      and Chunk/Byte Readout
    - 4-Grid Telemetry Blocks (Size, Highlighted Yellow Speed, Peak Speed, ETA Remain)
    - Tactile Brutalist Bottom Controls (Pause, Cancel, Open File Location, Done)
    """
    def __init__(
        self,
        page: ft.Page,
        mode: str,  # "send" or "receive"
        title_text: str,
        item_name: str,
        item_size_str: str,
        is_folder: bool = False,
        on_cancel=None,
        on_done=None,
        on_pause_toggle=None
    ):
        super().__init__(expand=True)
        self.page_ref = page
        self.mode = mode
        self.logo_path = get_resource_path(os.path.join("assets", "logo.png"))
        self.title_text = title_text
        self.item_name = item_name
        self.item_size_str = item_size_str
        self.is_folder = is_folder
        self.on_cancel_cb = on_cancel
        self.on_done_cb = on_done
        self.on_pause_toggle_cb = on_pause_toggle

        self.is_dark = page.theme_mode == ft.ThemeMode.DARK
        self.tokens = config.THEME_DARK if self.is_dark else config.THEME_LIGHT

        # Transfer state
        self.transfer_state = "transferring"  # "transferring", "completed", "error"
        self.progress_percent = 0.0
        self.cur_speed_val = "--"
        self.avg_speed_val = "--"
        self.peak_speed_val = "--"
        self.size_info_val = item_size_str
        self.eta_val = "--"
        self.elapsed_val = "--"
        self.status_text_val = "TRANSFERRING PAYLOAD STREAM"
        self.received_filepath = None
        self.is_paused = False

        self._current_action_state = None
        self.pause_icon = None
        self.pause_text = None
        self.pause_btn_container = None
        self.pause_btn = None
        self.cancel_btn = None

        self._last_ui_update = 0.0
        self.main_loop = getattr(page, "loop", None)
        if not self.main_loop:
            try:
                self.main_loop = asyncio.get_running_loop()
            except Exception:
                self.main_loop = None

        self.build_ui()

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

        status_label_str = "BROADCASTING // P2P" if self.mode == "send" else "STREAMING // IN"
        self.titlebar_status_pill = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(width=7, height=7, border_radius=4, bgcolor=tokens["green"], border=ft.Border.all(1, tokens["status_border"])),
                    ft.Text(f"[ {status_label_str} ]", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["status_fg"])
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER
            ),
            bgcolor=tokens["status_bg"],
            border=ft.Border.all(1.5, tokens["status_border"]),
            padding=ft.Padding(left=6, top=2, right=6, bottom=2),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["status_border"] if self.is_dark else "#000000", offset=ft.Offset(2, 2))
        )

        titlebar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(controls=[title_icon, title_text, self.titlebar_status_pill], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(
                        content=ft.Text("BUF:256KB", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["muted"]),
                        padding=ft.Padding(left=6, top=2, right=6, bottom=2),
                        border=ft.Border.all(1, tokens["border"]),
                        bgcolor=tokens["card"]
                    )
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
        # 2. View Header (Back Button, Title, LIVE Status Badge)
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
                tooltip="Back to Overview",
            ),
            on_click_handler=self.handle_cancel,
            idle_shadow_x=2,
            idle_shadow_y=2,
            shadow_color=tokens["shadow"]
        )

        self.view_title = ft.Text(
            "TRANSFER ACTIVE",
            size=20,
            weight=ft.FontWeight.W_900,
            font_family=config.FONT_DISPLAY,
            color=tokens["text"]
        )

        self.live_badge = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(width=6, height=6, border_radius=3, bgcolor=tokens["green"], border=ft.Border.all(1, tokens["border"])),
                    ft.Text("LIVE", size=10, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"])
                ],
                spacing=4
            ),
            bgcolor=tokens["card"],
            border=ft.Border.all(1.5, tokens["border"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(2, 2)),
            padding=ft.Padding(left=8, top=3, right=8, bottom=3)
        )

        header_row = ft.Row(
            controls=[
                ft.Row(controls=[back_btn, self.view_title], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                self.live_badge
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

        # ---------------------------------------------------------
        # 3. Active Payload Staged Card
        # ---------------------------------------------------------
        item_icon = ft.Icons.FOLDER_ROUNDED if self.is_folder else ft.Icons.INSERT_DRIVE_FILE_ROUNDED
        ext_str = "DIR" if self.is_folder else (os.path.splitext(self.item_name)[1].replace(".", "").upper() or "PAYLOAD")

        self.item_icon_widget = ft.Icon(item_icon, size=22, color="#000000")
        self.txt_item_name = ft.Text(self.item_name, size=12, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"], overflow=ft.TextOverflow.ELLIPSIS)
        self.txt_item_type = ft.Text(f"{'FOLDER' if self.is_folder else 'PAYLOAD'}", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["muted"])
        self.txt_item_size_ext = ft.Text(f"[ {self.item_size_str} // {ext_str} ]", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"])

        payload_card = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=self.item_icon_widget,
                        width=42,
                        height=42,
                        bgcolor=tokens["yellow"],
                        border=ft.Border.all(2, tokens["border"]),
                        shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(2, 2)),
                        alignment=ft.Alignment.CENTER
                    ),
                    ft.Column(
                        controls=[
                            self.txt_item_name,
                            ft.Row(
                                controls=[
                                    self.txt_item_type,
                                    ft.Text("•", size=9, color=tokens["muted"]),
                                    ft.Container(
                                        content=self.txt_item_size_ext,
                                        bgcolor=tokens["card_alt"],
                                        border=ft.Border.all(1, tokens["border"]),
                                        padding=ft.Padding(left=5, top=1, right=5, bottom=1)
                                    )
                                ],
                                spacing=5
                            )
                        ],
                        spacing=2,
                        expand=True
                    )
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=tokens["card"],
            border=ft.Border.all(2.5, tokens["border"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(3, 3)),
            padding=10
        )

        # ---------------------------------------------------------
        # 4. Connected Target Device Alert Box
        # ---------------------------------------------------------
        target_icon = ft.Icons.PHONE_ANDROID_ROUNDED if "Mobile" in self.title_text else ft.Icons.COMPUTER_ROUNDED
        self.target_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(target_icon, size=16, color=tokens["text"]),
                                width=24,
                                height=24,
                                bgcolor=tokens["card_alt"],
                                border=ft.Border.all(1.5, tokens["border"]),
                                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(1.5, 1.5)),
                                alignment=ft.Alignment.CENTER
                            ),
                            ft.Text(self.title_text.upper(), size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["text"])
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(width=6, height=6, border_radius=3, bgcolor=tokens["green"], border=ft.Border.all(1, tokens["status_border"])),
                                ft.Text("STREAM CHANNEL VERIFIED", size=10, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["status_fg"])
                            ],
                            spacing=6,
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        bgcolor=tokens["status_bg"],
                        border=ft.Border.all(1.5, tokens["status_border"]),
                        shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["status_border"] if self.is_dark else "#000000", offset=ft.Offset(1.5, 1.5)),
                        padding=ft.Padding(left=10, top=3, right=10, bottom=3)
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6
            ),
            bgcolor=tokens["card"],
            border=ft.Border.all(2.5, tokens["border"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(3, 3)),
            padding=10
        )

        # ---------------------------------------------------------
        # 5. Hero Telemetry & Visual Progress HUD
        # ---------------------------------------------------------
        is_completed = self.transfer_state == "completed"

        self.txt_percent_val = ft.Text(
            "100" if is_completed else f"{int(self.progress_percent)}",
            size=60,
            weight=ft.FontWeight.W_900,
            font_family=config.FONT_MONO,
            color=tokens["text"],
            style=ft.TextStyle(letter_spacing=-2.0)
        )

        self.txt_percent_sign = ft.Text(
            "%",
            size=28,
            weight=ft.FontWeight.W_900,
            font_family=config.FONT_DISPLAY,
            color=tokens["text"]
        )

        self.status_descriptor = ft.Text(
            "TRANSFER COMPLETED SUCCESSFULLY!" if is_completed else self.status_text_val,
            size=10,
            weight=ft.FontWeight.W_900,
            font_family=config.FONT_MONO,
            color=tokens["green"] if is_completed else tokens["muted"]
        )

        # Neo-brutalist heavy progress bar with vertical head marker
        initial_pbar_w = 385.0 if is_completed else max(0.0, (self.progress_percent / 100.0) * 385.0)
        self.pbar_inner = ft.Container(
            bgcolor=tokens["green"] if is_completed else tokens["yellow"],
            border=ft.Border(right=ft.BorderSide(2.5, tokens["border"])),
            height=20,
            width=initial_pbar_w,
            alignment=ft.Alignment.CENTER_RIGHT,
            padding=ft.Padding(right=2, top=0, bottom=0, left=0),
            content=ft.Container(width=4, height=12, bgcolor="#000000")
        )

        self.pbar_track = ft.Container(
            content=self.pbar_inner,
            bgcolor=tokens["card_alt"],
            border=ft.Border.all(2.5, tokens["border"]),
            height=20,
            alignment=ft.Alignment.CENTER_LEFT
        )

        self.hud_chunk_counter = ft.Text("Socket Buffer Active", size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"])
        self.hud_size_readout = ft.Text(self.item_size_str, size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=tokens["text"])

        hud_footer = ft.Row(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(width=6, height=6, bgcolor=tokens["border"]),
                        self.hud_chunk_counter
                    ],
                    spacing=5
                ),
                ft.Container(
                    content=self.hud_size_readout,
                    bgcolor=tokens["card_alt"],
                    border=ft.Border.all(1, tokens["border"]),
                    padding=ft.Padding(left=6, top=1, right=6, bottom=1)
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        hero_progress_hud = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[self.txt_percent_val, self.txt_percent_sign],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        spacing=2
                    ),
                    self.status_descriptor,
                    ft.Container(height=4),
                    self.pbar_track,
                    ft.Container(height=4),
                    hud_footer
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4
            ),
            bgcolor=tokens["card"],
            border=ft.Border.all(2.5, tokens["border"]),
            shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(4, 4)),
            padding=14
        )

        # ---------------------------------------------------------
        # 6. 4-Grid Telemetry Block
        # ---------------------------------------------------------
        self.val_size = ft.Text(self.item_size_str, size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_MONO, color=tokens["text"])
        self.val_speed = ft.Text("--", size=13, weight=ft.FontWeight.W_900, font_family=config.FONT_MONO, color="#000000")
        self.val_peak = ft.Text("--", size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_MONO, color=tokens["text"])
        self.val_eta = ft.Text("--", size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_MONO, color=tokens["text"])

        def make_telemetry_tile(title_str, val_control, unit_str, is_highlight=False):
            bg_col = tokens["yellow"] if is_highlight else tokens["card"]
            title_col = "#000000" if is_highlight else tokens["muted"]
            unit_col = "#000000" if is_highlight else tokens["muted"]

            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(title_str, size=9, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=title_col),
                        val_control,
                        ft.Text(unit_str, size=8, weight=ft.FontWeight.BOLD, font_family=config.FONT_MONO, color=unit_col)
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=2
                ),
                bgcolor=bg_col,
                border=ft.Border.all(2, tokens["border"]),
                shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(2, 2)),
                padding=8,
                expand=True
            )

        telemetry_grid = ft.Row(
            controls=[
                make_telemetry_tile("SIZE", self.val_size, "BYTES"),
                make_telemetry_tile("SPEED", self.val_speed, "MB/S", is_highlight=True),
                make_telemetry_tile("PEAK", self.val_peak, "MB/S"),
                make_telemetry_tile("ETA", self.val_eta, "REMAIN")
            ],
            spacing=8
        )

        # ---------------------------------------------------------
        # 7. Dynamic Tactile Action Controls
        # ---------------------------------------------------------
        self.actions_container = ft.Container()
        self.update_action_buttons()

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
                            payload_card,
                            self.target_box,
                            hero_progress_hud,
                            telemetry_grid,
                            ft.Container(expand=True),
                            self.actions_container,
                            ft.Container(height=2)
                        ],
                        spacing=8,
                        expand=True
                    ),
                    padding=ft.Padding(left=16, top=8, right=16, bottom=8),
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        )

    def update_action_buttons(self):
        tokens = self.tokens
        if self.transfer_state == "transferring":
            if self.pause_btn is None:
                pause_text = "RESUME TRANSFER" if self.is_paused else "PAUSE TRANSFER"
                pause_icon = ft.Icons.PLAY_ARROW_ROUNDED if self.is_paused else ft.Icons.PAUSE_ROUNDED
                pause_bg = tokens["yellow"] if self.is_paused else tokens["card"]
                pause_fg = "#000000" if self.is_paused else tokens["text"]
                pause_border = "#000000" if self.is_paused else tokens["border"]
                pause_shadow = tokens.get("btn_primary_shadow", "#000000") if self.is_paused else tokens["shadow"]

                self.pause_icon = ft.Icon(pause_icon, size=16, color=pause_fg)
                self.pause_text = ft.Text(pause_text, size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=pause_fg)
                self.pause_btn_container = ft.Container(
                    content=ft.Row(
                        controls=[
                            self.pause_icon,
                            self.pause_text
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6
                    ),
                    bgcolor=pause_bg,
                    border=ft.Border.all(2.5, pause_border),
                    shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=pause_shadow, offset=ft.Offset(3, 3)),
                    height=46,
                    expand=True,
                )
                self.pause_btn = make_tactile(
                    self.pause_btn_container,
                    on_click_handler=self.toggle_pause,
                    idle_shadow_x=3,
                    idle_shadow_y=3,
                    shadow_color=pause_shadow
                )

                self.cancel_btn = make_tactile(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CLOSE_ROUNDED, size=16, color="#000000"),
                                ft.Text("CANCEL TRANSFER", size=11, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color="#000000")
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=6
                        ),
                        bgcolor=tokens["red_light"] if not self.is_dark else "#FFA5A5",
                        border=ft.Border.all(2.5, "#000000"),
                        shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(3, 3)),
                        height=46,
                        expand=True,
                    ),
                    on_click_handler=self.handle_cancel,
                    idle_shadow_x=3,
                    idle_shadow_y=3,
                    shadow_color=tokens["shadow"]
                )

            self.actions_container.content = ft.Row(controls=[self.pause_btn, self.cancel_btn], spacing=10)
            self._current_action_state = "transferring"

        elif self.transfer_state == "completed":
            if self.mode == "receive":
                show_payload_btn = make_tactile(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=18, color="#000000"),
                                ft.Text("SHOW PAYLOAD", size=12, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color="#000000")
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=6
                        ),
                        bgcolor=tokens["green"],
                        border=ft.Border.all(2.5, "#000000"),
                        shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens.get("btn_secondary_shadow", "#000000"), offset=ft.Offset(3, 3)),
                        height=48,
                        expand=True,
                    ),
                    on_click_handler=self.handle_open_file,
                    idle_shadow_x=3,
                    idle_shadow_y=3,
                    shadow_color=tokens.get("btn_secondary_shadow", "#000000")
                )

                done_btn = make_tactile(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CHECK_ROUNDED, size=18, color="#000000"),
                                ft.Text("DONE", size=12, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color="#000000")
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=6
                        ),
                        bgcolor=tokens["btn_secondary_bg"],
                        border=ft.Border.all(2.5, "#000000"),
                        shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens.get("btn_secondary_shadow", "#000000"), offset=ft.Offset(3, 3)),
                        height=48,
                        expand=True,
                    ),
                    on_click_handler=self.handle_done,
                    idle_shadow_x=3,
                    idle_shadow_y=3,
                    shadow_color=tokens.get("btn_secondary_shadow", "#000000")
                )

                self.actions_container.content = ft.Row(controls=[show_payload_btn, done_btn], spacing=10)
            else:
                done_btn = make_tactile(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, size=18, color="#000000"),
                                ft.Text("DONE", size=13, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color="#000000")
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8
                        ),
                        bgcolor=tokens["yellow"],
                        border=ft.Border.all(3, "#000000"),
                        shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens.get("btn_primary_shadow", "#000000"), offset=ft.Offset(4, 4)),
                        height=48,
                        expand=True,
                    ),
                    on_click_handler=self.handle_done,
                    idle_shadow_x=4,
                    idle_shadow_y=4,
                    shadow_color=tokens.get("btn_primary_shadow", "#000000")
                )
                self.actions_container.content = done_btn
            self._current_action_state = "completed"
        else:
            # Error State
            self.actions_container.content = make_tactile(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ARROW_BACK_ROUNDED, size=18, color=tokens["btn_secondary_fg"]),
                            ft.Text("BACK TO OVERVIEW", size=12, weight=ft.FontWeight.W_900, font_family=config.FONT_DISPLAY, color=tokens["btn_secondary_fg"])
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8
                    ),
                    bgcolor=tokens["card"],
                    border=ft.Border.all(2.5, tokens["border"]),
                    shadow=ft.BoxShadow(spread_radius=0, blur_radius=0, color=tokens["shadow"], offset=ft.Offset(3, 3)),
                    height=48,
                ),
                on_click_handler=self.handle_done,
                idle_shadow_x=3,
                idle_shadow_y=3,
                shadow_color=tokens["shadow"]
            )
            self._current_action_state = "error"

    def toggle_pause(self, e=None):
        self.is_paused = not self.is_paused
        if self.on_pause_toggle_cb:
            try:
                self.on_pause_toggle_cb(self.is_paused)
            except Exception as ex:
                logger.debug(f"Error executing on_pause_toggle_cb: {ex}")

        tokens = self.tokens
        if self.is_paused:
            if self.pause_text:
                self.pause_text.value = "RESUME TRANSFER"
                self.pause_text.color = "#000000"
            if self.pause_icon:
                self.pause_icon.icon = ft.Icons.PLAY_ARROW_ROUNDED
                self.pause_icon.color = "#000000"
            if self.pause_btn_container:
                self.pause_btn_container.bgcolor = tokens["yellow"]
                self.pause_btn_container.border = ft.Border.all(2.5, "#000000")
                pause_shadow = tokens.get("btn_primary_shadow", "#000000")
                self.pause_btn_container.shadow = ft.BoxShadow(spread_radius=0, blur_radius=0, color=pause_shadow, offset=ft.Offset(3, 3))

            self.status_descriptor.value = "TRANSFER PAUSED // SOCKET BUFFER ACTIVE"
            self.status_descriptor.color = tokens["yellow"]
            self.val_speed.value = "PAUSED"
            self.val_eta.value = "--"
            if hasattr(self, "live_badge") and hasattr(self.live_badge, "content"):
                self.live_badge.content.controls[1].value = "PAUSED"
                self.live_badge.bgcolor = tokens["yellow"]
        else:
            if self.pause_text:
                self.pause_text.value = "PAUSE TRANSFER"
                self.pause_text.color = tokens["text"]
            if self.pause_icon:
                self.pause_icon.icon = ft.Icons.PAUSE_ROUNDED
                self.pause_icon.color = tokens["text"]
            if self.pause_btn_container:
                self.pause_btn_container.bgcolor = tokens["card"]
                self.pause_btn_container.border = ft.Border.all(2.5, tokens["border"])
                pause_shadow = tokens["shadow"]
                self.pause_btn_container.shadow = ft.BoxShadow(spread_radius=0, blur_radius=0, color=pause_shadow, offset=ft.Offset(3, 3))

            self.status_descriptor.value = self.status_text_val
            self.status_descriptor.color = tokens["muted"]
            self.val_speed.value = self.cur_speed_val
            self.val_eta.value = self.eta_val
            if hasattr(self, "live_badge") and hasattr(self.live_badge, "content"):
                self.live_badge.content.controls[1].value = "LIVE"
                self.live_badge.bgcolor = tokens["green_light"]

        try:
            self.update()
        except Exception:
            try:
                self.page_ref.update()
            except Exception:
                pass

    def update_item_info(self, name: str, size_str: str = "--", is_folder: bool = False):
        self.item_name = name
        self.item_size_str = size_str
        self.is_folder = is_folder
        ext_str = "DIR" if self.is_folder else (os.path.splitext(self.item_name)[1].replace(".", "").upper() or "PAYLOAD")
        if hasattr(self, "txt_item_name"):
            self.txt_item_name.value = name
        if hasattr(self, "item_icon_widget"):
            self.item_icon_widget.icon = ft.Icons.FOLDER_ROUNDED if is_folder else ft.Icons.INSERT_DRIVE_FILE_ROUNDED
        if hasattr(self, "txt_item_type"):
            self.txt_item_type.value = "FOLDER" if is_folder else "PAYLOAD"
        if hasattr(self, "txt_item_size_ext"):
            self.txt_item_size_ext.value = f"[ {size_str} // {ext_str} ]"
        if hasattr(self, "hud_size_readout"):
            self.hud_size_readout.value = size_str
        self._schedule_ui_update()

    def _safe_ui_update(self):
        try:
            tokens = self.tokens
            is_completed = self.transfer_state == "completed"
            is_error = self.transfer_state == "error"

            if is_completed:
                self.txt_percent_val.value = "100"
                self.pbar_inner.width = 385.0
                self.pbar_inner.bgcolor = tokens["green"]
                self.status_descriptor.value = "TRANSFER COMPLETED SUCCESSFULLY!"
                self.status_descriptor.color = tokens["green"]
                self.view_title.value = "TRANSFER COMPLETE"
                if hasattr(self, "live_badge") and hasattr(self.live_badge, "content"):
                    self.live_badge.content.controls[1].value = "DONE"
                    self.live_badge.bgcolor = tokens["green"]
            elif is_error:
                self.status_descriptor.value = "TRANSFER FAILED // DISCONNECTED"
                self.status_descriptor.color = tokens["red"]
                self.view_title.value = "TRANSFER FAILED"
                if hasattr(self, "live_badge") and hasattr(self.live_badge, "content"):
                    self.live_badge.content.controls[1].value = "ERR"
                    self.live_badge.bgcolor = tokens["red"]
            elif self.is_paused:
                self.txt_percent_val.value = f"{int(self.progress_percent)}"
                bar_w = max(4.0, (self.progress_percent / 100.0) * 385.0)
                self.pbar_inner.width = bar_w
                self.status_descriptor.value = "TRANSFER PAUSED // SOCKET BUFFER ACTIVE"
                self.status_descriptor.color = tokens["yellow"]
                if hasattr(self, "live_badge") and hasattr(self.live_badge, "content"):
                    self.live_badge.content.controls[1].value = "PAUSED"
                    self.live_badge.bgcolor = tokens["yellow"]
            else:
                self.txt_percent_val.value = f"{int(self.progress_percent)}"
                bar_w = max(4.0, (self.progress_percent / 100.0) * 385.0)
                self.pbar_inner.width = bar_w
                self.status_descriptor.value = self.status_text_val
                self.status_descriptor.color = tokens["muted"]
                if hasattr(self, "live_badge") and hasattr(self.live_badge, "content"):
                    self.live_badge.content.controls[1].value = "LIVE"
                    self.live_badge.bgcolor = tokens["green_light"]

            if self.is_paused:
                self.val_speed.value = "PAUSED"
                self.val_eta.value = "--"
            else:
                self.val_speed.value = self.cur_speed_val
                self.val_eta.value = self.eta_val

            self.val_peak.value = self.peak_speed_val
            self.val_size.value = self.size_info_val
            self.hud_size_readout.value = self.size_info_val

            if self._current_action_state != self.transfer_state:
                self.update_action_buttons()

            try:
                self.update()
            except Exception:
                try:
                    self.page_ref.update()
                except Exception:
                    pass
        except Exception:
            pass

    def _schedule_ui_update(self):
        loop = getattr(self.page_ref, "loop", None) or self.main_loop
        if loop is None or not loop.is_running():
            try:
                loop = asyncio.get_running_loop()
                self.main_loop = loop
            except Exception:
                loop = None

        if loop and loop.is_running():
            try:
                loop.call_soon_threadsafe(self._safe_ui_update)
                return
            except Exception:
                pass
        self._safe_ui_update()

    def on_status(self, msg):
        self.status_text_val = msg.upper()
        self._schedule_ui_update()

    def on_progress(self, percent, cur_speed, avg_speed, peak_speed, size_info, eta_str="--", elapsed_str="--"):
        is_completed = percent >= 100.0
        self.transfer_state = "completed" if is_completed else "transferring"
        self.progress_percent = percent
        self.cur_speed_val = cur_speed
        self.avg_speed_val = avg_speed
        self.peak_speed_val = peak_speed
        self.size_info_val = size_info
        self.eta_val = eta_str
        self.elapsed_val = elapsed_str

        now = time.time()
        if not is_completed and (now - self._last_ui_update < 0.12):
            return
        self._last_ui_update = now

        self._schedule_ui_update()

    def on_complete(self, success, details_or_path=None):
        if success:
            self.transfer_state = "completed"
            self.progress_percent = 100.0
            self.status_text_val = "TRANSFER COMPLETED SUCCESSFULLY!"
            if details_or_path:
                self.received_filepath = details_or_path
            elif not self.received_filepath and self.item_name:
                cand = os.path.join(config.DOWNLOADS_DIR, self.item_name)
                if os.path.exists(cand):
                    self.received_filepath = cand
        else:
            self.transfer_state = "error"
            self.status_text_val = "TRANSFER INTERRUPTED"
        self._schedule_ui_update()

    def handle_cancel(self, e):
        if self.on_cancel_cb:
            self.on_cancel_cb()

    def handle_done(self, e):
        if self.on_done_cb:
            self.on_done_cb()

    def handle_open_file(self, e):
        path = self.received_filepath
        if not path and self.item_name:
            cand = os.path.join(config.DOWNLOADS_DIR, self.item_name)
            if os.path.exists(cand):
                path = cand
        if not path:
            path = config.DOWNLOADS_DIR
        open_file_location(path)

    def dispose(self):
        pass
