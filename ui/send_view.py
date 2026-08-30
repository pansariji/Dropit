import flet as ft
import os
import config
from utils import get_local_ip, format_size, generate_qr_image, pil_to_b64
from p2p.client import Sender
from web.server import WebSender

class SendView(ft.Container):
    """
    Send Screen for DropIt.
    Provides:
      - File & Folder Selection via FilePicker & Drag & Drop Target
      - Mobile Transfer Mode (QR code Web Sender for Mobile Download)
      - PC Transfer Mode (Passcode & IP fields for binary P2P stream)
      - Real-time performance dashboard with progress, speed, ETA, and post-transfer summary.
    """
    def __init__(self, page: ft.Page, on_back):
        super().__init__(expand=True)
        self.page_ref = page
        self.on_back = on_back

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

        # Metrics state
        self.transfer_state = "idle"  # "idle", "transferring", "completed", "error"
        self.status_text_val = "Select a file or folder to start"
        self.progress_percent = 0.0
        self.cur_speed_val = "--"
        self.avg_speed_val = "--"
        self.peak_speed_val = "--"
        self.size_info_val = "--"
        self.eta_val = "--"
        self.elapsed_val = "--"

        # Setup Flet FilePicker control
        self.file_picker = ft.FilePicker()
        if self.file_picker not in self.page_ref.services:
            self.page_ref.services.append(self.file_picker)

        self.build_ui()

    def build_ui(self):
        tokens = self.tokens

        # Top Bar: Back Button & Title
        back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK_ROUNDED,
            icon_color=tokens["text"],
            icon_size=22,
            tooltip="Back to Home",
            on_click=self.handle_back
        )

        title_text = ft.Text(
            "Send Payload",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=tokens["text"]
        )

        top_bar = ft.Row(
            controls=[
                back_btn,
                title_text,
                ft.Container(width=40)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # File & Folder Selection Buttons + Drag Target Zone
        file_pick_btn = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.INSERT_DRIVE_FILE_ROUNDED, size=16, color=tokens["text"]),
                    ft.Text("Select File", size=12, weight=ft.FontWeight.W_600, color=tokens["text"])
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            ),
            style=ft.ButtonStyle(
                bgcolor=tokens["card_alt"],
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(left=0, top=10, right=0, bottom=10)
            ),
            on_click=self.pick_file,
            expand=True
        )

        folder_pick_btn = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FOLDER_ROUNDED, size=16, color=tokens["text"]),
                    ft.Text("Select Folder", size=12, weight=ft.FontWeight.W_600, color=tokens["text"])
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            ),
            style=ft.ButtonStyle(
                bgcolor=tokens["card_alt"],
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(left=0, top=10, right=0, bottom=10)
            ),
            on_click=self.pick_folder,
            expand=True
        )

        # Drag and Drop Target Zone
        self.drop_target_content = ft.Column(
            controls=[
                ft.Icon(ft.Icons.CLOUD_UPLOAD_ROUNDED, size=32, color=tokens["green"]),
                ft.Text("Drag & Drop File or Folder Here", size=13, weight=ft.FontWeight.BOLD, color=tokens["text"]),
                ft.Text("or click buttons above to browse", size=11, color=tokens["muted"])
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=4
        )

        self.drop_zone = ft.DragTarget(
            group="drop_files",
            content=ft.Container(
                content=self.drop_target_content,
                border_radius=12,
                border=ft.Border.all(1, tokens["border"]),
                bgcolor=tokens["card"],
                padding=14,
                alignment=ft.Alignment.CENTER
            ),
            on_accept=self.handle_drag_drop
        )

        # Mode Selection Buttons (PC Transfer vs Mobile Transfer)
        self.pc_mode_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.COMPUTER_ROUNDED, size=16),
                    ft.Text("PC Transfer", size=12, weight=ft.FontWeight.W_600)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            ),
            padding=ft.Padding(left=12, top=8, right=12, bottom=8),
            border_radius=8,
            on_click=lambda e: self.switch_mode("pc")
        )

        self.mobile_mode_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PHONE_ANDROID_ROUNDED, size=16),
                    ft.Text("Mobile Transfer", size=12, weight=ft.FontWeight.W_600)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            ),
            padding=ft.Padding(left=12, top=8, right=12, bottom=8),
            border_radius=8,
            on_click=lambda e: self.switch_mode("mobile")
        )

        mode_tabs = ft.Container(
            content=ft.Row(
                controls=[self.pc_mode_btn, self.mobile_mode_btn],
                alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                expand=True
            ),
            bgcolor=tokens["card_alt"],
            border_radius=10,
            padding=3
        )

        # Dynamic Options Container (Passcode & IP fields OR Mobile QR)
        self.options_container = ft.Container(
            border_radius=12,
            bgcolor=tokens["card"],
            border=ft.Border.all(1, tokens["border"]),
            padding=14
        )

        # Metrics Card Container
        self.metrics_container = ft.Container(
            border_radius=12,
            bgcolor=tokens["card"],
            border=ft.Border.all(1, tokens["border"]),
            padding=14
        )

        # PC Transfer Inputs
        self.passcode_input = ft.TextField(
            label="4-Digit Receiver Passcode",
            hint_text="e.g. 4819",
            text_size=13,
            label_style=ft.TextStyle(size=12, color=tokens["muted"]),
            border_color=tokens["border"],
            focused_border_color=tokens["green"],
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, color=tokens["text"]),
            dense=True,
            max_length=4
        )

        self.ip_input = ft.TextField(
            label="Receiver IP (Optional)",
            hint_text="Leave blank to auto-scan local network",
            text_size=12,
            label_style=ft.TextStyle(size=12, color=tokens["muted"]),
            border_color=tokens["border"],
            focused_border_color=tokens["green"],
            text_style=ft.TextStyle(color=tokens["text"]),
            dense=True
        )

        self.send_btn = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SEND_ROUNDED, size=18, color=tokens["btn_primary_fg"]),
                    ft.Text("Send Now", size=14, weight=ft.FontWeight.BOLD, color=tokens["btn_primary_fg"])
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=6
            ),
            style=ft.ButtonStyle(
                bgcolor=tokens["btn_primary_bg"],
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=ft.Padding(left=0, top=14, right=0, bottom=14)
            ),
            on_click=self.start_p2p_send,
            expand=True
        )

        self.update_mode_tabs_ui()
        self.update_options_container_ui()
        self.update_metrics_ui()

        self.bgcolor = tokens["bg"]
        self.padding = ft.Padding(left=18, top=14, right=18, bottom=14)
        self.content = ft.Column(
            controls=[
                top_bar,
                ft.Row(controls=[file_pick_btn, folder_pick_btn], spacing=10),
                ft.Container(height=4),
                self.drop_zone,
                ft.Container(height=6),
                mode_tabs,
                ft.Container(height=6),
                self.options_container,
                ft.Container(height=6),
                ft.Container(content=self.metrics_container, expand=True)
            ],
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def update_selected_item_ui(self):
        tokens = self.tokens
        if not self.selected_path:
            self.drop_target_content.controls = [
                ft.Icon(ft.Icons.CLOUD_UPLOAD_ROUNDED, size=32, color=tokens["green"]),
                ft.Text("Drag & Drop File or Folder Here", size=13, weight=ft.FontWeight.BOLD, color=tokens["text"]),
                ft.Text("or click buttons above to browse", size=11, color=tokens["muted"])
            ]
        else:
            icon = ft.Icons.FOLDER_ROUNDED if self.is_folder else ft.Icons.INSERT_DRIVE_FILE_ROUNDED
            self.drop_target_content.controls = [
                ft.Row(
                    controls=[
                        ft.Icon(icon, size=24, color=tokens["green"]),
                        ft.Column(
                            controls=[
                                ft.Text(self.selected_name, size=13, weight=ft.FontWeight.BOLD, color=tokens["text"], overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(f"{'Folder' if self.is_folder else 'File'} • {self.selected_size_str}", size=11, color=tokens["muted"])
                            ],
                            spacing=1,
                            expand=True
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )
            ]
        try:
            self.drop_zone.content.update()
        except Exception:
            pass

    def update_mode_tabs_ui(self):
        tokens = self.tokens
        if self.active_mode == "pc":
            self.pc_mode_btn.bgcolor = tokens["btn_primary_bg"]
            self.pc_mode_btn.content.controls[0].color = tokens["btn_primary_fg"]
            self.pc_mode_btn.content.controls[1].color = tokens["btn_primary_fg"]

            self.mobile_mode_btn.bgcolor = ft.Colors.TRANSPARENT
            self.mobile_mode_btn.content.controls[0].color = tokens["muted"]
            self.mobile_mode_btn.content.controls[1].color = tokens["muted"]
        else:
            self.mobile_mode_btn.bgcolor = tokens["btn_primary_bg"]
            self.mobile_mode_btn.content.controls[0].color = tokens["btn_primary_fg"]
            self.mobile_mode_btn.content.controls[1].color = tokens["btn_primary_fg"]

            self.pc_mode_btn.bgcolor = ft.Colors.TRANSPARENT
            self.pc_mode_btn.content.controls[0].color = tokens["muted"]
            self.pc_mode_btn.content.controls[1].color = tokens["muted"]

    def update_options_container_ui(self):
        tokens = self.tokens
        if self.active_mode == "pc":
            self.options_container.content = ft.Column(
                controls=[
                    self.passcode_input,
                    self.ip_input,
                    ft.Container(height=4),
                    self.send_btn
                ],
                spacing=8
            )
        else:
            # Mobile Transfer Mode (QR code Web Sender)
            if not self.selected_path:
                self.options_container.content = ft.Column(
                    controls=[
                        ft.Text("Select a file or folder above to generate Mobile Download QR", size=12, color=tokens["muted"], text_align=ft.TextAlign.CENTER)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
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
                qr_img = generate_qr_image(url, fg_color=tokens["text"], bg_color=tokens["card"])
                qr_b64 = pil_to_b64(qr_img)

                qr_widget = ft.Image(
                    src=f"data:image/png;base64,{qr_b64}",
                    width=130,
                    height=130,
                    fit=ft.BoxFit.CONTAIN
                ) if qr_b64 else ft.Container(height=130, width=130)

                self.options_container.content = ft.Column(
                    controls=[
                        ft.Text("Scan QR on Mobile to Download", size=12, weight=ft.FontWeight.W_600, color=tokens["text"]),
                        qr_widget,
                        ft.Container(
                            content=ft.Text(url, size=11, weight=ft.FontWeight.BOLD, color=tokens["green"]),
                            bgcolor=tokens["card_alt"],
                            border_radius=6,
                            padding=ft.Padding(left=10, top=3, right=10, bottom=3)
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=2
                )

    def update_metrics_ui(self):
        tokens = self.tokens

        pbar = ft.ProgressBar(
            value=self.progress_percent / 100.0,
            color=tokens["green"],
            bgcolor=tokens["card_alt"],
            height=8
        )

        percent_text = ft.Text(
            f"{self.progress_percent:.1f}%",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=tokens["text"]
        )

        status_text = ft.Text(
            self.status_text_val,
            size=12,
            weight=ft.FontWeight.W_500,
            color=tokens["muted"],
            overflow=ft.TextOverflow.ELLIPSIS
        )

        if self.transfer_state == "completed":
            metrics_grid = ft.Row(
                controls=[
                    self._build_metric_tile("Size", self.size_info_val),
                    self._build_metric_tile("Avg Speed", self.avg_speed_val),
                    self._build_metric_tile("Peak Speed", self.peak_speed_val),
                    self._build_metric_tile("Time Taken", self.elapsed_val),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND
            )

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
                    pbar,
                    ft.Container(height=8),
                    metrics_grid
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4
            )

        elif self.transfer_state == "transferring":
            metrics_grid = ft.Row(
                controls=[
                    self._build_metric_tile("Size", self.size_info_val),
                    self._build_metric_tile("Speed", self.cur_speed_val),
                    self._build_metric_tile("Peak", self.peak_speed_val),
                    self._build_metric_tile("ETA", self.eta_val),
                ],
                alignment=ft.MainAxisAlignment.SPACE_AROUND
            )

            self.metrics_container.content = ft.Column(
                controls=[
                    ft.Row(
                        controls=[status_text, percent_text],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Container(height=4),
                    pbar,
                    ft.Container(height=8),
                    metrics_grid
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4
            )
        else:
            self.metrics_container.content = ft.Column(
                controls=[
                    ft.Text(self.status_text_val, size=12, weight=ft.FontWeight.W_500, color=tokens["muted"], text_align=ft.TextAlign.CENTER)
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )

    def _build_metric_tile(self, label, value):
        tokens = self.tokens
        return ft.Column(
            controls=[
                ft.Text(label, size=10, weight=ft.FontWeight.W_600, color=tokens["muted"]),
                ft.Text(value, size=12, weight=ft.FontWeight.BOLD, color=tokens["text"])
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2
        )

    async def pick_file(self, e):
        res = await self.file_picker.pick_files(dialog_title="Select File to Send")
        if res and len(res) > 0:
            file_obj = res[0]
            self.selected_path = file_obj.path
            self.selected_name = os.path.basename(file_obj.path)
            self.is_folder = False
            try:
                self.selected_size_str = format_size(os.path.getsize(file_obj.path))
            except Exception:
                self.selected_size_str = "--"
            self.update_selected_item_ui()
            if self.active_mode == "mobile":
                self.restart_web_sender()

    async def pick_folder(self, e):
        path = await self.file_picker.get_directory_path(dialog_title="Select Folder to Send")
        if path:
            self.selected_path = path
            self.selected_name = os.path.basename(path) or "Folder"
            self.is_folder = True
            try:
                total_size = sum(os.path.getsize(os.path.join(r, f)) for r, d, files in os.walk(path) for f in files)
                self.selected_size_str = format_size(total_size)
            except Exception:
                self.selected_size_str = "--"
            self.update_selected_item_ui()
            if self.active_mode == "mobile":
                self.restart_web_sender()

    def handle_drag_drop(self, e: ft.DragTargetEvent):
        if e.data:
            path = e.data.strip('"').strip("'")
            if os.path.exists(path):
                self.selected_path = path
                self.selected_name = os.path.basename(path) or "Item"
                self.is_folder = os.path.isdir(path)
                if self.is_folder:
                    try:
                        total_size = sum(os.path.getsize(os.path.join(r, f)) for r, d, files in os.walk(path) for f in files)
                        self.selected_size_str = format_size(total_size)
                    except Exception:
                        self.selected_size_str = "--"
                else:
                    try:
                        self.selected_size_str = format_size(os.path.getsize(path))
                    except Exception:
                        self.selected_size_str = "--"

                self.update_selected_item_ui()
                if self.active_mode == "mobile":
                    self.restart_web_sender()

    def switch_mode(self, mode):
        if self.active_mode == mode:
            return
        self.active_mode = mode
        self.stop_senders()
        self.transfer_state = "idle"
        self.progress_percent = 0.0
        self.update_mode_tabs_ui()
        self.update_options_container_ui()
        self.update_metrics_ui()

    def restart_web_sender(self):
        self.stop_senders()
        self.update_options_container_ui()

    def start_p2p_send(self, e):
        if not self.selected_path:
            self.status_text_val = "Please select a file or folder first"
            self.update_metrics_ui()
            return

        passcode = self.passcode_input.value.strip() if self.passcode_input.value else ""
        if not passcode or len(passcode) != 4 or not passcode.isdigit():
            self.status_text_val = "Please enter a valid 4-digit passcode"
            self.update_metrics_ui()
            return

        target_ip = self.ip_input.value.strip() if self.ip_input.value else None

        self.stop_senders()
        self.transfer_state = "transferring"
        self.progress_percent = 0.0

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

    def on_status(self, msg):
        self.status_text_val = msg
        try:
            self.update_metrics_ui()
            self.page_ref.update()
        except Exception:
            pass

    def on_progress(self, percent, cur_speed, avg_speed, peak_speed, size_info, eta_str="--", elapsed_str="--"):
        self.transfer_state = "completed" if percent >= 100.0 else "transferring"
        self.progress_percent = percent
        self.cur_speed_val = cur_speed
        self.avg_speed_val = avg_speed
        self.peak_speed_val = peak_speed
        self.size_info_val = size_info
        self.eta_val = eta_str
        self.elapsed_val = elapsed_str
        try:
            self.update_metrics_ui()
            self.page_ref.update()
        except Exception:
            pass

    def on_complete(self, success, details=None):
        if success:
            self.transfer_state = "completed"
        else:
            self.transfer_state = "error"
            self.status_text_val = "Transfer failed or canceled"
        try:
            self.update_metrics_ui()
            self.page_ref.update()
        except Exception:
            pass

    def handle_back(self, e):
        self.stop_senders()
        self.on_back()
