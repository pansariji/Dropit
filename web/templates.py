"""
DropIt Web Templates Module - Neo-Brutalist Mobile Interfaces.
Clean, modular, and fully aligned with the desktop 'DropIt Utility Brutalism' design system.

Features:
- Exact Neo-Brutalist design tokens: #F4F4EE canvas, #FFFFFF card, 2.5px solid #000 border,
  4px/3px/2px hard offset ink-black shadows, Space Grotesk + JetBrains Mono typography.
- Authentic mechanical tactile depression on button click (:active translate(2px, 2px) & reduced shadow).
- Real-time 4-grid telemetry HUD (SIZE, SPEED, PEAK, ETA), hero percentage display, and brutalist progress bar.
- Interactive 'Cancel Payload' safety red mechanical button with in-flight XHR abort and server cancellation.
- Universal mobile browser compatibility (Safari iOS, Chrome Android, Brave, Opera, Firefox).
"""

# ------------------------------------------------------------------------------
# 1. Brand Vector Assets
# ------------------------------------------------------------------------------
DROPIT_LOGO_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="60" height="60" style="margin-bottom: 8px; display: inline-block;">
    <rect x="76" y="76" width="380" height="380" rx="40" fill="#000000" />
    <rect x="56" y="56" width="380" height="380" rx="40" fill="#FFE600" stroke="#000000" stroke-width="16" />
    <path d="M84 100 H100 M92 92 V108" stroke="#000000" stroke-width="4" stroke-linecap="square" />
    <path d="M392 100 H408 M400 92 V108" stroke="#000000" stroke-width="4" stroke-linecap="square" />
    <path d="M84 400 H100 M92 392 V408" stroke="#000000" stroke-width="4" stroke-linecap="square" />
    <path d="M392 400 H408 M400 392 V408" stroke="#000000" stroke-width="4" stroke-linecap="square" />
    <rect x="300" y="32" width="124" height="34" rx="6" fill="#A7F3D0" stroke="#000000" stroke-width="6" />
    <text x="362" y="55" font-family="'Space Grotesk', system-ui, sans-serif" font-size="15" font-weight="900" text-anchor="middle" fill="#000000">DropIt</text>
    <g id="bidirectional-arrows">
        <polygon points="196,140 136,216 172,216 172,316 220,316 220,216 256,216" fill="#000000" stroke="#000000" stroke-width="6" stroke-linejoin="miter" />
        <polygon points="316,372 376,296 340,296 340,196 292,196 292,296 256,296" fill="#FFFFFF" stroke="#000000" stroke-width="12" stroke-linejoin="miter" />
        <rect x="238" y="244" width="36" height="24" rx="4" fill="#000000" />
        <circle cx="256" cy="256" r="4" fill="#FFE600" />
    </g>
</svg>"""

# ------------------------------------------------------------------------------
# 2. Shared Neo-Brutalist CSS Styles
# ------------------------------------------------------------------------------
SHARED_BRUTALIST_CSS = """
    :root {
        --bg-canvas: #F4F4EE;
        --card-surface: #FFFFFF;
        --card-alt: #FAF9F5;
        --border-ink: #000000;
        --text-primary: #000000;
        --text-muted: #6B7280;
        --hazard-yellow: #FFE600;
        --neo-mint: #00F090;
        --mint-light: #D1FAE5;
        --safety-red: #FF5555;
        --safety-red-light: #FFA5A5;
        --alert-crimson-bg: #FFE4E6;
        --shadow-ink: #000000;
        --font-display: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
    }

    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        -webkit-tap-highlight-color: transparent;
    }

    body {
        font-family: var(--font-display);
        background-color: var(--bg-canvas);
        color: var(--text-primary);
        min-height: 100vh;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 20px 14px;
        background-image: radial-gradient(#d1d1c7 1px, transparent 1px);
        background-size: 16px 16px;
    }

    /* Container Card */
    .terminal-card {
        background-color: var(--card-surface);
        border: 2.5px solid var(--border-ink);
        box-shadow: 4px 4px 0px var(--shadow-ink);
        padding: 28px 22px;
        width: 100%;
        max-width: 440px;
        text-align: center;
        position: relative;
    }

    /* Status Badges & Pills */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: var(--mint-light);
        color: var(--text-primary);
        font-family: var(--font-mono);
        font-weight: 700;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 4px 10px;
        border: 1.5px solid var(--border-ink);
        box-shadow: 2px 2px 0px var(--shadow-ink);
        margin-bottom: 16px;
    }

    .status-pill.cancelled {
        background-color: var(--alert-crimson-bg);
        color: #991B1B;
    }

    .pulse-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: var(--neo-mint);
        border: 1px solid var(--border-ink);
        display: inline-block;
    }

    .pulse-dot.danger {
        background-color: var(--safety-red);
    }

    /* Typography */
    h1.brand-title {
        font-family: var(--font-display);
        font-size: 26px;
        font-weight: 900;
        letter-spacing: -0.5px;
        text-transform: uppercase;
        margin-bottom: 4px;
        color: var(--text-primary);
    }

    p.brand-subtitle {
        font-family: var(--font-mono);
        font-size: 11px;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 22px;
    }

    /* Tactile Neo-Brutalist Buttons */
    .btn-group {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-bottom: 16px;
    }

    .btn-brutal {
        font-family: var(--font-display);
        font-size: 14px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 15px 20px;
        border: 2.5px solid var(--border-ink);
        box-shadow: 3px 3px 0px var(--shadow-ink);
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        text-decoration: none;
        transition: transform 0.08s ease, box-shadow 0.08s ease;
        user-select: none;
        width: 100%;
    }

    .btn-brutal:active {
        transform: translate(2px, 2px);
        box-shadow: 1px 1px 0px var(--shadow-ink);
    }

    .btn-primary {
        background-color: var(--hazard-yellow);
        color: var(--text-primary);
    }

    .btn-secondary {
        background-color: var(--card-surface);
        color: var(--text-primary);
    }

    .btn-cancel {
        background-color: var(--safety-red-light);
        color: var(--text-primary);
        font-size: 13px;
        padding: 13px 18px;
    }

    .btn-restart {
        background-color: var(--neo-mint);
        color: var(--text-primary);
        margin-top: 14px;
    }

    /* Staged Payload Card */
    .payload-card {
        background-color: var(--card-surface);
        border: 2px solid var(--border-ink);
        box-shadow: 2px 2px 0px var(--shadow-ink);
        padding: 12px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        text-align: left;
    }

    .payload-icon-bay {
        width: 44px;
        height: 44px;
        min-width: 44px;
        background-color: var(--hazard-yellow);
        border: 2px solid var(--border-ink);
        box-shadow: 2px 2px 0px var(--shadow-ink);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }

    .payload-info {
        flex: 1;
        overflow: hidden;
    }

    .payload-title {
        font-family: var(--font-display);
        font-size: 13px;
        font-weight: 800;
        color: var(--text-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-bottom: 3px;
    }

    .payload-meta-pill {
        display: inline-block;
        font-family: var(--font-mono);
        font-size: 9px;
        font-weight: 700;
        color: var(--text-primary);
        background-color: var(--card-alt);
        border: 1px solid var(--border-ink);
        padding: 2px 6px;
    }

    /* Drop Zone Bay */
    .drop-zone {
        border: 2.5px dashed var(--border-ink);
        background-color: var(--card-alt);
        padding: 24px 16px;
        margin-bottom: 16px;
        transition: background-color 0.15s ease, border-color 0.15s ease;
    }

    .drop-zone.drag-active {
        background-color: var(--mint-light);
        border-style: solid;
        border-color: var(--border-ink);
    }

    .drop-hint {
        font-family: var(--font-mono);
        font-size: 10px;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        margin-top: 10px;
    }

    /* Telemetry HUD & Progress */
    .telemetry-hud {
        display: none;
        background-color: var(--card-surface);
        border: 2.5px solid var(--border-ink);
        box-shadow: 3px 3px 0px var(--shadow-ink);
        padding: 16px 14px;
        margin-bottom: 16px;
        text-align: center;
    }

    .percent-row {
        display: flex;
        align-items: flex-start;
        justify-content: center;
        margin-bottom: 2px;
    }

    .percent-number {
        font-family: var(--font-mono);
        font-size: 56px;
        font-weight: 900;
        line-height: 1;
        letter-spacing: -2px;
        color: var(--text-primary);
    }

    .percent-sign {
        font-family: var(--font-display);
        font-size: 24px;
        font-weight: 900;
        color: var(--text-primary);
        margin-left: 2px;
    }

    .status-descriptor {
        font-family: var(--font-mono);
        font-size: 10px;
        font-weight: 800;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
        min-height: 14px;
    }

    /* Brutalist Progress Bar */
    .progress-track {
        height: 20px;
        background-color: var(--card-alt);
        border: 2.5px solid var(--border-ink);
        position: relative;
        overflow: hidden;
        margin-bottom: 8px;
    }

    .progress-fill {
        height: 100%;
        width: 0%;
        background-color: var(--hazard-yellow);
        border-right: 2.5px solid var(--border-ink);
        position: relative;
        transition: width 0.12s linear;
    }

    .progress-fill.completed {
        background-color: var(--neo-mint);
    }

    .progress-head-marker {
        position: absolute;
        right: 2px;
        top: 2px;
        bottom: 2px;
        width: 4px;
        background-color: var(--border-ink);
    }

    .progress-footer {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-family: var(--font-mono);
        font-size: 9px;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 14px;
    }

    .channel-indicator {
        display: flex;
        align-items: center;
        gap: 5px;
    }

    .channel-box {
        width: 6px;
        height: 6px;
        background-color: var(--border-ink);
    }

    /* 4-Grid Telemetry Block */
    .telemetry-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin-bottom: 14px;
    }

    .telemetry-tile {
        background-color: var(--card-surface);
        border: 2px solid var(--border-ink);
        box-shadow: 2px 2px 0px var(--shadow-ink);
        padding: 8px 6px;
        text-align: center;
    }

    .telemetry-tile.highlight {
        background-color: var(--hazard-yellow);
    }

    .tile-label {
        font-family: var(--font-mono);
        font-size: 9px;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
        margin-bottom: 2px;
    }

    .telemetry-tile.highlight .tile-label {
        color: var(--text-primary);
    }

    .tile-value {
        font-family: var(--font-mono);
        font-size: 12px;
        font-weight: 900;
        color: var(--text-primary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-bottom: 2px;
    }

    .telemetry-tile.highlight .tile-value {
        font-size: 13px;
    }

    .tile-unit {
        font-family: var(--font-mono);
        font-size: 8px;
        font-weight: 700;
        color: var(--text-muted);
        text-transform: uppercase;
    }

    .telemetry-tile.highlight .tile-unit {
        color: var(--text-primary);
    }

    /* Result State Banners */
    .result-banner {
        display: none;
        padding: 16px;
        border: 2px solid var(--border-ink);
        box-shadow: 2px 2px 0px var(--shadow-ink);
        margin-top: 14px;
        text-align: center;
    }

    .result-banner.success {
        background-color: var(--mint-light);
    }

    .result-banner.cancelled {
        background-color: var(--alert-crimson-bg);
    }

    .result-title {
        font-family: var(--font-display);
        font-size: 14px;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 4px;
    }

    .result-desc {
        font-family: var(--font-mono);
        font-size: 10px;
        font-weight: 700;
        color: var(--text-muted);
    }
"""

# ------------------------------------------------------------------------------
# 3. HTML Web Interface for Mobile UPLOADING (Laptop Receiving)
# ------------------------------------------------------------------------------
MOBILE_UPLOAD_HTML_PAGE = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>DropIt // Mobile Upload</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700;800;900&family=Space+Grotesk:wght@600;700;800;900&display=swap" rel="stylesheet">
    <style>
{SHARED_BRUTALIST_CSS}
        input[type="file"] {{ display: none; }}
    </style>
</head>
<body>
    <main class="terminal-card">
        <!-- Status Indicator Pill -->
        <div class="status-pill" id="headerPill">
            <span class="pulse-dot" id="headerDot"></span>
            <span id="headerStatusText">LAN ROUTE ACTIVE</span>
        </div>

        <!-- Official Stitch Logo -->
        <div>
            {DROPIT_LOGO_SVG}
        </div>

        <h1 class="brand-title">DropIt</h1>
        <p class="brand-subtitle">Stream Payloads to Device</p>

        <!-- Stage 1: File & Folder Selection Bay -->
        <section class="drop-zone" id="dropZone">
            <div class="btn-group">
                <button class="btn-brutal btn-primary" type="button" onclick="document.getElementById('fileInput').click()">
                    📄 Select Payload(s)
                </button>
                <button class="btn-brutal btn-secondary" type="button" onclick="document.getElementById('folderInput').click()">
                    📁 Select Folder
                </button>
            </div>
            <p class="drop-hint">[ or drop items anywhere inside ]</p>
        </section>

        <!-- Hidden Native File Inputs -->
        <input type="file" id="fileInput" multiple onchange="uploader.handleFiles(this.files)">
        <input type="file" id="folderInput" webkitdirectory directory multiple onchange="uploader.handleFiles(this.files)">

        <!-- Stage 2: Real-time Telemetry HUD -->
        <section class="telemetry-hud" id="telemetryHud">
            <!-- Staged File Card -->
            <div class="payload-card" id="payloadCard">
                <div class="payload-icon-bay" id="payloadIcon">📄</div>
                <div class="payload-info">
                    <div class="payload-title" id="payloadName">staging_payload.bin</div>
                    <span class="payload-meta-pill" id="payloadMetaPill">[ 0 B // PAYLOAD ]</span>
                </div>
            </div>

            <!-- Hero Percentage Readout -->
            <div class="percent-row">
                <span class="percent-number" id="percentNumber">0</span>
                <span class="percent-sign">%</span>
            </div>
            <div class="status-descriptor" id="statusDescriptor">PREPARING PAYLOAD STREAM...</div>

            <!-- Brutalist Progress Bar -->
            <div class="progress-track">
                <div class="progress-fill" id="progressFill">
                    <div class="progress-head-marker"></div>
                </div>
            </div>

            <!-- Sub-Progress Readout -->
            <div class="progress-footer">
                <div class="channel-indicator">
                    <div class="channel-box"></div>
                    <span id="channelStatusText">STREAM ACTIVE</span>
                </div>
                <div id="fileIndexCount">1 OF 1</div>
            </div>

            <!-- 4-Grid Telemetry Block -->
            <div class="telemetry-grid">
                <!-- 1. Size Block -->
                <div class="telemetry-tile">
                    <div class="tile-label">SIZE</div>
                    <div class="tile-value" id="valSize">--</div>
                    <div class="tile-unit" id="unitSize">TOTAL</div>
                </div>
                <!-- 2. Speed Block (Primary Accent) -->
                <div class="telemetry-tile highlight">
                    <div class="tile-label">SPEED</div>
                    <div class="tile-value" id="valSpeed">--</div>
                    <div class="tile-unit">RATE</div>
                </div>
                <!-- 3. Peak Block -->
                <div class="telemetry-tile">
                    <div class="tile-label">PEAK</div>
                    <div class="tile-value" id="valPeak">--</div>
                    <div class="tile-unit">MAX RATE</div>
                </div>
                <!-- 4. ETA Block -->
                <div class="telemetry-tile">
                    <div class="tile-label">ETA</div>
                    <div class="tile-value" id="valEta">--</div>
                    <div class="tile-unit">REMAINING</div>
                </div>
            </div>

            <!-- Cancel Payload Button (Tactile Safety Red) -->
            <button class="btn-brutal btn-cancel" id="btnCancel" type="button" onclick="uploader.cancel()">
                ✕ CANCEL PAYLOAD
            </button>
        </section>

        <!-- Stage 3: Result Banners -->
        <div class="result-banner success" id="successBanner">
            <div class="result-title">✔ PAYLOAD DELIVERED</div>
            <div class="result-desc">Stream verified and stored on target device.</div>
            <button class="btn-brutal btn-restart" type="button" onclick="uploader.reset()">
                ↺ SEND ANOTHER PAYLOAD
            </button>
        </div>

        <div class="result-banner cancelled" id="cancelledBanner">
            <div class="result-title">✕ TRANSFER ABORTED</div>
            <div class="result-desc">Payload cancelled. Partial files cleaned from device.</div>
            <button class="btn-brutal btn-secondary" style="margin-top: 14px;" type="button" onclick="uploader.reset()">
                ↺ SELECT NEW PAYLOAD
            </button>
        </div>
    </main>

    <script>
        /**
         * DropItUploadController
         * Manages client-side queue execution, real-time telemetry calculations,
         * UI state transitions, and server-side cancellation dispatches.
         */
        class DropItUploadController {{
            constructor() {{
                this.dropZone = document.getElementById('dropZone');
                this.telemetryHud = document.getElementById('telemetryHud');
                this.successBanner = document.getElementById('successBanner');
                this.cancelledBanner = document.getElementById('cancelledBanner');
                this.headerPill = document.getElementById('headerPill');
                this.headerDot = document.getElementById('headerDot');
                this.headerStatusText = document.getElementById('headerStatusText');

                this.payloadIcon = document.getElementById('payloadIcon');
                this.payloadName = document.getElementById('payloadName');
                this.payloadMetaPill = document.getElementById('payloadMetaPill');

                this.percentNumber = document.getElementById('percentNumber');
                this.statusDescriptor = document.getElementById('statusDescriptor');
                this.progressFill = document.getElementById('progressFill');
                this.channelStatusText = document.getElementById('channelStatusText');
                this.fileIndexCount = document.getElementById('fileIndexCount');

                this.valSize = document.getElementById('valSize');
                this.valSpeed = document.getElementById('valSpeed');
                this.valPeak = document.getElementById('valPeak');
                this.valEta = document.getElementById('valEta');
                this.btnCancel = document.getElementById('btnCancel');

                this.fileQueue = [];
                this.currentIndex = 0;
                this.totalBytes = 0;
                this.uploadedBytes = 0;
                this.peakSpeedBytesSec = 0;
                this.smoothedSpeedBytesSec = 0;
                this.sampleHistory = [];

                this.startTime = 0;
                this.lastTime = 0;
                this.lastUploaded = 0;

                this.activeXhr = null;
                this.isCancelled = false;

                this.bindEvents();
            }}

            bindEvents() {{
                ['dragenter', 'dragover'].forEach(name => {{
                    this.dropZone.addEventListener(name, (e) => {{
                        e.preventDefault();
                        e.stopPropagation();
                        this.dropZone.classList.add('drag-active');
                    }});
                }});

                ['dragleave', 'drop'].forEach(name => {{
                    this.dropZone.addEventListener(name, (e) => {{
                        e.preventDefault();
                        e.stopPropagation();
                        this.dropZone.classList.remove('drag-active');
                    }});
                }});

                this.dropZone.addEventListener('drop', (e) => {{
                    const files = e.dataTransfer.files;
                    if (files && files.length > 0) {{
                        this.handleFiles(files);
                    }}
                }});
            }}

            handleFiles(fileList) {{
                if (!fileList || fileList.length === 0) return;
                this.fileQueue = Array.from(fileList);
                this.currentIndex = 0;
                this.totalBytes = this.fileQueue.reduce((sum, f) => sum + f.size, 0);
                this.uploadedBytes = 0;
                this.peakSpeedBytesSec = 0;
                this.smoothedSpeedBytesSec = 0;
                this.sampleHistory = [];
                this.isCancelled = false;

                // UI Transition: Show Telemetry HUD
                this.dropZone.style.display = 'none';
                this.successBanner.style.display = 'none';
                this.cancelledBanner.style.display = 'none';
                this.telemetryHud.style.display = 'block';
                this.btnCancel.style.display = 'flex';
                this.progressFill.classList.remove('completed');

                this.setHeaderState('STREAMING // IN', false);
                this.startTime = Date.now();
                this.lastTime = this.startTime;
                this.lastUploaded = 0;

                this.uploadNext();
            }}

            async uploadNext() {{
                if (this.isCancelled) return;

                if (this.currentIndex >= this.fileQueue.length) {{
                    this.complete();
                    return;
                }}

                const file = this.fileQueue[this.currentIndex];
                const relPath = file.webkitRelativePath || file.name;
                const isFolderItem = !!file.webkitRelativePath && file.webkitRelativePath.includes('/');
                const ext = this.getFileExtension(file.name);

                // Update Staged Payload Info
                this.payloadIcon.textContent = isFolderItem ? '📁' : '📄';
                this.payloadName.textContent = file.name;
                this.payloadMetaPill.textContent = `[ ${{this.formatSize(file.size)}} // ${{ext}} ]`;
                this.statusDescriptor.textContent = `UPLOADING PAYLOAD (${{this.currentIndex + 1}}/${{this.fileQueue.length}})`;
                this.fileIndexCount.textContent = `${{this.currentIndex + 1}} OF ${{this.fileQueue.length}}`;

                try {{
                    await this.uploadFileStream(file, relPath);
                    if (this.isCancelled) return;

                    this.uploadedBytes += file.size;
                    this.currentIndex++;
                    this.uploadNext();
                }} catch (err) {{
                    if (!this.isCancelled) {{
                        this.handleError(err);
                    }}
                }}
            }}

            uploadFileStream(file, relPath) {{
                return new Promise((resolve, reject) => {{
                    const xhr = new XMLHttpRequest();
                    this.activeXhr = xhr;

                    xhr.open('POST', '/upload', true);
                    xhr.setRequestHeader('X-Relative-Path', encodeURIComponent(relPath));
                    xhr.setRequestHeader('Content-Type', 'application/octet-stream');

                    xhr.upload.onprogress = (e) => {{
                        if (this.isCancelled) return;

                        const currentUploaded = this.uploadedBytes + e.loaded;
                        const percent = this.totalBytes > 0 ? (currentUploaded / this.totalBytes) * 100 : 100;
                        const clampedPercent = Math.min(Math.max(percent, 0), 100);

                        this.percentNumber.textContent = Math.floor(clampedPercent);
                        this.progressFill.style.width = clampedPercent.toFixed(1) + '%';

                        const now = Date.now();
                        const timeDiff = (now - this.lastTime) / 1000;

                        if (timeDiff >= 0.1 || e.loaded === file.size) {{
                            const bytesDiff = currentUploaded - this.lastUploaded;
                            const rawSpeed = timeDiff > 0 ? Math.max(bytesDiff / timeDiff, 0) : 0;

                            // Rolling 1.0s window for smooth sustained throughput calculation
                            this.sampleHistory.push({{ time: now, bytes: currentUploaded }});
                            const cutoff = now - 1000;
                            while (this.sampleHistory.length > 1 && this.sampleHistory[0].time < cutoff) {{
                                this.sampleHistory.shift();
                            }}

                            let windowSpeed = rawSpeed;
                            if (this.sampleHistory.length >= 2) {{
                                const oldest = this.sampleHistory[0];
                                const spanSec = (now - oldest.time) / 1000;
                                if (spanSec >= 0.2) {{
                                    windowSpeed = (currentUploaded - oldest.bytes) / spanSec;
                                }}
                            }}

                            // Adaptive Exponential Moving Average to stabilize readout
                            if (!this.smoothedSpeedBytesSec || this.smoothedSpeedBytesSec <= 0) {{
                                this.smoothedSpeedBytesSec = windowSpeed;
                            }} else {{
                                const alpha = Math.min(1.0, Math.max(0.25, 1.0 - Math.exp(-timeDiff / 0.4)));
                                this.smoothedSpeedBytesSec = (alpha * windowSpeed) + ((1.0 - alpha) * this.smoothedSpeedBytesSec);
                            }}

                            const curSpeed = this.smoothedSpeedBytesSec;
                            const totalElapsedSec = (now - this.startTime) / 1000;
                            if (curSpeed > this.peakSpeedBytesSec && totalElapsedSec > 0.3) {{
                                this.peakSpeedBytesSec = curSpeed;
                            }}

                            const remainingBytes = Math.max(this.totalBytes - currentUploaded, 0);
                            const etaSec = curSpeed > 0 ? remainingBytes / curSpeed : null;

                            this.valSize.textContent = `${{this.formatSize(currentUploaded)}} / ${{this.formatSize(this.totalBytes)}}`;
                            this.valSpeed.textContent = this.formatSize(curSpeed) + '/s';
                            this.valPeak.textContent = this.formatSize(this.peakSpeedBytesSec) + '/s';
                            this.valEta.textContent = this.formatTime(etaSec);

                            this.lastTime = now;
                            this.lastUploaded = currentUploaded;
                        }}
                    }};

                    xhr.onload = () => {{
                        this.activeXhr = null;
                        if (xhr.status === 200) {{
                            resolve();
                        }} else if (xhr.status === 499) {{
                            reject(new Error('Transfer aborted by server'));
                        }} else {{
                            reject(new Error(`Server error ${{xhr.status}}`));
                        }}
                    }};

                    xhr.onerror = () => {{
                        this.activeXhr = null;
                        reject(new Error('Network error during upload'));
                    }};

                    xhr.onabort = () => {{
                        this.activeXhr = null;
                        reject(new Error('Upload aborted'));
                    }};

                    xhr.send(file);
                }});
            }}

            cancel() {{
                if (this.isCancelled) return;
                this.isCancelled = true;

                // 1. Abort active client socket stream
                if (this.activeXhr) {{
                    try {{
                        this.activeXhr.abort();
                    }} catch (e) {{}}
                    this.activeXhr = null;
                }}

                // 2. Dispatch cancellation notification to backend server
                fetch('/cancel', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }}
                }}).catch(() => {{}});

                // 3. Transition UI to Cancelled state
                this.btnCancel.style.display = 'none';
                this.statusDescriptor.textContent = 'TRANSFER CANCELLED // PAYLOAD ABORTED';
                this.valSpeed.textContent = '--';
                this.valEta.textContent = '--';
                this.setHeaderState('PAYLOAD CANCELLED', true);

                setTimeout(() => {{
                    this.telemetryHud.style.display = 'none';
                    this.cancelledBanner.style.display = 'block';
                }}, 300);
            }}

            complete() {{
                this.percentNumber.textContent = '100';
                this.progressFill.style.width = '100%';
                this.progressFill.classList.add('completed');
                this.statusDescriptor.textContent = 'TRANSFER COMPLETE // ALL PAYLOADS DELIVERED';
                this.valSpeed.textContent = 'Done';
                this.valEta.textContent = '0s';
                this.btnCancel.style.display = 'none';
                this.setHeaderState('TRANSFER VERIFIED', false);

                setTimeout(() => {{
                    this.telemetryHud.style.display = 'none';
                    this.successBanner.style.display = 'block';
                }}, 500);
            }}

            handleError(err) {{
                this.statusDescriptor.textContent = `TRANSFER ERROR: ${{err.message}}`;
                this.setHeaderState('ERROR OCCURRED', true);
            }}

            reset() {{
                this.fileQueue = [];
                this.currentIndex = 0;
                this.totalBytes = 0;
                this.uploadedBytes = 0;
                this.peakSpeedBytesSec = 0;
                this.smoothedSpeedBytesSec = 0;
                this.sampleHistory = [];
                this.isCancelled = false;
                this.activeXhr = null;

                document.getElementById('fileInput').value = '';
                document.getElementById('folderInput').value = '';

                this.percentNumber.textContent = '0';
                this.progressFill.style.width = '0%';
                this.progressFill.classList.remove('completed');
                this.valSize.textContent = '--';
                this.valSpeed.textContent = '--';
                this.valPeak.textContent = '--';
                this.valEta.textContent = '--';

                this.telemetryHud.style.display = 'none';
                this.successBanner.style.display = 'none';
                this.cancelledBanner.style.display = 'none';
                this.dropZone.style.display = 'block';

                this.setHeaderState('LAN ROUTE ACTIVE', false);
            }}

            setHeaderState(label, isDanger) {{
                this.headerStatusText.textContent = label;
                if (isDanger) {{
                    this.headerPill.classList.add('cancelled');
                    this.headerDot.classList.add('danger');
                }} else {{
                    this.headerPill.classList.remove('cancelled');
                    this.headerDot.classList.remove('danger');
                }}
            }}

            formatSize(bytes) {{
                if (!bytes || bytes <= 0) return '0 B';
                const k = 1024;
                const units = ['B', 'KB', 'MB', 'GB', 'TB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + units[i];
            }}

            formatTime(seconds) {{
                if (seconds === null || seconds === undefined || isNaN(seconds) || seconds < 0) return '--';
                seconds = Math.round(seconds);
                if (seconds < 60) return `${{seconds}}s`;
                const minutes = Math.floor(seconds / 60);
                const secs = seconds % 60;
                if (minutes < 60) return `${{String(minutes).padStart(2, '0')}}m ${{String(secs).padStart(2, '0')}}s`;
                const hours = Math.floor(minutes / 60);
                const mins = minutes % 60;
                return `${{String(hours).padStart(2, '0')}}h ${{String(mins).padStart(2, '0')}}m`;
            }}

            getFileExtension(filename) {{
                if (!filename || !filename.includes('.')) return 'PAYLOAD';
                return filename.split('.').pop().toUpperCase();
            }}
        }}

        // Initialize Controller
        const uploader = new DropItUploadController();
    </script>
</body>
</html>"""

# ------------------------------------------------------------------------------
# 4. HTML Web Interface for Mobile DOWNLOADING (Laptop Sending)
# ------------------------------------------------------------------------------
MOBILE_DOWNLOAD_HTML_PAGE = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>DropIt // Download Payload</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;700;800;900&family=Space+Grotesk:wght@600;700;800;900&display=swap" rel="stylesheet">
    <style>
{SHARED_BRUTALIST_CSS}
        .download-stage {{
            margin-bottom: 20px;
        }}
        .instruction-box {{
            background-color: var(--card-alt);
            border: 2px solid var(--border-ink);
            padding: 12px;
            font-family: var(--font-mono);
            font-size: 10px;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-top: 14px;
        }}
    </style>
</head>
<body>
    <main class="terminal-card">
        <!-- Status Indicator Pill -->
        <div class="status-pill">
            <span class="pulse-dot"></span>
            <span>DOWNLOAD READY</span>
        </div>

        <!-- Official Stitch Logo -->
        <div>
            {DROPIT_LOGO_SVG}
        </div>

        <h1 class="brand-title">DropIt</h1>
        <p class="brand-subtitle">Download Shared Item to Device</p>

        <!-- Staged File Card -->
        <div class="download-stage">
            <div class="payload-card" style="box-shadow: 3px 3px 0px var(--shadow-ink); border-width: 2.5px;">
                <div class="payload-icon-bay" style="font-size: 24px; width: 50px; height: 50px;">{{{{ICON}}}}</div>
                <div class="payload-info">
                    <div class="payload-title" style="font-size: 15px;">{{{{ITEM_NAME}}}}</div>
                    <span class="payload-meta-pill">[ {{{{ITEM_SIZE}}}} // {{{{ITEM_TYPE}}}} ]</span>
                </div>
            </div>

            <!-- Primary Download Trigger Action -->
            <a class="btn-brutal btn-primary" id="btnDownload" href="/download" download onclick="handleDownloadTrigger()">
                📥 DOWNLOAD {{{{ITEM_TYPE}}}}
            </a>

            <!-- Download Active Feedback Banner -->
            <div class="result-banner success" id="downloadActiveBanner">
                <div class="result-title">📥 DOWNLOAD INITIATED</div>
                <div class="result-desc">Streaming payload directly to your device browser. Check your notification tray for progress.</div>
            </div>

            <div class="instruction-box">
                [ Direct High-Speed LAN Connection Active ]
            </div>
        </div>
    </main>

    <script>
        function handleDownloadTrigger() {{
            setTimeout(() => {{
                document.getElementById('btnDownload').style.display = 'none';
                document.getElementById('downloadActiveBanner').style.display = 'block';
            }}, 150);
        }}
    </script>
</body>
</html>"""
