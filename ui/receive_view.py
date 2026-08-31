import flet as ft
import os
import time
import subprocess
import config
from utils import get_local_ip, generate_passcode, generate_qr_image, pil_to_b64
from p2p.server import Receiver
from web.server import WebReceiver

class ReceiveView(ft.Container):
    """
    Receive Screen for DropIt.
    Provides 2 selection modes:
      1) Mobile (QR code for Web HTTP server upload)
      2) PC (4-digit passcode & Local IP for binary P2P stream)
    Displays live performance metrics during transfer and post-transfer summary with "Show Received File".
    """
    def __init__(self, page: ft.Page, on_back):
        super().__init__(expand=True)
        self.page_ref = page
        self.on_back = on_back

        self.is_dark = page.theme_mode == ft.ThemeMode.DARK
        self.tokens = config.THEME_DARK if self.is_dark else config.THEME_LIGHT

        # State Variables
        self.active_mode = "mobile"  # "mobile" or "pc"
        self.passcode = generate_passcode()
        self.local_ip = get_local_ip()
        
        # Engine instances
        self.p2p_receiver = None
        self.web_receiver = None

        # Metrics state
        self.transfer_state = "idle"  # "idle", "transferring", "completed", "error"
        self.received_filepath = None
        self.status_text_val = "Select mode to start receiving"
        self.progress_percent = 0.0
        self.cur_speed_val = "--"
        self.avg_speed_val = "--"
        self.peak_speed_val = "--"
        self.size_info_val = "--"
        self.eta_val = "--"
        self.elapsed_val = "--"

        # UI state and rate-limiting
        self._last_ui_update = 0.0
        self._rendered_metrics_state = None

        # Persistent UI controls for metrics dashboard
        tokens = self.tokens
        self.pbar = ft.ProgressBar(
            value=0.0,
            color=tokens["green"],
            bgcolor=tokens["card_alt"],
            height=8
        )
        self.percent_text = ft.Text(
            "0.0%",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=tokens["text"]
        )
        self.status_text = ft.Text(
            self.status_text_val,
            size=12,
            weight=ft.FontWeight.W_500,
            color=tokens["muted"],
            overflow=ft.TextOverflow.ELLIPSIS
        )
        self.lbl_size = ft.Text("Size", size=10, weight=ft.FontWeight.W_600, color=tokens["muted"])
        self.val_size = ft.Text("--", size=12, weight=ft.FontWeight.BOLD, color=tokens["text"])
        self.lbl_speed = ft.Text("Speed", size=10, weight=ft.FontWeight.W_600, color=tokens["muted"])
        self.val_speed = ft.Text("--", size=12, weight=ft.FontWeight.BOLD, color=tokens["text"])
        self.lbl_peak = ft.Text("Peak", size=10, weight=ft.FontWeight.W_600, color=tokens["muted"])
        self.val_peak = ft.Text("--", size=12, weight=ft.FontWeight.BOLD, color=tokens["text"])
        self.lbl_time = ft.Text("ETA", size=10, weight=ft.FontWeight.W_600, color=tokens["muted"])
        self.val_time = ft.Text("--", size=12, weight=ft.FontWeight.BOLD, color=tokens["text"])

        self.tile_size = ft.Column(controls=[self.lbl_size, self.val_size], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
        self.tile_speed = ft.Column(controls=[self.lbl_speed, self.val_speed], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
        self.tile_peak = ft.Column(controls=[self.lbl_peak, self.val_peak], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
        self.tile_time = ft.Column(controls=[self.lbl_time, self.val_time], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
        self.metrics_grid_row = ft.Row(
            controls=[self.tile_size, self.tile_speed, self.tile_peak, self.tile_time],
            alignment=ft.MainAxisAlignment.SPACE_AROUND
        )

        self.show_file_btn = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_OPEN_ROUNDED, size=18, color=tokens["btn_primary_fg"]),
                    ft.Text("Show Received File", size=13, weight=ft.FontWeight.BOLD, color=tokens["btn_primary_fg"])
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            ),
            style=ft.ButtonStyle(
                color=tokens["btn_primary_fg"],
                bgcolor=tokens["btn_primary_bg"],
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(left=0, top=12, right=0, bottom=12)
            ),
            on_click=self.open_received_file,
            expand=True
        )

        self.build_ui()
        self.start_mode_server()

    def build_ui(self):
        tokens = self.tokens

        # Top Bar: Back Button & Screen Title
        back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            icon_color=tokens["text"],
            icon_size=22,
            tooltip="Back to Home",
            on_click=self.handle_back
        )

        title_text = ft.Text(
            "Receive Payload",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=tokens["text"]
        )

        top_bar = ft.Row(
            controls=[
                back_btn,
                title_text,
                ft.Container(width=40)  # Balance layout
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # Mode Selector Buttons (Mobile vs PC)
        self.mobile_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PHONE_ANDROID_ROUNDED, size=18),
                    ft.Text("Mobile (QR)", size=13, weight=ft.FontWeight.W_600)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            ),
            padding=ft.Padding(left=14, top=10, right=14, bottom=10),
            border_radius=8,
            on_click=lambda e: self.switch_mode("mobile")
        )

        self.pc_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.COMPUTER_ROUNDED, size=18),
                    ft.Text("PC (Passcode)", size=13, weight=ft.FontWeight.W_600)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            ),
            padding=ft.Padding(left=14, top=10, right=14, bottom=10),
            border_radius=8,
            on_click=lambda e: self.switch_mode("pc")
        )

        mode_tabs = ft.Container(
            content=ft.Row(
                controls=[self.mobile_btn, self.pc_btn],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                expand=True
            ),
            bgcolor=tokens["card_alt"],
            border_radius=10,
            padding=4
        )

        # Dynamic Content Container (QR Code or Passcode Display)
        self.info_container = ft.Container(
            border_radius=14,
            bgcolor=tokens["card"],
            border=ft.Border.all(1, tokens["border"]),
            padding=16,
            alignment=ft.Alignment.CENTER
        )

        # Metrics Card Container
        self.metrics_container = ft.Container(
            border_radius=14,
            bgcolor=tokens["card"],
            border=ft.Border.all(1, tokens["border"]),
            padding=16
        )

        self.update_mode_tabs_ui()
        self.update_metrics_ui()

        self.bgcolor = tokens["bg"]
        self.padding = ft.Padding(left=18, top=14, right=18, bottom=14)
        self.content = ft.Column(
            controls=[
                top_bar,
                ft.Container(height=4),
                mode_tabs,
                ft.Container(height=10),
                self.info_container,
                ft.Container(height=10),
                ft.Container(content=self.metrics_container, expand=True)
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def update_mode_tabs_ui(self):
        tokens = self.tokens
        if self.active_mode == "mobile":
            self.mobile_btn.bgcolor = tokens["btn_primary_bg"]
            self.mobile_btn.content.controls[0].color = tokens["btn_primary_fg"]
            self.mobile_btn.content.controls[1].color = tokens["btn_primary_fg"]

            self.pc_btn.bgcolor = ft.Colors.TRANSPARENT
            self.pc_btn.content.controls[0].color = tokens["muted"]
            self.pc_btn.content.controls[1].color = tokens["muted"]
        else:
            self.pc_btn.bgcolor = tokens["btn_primary_bg"]
            self.pc_btn.content.controls[0].color = tokens["btn_primary_fg"]
            self.pc_btn.content.controls[1].color = tokens["btn_primary_fg"]

            self.mobile_btn.bgcolor = ft.Colors.TRANSPARENT
            self.mobile_btn.content.controls[0].color = tokens["muted"]
            self.mobile_btn.content.controls[1].color = tokens["muted"]

    def update_info_container_ui(self):
        tokens = self.tokens
        if self.active_mode == "mobile":
            url = f"http://{self.local_ip}:{config.DEFAULT_WEB_PORT}"
            if self.web_receiver and hasattr(self.web_receiver, 'url'):
                url = self.web_receiver.url

            qr_img = generate_qr_image(url, fg_color=tokens["text"], bg_color=tokens["card"])
            qr_b64 = pil_to_b64(qr_img)

            qr_widget = ft.Image(
                src=f"data:image/png;base64,{qr_b64}",
                width=160,
                height=160,
                fit=ft.BoxFit.CONTAIN
            ) if qr_b64 else ft.Container(height=160, width=160)

            self.info_container.content = ft.Column(
                controls=[
                    ft.Text("Scan QR with Mobile Phone", size=13, weight=ft.FontWeight.W_600, color=tokens["text"]),
                    ft.Container(height=4),
                    qr_widget,
                    ft.Container(height=4),
                    ft.Container(
                        content=ft.Text(url, size=12, weight=ft.FontWeight.BOLD, color=tokens["green"]),
                        bgcolor=tokens["card_alt"],
                        border_radius=8,
                        padding=ft.Padding(left=12, top=4, right=12, bottom=4)
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=2
            )
        else:
            # PC Passcode & IP Mode
            self.info_container.content = ft.Column(
                controls=[
                    ft.Text("Enter Passcode on Sender PC", size=13, weight=ft.FontWeight.W_600, color=tokens["muted"]),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Text(
                            self.passcode,
                            size=36,
                            weight=ft.FontWeight.BOLD,
                            style=ft.TextStyle(letter_spacing=6),
                            color=tokens["green"]
                        ),
                        bgcolor=tokens["card_alt"],
                        border_radius=12,
                        padding=ft.Padding(left=24, top=10, right=24, bottom=10)
                    ),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.WIFI_ROUNDED, size=16, color=tokens["muted"]),
                            ft.Text(f"Laptop IP: {self.local_ip}", size=12, weight=ft.FontWeight.W_500, color=tokens["text"])
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=4
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=2
            )

    def update_metrics_ui(self):
        tokens = self.tokens

        # In-place property mutation of persistent controls
        self.pbar.value = max(0.0, min(1.0, self.progress_percent / 100.0))
        self.percent_text.value = f"{self.progress_percent:.1f}%"
        self.status_text.value = self.status_text_val
        self.val_size.value = self.size_info_val
        self.val_peak.value = self.peak_speed_val

        if self.transfer_state == "completed":
            self.lbl_speed.value = "Avg Speed"
            self.val_speed.value = self.avg_speed_val
            self.lbl_time.value = "Time Taken"
            self.val_time.value = self.elapsed_val
        else:
            self.lbl_speed.value = "Speed"
            self.val_speed.value = self.cur_speed_val
            self.lbl_time.value = "ETA"
            self.val_time.value = self.eta_val

        # Only update metric container hierarchy when layout state changes
        if self._rendered_metrics_state != self.transfer_state:
            self._rendered_metrics_state = self.transfer_state

            if self.transfer_state == "completed":
                self.metrics_container.content = ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.CHECK_CIRCLE_ROUNDED, color=tokens["green"], size=22),
                                ft.Text("Transfer Completed!", size=15, weight=ft.FontWeight.BOLD, color=tokens["green"])
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8
                        ),
                        ft.Container(height=4),
                        self.pbar,
                        ft.Container(height=8),
                        self.metrics_grid_row,
                        ft.Container(height=12),
                        self.show_file_btn
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4
                )

            elif self.transfer_state == "transferring":
                self.metrics_container.content = ft.Column(
                    controls=[
                        ft.Row(
                            controls=[self.status_text, self.percent_text],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Container(height=4),
                        self.pbar,
                        ft.Container(height=10),
                        self.metrics_grid_row
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4
                )
            else:
                self.metrics_container.content = ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.ProgressRing(width=16, height=16, stroke_width=2, color=tokens["green"]),
                                ft.Text("Ready to receive files...", size=13, weight=ft.FontWeight.W_500, color=tokens["muted"])
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=10
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                )

    def switch_mode(self, mode):
        if self.active_mode == mode:
            return
        self.active_mode = mode
        self.stop_servers()
        self.transfer_state = "idle"
        self.progress_percent = 0.0
        self.update_mode_tabs_ui()
        self.start_mode_server()

    def start_mode_server(self):
        self.update_info_container_ui()
        self.update_metrics_ui()

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

    def on_status(self, msg):
        self.status_text_val = msg
        try:
            self.update_metrics_ui()
            self.page_ref.update()
        except Exception:
            pass

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

        # Throttle page updates to max once per ~120ms during active transfer (always update on completion)
        now = time.time()
        if not is_completed and (now - self._last_ui_update < 0.12):
            return
        self._last_ui_update = now

        try:
            self.update_metrics_ui()
            self.page_ref.update()
        except Exception:
            pass

    def on_complete(self, success, filepath=None):
        if success:
            self.transfer_state = "completed"
            self.received_filepath = filepath or config.DOWNLOADS_DIR
        else:
            self.transfer_state = "error"
            self.status_text_val = "Transfer failed or interrupted"
        try:
            self.update_metrics_ui()
            self.page_ref.update()
        except Exception:
            pass

    def open_received_file(self, e):
        path = self.received_filepath or config.DOWNLOADS_DIR
        if not os.path.exists(path):
            path = config.DOWNLOADS_DIR
            os.makedirs(path, exist_ok=True)
            
        try:
            if os.name == 'nt':
                # Windows Explorer highlight file
                if os.path.isfile(path):
                    subprocess.run(['explorer', '/select,', os.path.normpath(path)])
                else:
                    os.startfile(path)
            else:
                subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', path])
        except Exception as ex:
            print(f"Failed to open file: {ex}")

    def handle_back(self, e):
        self.stop_servers()
        self.on_back()
