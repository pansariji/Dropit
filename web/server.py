import http.server
import socket
import socketserver
import threading
import urllib.parse
import os
import time
import tempfile
import zipfile

import config
from utils import get_local_ip, format_size, format_time, TransferMetricsTracker, optimize_tcp_socket
from web.templates import MOBILE_UPLOAD_HTML_PAGE, MOBILE_DOWNLOAD_HTML_PAGE

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True

class DropItHTTPHandler(http.server.BaseHTTPRequestHandler):
    """
    HTTP request handler serving mobile web interfaces for uploading files/folders
    to the laptop or downloading shared items from the laptop.
    """
    def log_message(self, format, *args):
        """Suppresses default HTTP server stdout logging."""
        pass

    def send_cors_headers(self):
        """Adds CORS and cache headers for universal browser compatibility (Brave, Opera, Chrome, Safari)."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'X-Relative-Path, Content-Type, Content-Length')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')

    def do_OPTIONS(self):
        """Handles HTTP OPTIONS preflight requests sent by privacy-focused browsers like Brave and Opera."""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handles HTTP GET requests for rendering web pages or streaming downloads."""
        if hasattr(self.server, 'web_receiver'):
            self._handle_receiver_get()
        elif hasattr(self.server, 'web_sender'):
            self._handle_sender_get()
        else:
            self.send_error(404, "Not Found")

    def _handle_receiver_get(self):
        """Serves the Neo-Brutalist upload web interface to mobile browsers."""
        if self.path in ('/', '/index.html'):
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(MOBILE_UPLOAD_HTML_PAGE.encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

    def _handle_sender_get(self):
        """Dispatches GET requests in sender mode (page preview or binary download stream)."""
        ws = self.server.web_sender

        # Wait briefly for background folder compression if archive is being generated
        while ws.running and not ws.ready:
            time.sleep(0.1)

        if not ws.running or not ws.ready or not ws.serve_path:
            self.send_error(503, "Archive compression in progress. Please refresh in a moment.")
            return

        if self.path in ('/', '/index.html'):
            self._render_sender_page(ws)
        elif self.path == '/download':
            self._stream_download(ws)
        else:
            self.send_error(404, "Not Found")

    def _render_sender_page(self, ws):
        """Renders the Neo-Brutalist download landing page populated with staged asset metadata."""
        item_name = os.path.basename(ws.target_filename)
        item_size = format_size(ws.file_size)
        icon = "📦" if ws.is_dir else "📄"
        item_type = "Folder (.zip)" if ws.is_dir else "Payload"

        page = (
            MOBILE_DOWNLOAD_HTML_PAGE
            .replace("{{ICON}}", icon)
            .replace("{{ITEM_NAME}}", item_name)
            .replace("{{ITEM_SIZE}}", item_size)
            .replace("{{ITEM_TYPE}}", item_type)
        )
        self.send_response(200)
        self.send_cors_headers()
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(page.encode('utf-8'))

    def _stream_download(self, ws):
        """Streams the requested payload or zip archive chunk-by-chunk to the client."""
        sent = 0
        start_time = time.time()
        try:
            file_path = ws.serve_path
            filename = os.path.basename(ws.target_filename)

            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(ws.file_size))
            self.end_headers()

            optimize_tcp_socket(self.connection)
            last_update = start_time
            last_sent = 0

            with open(file_path, 'rb', buffering=config.DISK_BUFFER_SIZE) as f:
                while sent < ws.file_size and ws.running:
                    if not ws.pause_event.wait(timeout=0.2):
                        continue
                    if not ws.running:
                        break
                    chunk = f.read(config.CHUNK_SIZE_WEB)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    sent += len(chunk)

                    now = time.time()
                    if now - last_update > 0.1:
                        ws.notify_progress(sent, ws.file_size, now - last_update, sent - last_sent)
                        last_update = now
                        last_sent = sent

            try:
                self.wfile.flush()
            except Exception:
                pass

            if sent >= ws.file_size:
                ws.notify_progress(ws.file_size, ws.file_size, max(time.time() - start_time, 0.001), ws.file_size - last_sent)
                ws.notify_complete(True)
            elif sent > 0:
                ws.notify_complete(False)

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, socket.error):
            if sent >= ws.file_size:
                ws.notify_complete(True)
            elif sent > 0:
                ws.notify_complete(False)
        except Exception as e:
            if sent >= ws.file_size:
                ws.notify_complete(True)
            else:
                if sent > 0:
                    ws.notify_complete(False)
                try:
                    self.send_error(500, f"Download Error: {e}")
                except Exception:
                    pass

    def do_POST(self):
        """Dispatches HTTP POST requests for upload streaming and transfer cancellation."""
        if hasattr(self.server, 'web_receiver'):
            if self.path == '/cancel':
                self._handle_cancel()
                return
            elif self.path == '/upload':
                self._handle_upload()
                return
        self.send_error(404, "Not Found")

    def _handle_cancel(self):
        """Processes mobile client transfer cancellation and responds with JSON confirmation."""
        try:
            if self.server.web_receiver:
                self.server.web_receiver.notify_cancelled("Upload cancelled by mobile client")
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "cancelled"}')
        except Exception as e:
            self.send_error(500, f"Server Error: {e}")

    def _cleanup_partial_file(self, target_path, received, content_len):
        """Removes incomplete or corrupted partial files from disk upon client abort or error."""
        if target_path and os.path.exists(target_path) and received < content_len:
            try:
                os.remove(target_path)
            except Exception:
                pass

    def _handle_upload(self):
        """Streams incoming multipart/octet upload chunk-by-chunk to the downloads directory."""
        target_path = None
        received = 0
        content_len = 0
        try:
            raw_relpath = self.headers.get('X-Relative-Path', '')
            rel_path = urllib.parse.unquote(raw_relpath) if raw_relpath else "uploaded_file"
            content_len = int(self.headers.get('Content-Length', 0))

            downloads_dir = self.server.web_receiver.downloads_dir
            parts = rel_path.split('/')
            target_path = os.path.join(downloads_dir, *parts)

            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            if self.server.web_receiver.on_status:
                self.server.web_receiver.on_status(f"Receiving {os.path.basename(rel_path)} ({format_size(content_len)})")

            optimize_tcp_socket(self.connection)
            start_time = time.time()
            last_update = start_time
            last_received = 0

            with open(target_path, 'wb', buffering=config.DISK_BUFFER_SIZE) as f:
                while received < content_len and self.server.web_receiver.running:
                    if not self.server.web_receiver.pause_event.wait(timeout=0.2):
                        continue
                    if not self.server.web_receiver.running:
                        break
                    chunk_size = min(config.CHUNK_SIZE_WEB, content_len - received)
                    chunk = self.rfile.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)

                    now = time.time()
                    if now - last_update > 0.1:
                        self.server.web_receiver.notify_progress(rel_path, received, content_len, now - last_update, received - last_received)
                        last_update = now
                        last_received = received

            if received >= content_len:
                self.server.web_receiver.notify_progress(rel_path, content_len, content_len, max(time.time() - start_time, 0.001), content_len - last_received)
                self.server.web_receiver.notify_complete(target_path)

                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')
            else:
                self._cleanup_partial_file(target_path, received, content_len)
                self.server.web_receiver.notify_cancelled(f"Transfer interrupted: {os.path.basename(rel_path)}")
                self.send_response(499)
                self.send_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "aborted"}')

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, socket.error):
            self._cleanup_partial_file(target_path, received, content_len)
            if hasattr(self.server, 'web_receiver') and self.server.web_receiver:
                self.server.web_receiver.notify_cancelled("Transfer aborted by client")
        except Exception as e:
            self._cleanup_partial_file(target_path, received, content_len)
            if hasattr(self.server, 'web_receiver') and self.server.web_receiver:
                self.server.web_receiver.notify_cancelled(f"Upload error: {e}")
            try:
                self.send_error(500, f"Server Error: {e}")
            except Exception:
                pass


class WebReceiver:
    """
    HTTP Web Receiver server enabling mobile browser users to upload files/folders directly to the laptop.
    """
    def __init__(self, port=config.DEFAULT_WEB_PORT, on_status_callback=None, on_progress_callback=None, on_complete_callback=None):
        self.port = port
        self.on_status = on_status_callback
        self.on_progress = on_progress_callback
        self.on_complete = on_complete_callback
        
        self.local_ip = get_local_ip()
        self.url = f"http://{self.local_ip}:{self.port}"
        
        self.running = False
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.httpd = None
        self.tracker = TransferMetricsTracker()
        
        self.downloads_dir = config.DOWNLOADS_DIR
        if not os.path.exists(self.downloads_dir):
            os.makedirs(self.downloads_dir)

    def pause(self):
        """Pauses the active receiving stream."""
        self.pause_event.clear()
        if hasattr(self, 'tracker') and self.tracker:
            self.tracker.pause()

    def resume(self):
        """Resumes the active receiving stream."""
        self.pause_event.set()
        if hasattr(self, 'tracker') and self.tracker:
            self.tracker.resume()

    def start(self):
        """Starts the HTTP server on an available port in a background daemon thread."""
        self.running = True
        self.pause_event.set()
        self.tracker.reset()
        socketserver.TCPServer.allow_reuse_address = True
        while self.running:
            try:
                self.httpd = ThreadedHTTPServer(('0.0.0.0', self.port), DropItHTTPHandler)
                optimize_tcp_socket(self.httpd.socket)
                self.httpd.web_receiver = self
                break
            except OSError:
                self.port += 1
                self.url = f"http://{self.local_ip}:{self.port}"
                
        if self.on_status:
            self.on_status(f"Web Receiver active at {self.url}")
            
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self):
        """Shuts down the HTTP server."""
        self.running = False
        self.pause_event.set()
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception:
                pass

    def notify_progress(self, rel_path, received, total, elapsed, bytes_diff):
        """Reports transfer progress percentage and speed metrics."""
        metrics = self.tracker.update(received, total, elapsed, bytes_diff)
        if self.on_progress:
            self.on_progress(
                metrics["percent"],
                metrics["cur_speed_str"],
                metrics["avg_speed_str"],
                metrics["peak_speed_str"],
                metrics["size_info_str"],
                metrics["eta_str"],
                metrics["elapsed_str"]
            )
        if self.on_status:
            self.on_status(f"Receiving {rel_path} ({format_size(received)} / {format_size(total)})")

    def notify_complete(self, filepath):
        """Triggers transfer completion callbacks."""
        if self.on_progress:
            tot = self.tracker.last_bytes
            rec = tot
            metrics = self.tracker.update(rec, tot)
            self.on_progress(100.0, "Done", metrics["avg_speed_str"], metrics["peak_speed_str"], metrics["size_info_str"], "0s", metrics["elapsed_str"])
        if self.on_status:
            self.on_status(f"Saved: {os.path.basename(filepath)}")
        if self.on_complete:
            try:
                self.on_complete(True, filepath)
            except TypeError:
                try:
                    self.on_complete(filepath)
                except Exception:
                    pass
            except Exception:
                pass

    def notify_cancelled(self, reason="Transfer Cancelled"):
        """Triggers transfer cancellation callbacks and notifies the UI."""
        if self.on_status:
            self.on_status(reason)
        if self.on_complete:
            try:
                self.on_complete(False, reason)
            except TypeError:
                try:
                    self.on_complete(False)
                except Exception:
                    pass
            except Exception:
                pass


class WebSender:
    """
    HTTP Web Sender server enabling mobile browser users to download shared files/folders from the laptop.
    Automatically compresses shared folders into temporary ZIP archives in a background thread to keep GUI smooth.
    """
    def __init__(self, shared_path, port=config.DEFAULT_WEB_PORT, on_status_callback=None, on_progress_callback=None, on_complete_callback=None):
        self.shared_path = shared_path
        self.port = port
        self.on_status = on_status_callback
        self.on_progress = on_progress_callback
        self.on_complete = on_complete_callback

        self.local_ip = get_local_ip()
        self.url = f"http://{self.local_ip}:{self.port}"

        self.running = False
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.ready = False
        self.error = None
        self.httpd = None
        self.shared_path = shared_path
        self.is_dir = os.path.isdir(shared_path)

        if self.is_dir:
            base_name = os.path.basename(os.path.normpath(shared_path))
            self.target_filename = f"{base_name}.zip"
            self.serve_path = None
            self.file_size = 0
            self.ready = False
        else:
            self.serve_path = shared_path
            self.target_filename = os.path.basename(shared_path)
            self.file_size = os.path.getsize(shared_path)
            self.ready = True

        self.temp_zip_path = None
        self.tracker = TransferMetricsTracker()

    def pause(self):
        """Pauses the active sending stream."""
        self.pause_event.clear()
        if hasattr(self, 'tracker') and self.tracker:
            self.tracker.pause()

    def resume(self):
        """Resumes the active sending stream."""
        self.pause_event.set()
        if hasattr(self, 'tracker') and self.tracker:
            self.tracker.resume()

    def start(self):
        """Starts the HTTP server serving the shared asset on an available port."""
        self.running = True
        self.pause_event.set()
        self.tracker.reset()
        socketserver.TCPServer.allow_reuse_address = True
        while self.running:
            try:
                self.httpd = ThreadedHTTPServer(('0.0.0.0', self.port), DropItHTTPHandler)
                optimize_tcp_socket(self.httpd.socket)
                self.httpd.web_sender = self
                break
            except OSError:
                self.port += 1
                self.url = f"http://{self.local_ip}:{self.port}"

        if self.is_dir:
            def _prepare_zip():
                if self.on_status:
                    self.on_status("Packaging folder for mobile web sharing...")
                try:
                    base_name = os.path.basename(os.path.normpath(self.shared_path))
                    temp_dir = tempfile.gettempdir()
                    zip_path = os.path.join(temp_dir, f"dropit_{base_name}.zip")
                    
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zipf:
                        for root, dirs, files in os.walk(self.shared_path):
                            for file in files:
                                abs_path = os.path.join(root, file)
                                rel_path = os.path.relpath(abs_path, self.shared_path)
                                zipf.write(abs_path, rel_path)

                    self.temp_zip_path = zip_path
                    self.serve_path = self.temp_zip_path
                    self.file_size = os.path.getsize(self.temp_zip_path)
                    self.ready = True
                    if self.on_status:
                        self.on_status(f"Sharing via Web at {self.url}")
                except Exception as e:
                    self.error = str(e)
                    self.ready = True
                    if self.on_status:
                        self.on_status(f"Zip Error: {e}")

            threading.Thread(target=_prepare_zip, daemon=True).start()
        else:
            if self.on_status:
                self.on_status(f"Sharing via Web at {self.url}")

        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self):
        """Shuts down the HTTP server and removes any temporary ZIP archive created for directory sharing."""
        self.running = False
        if self.httpd:
            try:
                self.httpd.shutdown()
                self.httpd.server_close()
            except Exception:
                pass
        if self.temp_zip_path and os.path.exists(self.temp_zip_path):
            try:
                os.remove(self.temp_zip_path)
            except Exception:
                pass

    def notify_progress(self, sent, total, elapsed, bytes_diff):
        """Reports transfer progress percentage and transfer speed metrics."""
        metrics = self.tracker.update(sent, total, elapsed, bytes_diff)
        if self.on_progress:
            self.on_progress(
                metrics["percent"],
                metrics["cur_speed_str"],
                metrics["avg_speed_str"],
                metrics["peak_speed_str"],
                metrics["size_info_str"],
                metrics["eta_str"],
                metrics["elapsed_str"]
            )
        if self.on_status:
            self.on_status(f"Sending {self.target_filename} ({format_size(sent)} / {format_size(total)})")

    def notify_complete(self, success):
        """Triggers transfer completion callbacks."""
        if self.on_progress and success:
            metrics = self.tracker.update(self.file_size, self.file_size)
            self.on_progress(100.0, "Done", metrics["avg_speed_str"], metrics["peak_speed_str"], metrics["size_info_str"], "0s", metrics["elapsed_str"])
        if self.on_status:
            self.on_status("Transfer complete!" if success else "Transfer failed.")
        if self.on_complete:
            self.on_complete(success)

