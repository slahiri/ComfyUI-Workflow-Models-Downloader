import { api } from "../../scripts/api.js";
import { app } from "../../scripts/app.js";
import { $el } from "../../scripts/ui.js";

const VERSION = "1.7.0";

// Common model directories in ComfyUI
const MODEL_DIRECTORIES = [
    "checkpoints",
    "clip",
    "clip_vision",
    "controlnet",
    "diffusion_models",
    "embeddings",
    "gligen",
    "hypernetworks",
    "ipadapter",
    "loras",
    "loras/flux",
    "loras/sd15",
    "loras/sdxl",
    "photomaker",
    "sams",
    "style_models",
    "text_encoders",
    "unet",
    "upscale_models",
    "vae",
    "vae_approx"
];

// Styles for the modal
const styles = `
.wmd-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
}

.wmd-modal {
    background-color: #1a1a1a;
    border: 1px solid #444;
    border-radius: 10px;
    width: 95%;
    max-width: 1400px;
    height: 90vh;
    max-height: 900px;
    display: flex;
    flex-direction: column;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
}

.wmd-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 18px 24px;
    border-bottom: 1px solid #444;
    background-color: #252525;
    border-radius: 10px 10px 0 0;
}

.wmd-modal-title {
    font-size: 20px;
    font-weight: bold;
    color: #fff;
    margin: 0;
}

.wmd-modal-close {
    background: none;
    border: none;
    color: #888;
    font-size: 28px;
    cursor: pointer;
    padding: 0 8px;
    line-height: 1;
}

.wmd-modal-close:hover {
    color: #fff;
}

.wmd-modal-body {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
}

.wmd-modal-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 18px 24px;
    border-top: 1px solid #444;
    background-color: #252525;
    border-radius: 0 0 10px 10px;
}

.wmd-summary {
    display: flex;
    gap: 30px;
    margin-bottom: 24px;
    padding: 20px;
    background-color: #252525;
    border-radius: 8px;
}

.wmd-summary-item {
    text-align: center;
}

.wmd-summary-value {
    font-size: 28px;
    font-weight: bold;
    color: #4CAF50;
}

.wmd-summary-value.missing {
    color: #f44336;
}

.wmd-summary-label {
    font-size: 12px;
    color: #888;
    text-transform: uppercase;
    margin-top: 4px;
}

.wmd-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}

.wmd-table th {
    background-color: #333;
    color: #fff;
    padding: 14px 12px;
    text-align: left;
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 1;
}

.wmd-table td {
    padding: 12px;
    border-bottom: 1px solid #333;
    color: #ddd;
    vertical-align: middle;
}

.wmd-table tr:hover {
    background-color: #2a2a2a;
}

.wmd-status-exists {
    color: #4CAF50;
    font-weight: bold;
}

.wmd-status-missing {
    color: #f44336;
    font-weight: bold;
}

.wmd-status-checking {
    color: #ff9800;
    font-style: italic;
}

.wmd-btn {
    padding: 10px 18px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
}

.wmd-btn-primary {
    background-color: #4CAF50;
    color: white;
}

.wmd-btn-primary:hover {
    background-color: #45a049;
    transform: translateY(-1px);
}

.wmd-btn-primary:disabled {
    background-color: #666;
    cursor: not-allowed;
    transform: none;
}

.wmd-btn-secondary {
    background-color: #555;
    color: white;
}

.wmd-btn-secondary:hover {
    background-color: #666;
}

.wmd-btn-warning {
    background-color: #ff9800;
    color: white;
}

.wmd-btn-warning:hover {
    background-color: #f57c00;
}

.wmd-btn-danger {
    background-color: #f44336;
    color: white;
}

.wmd-btn-danger:hover {
    background-color: #d32f2f;
}

.wmd-cancel-btn {
    background: none;
    border: 1px solid #666;
    color: #999;
    width: 22px;
    height: 22px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.wmd-cancel-btn:hover {
    background-color: #f44336;
    border-color: #f44336;
    color: white;
}

.wmd-btn-info {
    background-color: #2196F3;
    color: white;
}

.wmd-btn-info:hover {
    background-color: #1976D2;
}

.wmd-btn-small {
    padding: 6px 12px;
    font-size: 13px;
}

.wmd-progress-bar {
    width: 100%;
    height: 8px;
    background-color: #333;
    border-radius: 4px;
    overflow: hidden;
    margin-top: 6px;
}

.wmd-progress-fill {
    height: 100%;
    background-color: #4CAF50;
    transition: width 0.3s;
}

.wmd-download-status {
    font-size: 12px;
    color: #888;
    margin-top: 4px;
}

.wmd-hf-link {
    color: #5599ff;
    text-decoration: none;
}

.wmd-hf-link:hover {
    text-decoration: underline;
}

.wmd-loading {
    text-align: center;
    padding: 60px;
    color: #888;
}

.wmd-spinner {
    border: 4px solid #333;
    border-top: 4px solid #4CAF50;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: wmd-spin 1s linear infinite;
    margin: 0 auto 20px;
}

@keyframes wmd-spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.wmd-empty {
    text-align: center;
    padding: 60px;
    color: #888;
}

.wmd-type-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 14px;
    font-size: 12px;
    background-color: #444;
    color: #ddd;
    white-space: nowrap;
}

.wmd-dir-select {
    background-color: #333;
    color: #ddd;
    border: 1px solid #555;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    min-width: 180px;
    cursor: pointer;
}

.wmd-dir-select:hover {
    border-color: #777;
}

.wmd-dir-select:focus {
    outline: none;
    border-color: #4CAF50;
}

.wmd-action-cell {
    display: flex;
    flex-direction: column;
    gap: 6px;
    min-width: 140px;
}

.wmd-action-buttons {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}

.wmd-url-input-row {
    display: flex;
    gap: 8px;
    margin-top: 6px;
}

.wmd-url-input {
    flex: 1;
    background-color: #333;
    color: #ddd;
    border: 1px solid #555;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
    min-width: 200px;
}

.wmd-url-input:focus {
    outline: none;
    border-color: #4CAF50;
}

.wmd-url-input::placeholder {
    color: #666;
}

.wmd-source-badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    margin-left: 6px;
    background-color: #333;
    color: #888;
}

.wmd-source-badge.hf {
    background-color: #1a4a3a;
    color: #4CAF50;
}

.wmd-source-badge.civit {
    background-color: #3a1a4a;
    color: #9c27b0;
}

.wmd-source-badge.popular {
    background-color: #4a3a1a;
    color: #ff9800;
}

.wmd-filename-cell {
    max-width: 300px;
    word-break: break-all;
}

.wmd-settings-btn {
    background: none;
    border: none;
    color: #888;
    font-size: 20px;
    cursor: pointer;
    padding: 4px 8px;
    margin-right: 10px;
}

.wmd-settings-btn:hover {
    color: #fff;
}

.wmd-settings-panel {
    background-color: #252525;
    border: 1px solid #444;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

.wmd-settings-title {
    font-size: 16px;
    font-weight: bold;
    color: #fff;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.wmd-settings-row {
    display: flex;
    align-items: center;
    margin-bottom: 14px;
    gap: 12px;
}

.wmd-settings-label {
    min-width: 140px;
    color: #ccc;
    font-size: 14px;
}

.wmd-settings-input {
    flex: 1;
    background-color: #333;
    color: #ddd;
    border: 1px solid #555;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 14px;
    font-family: monospace;
}

.wmd-settings-input:focus {
    outline: none;
    border-color: #4CAF50;
}

.wmd-settings-input::placeholder {
    color: #666;
}

.wmd-settings-status {
    font-size: 12px;
    padding: 4px 8px;
    border-radius: 4px;
    min-width: 80px;
    text-align: center;
}

.wmd-settings-status.set {
    background-color: #1a4a3a;
    color: #4CAF50;
}

.wmd-settings-status.not-set {
    background-color: #4a3a1a;
    color: #ff9800;
}

.wmd-settings-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #444;
}

.wmd-settings-hint {
    font-size: 12px;
    color: #666;
    margin-top: 4px;
}

.wmd-settings-link {
    color: #5599ff;
    text-decoration: none;
}

.wmd-settings-link:hover {
    text-decoration: underline;
}

.wmd-filter-select {
    background-color: #333;
    color: #ddd;
    border: 1px solid #555;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 13px;
    cursor: pointer;
    margin-right: 10px;
}

.wmd-filter-select:hover {
    border-color: #777;
}

.wmd-filter-select:focus {
    outline: none;
    border-color: #4CAF50;
}

.wmd-header-controls {
    display: flex;
    align-items: center;
}

.wmd-info-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background-color: #2196F3;
    color: white;
    font-size: 12px;
    font-weight: bold;
    font-style: italic;
    font-family: Georgia, serif;
    cursor: help;
    margin-left: 6px;
    position: relative;
}

.wmd-info-icon:hover {
    background-color: #1976D2;
}

.wmd-info-tooltip {
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    background-color: #1a1a1a;
    border: 1px solid #444;
    border-radius: 6px;
    padding: 10px 12px;
    min-width: 250px;
    max-width: 350px;
    z-index: 10003;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    font-style: normal;
    font-family: inherit;
    font-weight: normal;
    font-size: 12px;
    color: #ddd;
    text-align: left;
    display: none;
    margin-bottom: 8px;
}

.wmd-info-icon:hover .wmd-info-tooltip {
    display: block;
}

.wmd-info-tooltip::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 6px solid transparent;
    border-top-color: #444;
}

.wmd-info-tooltip-row {
    margin-bottom: 6px;
}

.wmd-info-tooltip-row:last-child {
    margin-bottom: 0;
}

.wmd-info-tooltip-label {
    color: #888;
    font-size: 10px;
    text-transform: uppercase;
}

.wmd-info-tooltip-value {
    color: #fff;
    word-break: break-all;
}

.wmd-info-tooltip-value a {
    color: #5599ff;
    text-decoration: none;
}

.wmd-info-tooltip-value a:hover {
    text-decoration: underline;
}
`;

// Add styles to document
const styleElement = document.createElement('style');
styleElement.textContent = styles;
document.head.appendChild(styleElement);


class WorkflowModelsDownloader {
    constructor() {
        this.modal = null;
        this.models = [];
        this.downloads = {};
        this.progressInterval = null;
        this.showSettings = false;
        this.settings = null;
        this.currentFilter = "all"; // all, existing, ready, unknown
    }

    async show() {
        this.createModal();
        document.body.appendChild(this.modal);
        await this.scanWorkflow();

        // Check for any active downloads and restore progress tracking
        await this.checkActiveDownloads();
    }

    close() {
        // Don't stop the progress polling - downloads continue in background
        // Just close the modal UI
        if (this.modal) {
            this.modal.remove();
            this.modal = null;
        }
        // Note: progressInterval keeps running to track background downloads
    }

    async checkActiveDownloads() {
        // Check if there are any active downloads on the server
        try {
            const response = await api.fetchApi("/workflow-models/progress");
            const allProgress = await response.json();

            let hasActiveDownloads = false;

            // Check each model to see if it has an active download
            for (let i = 0; i < this.models.length; i++) {
                const model = this.models[i];

                // Check various possible download IDs for this model
                const possibleIds = [
                    `${model.hf_repo}/${model.filename}`.replace(/\//g, '_'),
                    `direct_${model.filename}`.replace(/[\/\\]/g, '_')
                ];

                for (const downloadId of possibleIds) {
                    if (allProgress[downloadId]) {
                        const progress = allProgress[downloadId];
                        if (progress.status === 'downloading' || progress.status === 'starting') {
                            // Found an active download for this model
                            this.downloads[i] = downloadId;
                            hasActiveDownloads = true;

                            // Update UI to show progress
                            const btn = document.getElementById(`wmd-dl-btn-${i}`);
                            const progressDiv = document.getElementById(`wmd-progress-${i}`);
                            const urlRow = document.getElementById(`wmd-url-row-${i}`);
                            const searchBtn = document.getElementById(`wmd-search-btn-${i}`);

                            if (btn) btn.style.display = "none";
                            if (progressDiv) progressDiv.style.display = "block";
                            if (urlRow) urlRow.style.display = "none";
                            if (searchBtn) searchBtn.style.display = "none";

                            this.updateDownloadUI(i, progress);
                        } else if (progress.status === 'completed') {
                            // Download completed while modal was closed
                            model.exists = true;
                            const statusCell = document.getElementById(`wmd-status-cell-${i}`);
                            if (statusCell) {
                                statusCell.className = "wmd-status-exists";
                                this.recheckModelStatus(i);
                            }
                        }
                        break;
                    }
                }
            }

            if (hasActiveDownloads) {
                this.startProgressPolling();
            }
        } catch (error) {
            console.error("[WMD] Error checking active downloads:", error);
        }
    }

    createModal() {
        this.modal = $el("div.wmd-modal-overlay", {
            onclick: (e) => {
                if (e.target === this.modal) this.close();
            }
        }, [
            $el("div.wmd-modal", [
                $el("div.wmd-modal-header", [
                    $el("h2.wmd-modal-title", ["Workflow Models Downloader"]),
                    $el("div.wmd-header-controls", [
                        $el("select.wmd-filter-select", {
                            id: "wmd-filter-select",
                            onchange: (e) => this.onFilterChange(e.target.value),
                            title: "Filter models"
                        }, [
                            $el("option", { value: "all" }, ["All Models"]),
                            $el("option", { value: "existing" }, ["Existing Models"]),
                            $el("option", { value: "ready" }, ["Ready For Download"]),
                            $el("option", { value: "unknown" }, ["Missing URLs / Unknown"])
                        ]),
                        $el("button.wmd-settings-btn", {
                            onclick: () => this.toggleSettings(),
                            title: "Settings"
                        }, ["\u2699"]),
                        $el("button.wmd-modal-close", {
                            onclick: () => this.close()
                        }, ["\u00D7"])
                    ])
                ]),
                $el("div.wmd-modal-body", { id: "wmd-body" }, [
                    $el("div.wmd-loading", [
                        $el("div.wmd-spinner"),
                        $el("div", ["Scanning workflow for models..."])
                    ])
                ]),
                $el("div.wmd-modal-footer", [
                    $el("div", { id: "wmd-footer-info" }, [""]),
                    $el("div", { style: { display: "flex", gap: "10px" } }, [
                        $el("button.wmd-btn.wmd-btn-secondary", {
                            onclick: () => this.close()
                        }, ["Close"]),
                        $el("button.wmd-btn.wmd-btn-primary", {
                            id: "wmd-download-all-btn",
                            style: { display: "none" },
                            onclick: () => this.downloadAllMissing()
                        }, ["Download All Missing"])
                    ])
                ])
            ])
        ]);
    }

    async scanWorkflow() {
        try {
            // Load settings first (for advanced search button display)
            await this.loadSettings();

            // Get current workflow from app
            const workflow = app.graph.serialize();

            const response = await api.fetchApi("/workflow-models/scan", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ workflow })
            });

            const result = await response.json();

            if (result.success) {
                this.models = result.models;
                this.renderModels(result.models, result.summary);
            } else {
                this.showError(result.error || "Failed to scan workflow");
            }
        } catch (error) {
            console.error("[WMD] Scan error:", error);
            this.showError("Failed to scan workflow: " + error.message);
        }
    }

    buildDirectoryOptions(currentDir) {
        // Ensure current directory is in the list
        let dirs = [...MODEL_DIRECTORIES];
        if (currentDir && !dirs.includes(currentDir)) {
            dirs.unshift(currentDir);
        }
        dirs.sort();

        return dirs.map(dir => {
            const selected = dir === currentDir ? 'selected' : '';
            return `<option value="${dir}" ${selected}>models/${dir}/</option>`;
        }).join('');
    }

    getSourceBadge(model) {
        if (model.url_source === 'popular_models') {
            return '<span class="wmd-source-badge popular">Popular</span>';
        } else if (model.url_source === 'model_list') {
            return '<span class="wmd-source-badge">Manager</span>';
        } else if (model.url_source === 'huggingface_api') {
            return '<span class="wmd-source-badge hf">HF API</span>';
        } else if (model.url_source === 'civitai_api') {
            return '<span class="wmd-source-badge civit">CivitAI</span>';
        }
        return '';
    }

    renderModels(models, summary) {
        const body = document.getElementById("wmd-body");
        const footerInfo = document.getElementById("wmd-footer-info");
        const downloadAllBtn = document.getElementById("wmd-download-all-btn");

        if (models.length === 0) {
            body.innerHTML = `
                <div class="wmd-empty">
                    <p>No models found in the current workflow.</p>
                </div>
            `;
            return;
        }

        // Update footer info
        footerInfo.textContent = `Total: ${summary.total} | Existing: ${summary.existing} | Missing: ${summary.missing}`;

        // Show download all button if there are missing models with URLs
        const downloadableCount = models.filter(m => !m.exists && m.url).length;
        if (downloadableCount > 0) {
            downloadAllBtn.style.display = "inline-block";
            downloadAllBtn.textContent = `Download All Missing (${downloadableCount})`;
        }

        // Build summary
        const summaryHtml = `
            <div class="wmd-summary">
                <div class="wmd-summary-item">
                    <div class="wmd-summary-value">${summary.total}</div>
                    <div class="wmd-summary-label">Total Models</div>
                </div>
                <div class="wmd-summary-item">
                    <div class="wmd-summary-value">${summary.existing}</div>
                    <div class="wmd-summary-label">Existing</div>
                </div>
                <div class="wmd-summary-item">
                    <div class="wmd-summary-value missing">${summary.missing}</div>
                    <div class="wmd-summary-label">Missing</div>
                </div>
                <div class="wmd-summary-item">
                    <div class="wmd-summary-value">${downloadableCount}</div>
                    <div class="wmd-summary-label">Downloadable</div>
                </div>
            </div>
        `;

        // Build table
        const tableRows = models.map((model, index) => {
            const statusClass = model.exists ? "wmd-status-exists" : "wmd-status-missing";
            const statusText = model.exists ? `EXISTS (${model.local_size})` : "MISSING";

            // Directory dropdown
            const dirOptions = this.buildDirectoryOptions(model.directory);
            const dirDropdown = `
                <select class="wmd-dir-select"
                        id="wmd-dir-${index}"
                        onchange="window.wmdInstance.onDirectoryChange(${index}, this.value)">
                    ${dirOptions}
                </select>
            `;

            // Source badge
            const sourceBadge = this.getSourceBadge(model);

            // Action cell
            let actionCell = "";
            if (model.url) {
                // Has URL - show download button
                const btnClass = model.exists ? "wmd-btn-warning" : "wmd-btn-primary";
                const btnText = model.exists ? "Re-download" : "Download";
                const infoIcon = this.buildMetadataInfoIcon(model);
                actionCell = `
                    <div class="wmd-action-cell">
                        <div class="wmd-action-buttons">
                            <button class="wmd-btn ${btnClass} wmd-btn-small"
                                    id="wmd-dl-btn-${index}"
                                    onclick="window.wmdInstance.downloadModel(${index})">
                                ${btnText}
                            </button>
                            ${infoIcon}
                        </div>
                        <div id="wmd-progress-${index}" style="display:none;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <div class="wmd-progress-bar" style="flex: 1;">
                                    <div class="wmd-progress-fill" id="wmd-progress-fill-${index}" style="width: 0%"></div>
                                </div>
                                <button class="wmd-cancel-btn" id="wmd-cancel-${index}"
                                        onclick="window.wmdInstance.cancelDownload(${index})"
                                        title="Cancel download">
                                    \u00D7
                                </button>
                            </div>
                            <div class="wmd-download-status" id="wmd-status-${index}">Starting...</div>
                        </div>
                    </div>
                `;
            } else {
                // No URL - show search, hash lookup (if exists), and manual input options
                const hashLookupBtn = model.exists ? `
                    <button class="wmd-btn wmd-btn-secondary wmd-btn-small"
                            id="wmd-hash-btn-${index}"
                            onclick="window.wmdInstance.lookupHash(${index})"
                            title="Calculate file hash and lookup on CivitAI">
                        Lookup Hash
                    </button>
                ` : '';

                // Check if advanced search is enabled
                const advancedSearchEnabled = this.settings?.enable_advanced_search && this.settings?.tavily_api_key_set;
                const searchBtnText = advancedSearchEnabled ? 'Advanced Search' : 'Search URL';
                const searchBtnClass = advancedSearchEnabled ? 'wmd-btn-warning' : 'wmd-btn-info';
                const searchBtnHandler = advancedSearchEnabled ? 'advancedSearch' : 'searchUrl';

                // Show info icon if there's cached suggestions
                const suggestionsIcon = this.buildSuggestionsInfoIcon(model);

                actionCell = `
                    <div class="wmd-action-cell">
                        <div class="wmd-action-buttons">
                            <button class="wmd-btn ${searchBtnClass} wmd-btn-small"
                                    id="wmd-search-btn-${index}"
                                    onclick="window.wmdInstance.${searchBtnHandler}(${index})">
                                ${searchBtnText}
                            </button>
                            ${hashLookupBtn}
                            ${suggestionsIcon}
                        </div>
                        <div class="wmd-url-input-row" id="wmd-url-row-${index}">
                            <input type="text" class="wmd-url-input"
                                   id="wmd-url-input-${index}"
                                   placeholder="Or paste direct URL here..."
                                   onkeypress="if(event.key==='Enter') window.wmdInstance.downloadFromManualUrl(${index})">
                            <button class="wmd-btn wmd-btn-primary wmd-btn-small"
                                    onclick="window.wmdInstance.downloadFromManualUrl(${index})">
                                Go
                            </button>
                        </div>
                        <div id="wmd-progress-${index}" style="display:none;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <div class="wmd-progress-bar" style="flex: 1;">
                                    <div class="wmd-progress-fill" id="wmd-progress-fill-${index}" style="width: 0%"></div>
                                </div>
                                <button class="wmd-cancel-btn" id="wmd-cancel-${index}"
                                        onclick="window.wmdInstance.cancelDownload(${index})"
                                        title="Cancel download">
                                    \u00D7
                                </button>
                            </div>
                            <div class="wmd-download-status" id="wmd-status-${index}">Starting...</div>
                        </div>
                    </div>
                `;
            }

            const hfLink = model.hf_repo
                ? `<a href="https://huggingface.co/${model.hf_repo}" target="_blank" class="wmd-hf-link">${model.hf_repo}</a>${sourceBadge}`
                : (model.url ? `<span style="color:#888;">Direct URL</span>${sourceBadge}` : `<span style="color:#666;">No URL</span>`);

            return `
                <tr id="wmd-row-${index}">
                    <td class="wmd-filename-cell"><strong>${model.filename}</strong></td>
                    <td><span class="wmd-type-badge">${model.type}</span></td>
                    <td>${dirDropdown}</td>
                    <td class="${statusClass}" id="wmd-status-cell-${index}">${statusText}</td>
                    <td>${hfLink}</td>
                    <td>${actionCell}</td>
                </tr>
            `;
        }).join("");

        body.innerHTML = `
            ${summaryHtml}
            <table class="wmd-table">
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Type</th>
                        <th>Directory</th>
                        <th>Status</th>
                        <th>Source</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableRows}
                </tbody>
            </table>
        `;

        // Make instance accessible for onclick handlers
        window.wmdInstance = this;

        // Restore filter selection and apply filter
        const filterSelect = document.getElementById("wmd-filter-select");
        if (filterSelect) {
            filterSelect.value = this.currentFilter;
        }
        this.applyFilter();
    }

    async searchUrl(index) {
        const model = this.models[index];
        if (!model) return;

        const searchBtn = document.getElementById(`wmd-search-btn-${index}`);
        if (searchBtn) {
            searchBtn.disabled = true;
            searchBtn.textContent = "Searching...";
        }

        try {
            const response = await api.fetchApi("/workflow-models/search-url", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename: model.filename })
            });

            const result = await response.json();

            if (result.success && result.url) {
                // Update model with found URL
                model.url = result.url;
                model.hf_repo = result.hf_repo || '';
                model.hf_path = result.hf_path || '';
                model.url_source = result.source;
                model.source = result.hf_repo ? 'HuggingFace' : 'Direct';

                // Re-render the row
                this.updateRowWithUrl(index);
            } else {
                alert(`No URL found for ${model.filename}.\n\nYou can manually paste a direct download URL in the input field.`);
                if (searchBtn) {
                    searchBtn.disabled = false;
                    searchBtn.textContent = "Search URL";
                }
            }
        } catch (error) {
            console.error("[WMD] Search URL error:", error);
            alert(`Error searching for URL: ${error.message}`);
            if (searchBtn) {
                searchBtn.disabled = false;
                searchBtn.textContent = "Search URL";
            }
        }
    }

    async advancedSearch(index) {
        const model = this.models[index];
        if (!model) return;

        const searchBtn = document.getElementById(`wmd-search-btn-${index}`);
        if (searchBtn) {
            searchBtn.disabled = true;
            searchBtn.textContent = "Searching...";
        }

        try {
            const response = await api.fetchApi("/workflow-models/advanced-search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename: model.filename })
            });

            const result = await response.json();

            if (result.success && result.url) {
                // Direct URL found - store metadata
                model.url = result.url;
                model.hf_repo = result.hf_repo || '';
                model.hf_path = result.hf_path || '';
                model.url_source = result.source;
                model.source = result.hf_repo ? 'HuggingFace' : 'Direct';
                model.search_metadata = result.metadata || {
                    url: result.url,
                    source: result.source,
                    model_name: result.model_name,
                    civitai_url: result.civitai_url,
                    hf_repo: result.hf_repo,
                    from_cache: result.from_cache
                };

                // Show notification instead of alert
                const fromCache = result.from_cache ? ' (cached)' : '';
                this.showNotification(`Found URL for ${model.filename}${fromCache}`, 'success');

                // Re-render the row with URL and info icon
                this.updateRowWithUrl(index);
            } else if (result.suggestions && result.suggestions.length > 0) {
                // Store suggestions as metadata
                model.search_metadata = {
                    suggestions: result.suggestions,
                    search_method: 'tavily_suggestions'
                };

                // Show notification
                this.showNotification(`Found ${result.suggestions.length} suggestions for ${model.filename}. Check info icon for details.`, 'info');

                // Add info icon to show suggestions
                this.addSuggestionsInfoIcon(index, result.suggestions);

                if (searchBtn) {
                    searchBtn.disabled = false;
                    searchBtn.textContent = "Advanced Search";
                }
            } else {
                this.showNotification(`No results found for ${model.filename}`, 'error');
                if (searchBtn) {
                    searchBtn.disabled = false;
                    searchBtn.textContent = "Advanced Search";
                }
            }
        } catch (error) {
            console.error("[WMD] Advanced search error:", error);
            this.showNotification(`Search error: ${error.message}`, 'error');
            if (searchBtn) {
                searchBtn.disabled = false;
                searchBtn.textContent = "Advanced Search";
            }
        }
    }

    addSuggestionsInfoIcon(index, suggestions) {
        const actionButtons = document.querySelector(`#wmd-row-${index} .wmd-action-buttons`);
        if (!actionButtons) return;

        // Remove existing info icon if any
        const existingIcon = actionButtons.querySelector('.wmd-info-icon');
        if (existingIcon) existingIcon.remove();

        // Build suggestions tooltip content
        let tooltipContent = suggestions.map((s, i) => `
            <div class="wmd-info-tooltip-row">
                <div class="wmd-info-tooltip-label">Result ${i + 1}</div>
                <div class="wmd-info-tooltip-value">
                    <a href="${s.url}" target="_blank">${s.title || s.url}</a>
                </div>
            </div>
        `).join('');

        const infoIcon = document.createElement('span');
        infoIcon.className = 'wmd-info-icon';
        infoIcon.innerHTML = `i<div class="wmd-info-tooltip">
            <div class="wmd-info-tooltip-row">
                <div class="wmd-info-tooltip-label">Search Suggestions</div>
                <div class="wmd-info-tooltip-value" style="color: #888; font-size: 11px;">Click links to find model</div>
            </div>
            ${tooltipContent}
        </div>`;

        actionButtons.appendChild(infoIcon);
    }

    async lookupHash(index) {
        const model = this.models[index];
        if (!model || !model.exists) return;

        const hashBtn = document.getElementById(`wmd-hash-btn-${index}`);
        if (hashBtn) {
            hashBtn.disabled = true;
            hashBtn.textContent = "Calculating...";
        }

        try {
            const response = await api.fetchApi("/workflow-models/lookup-hash", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    filename: model.filename,
                    directory: model.directory
                })
            });

            const result = await response.json();

            if (result.success && result.url) {
                // Update model with found URL
                model.url = result.url;
                model.url_source = 'civitai_hash';
                model.civitai_url = result.civitai_url;
                model.civitai_model_name = result.model_name;

                // Show success message with model info
                const info = `Found on CivitAI!\n\nModel: ${result.model_name}\nType: ${result.model_type}\nVersion: ${result.version_name}\nOriginal filename: ${result.original_filename}\n\nCivitAI page: ${result.civitai_url}`;
                alert(info);

                // Re-render the row with download button
                this.updateRowWithUrl(index);
            } else {
                const msg = result.hash
                    ? `Model not found on CivitAI.\n\nSHA256: ${result.hash.substring(0, 16)}...\n\nThis model may not be from CivitAI, or may have been modified.`
                    : `Could not calculate hash or lookup failed.`;
                alert(msg);

                if (hashBtn) {
                    hashBtn.disabled = false;
                    hashBtn.textContent = "Lookup Hash";
                }
            }
        } catch (error) {
            console.error("[WMD] Hash lookup error:", error);
            alert(`Error looking up hash: ${error.message}`);
            if (hashBtn) {
                hashBtn.disabled = false;
                hashBtn.textContent = "Lookup Hash";
            }
        }
    }

    async cancelDownload(index) {
        const model = this.models[index];
        const downloadId = this.downloads[index];
        if (!model || !downloadId) return;

        const cancelBtn = document.getElementById(`wmd-cancel-${index}`);
        if (cancelBtn) {
            cancelBtn.disabled = true;
            cancelBtn.style.opacity = "0.5";
        }

        try {
            const response = await api.fetchApi(`/workflow-models/cancel/${encodeURIComponent(downloadId)}`, {
                method: "POST"
            });

            const result = await response.json();

            if (result.success) {
                this.updateDownloadStatus(index, "cancelled", "Download cancelled");

                // Hide progress, show download button again
                const progressDiv = document.getElementById(`wmd-progress-${index}`);
                const dlBtn = document.getElementById(`wmd-dl-btn-${index}`);

                if (progressDiv) progressDiv.style.display = "none";
                if (dlBtn) {
                    dlBtn.style.display = "inline-block";
                    dlBtn.disabled = false;
                }
            }
        } catch (error) {
            console.error("[WMD] Cancel download error:", error);
            if (cancelBtn) {
                cancelBtn.disabled = false;
                cancelBtn.style.opacity = "1";
            }
        }
    }

    updateRowWithUrl(index) {
        const model = this.models[index];
        const row = document.getElementById(`wmd-row-${index}`);
        if (!row || !model.url) return;

        // Update source column
        const sourceCell = row.cells[4];
        const sourceBadge = this.getSourceBadge(model);
        if (model.hf_repo) {
            sourceCell.innerHTML = `<a href="https://huggingface.co/${model.hf_repo}" target="_blank" class="wmd-hf-link">${model.hf_repo}</a>${sourceBadge}`;
        } else {
            sourceCell.innerHTML = `<span style="color:#888;">Direct URL</span>${sourceBadge}`;
        }

        // Build info icon if metadata exists
        const infoIcon = this.buildMetadataInfoIcon(model);

        // Update action column with download button
        const actionCell = row.cells[5];
        const btnClass = model.exists ? "wmd-btn-warning" : "wmd-btn-primary";
        const btnText = model.exists ? "Re-download" : "Download";
        actionCell.innerHTML = `
            <div class="wmd-action-cell">
                <div class="wmd-action-buttons">
                    <button class="wmd-btn ${btnClass} wmd-btn-small"
                            id="wmd-dl-btn-${index}"
                            onclick="window.wmdInstance.downloadModel(${index})">
                        ${btnText}
                    </button>
                    ${infoIcon}
                </div>
                <div id="wmd-progress-${index}" style="display:none;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div class="wmd-progress-bar" style="flex: 1;">
                            <div class="wmd-progress-fill" id="wmd-progress-fill-${index}" style="width: 0%"></div>
                        </div>
                        <button class="wmd-cancel-btn" id="wmd-cancel-${index}"
                                onclick="window.wmdInstance.cancelDownload(${index})"
                                title="Cancel download">
                            \u00D7
                        </button>
                    </div>
                    <div class="wmd-download-status" id="wmd-status-${index}">Starting...</div>
                </div>
            </div>
        `;

        this.updateSummary();
    }

    buildMetadataInfoIcon(model) {
        const metadata = model.search_metadata;
        if (!metadata) return '';

        let tooltipRows = [];

        if (metadata.source) {
            tooltipRows.push(`
                <div class="wmd-info-tooltip-row">
                    <div class="wmd-info-tooltip-label">Source</div>
                    <div class="wmd-info-tooltip-value">${metadata.source}</div>
                </div>
            `);
        }

        if (metadata.model_name) {
            tooltipRows.push(`
                <div class="wmd-info-tooltip-row">
                    <div class="wmd-info-tooltip-label">Model Name</div>
                    <div class="wmd-info-tooltip-value">${metadata.model_name}</div>
                </div>
            `);
        }

        if (metadata.hf_repo) {
            tooltipRows.push(`
                <div class="wmd-info-tooltip-row">
                    <div class="wmd-info-tooltip-label">HuggingFace Repo</div>
                    <div class="wmd-info-tooltip-value">
                        <a href="https://huggingface.co/${metadata.hf_repo}" target="_blank">${metadata.hf_repo}</a>
                    </div>
                </div>
            `);
        }

        if (metadata.civitai_url) {
            tooltipRows.push(`
                <div class="wmd-info-tooltip-row">
                    <div class="wmd-info-tooltip-label">CivitAI Page</div>
                    <div class="wmd-info-tooltip-value">
                        <a href="${metadata.civitai_url}" target="_blank">View on CivitAI</a>
                    </div>
                </div>
            `);
        }

        if (metadata.cached_at) {
            const cachedDate = new Date(metadata.cached_at).toLocaleDateString();
            tooltipRows.push(`
                <div class="wmd-info-tooltip-row">
                    <div class="wmd-info-tooltip-label">Cached</div>
                    <div class="wmd-info-tooltip-value">${cachedDate}</div>
                </div>
            `);
        }

        if (tooltipRows.length === 0) return '';

        return `
            <span class="wmd-info-icon">i
                <div class="wmd-info-tooltip">
                    <div class="wmd-info-tooltip-row">
                        <div class="wmd-info-tooltip-label" style="font-size: 11px; color: #4CAF50;">Search Metadata</div>
                    </div>
                    ${tooltipRows.join('')}
                </div>
            </span>
        `;
    }

    buildSuggestionsInfoIcon(model) {
        const metadata = model.search_metadata;
        if (!metadata || !metadata.suggestions || metadata.suggestions.length === 0) return '';

        const suggestions = metadata.suggestions;
        let tooltipContent = suggestions.slice(0, 5).map((s, i) => `
            <div class="wmd-info-tooltip-row">
                <div class="wmd-info-tooltip-label">Result ${i + 1}</div>
                <div class="wmd-info-tooltip-value">
                    <a href="${s.url}" target="_blank">${s.title || 'View Link'}</a>
                </div>
            </div>
        `).join('');

        return `
            <span class="wmd-info-icon" style="background-color: #FF9800;">i
                <div class="wmd-info-tooltip">
                    <div class="wmd-info-tooltip-row">
                        <div class="wmd-info-tooltip-label" style="font-size: 11px; color: #FF9800;">Previous Search Results</div>
                        <div class="wmd-info-tooltip-value" style="color: #888; font-size: 11px;">Click links to find model manually</div>
                    </div>
                    ${tooltipContent}
                </div>
            </span>
        `;
    }

    async downloadFromManualUrl(index) {
        const model = this.models[index];
        if (!model) return;

        const urlInput = document.getElementById(`wmd-url-input-${index}`);
        const url = urlInput?.value?.trim();

        if (!url) {
            alert("Please enter a URL");
            return;
        }

        // Validate URL format
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            alert("Please enter a valid URL starting with http:// or https://");
            return;
        }

        // Hide input row, show progress
        const urlRow = document.getElementById(`wmd-url-row-${index}`);
        const searchBtn = document.getElementById(`wmd-search-btn-${index}`);
        const progressDiv = document.getElementById(`wmd-progress-${index}`);

        if (urlRow) urlRow.style.display = "none";
        if (searchBtn) searchBtn.style.display = "none";
        if (progressDiv) progressDiv.style.display = "block";

        try {
            const response = await api.fetchApi("/workflow-models/download-url", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: url,
                    filename: model.filename,
                    directory: model.directory
                })
            });

            const result = await response.json();

            if (result.success) {
                this.downloads[index] = result.download_id;
                // Track in background downloads
                backgroundDownloads[result.download_id] = { status: 'starting', filename: model.filename };
                this.startProgressPolling();
                // Start background polling for notifications when modal is closed
                startBackgroundPolling();
            } else {
                this.updateDownloadStatus(index, "error", result.error);
                if (urlRow) urlRow.style.display = "flex";
                if (searchBtn) searchBtn.style.display = "inline-block";
            }
        } catch (error) {
            console.error("[WMD] Manual URL download error:", error);
            this.updateDownloadStatus(index, "error", error.message);
            if (urlRow) urlRow.style.display = "flex";
            if (searchBtn) searchBtn.style.display = "inline-block";
        }
    }

    async onDirectoryChange(index, newDirectory) {
        const model = this.models[index];
        if (!model) return;

        // Update model directory
        model.directory = newDirectory;

        // Update status cell to show checking
        const statusCell = document.getElementById(`wmd-status-cell-${index}`);
        if (statusCell) {
            statusCell.className = "wmd-status-checking";
            statusCell.textContent = "Checking...";
        }

        // Check if model exists in new directory
        try {
            const response = await api.fetchApi("/workflow-models/check-exists", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    filename: model.filename,
                    directory: newDirectory
                })
            });

            const result = await response.json();

            // Update model status
            model.exists = result.exists;
            model.local_size = result.size || "";

            // Update UI
            if (statusCell) {
                if (result.exists) {
                    statusCell.className = "wmd-status-exists";
                    statusCell.textContent = `EXISTS (${result.size})`;
                } else {
                    statusCell.className = "wmd-status-missing";
                    statusCell.textContent = "MISSING";
                }
            }

            // Update download button text
            const dlBtn = document.getElementById(`wmd-dl-btn-${index}`);
            if (dlBtn) {
                if (result.exists) {
                    dlBtn.className = "wmd-btn wmd-btn-warning wmd-btn-small";
                    dlBtn.textContent = "Re-download";
                } else {
                    dlBtn.className = "wmd-btn wmd-btn-primary wmd-btn-small";
                    dlBtn.textContent = "Download";
                }
            }

            // Recalculate summary
            this.updateSummary();

        } catch (error) {
            console.error("[WMD] Check exists error:", error);
            if (statusCell) {
                statusCell.className = "wmd-status-missing";
                statusCell.textContent = "Error checking";
            }
        }
    }

    updateSummary() {
        const total = this.models.length;
        const existing = this.models.filter(m => m.exists).length;
        const missing = total - existing;
        const downloadable = this.models.filter(m => !m.exists && m.url).length;

        // Update download all button
        const downloadAllBtn = document.getElementById("wmd-download-all-btn");
        if (downloadAllBtn) {
            if (downloadable > 0) {
                downloadAllBtn.style.display = "inline-block";
                downloadAllBtn.textContent = `Download All Missing (${downloadable})`;
            } else {
                downloadAllBtn.style.display = "none";
            }
        }

        // Re-apply filter to update row visibility and footer counts
        this.applyFilter();
    }

    getFilteredModels() {
        switch (this.currentFilter) {
            case "existing":
                return this.models.filter(m => m.exists);
            case "ready":
                return this.models.filter(m => !m.exists && m.url);
            case "unknown":
                return this.models.filter(m => !m.exists && !m.url);
            default:
                return this.models;
        }
    }

    onFilterChange(filter) {
        this.currentFilter = filter;
        this.applyFilter();
    }

    applyFilter() {
        // Show/hide rows based on filter
        for (let i = 0; i < this.models.length; i++) {
            const model = this.models[i];
            const row = document.getElementById(`wmd-row-${i}`);
            if (!row) continue;

            let show = false;
            switch (this.currentFilter) {
                case "existing":
                    show = model.exists;
                    break;
                case "ready":
                    show = !model.exists && model.url;
                    break;
                case "unknown":
                    show = !model.exists && !model.url;
                    break;
                default:
                    show = true;
            }

            row.style.display = show ? "" : "none";
        }

        // Update filter count in footer
        const filteredCount = this.getFilteredModels().length;
        const footerInfo = document.getElementById("wmd-footer-info");
        if (footerInfo) {
            const total = this.models.length;
            const existing = this.models.filter(m => m.exists).length;
            const missing = total - existing;

            if (this.currentFilter === "all") {
                footerInfo.textContent = `Total: ${total} | Existing: ${existing} | Missing: ${missing}`;
            } else {
                footerInfo.textContent = `Showing: ${filteredCount} | Total: ${total} | Existing: ${existing} | Missing: ${missing}`;
            }
        }
    }

    showError(message) {
        const body = document.getElementById("wmd-body");
        body.innerHTML = `
            <div class="wmd-empty" style="color: #f44336;">
                <p>Error: ${message}</p>
            </div>
        `;
    }

    async downloadModel(index) {
        const model = this.models[index];
        if (!model) return;

        const btn = document.getElementById(`wmd-dl-btn-${index}`);
        const progressDiv = document.getElementById(`wmd-progress-${index}`);

        if (btn) btn.style.display = "none";
        if (progressDiv) progressDiv.style.display = "block";

        try {
            let response;

            if (model.hf_repo) {
                // Use HuggingFace download
                response = await api.fetchApi("/workflow-models/download", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        hf_repo: model.hf_repo,
                        hf_path: model.hf_path || model.filename,
                        filename: model.filename,
                        directory: model.directory,
                        force: model.exists
                    })
                });
            } else if (model.url) {
                // Use direct URL download
                response = await api.fetchApi("/workflow-models/download-url", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        url: model.url,
                        filename: model.filename,
                        directory: model.directory
                    })
                });
            } else {
                throw new Error("No download URL available");
            }

            const result = await response.json();

            if (result.success) {
                this.downloads[index] = result.download_id;
                // Track in background downloads
                backgroundDownloads[result.download_id] = { status: 'starting', filename: model.filename };
                this.startProgressPolling();
                // Start background polling for notifications when modal is closed
                startBackgroundPolling();
            } else {
                this.updateDownloadStatus(index, "error", result.error);
                if (btn) btn.style.display = "inline-block";
            }
        } catch (error) {
            console.error("[WMD] Download error:", error);
            this.updateDownloadStatus(index, "error", error.message);
            if (btn) btn.style.display = "inline-block";
        }
    }

    async downloadAllMissing() {
        const btn = document.getElementById("wmd-download-all-btn");
        if (btn) {
            btn.disabled = true;
            btn.textContent = "Downloading...";
        }

        for (let i = 0; i < this.models.length; i++) {
            const model = this.models[i];
            if (!model.exists && model.url) {
                await this.downloadModel(i);
                // Small delay between starting downloads
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }
    }

    startProgressPolling() {
        if (this.progressInterval) return;

        this.progressInterval = setInterval(async () => {
            try {
                const response = await api.fetchApi("/workflow-models/progress");
                const allProgress = await response.json();

                let hasActiveDownloads = false;

                for (const [index, downloadId] of Object.entries(this.downloads)) {
                    const progress = allProgress[downloadId];
                    if (progress) {
                        this.updateDownloadUI(index, progress);
                        if (progress.status === "downloading" || progress.status === "starting") {
                            hasActiveDownloads = true;
                        }
                    }
                }

                if (!hasActiveDownloads && Object.keys(this.downloads).length > 0) {
                    clearInterval(this.progressInterval);
                    this.progressInterval = null;
                }
            } catch (error) {
                console.error("[WMD] Progress poll error:", error);
            }
        }, 1000);
    }

    updateDownloadUI(index, progress) {
        const progressFill = document.getElementById(`wmd-progress-fill-${index}`);
        const statusDiv = document.getElementById(`wmd-status-${index}`);
        const dlBtn = document.getElementById(`wmd-dl-btn-${index}`);
        const statusCell = document.getElementById(`wmd-status-cell-${index}`);
        const cancelBtn = document.getElementById(`wmd-cancel-${index}`);

        if (progressFill) {
            progressFill.style.width = `${progress.progress || 0}%`;
        }

        if (statusDiv) {
            if (progress.status === "completed") {
                statusDiv.textContent = "Completed!";
                statusDiv.style.color = "#4CAF50";

                // Hide cancel button on completion
                if (cancelBtn) cancelBtn.style.display = "none";

                // Update model status
                this.models[index].exists = true;

                // Update status cell
                if (statusCell) {
                    statusCell.className = "wmd-status-exists";
                    // Re-check to get accurate size
                    this.recheckModelStatus(index);
                }

                // Show re-download button
                if (dlBtn) {
                    dlBtn.style.display = "inline-block";
                    dlBtn.className = "wmd-btn wmd-btn-warning wmd-btn-small";
                    dlBtn.textContent = "Re-download";
                }

                this.updateSummary();

            } else if (progress.status === "error") {
                statusDiv.textContent = `Error: ${progress.error}`;
                statusDiv.style.color = "#f44336";
                // Hide cancel button on error
                if (cancelBtn) cancelBtn.style.display = "none";
                if (dlBtn) dlBtn.style.display = "inline-block";

            } else if (progress.status === "cancelled") {
                statusDiv.textContent = "Cancelled";
                statusDiv.style.color = "#ff9800";
                // Hide cancel button
                if (cancelBtn) cancelBtn.style.display = "none";

            } else if (progress.status === "downloading") {
                const downloaded = this.formatSize(progress.downloaded || 0);
                const total = this.formatSize(progress.total_size || 0);
                statusDiv.textContent = `${downloaded} / ${total} (${progress.progress || 0}%)`;

            } else {
                statusDiv.textContent = progress.status || "Starting...";
            }
        }
    }

    async recheckModelStatus(index) {
        const model = this.models[index];
        if (!model) return;

        try {
            const response = await api.fetchApi("/workflow-models/check-exists", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    filename: model.filename,
                    directory: model.directory
                })
            });

            const result = await response.json();

            model.exists = result.exists;
            model.local_size = result.size || "";

            const statusCell = document.getElementById(`wmd-status-cell-${index}`);
            if (statusCell && result.exists) {
                statusCell.textContent = `EXISTS (${result.size})`;
            }
        } catch (error) {
            console.error("[WMD] Recheck status error:", error);
        }
    }

    updateDownloadStatus(index, status, message) {
        const statusDiv = document.getElementById(`wmd-status-${index}`);
        if (statusDiv) {
            statusDiv.textContent = message || status;
            statusDiv.style.color = status === "error" ? "#f44336" : "#888";
        }
    }

    formatSize(bytes) {
        if (bytes === 0) return "0 B";
        const k = 1024;
        const sizes = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
    }

    async toggleSettings() {
        this.showSettings = !this.showSettings;
        const body = document.getElementById("wmd-body");

        if (this.showSettings) {
            // Load current settings
            await this.loadSettings();
            // Insert settings panel at the top
            const settingsPanel = this.createSettingsPanel();
            body.insertBefore(settingsPanel, body.firstChild);
        } else {
            // Remove settings panel
            const panel = document.getElementById("wmd-settings-panel");
            if (panel) panel.remove();
        }
    }

    async loadSettings() {
        try {
            const response = await api.fetchApi("/workflow-models/settings");
            this.settings = await response.json();
        } catch (error) {
            console.error("[WMD] Error loading settings:", error);
            this.settings = {
                huggingface_token: '',
                civitai_api_key: '',
                huggingface_token_set: false,
                civitai_api_key_set: false
            };
        }
    }

    createSettingsPanel() {
        const panel = document.createElement('div');
        panel.id = 'wmd-settings-panel';
        panel.className = 'wmd-settings-panel';

        const hfStatus = this.settings?.huggingface_token_set ? 'set' : 'not-set';
        const hfStatusText = this.settings?.huggingface_token_set ? 'Configured' : 'Not Set';
        const civitStatus = this.settings?.civitai_api_key_set ? 'set' : 'not-set';
        const civitStatusText = this.settings?.civitai_api_key_set ? 'Configured' : 'Not Set';
        const tavilyStatus = this.settings?.tavily_api_key_set ? 'set' : 'not-set';
        const tavilyStatusText = this.settings?.tavily_api_key_set ? 'Configured' : 'Not Set';
        const advancedSearchEnabled = this.settings?.enable_advanced_search || false;

        panel.innerHTML = `
            <div class="wmd-settings-title">
                <span>\u2699</span> API Settings
            </div>

            <div class="wmd-settings-row">
                <label class="wmd-settings-label">HuggingFace Token</label>
                <input type="password"
                       class="wmd-settings-input"
                       id="wmd-hf-token"
                       placeholder="${this.settings?.huggingface_token_set ? '••••••••••••' : 'Enter your HuggingFace token'}"
                       value="">
                <span class="wmd-settings-status ${hfStatus}">${hfStatusText}</span>
            </div>
            <div class="wmd-settings-hint" style="margin-left: 152px; margin-bottom: 14px;">
                Get your token at <a href="https://huggingface.co/settings/tokens" target="_blank" class="wmd-settings-link">huggingface.co/settings/tokens</a>
                - Required for gated models (Flux, SD3, etc.)
            </div>

            <div class="wmd-settings-row">
                <label class="wmd-settings-label">CivitAI API Key</label>
                <input type="password"
                       class="wmd-settings-input"
                       id="wmd-civit-key"
                       placeholder="${this.settings?.civitai_api_key_set ? '••••••••••••' : 'Enter your CivitAI API key'}"
                       value="">
                <span class="wmd-settings-status ${civitStatus}">${civitStatusText}</span>
            </div>
            <div class="wmd-settings-hint" style="margin-left: 152px; margin-bottom: 14px;">
                Get your API key at <a href="https://civitai.com/user/account" target="_blank" class="wmd-settings-link">civitai.com/user/account</a>
                - Required for downloading from CivitAI
            </div>

            <div class="wmd-settings-row">
                <label class="wmd-settings-label">Tavily API Key</label>
                <input type="password"
                       class="wmd-settings-input"
                       id="wmd-tavily-key"
                       placeholder="${this.settings?.tavily_api_key_set ? '••••••••••••' : 'Enter your Tavily API key'}"
                       value="">
                <span class="wmd-settings-status ${tavilyStatus}">${tavilyStatusText}</span>
            </div>
            <div class="wmd-settings-hint" style="margin-left: 152px; margin-bottom: 14px;">
                Get your API key at <a href="https://tavily.com" target="_blank" class="wmd-settings-link">tavily.com</a>
                - Required for Advanced Search feature
            </div>

            <div class="wmd-settings-row" style="margin-top: 10px;">
                <label class="wmd-settings-label">Advanced Search</label>
                <label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                    <input type="checkbox"
                           id="wmd-advanced-search-enabled"
                           ${advancedSearchEnabled ? 'checked' : ''}
                           ${!this.settings?.tavily_api_key_set ? 'disabled' : ''}
                           style="width: 18px; height: 18px; cursor: pointer;">
                    <span style="color: ${this.settings?.tavily_api_key_set ? '#ddd' : '#666'};">
                        Enable Advanced Search (uses Tavily AI)
                    </span>
                </label>
            </div>
            <div class="wmd-settings-hint" style="margin-left: 152px;">
                When enabled, replaces "Search URL" with "Advanced Search" using AI-powered web search
            </div>

            <div class="wmd-settings-actions">
                <button class="wmd-btn wmd-btn-secondary" onclick="window.wmdInstance.clearSettings()">
                    Clear All
                </button>
                <button class="wmd-btn wmd-btn-primary" onclick="window.wmdInstance.saveSettings()">
                    Save Settings
                </button>
            </div>
        `;

        return panel;
    }

    async saveSettings() {
        const hfToken = document.getElementById('wmd-hf-token')?.value || '';
        const civitKey = document.getElementById('wmd-civit-key')?.value || '';
        const tavilyKey = document.getElementById('wmd-tavily-key')?.value || '';
        const advancedSearchEnabled = document.getElementById('wmd-advanced-search-enabled')?.checked || false;

        const data = {};

        // Only include if user entered a new value
        if (hfToken && !hfToken.startsWith('•')) {
            data.huggingface_token = hfToken;
        }
        if (civitKey && !civitKey.startsWith('•')) {
            data.civitai_api_key = civitKey;
        }
        if (tavilyKey && !tavilyKey.startsWith('•')) {
            data.tavily_api_key = tavilyKey;
        }

        // Always save the checkbox state
        data.enable_advanced_search = advancedSearchEnabled;

        // If only checkbox changed (no new keys), still save
        const hasNewKeys = Object.keys(data).filter(k => k !== 'enable_advanced_search').length > 0;
        const checkboxChanged = advancedSearchEnabled !== this.settings?.enable_advanced_search;

        if (!hasNewKeys && !checkboxChanged) {
            this.showSettings = false;
            const panel = document.getElementById("wmd-settings-panel");
            if (panel) panel.remove();
            return;
        }

        try {
            const response = await api.fetchApi("/workflow-models/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                // Refresh settings and update UI
                await this.loadSettings();

                // Update status badges
                const hfStatusEl = document.querySelector('#wmd-settings-panel .wmd-settings-row:first-of-type .wmd-settings-status');
                const civitStatusEl = document.querySelector('#wmd-settings-panel .wmd-settings-row:last-of-type .wmd-settings-status');

                if (hfStatusEl) {
                    hfStatusEl.className = `wmd-settings-status ${this.settings.huggingface_token_set ? 'set' : 'not-set'}`;
                    hfStatusEl.textContent = this.settings.huggingface_token_set ? 'Configured' : 'Not Set';
                }
                if (civitStatusEl) {
                    civitStatusEl.className = `wmd-settings-status ${this.settings.civitai_api_key_set ? 'set' : 'not-set'}`;
                    civitStatusEl.textContent = this.settings.civitai_api_key_set ? 'Configured' : 'Not Set';
                }

                // Clear input fields
                document.getElementById('wmd-hf-token').value = '';
                document.getElementById('wmd-civit-key').value = '';
                document.getElementById('wmd-hf-token').placeholder = this.settings.huggingface_token_set ? '••••••••••••' : 'Enter your HuggingFace token';
                document.getElementById('wmd-civit-key').placeholder = this.settings.civitai_api_key_set ? '••••••••••••' : 'Enter your CivitAI API key';

                // Show success notification
                this.showNotification('Settings saved successfully', 'success');
            } else {
                this.showNotification('Failed to save settings: ' + (result.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error("[WMD] Save settings error:", error);
            this.showNotification('Error saving settings: ' + error.message, 'error');
        }
    }

    async clearSettings() {
        if (!confirm('Are you sure you want to clear all API keys?')) {
            return;
        }

        try {
            const response = await api.fetchApi("/workflow-models/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    huggingface_token: '',
                    civitai_api_key: '',
                    tavily_api_key: '',
                    enable_advanced_search: false
                })
            });

            const result = await response.json();

            if (result.success) {
                await this.loadSettings();

                // Update UI
                const panel = document.getElementById("wmd-settings-panel");
                if (panel) {
                    panel.remove();
                    const newPanel = this.createSettingsPanel();
                    document.getElementById("wmd-body").insertBefore(newPanel, document.getElementById("wmd-body").firstChild);
                }

                this.showNotification('Settings cleared', 'success');
            }
        } catch (error) {
            console.error("[WMD] Clear settings error:", error);
            this.showNotification('Error clearing settings: ' + error.message, 'error');
        }
    }

    showNotification(message, type = 'info') {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #1a1a1a;
            border: 1px solid ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
            border-radius: 8px;
            padding: 16px 20px;
            color: #fff;
            font-size: 14px;
            z-index: 10002;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            animation: wmd-slide-in 0.3s ease;
        `;

        const icon = type === 'success' ? '\u2713' : type === 'error' ? '\u2717' : '\u2139';
        const color = type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3';

        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="color: ${color}; font-size: 20px;">${icon}</span>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'wmd-slide-out 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// Global instance - persists across modal open/close
let wmdInstance = null;

// Track background downloads globally
let backgroundDownloads = {};
let backgroundPollInterval = null;

function startBackgroundPolling() {
    if (backgroundPollInterval) return;

    backgroundPollInterval = setInterval(async () => {
        try {
            const response = await api.fetchApi("/workflow-models/progress");
            const allProgress = await response.json();

            let hasActiveDownloads = false;
            let completedDownloads = [];

            for (const [downloadId, progress] of Object.entries(allProgress)) {
                if (progress.status === 'downloading' || progress.status === 'starting') {
                    hasActiveDownloads = true;
                    backgroundDownloads[downloadId] = progress;
                } else if (progress.status === 'completed' && backgroundDownloads[downloadId]) {
                    // Download just completed
                    completedDownloads.push(progress.filename || downloadId);
                    delete backgroundDownloads[downloadId];
                }
            }

            // Show notification for completed downloads
            if (completedDownloads.length > 0) {
                showDownloadNotification(completedDownloads);
            }

            // Stop polling if no active downloads
            if (!hasActiveDownloads) {
                clearInterval(backgroundPollInterval);
                backgroundPollInterval = null;
                backgroundDownloads = {};
            }
        } catch (error) {
            console.error("[WMD] Background poll error:", error);
        }
    }, 2000);
}

function showDownloadNotification(filenames) {
    // Create a toast notification
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #1a1a1a;
        border: 1px solid #4CAF50;
        border-radius: 8px;
        padding: 16px 20px;
        color: #fff;
        font-size: 14px;
        z-index: 10001;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        max-width: 300px;
        animation: wmd-slide-in 0.3s ease;
    `;

    const title = filenames.length === 1
        ? 'Download Complete'
        : `${filenames.length} Downloads Complete`;

    toast.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="color: #4CAF50; font-size: 20px;">✓</span>
            <div>
                <strong>${title}</strong>
                <div style="color: #888; font-size: 12px; margin-top: 4px;">
                    ${filenames.slice(0, 3).join(', ')}${filenames.length > 3 ? '...' : ''}
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(toast);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        toast.style.animation = 'wmd-slide-out 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// Add notification animation styles
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
@keyframes wmd-slide-in {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}
@keyframes wmd-slide-out {
    from { transform: translateX(0); opacity: 1; }
    to { transform: translateX(100%); opacity: 0; }
}
`;
document.head.appendChild(notificationStyles);

function showMissingModelsDialog() {
    if (!wmdInstance) {
        wmdInstance = new WorkflowModelsDownloader();
    }
    wmdInstance.show();
}

// Register the extension
app.registerExtension({
    name: "Comfy.WorkflowModelsDownloader",

    async setup() {
        console.log(`[Workflow-Models-Downloader] v${VERSION} initializing...`);

        // Register settings in ComfyUI Settings panel
        app.ui.settings.addSetting({
            id: "WorkflowModelsDownloader.HuggingFaceToken",
            category: ["Workflow Models Downloader", "API Keys", "HuggingFace"],
            name: "HuggingFace Token",
            tooltip: "Your HuggingFace access token for downloading gated models (Flux, SD3, etc.). Get it at huggingface.co/settings/tokens",
            type: "text",
            defaultValue: "",
            onChange: async (value) => {
                if (value && !value.startsWith('***')) {
                    try {
                        await api.fetchApi("/workflow-models/settings", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ huggingface_token: value })
                        });
                    } catch (e) {
                        console.error("[WMD] Failed to save HuggingFace token:", e);
                    }
                }
            }
        });

        app.ui.settings.addSetting({
            id: "WorkflowModelsDownloader.CivitAIApiKey",
            category: ["Workflow Models Downloader", "API Keys", "CivitAI"],
            name: "CivitAI API Key",
            tooltip: "Your CivitAI API key for downloading models. Get it at civitai.com/user/account",
            type: "text",
            defaultValue: "",
            onChange: async (value) => {
                if (value && !value.startsWith('***')) {
                    try {
                        await api.fetchApi("/workflow-models/settings", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ civitai_api_key: value })
                        });
                    } catch (e) {
                        console.error("[WMD] Failed to save CivitAI API key:", e);
                    }
                }
            }
        });

        app.ui.settings.addSetting({
            id: "WorkflowModelsDownloader.TavilyApiKey",
            category: ["Workflow Models Downloader", "API Keys", "Tavily"],
            name: "Tavily API Key",
            tooltip: "Your Tavily API key for Advanced Search feature. Get it at tavily.com",
            type: "text",
            defaultValue: "",
            onChange: async (value) => {
                if (value && !value.startsWith('***')) {
                    try {
                        await api.fetchApi("/workflow-models/settings", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ tavily_api_key: value })
                        });
                    } catch (e) {
                        console.error("[WMD] Failed to save Tavily API key:", e);
                    }
                }
            }
        });

        app.ui.settings.addSetting({
            id: "WorkflowModelsDownloader.EnableAdvancedSearch",
            category: ["Workflow Models Downloader", "Features"],
            name: "Enable Advanced Search",
            tooltip: "When enabled, uses Tavily AI-powered search instead of basic URL search. Requires Tavily API key.",
            type: "boolean",
            defaultValue: false,
            onChange: async (value) => {
                try {
                    await api.fetchApi("/workflow-models/settings", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ enable_advanced_search: value })
                    });
                } catch (e) {
                    console.error("[WMD] Failed to save Advanced Search setting:", e);
                }
            }
        });

        // Try new-style menu first
        try {
            const { ComfyButton } = await import("../../scripts/ui/components/button.js");

            const wmdButton = new ComfyButton({
                icon: "download",
                action: showMissingModelsDialog,
                tooltip: "Scan workflow for missing models and download from HuggingFace",
                content: "Missing Models",
                classList: "comfyui-button comfyui-menu-mobile-collapse"
            });

            // Add to new menu
            if (app.menu?.settingsGroup?.element) {
                app.menu.settingsGroup.element.before(wmdButton.element);
                console.log("[Workflow-Models-Downloader] Added button to new-style menu");
            }
        } catch (e) {
            console.log("[Workflow-Models-Downloader] New-style menu not available:", e.message);
        }

        // Also add to old-style menu (sidebar)
        const menu = document.querySelector(".comfy-menu");
        if (menu) {
            const separator = document.createElement("hr");
            separator.style.margin = "20px 0";
            separator.style.width = "100%";
            menu.append(separator);

            const button = document.createElement("button");
            button.textContent = "Missing Models";
            button.onclick = showMissingModelsDialog;
            menu.append(button);

            console.log("[Workflow-Models-Downloader] Added button to old-style menu");
        }

        console.log(`[Workflow-Models-Downloader] v${VERSION} loaded successfully`);
    }
});
