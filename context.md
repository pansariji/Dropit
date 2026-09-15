# DropIt — System Context & Agent Knowledge Base

> **Notice for AI Agents & Developers**:  
> This file is the single source of truth for repository architecture, implementation patterns, runtime constraints, and ongoing roadmaps.  
> **Always consult this document before proposing or executing changes, and update it whenever making architectural modifications or adding new features.**

---

## 1. Project Overview & Identity

- **Application Name**: DropIt
- **Version**: `2.2.0` (defined in `config.py`)
- **Motto**: `FAST • SECURE • ZERO-CLOUD`
- **Core Purpose**: Ultra-fast, zero-cloud peer-to-peer file and folder sharing between PCs and mobile devices on local networks (Wi-Fi, Hotspots, LAN). No third-party servers, internet access, or cloud accounts required.
- **Git Context**: Active branch is `migration-to-flet` (migrated from legacy CustomTkinter to modern Flet).
- **Target OS**: Multi-platform (Windows, macOS, Linux).

---

## 2. Technology Stack & Dependencies

- **Language**: Python 3.10+
- **GUI Engine**: [Flet](https://flet.dev/) (`>=0.28.0`) — Flutter-backed reactive UI framework for Python.
- **QR Code Engine**: `qrcode` (`>=7.4.2`) + `Pillow` (`>=10.0.0`) for runtime rendering into base64 PNG data URLs.
- **Packaging**: `pyinstaller` (`>=6.0.0`) for compiling standalone, single-file executables (`DropIt.exe`, `DropIt-macOS`, `DropIt-Linux`).
- **Core Standard Libraries**:
  - `socket` & `threading` (Raw TCP/UDP socket streaming and concurrent worker threads)
  - `struct` (Binary protocol framing for P2P file and directory metadata)
  - `http.server` & `socketserver` (Embedded HTTP web server with custom CORS/OPTIONS handling)
  - `zipfile` & `tempfile` (On-the-fly zip packaging for mobile folder downloads)
  - `asyncio` (Thread-safe dispatching back to Flet's event loop via `call_soon_threadsafe`)

---

## 3. Codebase Directory & File Inventory

```
DropIt/
├── .github/workflows/build.yml   # Multi-platform PyInstaller CI/CD pipeline
├── assets/
│   ├── logo.ico                  # Native window & executable icon
│   └── logo.png                  # High-resolution brand logo
├── p2p/                          # Direct PC-to-PC Socket Engine
│   ├── __init__.py               # Exports Sender and Receiver
│   ├── client.py                 # UDP broadcast discovery & TCP socket streaming sender
│   └── server.py                 # UDP discovery listener & TCP socket receiver
├── web/                          # Mobile Web Browser Engine (Zero-Install)
│   ├── __init__.py               # Package marker
│   ├── server.py                 # DropItHTTPHandler, WebReceiver, and WebSender
│   └── templates.py              # Embedded HTML5/CSS3/JS mobile client interfaces
├── ui/                           # Flet Reactive UI Views
│   ├── __init__.py               # Exports HomeView, ReceiveView, SendView, TransferView
│   ├── home_view.py              # Dashboard, status badge, theme switcher, nav buttons
│   ├── receive_view.py           # Receive screen (Mobile QR & PC Passcode modes)
│   ├── send_view.py              # Send screen (FilePicker, Drag & Drop, PC & QR modes)
│   └── transfer_view.py          # Unified transfer lifecycle & real-time telemetry dashboard
├── config.py                     # Theme tokens, network ports, buffer sizes, app metadata
├── utils.py                      # Network IP detection, QR generation, metrics tracking, OS tools
├── main.py                       # Application bootstrap, window properties & view routing
├── requirements.txt              # Production dependencies
├── DESIGN.md                     # FUTURE UI roadmap specification (DropIt Utility Brutalism)
├── workflow.md                   # Detailed networking protocol & architectural flow
├── README.md                     # User-facing project documentation
└── context.md                    # THIS FILE (Persistent agent knowledge base)
```

---

## 4. Key Architectural Patterns & Constraints

### 4.1 Flet Window Lifecycle & Geometry
- Defined in `main.py` and `config.py`:
  - Fixed 2:3 aspect ratio window: **Width 460px, Height 690px**.
  - Resizable is set to `False`.
  - Icon resolved using `utils.get_resource_path("assets/logo.ico")`.
  - Zero-scroll policy: All views (`HomeView`, `SendView`, `ReceiveView`, `TransferView`) are geometrically proportioned so that zero vertical or horizontal scrollbars ever render.
  - Padding & spacing reset to `0` at page level for pixel-accurate layout control.

### 4.2 Theme Management
- Two curated neo-brutalist themes in `config.py`:
  - **Light Mode**: Warm Canvas neo-brutalist palette (`bg: #F4F4EE`, `card: #FFFFFF`, `card_alt: #FAF9F5`, `border: #000000`, `shadow: #000000`, `text: #000000`).
  - **Dark Mode**: High-Voltage Cyber Neo-Brutalist palette (`bg: #0D0D12`, `card: #171720`, `card_alt: #1E1E2A`, `border: #323246`, `text: #FFFFFF`):
    - **Primary CTA (`SEND PAYLOAD`)**: High-Voltage Hazard Yellow (`#FFE600`) with solid `#000000` ink-black border and Electric Cyan (`#00E5FF`) 3D planar offset shadow.
    - **Secondary CTA (`RECEIVE PAYLOAD`)**: Pure White (`#FFFFFF`) with solid `#000000` ink-black border and Neo Mint (`#00F090`) 3D planar offset shadow.
    - **PIN Cypher Modules**: Deep titanium background (`#1E1E2A`) with Electric Yellow borders (`#FFE600`), yellow digits, and glowing yellow offset shadows.
    - **Mobile QR Frame**: Clean white inset card with solid `#000000` border and Neo Mint (`#00F090`) brutalist shadow.
    - **Status Pills**: Dark emerald fill (`#0F2E22`) with glowing mint borders (`#00F090`) and neon green text.
- Dynamic tactile button-press mechanism (`make_tactile`) dynamically animates the button depression into its respective shadow color (`#00E5FF` on Primary, `#00F090` on Secondary).

### 4.3 Multithreading & Thread-Safe UI Scheduling
- Socket transfers (both P2P and HTTP) run on daemon worker threads (`threading.Thread(daemon=True)`).
- **Rule**: NEVER mutate Flet controls or call `page.update()` directly from worker threads without proper event-loop scheduling.
- The UI components capture the running asyncio event loop (`asyncio.get_running_loop()`) during initialization and dispatch UI updates using:
  ```python
  self.main_loop.call_soon_threadsafe(self._safe_ui_update)
  ```

### 4.4 UI Rate-Limiting & Throttling (Crucial for Performance)
- Transfers over 5GHz Wi-Fi / Hotspot reach **50–90+ MB/s**, streaming in 64 KB chunks. This causes thousands of chunk iterations per second.
- To prevent freezing or crashing Flet's UI event loop, `ui/transfer_view.py`, `ui/receive_view.py`, and `ui/send_view.py` enforce a minimum update threshold of **120ms**:
  ```python
  now = time.time()
  if not is_completed and (now - self._last_ui_update < 0.12):
      return
  self._last_ui_update = now
  ```
- Completion events (`percent >= 100.0` or failure) bypass this check to ensure immediate visual feedback.

### 4.5 High-Precision Telemetry & Speed Smoothing (`TransferMetricsTracker`)
- Located in `utils.py`.
- **Anti-Jitter Architecture**:
  - Eliminates the erratic 70 KB/s <-> 40 MB/s speed oscillation caused by micro-interval sampling aliasing.
  - Maintains a 1.2-second rolling sample history (`sample_history`) to compute the true sustained throughput window.
  - Applies an adaptive time-weighted **Exponential Moving Average (EMA)** (`alpha = 0.25`), providing a rock-solid, stabilized readout that smoothly reflects real-world bandwidth changes without jumping on packet micro-bursts.
- Tracks:
  - Smoothed current speed (`cur_speed_str`).
  - Verified peak speed recorded during the session (`peak_speed_str`).
  - True overall average speed (`current_bytes / total_elapsed`).
  - Transferred vs Total byte strings via `format_size()`.
  - Dynamic ETA (`remaining_bytes / cur_bytes_sec`) formatted into `MMm SSs` or `HHh MMm`.
  - Seamless pause/resume with paused duration discounting.

### 4.6 Clipboard API in Flet >= 0.28
- The legacy synchronous method `page.set_clipboard(str)` has been deprecated and removed in Flet 0.28+.
- Clipboard copying must use the async `Clipboard` service:
  ```python
  await page.clipboard.set(str(text))
  ```
- All UI event handlers invoking clipboard actions must be defined as `async def` so Flet's event dispatcher automatically awaits them.

### 4.7 High-Speed TCP Pipeline & Throughput Stabilization
- **Nagle's Algorithm Disabled (`TCP_NODELAY = 1`)**:
  - Applied via `optimize_tcp_socket(sock)` in `utils.py` across P2P sockets and HTTP servers.
  - Eliminates the pathological 40ms–200ms Delayed-ACK stalls that previously caused speed to crash down to ~70 KB/s between bursts.
- **Sized Socket Buffers (`SO_SNDBUF` & `SO_RCVBUF` = 2 MB)**:
  - Prevents TCP window collapse on gigabit LAN and high-speed Wi-Fi, allowing continuous unblocked pipeline transmission.
- **256 KB Chunking (`CHUNK_SIZE_P2P` & `CHUNK_SIZE_WEB`)**:
  - Reduces Python system calls and GIL contention by 4x compared to legacy 64 KB chunks.
- **Buffered Disk I/O (`DISK_BUFFER_SIZE` = 1 MB)**:
  - Decouples physical disk block allocation and OS dirty page flush cycles from TCP socket reads, preventing Zero-Window sender throttling.

---

## 5. Transfer Engines & Protocols

### 5.1 P2P Engine (`p2p/client.py` & `p2p/server.py`)
1. **Discovery**:
   - Receiver binds UDP port `50025` and listens for `DROPIT_DISCOVER:<passcode>`.
   - Sender broadcasts to `255.255.255.255` and local subnet (`X.X.X.255`) up to 5 times.
   - Receiver validates passcode and replies with `DROPIT_ACCEPT:<tcp_port>`.
2. **AP Isolation Bypass**:
   - Sender allows entering the receiver's IP address directly. If provided, UDP broadcast discovery is completely skipped, connecting directly via unicast TCP.
3. **Binary Framing (TCP Socket)**:
   - Packets framed using `struct`:
     - File: `struct.pack('!cI', b'F', name_len) + name_bytes + struct.pack('!Q', file_size)`
     - Directory: `struct.pack('!cI', b'D', name_len) + name_bytes + struct.pack('!QI', total_size, total_entries)` followed by individual relative path entries.
   - Streamed in **64 KB chunks** directly to/from disk.
   - Directory hierarchy is recursively reconstructed in recipient's `Downloads/` directory.

### 5.2 Mobile Web Sharing Engine (`web/server.py` & `web/templates.py`)
1. **Embedded HTTP Server**:
   - Listens on port `8080` (auto-increments if port is busy).
   - Generates QR code pointing to `http://<LAN_IP>:8080`.
2. **CORS & Preflight Handling**:
   - All responses include `Access-Control-Allow-Origin: *` and `Cache-Control: no-cache`.
   - Implements `do_OPTIONS` preflight handler to support privacy browsers (Brave Shields, Opera, Safari).
3. **Web Receiver (Mobile -> PC)**:
   - Serves `MOBILE_UPLOAD_HTML_PAGE`.
   - Handles `POST /upload` requests with custom `X-Relative-Path` headers.
   - Writes directly to disk without storing payload in RAM.
4. **Web Sender (PC -> Mobile)**:
   - Serves `MOBILE_DOWNLOAD_HTML_PAGE`.
   - If sending a directory, compresses it on-the-fly to a `.zip` archive in a background worker thread.
   - Streams download via `GET /download` with chunked binary response.

---

## 6. Active UI Architecture: DropIt Utility Brutalism

The application has fully migrated to the **"DropIt Utility Brutalism"** design system, designed in Stitch MCP (Project `1789166660270960086`) and specified in `DESIGN.md`.

### Core Visual Principles:
- **Form Factor**: Calibrated **440×660px** (2:3 aspect ratio) compact handheld diagnostic terminal window.
- **Zero Border-Radius**: All buttons, cards, tags, inputs, and progress bars enforce `border-radius: 0px`.
- **Rigid Planar Borders**: Solid `2px` to `3px` pure black borders (`#000000`) in light mode; pure white borders (`#FFFFFF`) in dark mode.
- **Zero-Blur Kinetic Depth**: Planar hard-edge offset shadows (pure black `#000000` in light mode; crisp white `#FFFFFF` in dark mode):
  - Cards & Tiles: `3px 3px 0px` (`ft.BoxShadow(offset=ft.Offset(3, 3))`)
  - Primary CTAs & Active Bays: `4px 4px 0px` (`ft.BoxShadow(offset=ft.Offset(4, 4))`)
  - Sub-badges: `2px 2px 0px` (`ft.BoxShadow(offset=ft.Offset(2, 2))`)
- **Typography Engine**:
  - `Space Grotesk` (weights 700–900) for structural titles, action buttons, and brand headers.
  - `JetBrains Mono` (weights 500–800) for all telemetry, IPs, byte sizes, speeds, and technical status badges.
- **Signal Color Palette**:
  - Canvas: `#F4F4EE` (Light) / `#0D0D0D` (Dark)
  - Cards & Drop Bay: `#FFFFFF` / `#FAF9F5` (Light) / `#181818` / `#222222` (Dark)
  - Primary CTA: `#FFE600` (Electric Hazard Yellow)
  - Connected / Online: `#00F090` (Neo Mint Green) & `#D1FAE5`
  - Network / Sockets: `#2563EB` (Electric Cobalt)
  - Alert / Cancel: `#FFA5A5` & `#FF5555` (Safety Red)
  - Tile Highlight: `#58E1FF` (Cyan)

### View-by-View Implementation Map:
- **`HomeView`**: Clean titlebar without port clutter, enlarged 160×160px Stitch brand logo, giant `DROPIT` display title, motto badge, tactile `SEND PAYLOAD` (Yellow) and `RECEIVE PAYLOAD` (Dark/White responsive) CTAs with mechanical button-press animations, and footer badge reading `DROPIT`.
- **`SendView`**: Channel 01 header (titlebar without port clutter), full-size drag & drop bay with direct `BROWSE PAYLOAD` & `BROWSE FOLDER` in-card buttons, staged cyan payload card, segmented PC/Mobile tabs, center-aligned 0/4 passcode and IP inputs, centered mobile QR box, and punchy `SEND NOW` CTA with tactile depress animation.
- **`ReceiveView`**: Clean titlebar without port clutter, 4-box passcode PIN display with tactile regenerate action, WLAN interface banner with interactive tactile `COPY IP` button, diagnostic telemetry waveform, and enlarged 190×190px Mobile QR code in a lengthened container utilizing available vertical space. Automatically transitions directly to `TransferView` as soon as peer connection or incoming socket stream is detected.
- **`TransferView`**: Unified transfer screen for both sending and receiving: Connected target device alert box, giant monospace progress percentage, heavy brutalist progress bar with vertical head indicator, dynamically updated payload info card (`update_item_info`), and 4-grid telemetry HUD (Size, Speed in Yellow, Peak, ETA). Tactile action buttons with mechanical press response (`PAUSE TRANSFER`, `CANCEL TRANSFER`, `SHOW PAYLOAD`, `DONE`), fully styled with white shadows and borders in dark mode.

### 6.1 Mechanical Tactile Button Press Animation (`make_tactile`)
- Built in `utils.py`: `make_tactile(container, on_click_handler, idle_shadow_x, idle_shadow_y, press_shadow_x, press_shadow_y, duration_ms=50)`.
- Physical Neo-Brutalist mechanics & event loop execution:
  - On click, instantaneously collapses box shadow down to `(press_shadow_x, press_shadow_y)` and translates the container offset downwards by `(0.007, 0.018)`, physically depressing the button into the canvas.
  - Implemented as an `async def` event handler natively awaited by Flet's event loop (`await asyncio.sleep(0.05)`).
  - Restores the button to idle elevation, and then immediately invokes `on_click_handler` directly on Flet's main event loop (supporting both sync callbacks, async coroutines, 0-arg and 1-arg signatures).
  - **Single-Click Responsiveness**: By running directly on Flet's asyncio event loop rather than a detached OS thread, page navigation (`page.controls.clear()`, `page.update()`) and native dialogs (`pick_files()`) execute instantaneously on the first click without requiring a second click to flush UI changes.

### 6.2 OS Default Downloads Directory Integration
- DropIt automatically resolves the authentic OS Downloads folder across all supported operating systems via `get_system_downloads_dir()` in `utils.py`:
  - **Windows**: Queries the Windows Shell Known Folder API (`SHGetKnownFolderPath`) with `FOLDERID_Downloads` (`{374DE290-123F-4565-9164-39C4925E467B}`) via `ctypes`. Falls back to registry query and user home directory.
  - **macOS**: `~/Downloads`.
  - **Linux**: Resolves `XDG_DOWNLOAD_DIR` from `~/.config/user-dirs.dirs`, falling back to `~/Downloads`.
- All incoming payloads from both P2P and Mobile Web channels are saved cleanly to the OS default Downloads directory.

### 6.3 Cool "Payload" Terminology Standard
- In alignment with DropIt's terminal aesthetics, all user-facing interfaces and status updates use the word **"Payload"** instead of "file" (e.g. `SEND PAYLOAD`, `RECEIVE PAYLOAD`, `BROWSE PAYLOAD`, `SHOW PAYLOAD`, `STAGE A PAYLOAD`, `Payload transfer complete`). Internal filesystem handles and libraries remain standard.

### 6.4 Authentic Stitch Logo & Zero-Scroll Calibration
- **Stitch MCP Logo Integration**:
  - Sourced directly from Stitch project `1789166660270960086`, screen `6cf36bc30653446d9a5623f44fd1373a` (*DropIt Neo-Brutalist Logo / DropIt Tag*).
  - Features signature electric yellow squircle, corner crosshair markers, hard offset shadow, DropIt tag badge, and bidirectional black & white data transfer arrows.
  - Deployed to `assets/logo.png` (512x512 PNG) and `assets/logo.ico` (multi-size ICO).
  - **Clean Titlebar Rendering**: Sits directly in top titlebars across `HomeView`, `SendView`, `ReceiveView`, and `TransferView` as a standalone 26×26 brand asset without an enclosing yellow box or border wrapper (avoiding nested boxes).
  - **Enlarged Hero Brand Logo**: Prominently featured on `HomeView` at **120×120px** with high-impact visual presence and ample breathing room.
- **Zero-Scroll Policy**:
  - Replaced `scroll=ft.ScrollMode.AUTO` across all views with calculated pixel-perfect bounds.
  - Window calibrated to **460×690px** (exact 2:3 ratio), granting ample breathing room so elements never touch or trigger vertical overflow.

### 6.5 Symmetrical Mode Switcher Tabs & Shadow Invariance
- **Segmented Mode Tabs (`PC` vs `MOBILE`)**:
  - Active Tab: Styled in Hazard Yellow (`tokens["yellow"]`), `#000000` text & icon, 2px solid ink-black border, and `(2, 2)` hard offset shadow (`ft.BoxShadow`).
  - Inactive Tab: Styled in Surface Card (`tokens["card"]`), `tokens["muted"]` text & icon, 1.5px border, and `shadow = None`.
  - Solves the dual-black bug where transparent inactive tabs previously inherited an unremoved black shadow due to a Flet property typo (`box_shadow` vs `shadow`).
### 6.6 Cross-Platform Drag & Drop, File Attachment, and Clipboard Architecture (Windows, macOS, Linux)
- **Multi-Tier File & Folder Attachments**:
  - `ui/send_view.py` supports both file (`pick_file`) and directory (`pick_folder`) staging with tiered native fallbacks:
    - **Tier 1 (Flet Service)**: Uses `FilePicker.pick_files()` and `FilePicker.get_directory_path()`, mounted at the page level in `main.py` and referenced in `SendView`.
    - **Tier 2 (macOS Cocoa)**: Invokes `osascript -e 'POSIX path of (choose file/folder with prompt ...)'` to display the native AppleScript/Cocoa `NSOpenPanel` sheet with zero external dependencies.
    - **Tier 2 (Linux GNOME/KDE)**: Probes `zenity --file-selection [--directory]` (GNOME/GTK), `kdialog --getopenfilename / --getexistingdirectory` (KDE), and falls back to `tkinter.filedialog`.
    - **Tier 2 (Windows)**: Uses `tkinter.filedialog.askopenfilename` and `askdirectory` with `-topmost` attribute.
  - Interactive click target: Clicking anywhere in the large drop zone container when empty triggers `pick_file()`.
- **Cross-Platform Drag & Drop**:
  - **Windows (Win32 Overlay)**: `NativeDropOverlay` spawns a transparent layered popup window (`WS_EX_LAYERED | WS_EX_TOOLWINDOW`) registered with `shell32.DragAcceptFiles` (`WM_DROPFILES`) synchronized with DropIt's client coordinates. Files dropped from Windows Explorer are immediately delivered via `_on_native_drop` -> `stage_path()`. The overlay is automatically hidden while a payload is staged to ensure unhindered button interactions, and restored upon payload dismissal.
  - **macOS & Linux**: Seamlessly handled via command-line drop on launch (`sys.argv[1]` in `main.py` -> `show_send(initial_payload)`), native clipboard paste, and full drop-zone clickability. Safe no-op overlay lifecycle prevents any platform exceptions.
- **Cross-Platform Clipboard Integration (`get_clipboard_files`)**:
  - Direct `PASTE` tactile button in `SendView` and global `Ctrl+V` (Windows/Linux) / `Cmd+V` (macOS) keyboard shortcut.
  - Reads native OS clipboard files:
    - **Windows**: Win32 `CF_HDROP` (15) and `CF_UNICODETEXT` (13) via `ctypes.windll.user32` with 64-bit pointer safety.
    - **macOS**: AppleScript Cocoa Pasteboard reader query (`«class furl»`).
    - **Linux**: Queries `wl-paste` (Wayland) and `xclip` (X11) for `text/uri-list`.
    - **Fallback**: Tkinter clipboard URI reader.

### 6.7 Neo-Brutalist Mobile Web Experience, 4-Grid Telemetry HUD & Cancel Payload
- **Universal Mobile Web UI (`web/templates.py`)**:
  - Re-engineered with DropIt's exact Neo-Brutalist design tokens: `#F4F4EE` canvas background with subtle industrial grid dots, `#FFFFFF` high-contrast terminal card, `2.5px solid #000` ink-black structural borders, `4px 4px 0px #000` offset shadows, and Space Grotesk + JetBrains Mono typography.
  - Buttons feature physical mechanical depression: `transform: translate(2px, 2px); box-shadow: 1px 1px 0px #000` on active click/tap.
- **Client-Side Real-Time Telemetry HUD (`DropItUploadController`)**:
  - Replicates desktop `TransferView` directly inside the mobile browser:
    - Large 56px JetBrains Mono percentage readout with `%` sign.
    - Heavy brutalist progress bar with black head indicator marker.
    - 4-grid metrics dashboard:
      - **SIZE**: `uploaded_bytes / total_bytes` formatted via binary units (KB, MB, GB).
      - **SPEED**: Highlighted in Electric Hazard Yellow (`#FFE600`) displaying rolling transfer throughput (`X.X MB/s`).
      - **PEAK**: Highest throughput recorded during the active transfer session.
      - **ETA**: Dynamic time remaining formatted into human-readable duration (`ss`, `mm:ss`, `hh:mm`).
- **Safety Red "Cancel Payload" Button & Server Cleanup (`/cancel`)**:
  - During upload, a prominent tactile Safety Red button (`[✕ CANCEL PAYLOAD]`) is active.
  - On click, `xhr.abort()` immediately terminates client socket I/O, dispatches a `POST /cancel` notification to the backend, and transitions the web interface into an aborted state with an instant `[ ↺ SELECT NEW PAYLOAD ]` reset button.
  - Backend server (`DropItHTTPHandler` in `web/server.py`):
    - Catches aborts and socket disconnections mid-stream.
    - Automatically removes partial/corrupted files from the `Downloads/` folder (`_cleanup_partial_file()`).
    - Dispatches `notify_cancelled()` to update server status and notify desktop UI callbacks (`on_complete(False)`), preventing either device from hanging.

### 6.8 Non-Sticking Pause & Play Controls & Zero-Rebuild Architecture
- **Persistent Controls in `TransferView`**:
  - `actions_container` maintains single persistent references to `pause_btn` and `cancel_btn` for the entire active transfer lifecycle.
  - High-frequency progress updates (every 100-120ms) NEVER recreate action button controls, eliminating Flutter pointer-up aborts and dropped clicks.
  - State changes between pause and resume mutate `pause_icon.icon`, `pause_text.value`, and container background/shadow colors directly in-place, updating only the affected widget via `update()`.
- **Mechanical Non-Sticking Button Guarantee (`make_tactile`)**:
  - `make_tactile` encapsulates the press animation and release inside a guaranteed `finally:` block that unconditionally resets `container.offset = ft.Offset(0, 0)` and clears `is_animating = False`.
  - Prevents buttons from ever remaining stuck down on screen or locking out rapid clicks.
- **Metrics Tracker Time Integrity (`TransferMetricsTracker`)**:
  - Tracks `total_paused_time` and resets `last_update_time` upon resume across all streaming channels (`p2p/client.py`, `p2p/server.py`, `web/server.py`).
  - Guarantees speeds and ETAs are never artificially degraded by pause durations.

---

## 7. Guidelines for Agents Working on DropIt

1. **Keep `context.md` Updated**: Whenever you modify architecture, add endpoints, change ports, add UI screens, or begin the Neo-Brutalist migration, update this document immediately.
2. **Never Break Thread Safety**: Always use `call_soon_threadsafe` when updating Flet controls from network/worker threads.
3. **Respect UI Throttling**: Never remove rate-limiting on transfer progress callbacks. Rapid calls to `page.update()` will hang the desktop UI.
4. **Preserve Network Robustness**: Ensure changes to `p2p/client.py` and `p2p/server.py` keep binary struct protocol framing symmetrical.
5. **Cross-Platform Compatibility**: Test path handling with `os.path` and preserve `open_file_location`, `open_native_file_picker`, and `get_clipboard_files` compatibility for Windows, macOS, and Linux.
