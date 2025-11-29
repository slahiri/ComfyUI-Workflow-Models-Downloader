import { api } from "../../scripts/api.js";
import { app } from "../../scripts/app.js";
import { $el } from "../../scripts/ui.js";

const VERSION = "1.8.1";

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
    background-color: #3a3a3a;
    color: #ccc;
    border: 1px solid #555;
}

.wmd-btn-secondary:hover {
    background-color: #4a4a4a;
    color: #fff;
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

.wmd-unused-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    background-color: #8b5cf6;
    color: white;
    margin-left: 6px;
    white-space: nowrap;
}

.wmd-cache-controls {
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px solid #444;
}

.wmd-cache-controls-title {
    font-size: 12px;
    color: #888;
    margin-bottom: 8px;
    font-weight: 500;
}

.wmd-cache-info {
    font-size: 11px;
    color: #666;
    margin-bottom: 8px;
}

.wmd-cache-buttons {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.wmd-cache-buttons button {
    padding: 6px 10px;
    font-size: 11px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    text-align: left;
}

.wmd-cache-buttons button.scan {
    background: #2563eb;
    color: white;
}

.wmd-cache-buttons button.scan:hover {
    background: #1d4ed8;
}

.wmd-cache-buttons button.clear {
    background: #333;
    color: #aaa;
}

.wmd-cache-buttons button.clear:hover {
    background: #dc2626;
    color: white;
}

.wmd-scan-input {
    width: 100%;
    padding: 6px 8px;
    font-size: 11px;
    background: #333;
    border: 1px solid #444;
    border-radius: 4px;
    color: #ddd;
    margin-bottom: 6px;
}

.wmd-scan-input::placeholder {
    color: #666;
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

.wmd-confidence-badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: bold;
    margin-left: 6px;
}

.wmd-alternatives-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: bold;
    margin-left: 8px;
    background-color: #2196F3;
    color: #fff;
    cursor: pointer;
}

.wmd-alternatives-badge:hover {
    background-color: #1976D2;
}

.wmd-alternatives-popup {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: #2a2a2a;
    border: 1px solid #444;
    border-radius: 8px;
    padding: 20px;
    min-width: 400px;
    max-width: 600px;
    z-index: 10001;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}

.wmd-alternatives-popup h3 {
    margin: 0 0 16px 0;
    color: #4CAF50;
}

.wmd-alternatives-list {
    max-height: 300px;
    overflow-y: auto;
}

.wmd-alternative-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px;
    background: #1a1a1a;
    border-radius: 6px;
    margin-bottom: 8px;
}

.wmd-alternative-info {
    flex: 1;
}

.wmd-alternative-name {
    font-weight: bold;
    color: #fff;
    margin-bottom: 4px;
}

.wmd-alternative-meta {
    font-size: 12px;
    color: #888;
}

.wmd-format-badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 10px;
    font-weight: bold;
    background-color: #4a3a1a;
    color: #ff9800;
    margin-right: 8px;
}

.wmd-filename-cell {
    max-width: 300px;
    word-break: break-all;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.wmd-filename-wrapper {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
}

.wmd-filename-icons {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
}

.wmd-filename-link {
    color: #58a6ff;
    text-decoration: none;
    font-weight: bold;
}

.wmd-filename-link:hover {
    text-decoration: underline;
}

.wmd-filename-text {
    font-weight: bold;
}

.wmd-copy-btn {
    background: none;
    border: none;
    cursor: pointer;
    padding: 2px 4px;
    font-size: 12px;
    opacity: 0.5;
    margin-left: 6px;
    vertical-align: middle;
}

.wmd-copy-btn:hover {
    opacity: 1;
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

.wmd-help-btn {
    background: none;
    border: none;
    color: #888;
    font-size: 18px;
    cursor: pointer;
    padding: 4px 8px;
    margin-right: 6px;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}

.wmd-help-btn:hover {
    color: #fff;
    background-color: #2196F3;
}

.wmd-help-panel {
    background-color: #252525;
    border: 1px solid #444;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
}

.wmd-help-title {
    font-size: 16px;
    font-weight: bold;
    color: #fff;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.wmd-help-section {
    margin-bottom: 20px;
}

.wmd-help-section:last-child {
    margin-bottom: 0;
}

.wmd-help-section-title {
    font-size: 14px;
    font-weight: bold;
    color: #4CAF50;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.wmd-help-section-content {
    font-size: 13px;
    color: #ccc;
    line-height: 1.6;
    padding-left: 20px;
}

.wmd-help-section-content ol {
    margin: 8px 0;
    padding-left: 20px;
}

.wmd-help-section-content li {
    margin-bottom: 6px;
}

.wmd-help-section-content code {
    background-color: #333;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 12px;
    color: #ff9800;
}

.wmd-help-link {
    color: #5599ff;
    text-decoration: none;
}

.wmd-help-link:hover {
    text-decoration: underline;
}

.wmd-help-note {
    background-color: #1a3a4a;
    border-left: 3px solid #2196F3;
    padding: 10px 14px;
    margin: 10px 0;
    font-size: 12px;
    color: #aaa;
}

.wmd-help-warning {
    background-color: #4a3a1a;
    border-left: 3px solid #ff9800;
    padding: 10px 14px;
    margin: 10px 0;
    font-size: 12px;
    color: #ffcc80;
}

/* Tab Navigation */
.wmd-tabs {
    display: flex;
    gap: 0;
    background-color: #252525;
    border-bottom: 1px solid #444;
    padding: 0 16px;
}

.wmd-tab {
    background: none;
    border: none;
    color: #888;
    padding: 14px 24px;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s;
}

.wmd-tab:hover {
    color: #fff;
    background-color: rgba(255,255,255,0.05);
}

.wmd-tab.active {
    color: #4CAF50;
    border-bottom-color: #4CAF50;
}

.wmd-tab-badge {
    display: inline-block;
    background-color: #f44336;
    color: white;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 10px;
    margin-left: 6px;
    min-width: 18px;
    text-align: center;
}

.wmd-tab-badge.active-downloads {
    background-color: #2196F3;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.wmd-tab-content {
    display: none;
    height: 100%;
}

.wmd-tab-content.active {
    display: flex;
    flex-direction: column;
}

/* Downloads Tab */
.wmd-downloads-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 0;
    border-bottom: 1px solid #333;
    margin-bottom: 16px;
}

.wmd-downloads-stats {
    display: flex;
    gap: 24px;
}

.wmd-downloads-stat {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #888;
}

.wmd-downloads-stat-value {
    font-size: 18px;
    font-weight: bold;
    color: #fff;
}

.wmd-downloads-section {
    margin-bottom: 24px;
}

.wmd-downloads-section-title {
    font-size: 14px;
    font-weight: 600;
    color: #4CAF50;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.wmd-raw-download-section {
    background: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 20px;
}

.wmd-raw-download-input-row {
    display: flex;
    gap: 10px;
    align-items: center;
}

.wmd-raw-preview-card {
    background: #252525;
    border: 1px solid #444;
    border-radius: 8px;
    padding: 16px;
    margin-top: 12px;
}

.wmd-raw-preview-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
}

.wmd-raw-preview-row:last-of-type {
    margin-bottom: 0;
}

.wmd-raw-preview-label {
    min-width: 80px;
    color: #888;
    font-size: 13px;
}

.wmd-raw-preview-actions {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #333;
}

.wmd-download-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 16px;
    background-color: #2a2a2a;
    border-radius: 6px;
    margin-bottom: 8px;
}

.wmd-download-item-info {
    flex: 1;
    min-width: 0;
}

.wmd-download-item-name {
    color: #fff;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.wmd-download-item-meta {
    font-size: 12px;
    color: #888;
    margin-top: 4px;
}

.wmd-download-item-progress {
    width: 200px;
}

.wmd-download-item-actions {
    display: flex;
    gap: 8px;
}

/* Browser Tab */
.wmd-browser-controls {
    display: flex;
    gap: 12px;
    padding: 16px 0;
    border-bottom: 1px solid #333;
    margin-bottom: 16px;
    flex-wrap: wrap;
}

.wmd-browser-search {
    flex: 1;
    min-width: 200px;
    background-color: #333;
    color: #ddd;
    border: 1px solid #555;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 14px;
}

.wmd-browser-search:focus {
    outline: none;
    border-color: #4CAF50;
}

.wmd-browser-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    overflow-y: auto;
    flex: 1;
}

.wmd-browser-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 16px;
    background-color: #2a2a2a;
    border-radius: 6px;
    transition: background-color 0.2s;
}

.wmd-browser-item:hover {
    background-color: #333;
}

.wmd-browser-item-info {
    flex: 1;
    min-width: 0;
}

.wmd-browser-item-name {
    color: #fff;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.wmd-browser-item-meta {
    display: flex;
    gap: 12px;
    font-size: 12px;
    color: #888;
    margin-top: 4px;
}

.wmd-browser-item-actions {
    display: flex;
    gap: 6px;
}

.wmd-browser-item-actions button {
    background: none;
    border: 1px solid #555;
    color: #888;
    width: 32px;
    height: 32px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}

.wmd-browser-item-actions button:hover {
    background-color: #444;
    color: #fff;
    border-color: #666;
}

.wmd-browser-item-actions button.danger:hover {
    background-color: #f44336;
    border-color: #f44336;
}

.wmd-browser-empty {
    text-align: center;
    padding: 60px 20px;
    color: #666;
}

/* Browser with folder tree */
.wmd-browser-layout {
    display: flex;
    gap: 16px;
    height: 100%;
    overflow: hidden;
}

.wmd-browser-sidebar {
    width: 220px;
    min-width: 180px;
    background-color: #252525;
    border-radius: 6px;
    overflow-y: auto;
    flex-shrink: 0;
}

.wmd-browser-sidebar-title {
    padding: 12px 14px;
    font-weight: 600;
    color: #888;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #333;
}

.wmd-folder-tree {
    padding: 8px 0;
}

.wmd-folder-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;
    cursor: pointer;
    color: #ccc;
    font-size: 13px;
    transition: all 0.15s;
    border-left: 2px solid transparent;
}

.wmd-folder-item:hover {
    background-color: #333;
    color: #fff;
}

.wmd-folder-item.active {
    background-color: #2a3a2a;
    color: #4CAF50;
    border-left-color: #4CAF50;
}

.wmd-folder-item-icon {
    font-size: 14px;
    width: 18px;
    text-align: center;
}

.wmd-folder-item-name {
    flex: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.wmd-folder-item-count {
    font-size: 11px;
    color: #666;
    background-color: #333;
    padding: 2px 6px;
    border-radius: 10px;
}

.wmd-folder-item.active .wmd-folder-item-count {
    background-color: #4CAF50;
    color: #fff;
}

.wmd-browser-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    min-width: 0;
}

/* Workflows Tab - Three Column Layout */
.wmd-workflows-layout {
    display: flex;
    gap: 12px;
    height: 100%;
    overflow: hidden;
}

.wmd-workflows-column {
    display: flex;
    flex-direction: column;
    background-color: #252525;
    border-radius: 6px;
    overflow: hidden;
}

.wmd-workflows-column.workflows-list {
    width: 280px;
    min-width: 220px;
    flex-shrink: 0;
}

.wmd-workflows-column.models-list {
    width: 300px;
    min-width: 250px;
    flex-shrink: 0;
}

.wmd-workflows-column.model-details {
    flex: 1;
    min-width: 300px;
}

.wmd-workflows-column-header {
    padding: 12px 14px;
    font-weight: 600;
    color: #888;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
    border-bottom: 1px solid #333;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: #2a2a2a;
}

.wmd-workflows-column-header .count {
    font-size: 11px;
    color: #666;
    background-color: #333;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: normal;
}

.wmd-refresh-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 14px;
    padding: 2px 6px;
    border-radius: 4px;
    opacity: 0.6;
    transition: opacity 0.2s;
}

.wmd-refresh-btn:hover {
    opacity: 1;
    background-color: #333;
}

.wmd-workflows-column-content {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;
}

.wmd-workflow-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    cursor: pointer;
    color: #ccc;
    font-size: 13px;
    transition: all 0.15s;
    border-left: 2px solid transparent;
}

.wmd-workflow-item:hover {
    background-color: #333;
    color: #fff;
}

.wmd-workflow-item.active {
    background-color: #2a3a4a;
    color: #58a6ff;
    border-left-color: #58a6ff;
}

.wmd-workflow-item-icon {
    font-size: 14px;
}

.wmd-workflow-item-info {
    flex: 1;
    min-width: 0;
}

.wmd-workflow-item-name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-weight: 500;
}

.wmd-workflow-item-path {
    font-size: 10px;
    color: #666;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-top: 2px;
}

.wmd-model-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    cursor: pointer;
    color: #ccc;
    font-size: 13px;
    transition: all 0.15s;
    border-left: 2px solid transparent;
}

.wmd-model-item:hover {
    background-color: #333;
}

.wmd-model-item.active {
    background-color: #2a3a2a;
    color: #4CAF50;
    border-left-color: #4CAF50;
}

.wmd-model-item.missing {
    color: #f87171;
}

.wmd-model-item.missing.active {
    background-color: #3a2a2a;
    border-left-color: #f87171;
}

.wmd-model-item-info {
    flex: 1;
    min-width: 0;
}

.wmd-model-item-name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.wmd-model-item-type {
    font-size: 10px;
    color: #888;
    margin-top: 2px;
}

.wmd-model-item-status {
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
}

.wmd-model-item-status.exists {
    background-color: #1a3a1a;
    color: #4CAF50;
}

.wmd-model-item-status.missing {
    background-color: #3a1a1a;
    color: #f87171;
}

.wmd-user-url-badge {
    font-size: 9px;
    padding: 1px 4px;
    border-radius: 3px;
    background-color: #3a3a1a;
    color: #d4a017;
    margin-left: 4px;
    font-weight: normal;
}

.wmd-readme-content {
    font-size: 12px;
    line-height: 1.5;
    color: #aaa;
}

.wmd-readme-content h2, .wmd-readme-content h3, .wmd-readme-content h4 {
    color: #ccc;
    margin: 12px 0 8px 0;
}

.wmd-readme-content h2 { font-size: 16px; }
.wmd-readme-content h3 { font-size: 14px; }
.wmd-readme-content h4 { font-size: 13px; }

.wmd-readme-content p {
    margin: 8px 0;
}

.wmd-readme-content a {
    color: #4a9eff;
}

.wmd-readme-content strong {
    color: #ccc;
}

.wmd-loading-small {
    color: #666;
    font-size: 12px;
    padding: 10px;
}

.wmd-model-details-content {
    padding: 16px;
    overflow-y: auto;
    height: 100%;
}

.wmd-model-details-section {
    margin-bottom: 20px;
}

.wmd-model-details-section-title {
    font-size: 12px;
    color: #888;
    text-transform: uppercase;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #333;
}

.wmd-model-details-row {
    display: flex;
    margin-bottom: 10px;
    font-size: 13px;
}

.wmd-model-details-label {
    width: 100px;
    color: #888;
    flex-shrink: 0;
}

.wmd-model-details-value {
    flex: 1;
    color: #ddd;
    word-break: break-all;
}

.wmd-model-details-value a {
    color: #58a6ff;
    text-decoration: none;
}

.wmd-model-details-value a:hover {
    text-decoration: underline;
}

.wmd-alternatives-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.wmd-alternative-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    background-color: #2a2a2a;
    border-radius: 6px;
    font-size: 13px;
}

.wmd-alternative-item-name {
    flex: 1;
    color: #ccc;
    word-break: break-all;
}

.wmd-alternative-item-size {
    color: #888;
    font-size: 11px;
    margin-left: 8px;
}

.wmd-workflows-empty {
    text-align: center;
    padding: 40px 20px;
    color: #666;
}

.wmd-workflows-search {
    padding: 8px 12px;
    border-bottom: 1px solid #333;
}

.wmd-workflows-search input {
    width: 100%;
    padding: 8px 10px;
    border: 1px solid #444;
    border-radius: 4px;
    background-color: #1a1a1a;
    color: #fff;
    font-size: 12px;
}

.wmd-workflows-search input:focus {
    outline: none;
    border-color: #58a6ff;
}

/* Directory Management */
.wmd-dir-manager {
    background: #1e1e1e;
    border-bottom: 1px solid #333;
    padding: 12px 16px;
}

.wmd-dir-manager-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 8px;
}

.wmd-dir-manager-title {
    font-size: 12px;
    color: #888;
    font-weight: 500;
}

.wmd-dir-manager-toggle {
    background: none;
    border: none;
    color: #58a6ff;
    cursor: pointer;
    font-size: 12px;
    padding: 4px 8px;
}

.wmd-dir-manager-toggle:hover {
    text-decoration: underline;
}

.wmd-dir-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 10px;
    max-height: 150px;
    overflow-y: auto;
}

.wmd-dir-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    background: #252525;
    border-radius: 4px;
    font-size: 12px;
}

.wmd-dir-item-path {
    flex: 1;
    color: #ccc;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.wmd-dir-item-default {
    color: #888;
    font-size: 10px;
    background: #333;
    padding: 2px 6px;
    border-radius: 3px;
}

.wmd-dir-item-remove {
    background: none;
    border: none;
    color: #f87171;
    cursor: pointer;
    padding: 2px 6px;
    font-size: 14px;
    opacity: 0.7;
}

.wmd-dir-item-remove:hover {
    opacity: 1;
}

.wmd-dir-add {
    display: flex;
    gap: 8px;
}

.wmd-dir-add input {
    flex: 1;
    padding: 8px 10px;
    border: 1px solid #444;
    border-radius: 4px;
    background-color: #1a1a1a;
    color: #fff;
    font-size: 12px;
}

.wmd-dir-add input:focus {
    outline: none;
    border-color: #58a6ff;
}

.wmd-dir-add-btn {
    background: #2563eb;
    border: none;
    color: white;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 4px;
}

.wmd-dir-add-btn:hover {
    background: #1d4ed8;
}

/* Confidence Badge */
.wmd-confidence-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
    margin-left: 8px;
}

.wmd-confidence-100 {
    background-color: #1a4a3a;
    color: #4CAF50;
}

.wmd-confidence-high {
    background-color: #2a4a3a;
    color: #8BC34A;
}

.wmd-confidence-medium {
    background-color: #4a4a2a;
    color: #CDDC39;
}

.wmd-confidence-low {
    background-color: #4a3a2a;
    color: #FF9800;
}

/* Model metadata modal */
.wmd-metadata-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10001;
}

.wmd-metadata-modal {
    background-color: #1a1a1a;
    border: 1px solid #444;
    border-radius: 8px;
    width: 500px;
    max-width: 90%;
    max-height: 80vh;
    overflow-y: auto;
}

.wmd-metadata-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid #444;
    background-color: #252525;
    border-radius: 8px 8px 0 0;
}

.wmd-metadata-title {
    font-weight: 600;
    color: #fff;
}

.wmd-metadata-body {
    padding: 20px;
}

.wmd-metadata-row {
    display: flex;
    margin-bottom: 12px;
}

.wmd-metadata-label {
    width: 120px;
    color: #888;
    font-size: 13px;
}

.wmd-metadata-value {
    flex: 1;
    color: #ddd;
    font-size: 13px;
    word-break: break-all;
}

.wmd-metadata-value.mono {
    font-family: monospace;
    font-size: 12px;
    background-color: #2a2a2a;
    padding: 4px 8px;
    border-radius: 4px;
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
        this.settings = null;
        this.currentFilter = "all"; // all, existing, ready, unknown
        this.currentTab = "models"; // models, downloads, browser, settings, help
        this.installedModels = []; // For browser tab
        this.browserFilter = ""; // Search filter for browser
        this.browserType = ""; // Type filter for browser
        this.selectedBrowserModel = null; // Selected model in browser
        this.selectedModelInfo = null; // URL info for selected model
        this.selectedModelReadme = null; // README for selected model
        this.availableDirectories = []; // Fetched from backend
        this.downloadQueue = []; // Queued downloads
        this.downloadHistory = []; // Download history
        this.activeDownloadCount = 0; // Track active downloads for badge
        this.rawDownloadInfo = null; // For raw URL downloads
        this.searchCache = {}; // Cache for advanced search results
    }

    async show() {
        // Reset state for fresh scan
        this.models = [];
        this.downloads = {};
        this.currentTab = "models";
        this.currentFilter = "all";

        this.createModal();
        document.body.appendChild(this.modal);

        // Load directories and scan workflow in parallel
        await Promise.all([
            this.loadAvailableDirectories(),
            this.scanWorkflow()
        ]);

        // Check for any active downloads and restore progress tracking
        await this.checkActiveDownloads();
    }

    async loadAvailableDirectories() {
        try {
            const response = await api.fetchApi("/workflow-models/directories");
            const result = await response.json();
            if (result.success && result.directories) {
                this.availableDirectories = result.directories.map(d => d.name);
                console.log("[WMD] Loaded", this.availableDirectories.length, "available directories");
            }
        } catch (error) {
            console.error("[WMD] Error loading directories:", error);
            // Fall back to hardcoded list
            this.availableDirectories = [...MODEL_DIRECTORIES];
        }
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
                const modelFilename = model.filename.replace(/[\/\\]/g, '_');

                // Check ALL progress entries for this model's filename
                // This handles all download ID formats: direct_, hf_repo/, queued_
                for (const [downloadId, progress] of Object.entries(allProgress)) {
                    // Match by filename in the progress data or in the download ID
                    const progressFilename = (progress.filename || '').replace(/[\/\\]/g, '_');
                    const matchesFilename = progressFilename === modelFilename ||
                                           downloadId.includes(modelFilename) ||
                                           downloadId.endsWith(`_${modelFilename}`);

                    if (matchesFilename) {
                        if (progress.status === 'downloading' || progress.status === 'starting' || progress.status === 'queued') {
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
                            break;
                        } else if (progress.status === 'completed') {
                            // Download completed while modal was closed
                            model.exists = true;
                            const statusCell = document.getElementById(`wmd-status-cell-${i}`);
                            if (statusCell) {
                                statusCell.className = "wmd-status-exists";
                                this.recheckModelStatus(i);
                            }
                            break;
                        }
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
                // Header with title and close button
                $el("div.wmd-modal-header", [
                    $el("h2.wmd-modal-title", ["Workflow Models"]),
                    $el("button.wmd-modal-close", {
                        onclick: () => this.close()
                    }, ["\u00D7"])
                ]),
                // Tab navigation
                $el("div.wmd-tabs", [
                    $el("button.wmd-tab.active", {
                        onclick: () => this.selectTab('models'),
                        id: "wmd-tab-models"
                    }, ["Workflow Models"]),
                    $el("button.wmd-tab", {
                        onclick: () => this.selectTab('downloads'),
                        id: "wmd-tab-downloads"
                    }, [
                        "Downloads",
                        $el("span.wmd-tab-badge.active-downloads", {
                            id: "wmd-downloads-badge",
                            style: { display: "none" }
                        }, ["0"])
                    ]),
                    $el("button.wmd-tab", {
                        onclick: () => this.selectTab('browser'),
                        id: "wmd-tab-browser"
                    }, ["Local Browser"]),
                    $el("button.wmd-tab", {
                        onclick: () => this.selectTab('workflows'),
                        id: "wmd-tab-workflows"
                    }, ["Workflows"]),
                    $el("button.wmd-tab", {
                        onclick: () => this.selectTab('help'),
                        id: "wmd-tab-help"
                    }, ["Help"])
                ]),
                // Tab content container
                $el("div.wmd-modal-body", { id: "wmd-body" }, [
                    // Models tab content
                    $el("div.wmd-tab-content.active", { id: "wmd-content-models" }, [
                        $el("div.wmd-loading", [
                            $el("div.wmd-spinner"),
                            $el("div", ["Scanning workflow for models..."])
                        ])
                    ]),
                    // Downloads tab content
                    $el("div.wmd-tab-content", { id: "wmd-content-downloads" }, [
                        $el("div.wmd-loading", [
                            $el("div.wmd-spinner"),
                            $el("div", ["Loading downloads..."])
                        ])
                    ]),
                    // Browser tab content
                    $el("div.wmd-tab-content", { id: "wmd-content-browser" }, [
                        $el("div.wmd-loading", [
                            $el("div.wmd-spinner"),
                            $el("div", ["Loading installed models..."])
                        ])
                    ]),
                    // Workflows tab content
                    $el("div.wmd-tab-content", { id: "wmd-content-workflows" }, [
                        $el("div.wmd-loading", [
                            $el("div.wmd-spinner"),
                            $el("div", ["Loading workflows..."])
                        ])
                    ]),
                    // Help tab content
                    $el("div.wmd-tab-content", { id: "wmd-content-help" }, [
                        $el("div.wmd-loading", [
                            $el("div.wmd-spinner"),
                            $el("div", ["Loading help..."])
                        ])
                    ])
                ]),
                // Footer
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

    selectTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.wmd-tab').forEach(t => t.classList.remove('active'));
        document.getElementById(`wmd-tab-${tabName}`)?.classList.add('active');

        // Update tab content
        document.querySelectorAll('.wmd-tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(`wmd-content-${tabName}`)?.classList.add('active');

        this.currentTab = tabName;

        // Load tab-specific content
        if (tabName === 'downloads') this.loadDownloadsTab();
        if (tabName === 'browser') this.loadBrowserTab();
        if (tabName === 'workflows') this.loadWorkflowsTab();
        if (tabName === 'help') this.loadHelpTab();

        // Update footer based on tab
        this.updateFooterForTab(tabName);
    }

    updateFooterForTab(tabName) {
        const downloadAllBtn = document.getElementById("wmd-download-all-btn");
        const footerInfo = document.getElementById("wmd-footer-info");

        if (tabName === 'models') {
            // Show download all button if applicable
            const downloadableCount = this.models.filter(m => !m.exists && m.url).length;
            if (downloadAllBtn) {
                downloadAllBtn.style.display = downloadableCount > 0 ? "inline-block" : "none";
                downloadAllBtn.textContent = `Download All Missing (${downloadableCount})`;
            }
        } else {
            // Hide download all button on other tabs
            if (downloadAllBtn) downloadAllBtn.style.display = "none";
        }

        // Update footer info based on tab
        if (tabName === 'browser' && footerInfo) {
            const count = this.getFilteredBrowserModels().length;
            footerInfo.textContent = `Showing ${count} of ${this.installedModels.length} installed models`;
        }
    }

    async scanWorkflow() {
        try {
            // Load settings first (for advanced search button display)
            await this.loadSettings();

            // Get current workflow from app - force fresh serialize
            const workflow = app.graph.serialize();

            console.log("[WMD] Scanning workflow with", Object.keys(workflow.nodes || {}).length, "nodes");

            const response = await api.fetchApi("/workflow-models/scan", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Cache-Control": "no-cache"
                },
                body: JSON.stringify({ workflow })
            });

            const result = await response.json();

            if (result.success) {
                this.models = result.models;
                console.log("[WMD] Found", result.models.length, "models:", result.models.map(m => m.filename));
                this.renderModels(result.models, result.summary);

                // Track model usage for unused detection
                this.trackModelUsage(result.models);
            } else {
                this.showError(result.error || "Failed to scan workflow");
            }
        } catch (error) {
            console.error("[WMD] Scan error:", error);
            this.showError("Failed to scan workflow: " + error.message);
        }
    }

    buildDirectoryOptions(currentDir) {
        // Use fetched directories or fall back to hardcoded list
        let dirs = this.availableDirectories.length > 0
            ? [...this.availableDirectories]
            : [...MODEL_DIRECTORIES];

        // Ensure current directory is in the list
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
        let badges = '';

        // Source badge
        if (model.url_source === 'popular_models') {
            badges += '<span class="wmd-source-badge popular">Popular</span>';
        } else if (model.url_source === 'model_list') {
            badges += '<span class="wmd-source-badge">Manager</span>';
        } else if (model.url_source === 'huggingface_api') {
            badges += '<span class="wmd-source-badge hf">HF API</span>';
        } else if (model.url_source === 'civitai_api') {
            badges += '<span class="wmd-source-badge civit">CivitAI</span>';
        } else if (model.url_source === 'fuzzy_match' || model.url_source === 'search_cache') {
            badges += '<span class="wmd-source-badge">Cached</span>';
        }

        // Confidence badge (for fuzzy matches)
        if (model.confidence !== undefined && model.confidence !== null) {
            const color = model.confidence >= 100 ? '#4CAF50'
                        : model.confidence >= 90 ? '#8BC34A'
                        : model.confidence >= 80 ? '#CDDC39'
                        : model.confidence >= 70 ? '#FFC107'
                        : '#FF9800';
            const text = model.confidence >= 100 ? '100%' : `${model.confidence}%`;
            badges += `<span class="wmd-confidence-badge" style="background-color: ${color}; color: #000;">${text}</span>`;
        }

        return badges;
    }

    renderModels(models, summary) {
        const modelsContent = document.getElementById("wmd-content-models");
        const footerInfo = document.getElementById("wmd-footer-info");
        const downloadAllBtn = document.getElementById("wmd-download-all-btn");

        if (models.length === 0) {
            modelsContent.innerHTML = `
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

        // Build filter controls
        const filterHtml = `
            <div class="wmd-browser-controls" style="padding: 12px 0; margin-bottom: 0;">
                <select class="wmd-filter-select" id="wmd-filter-select"
                        onchange="window.wmdInstance.onFilterChange(this.value)" style="min-width: 180px;">
                    <option value="all">All Models</option>
                    <option value="existing">Existing Models</option>
                    <option value="ready">Ready For Download</option>
                    <option value="unknown">Missing URLs / Unknown</option>
                </select>
                <button class="wmd-btn wmd-btn-info wmd-btn-small" id="wmd-auto-resolve-btn"
                        onclick="window.wmdInstance.autoResolveMatches()"
                        title="Auto-download all models with 100% confidence URL matches"
                        style="display: ${downloadableCount > 0 ? 'inline-block' : 'none'};">
                    Auto-Resolve (${downloadableCount})
                </button>
            </div>
        `;

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
            let statusText = model.exists ? `EXISTS (${model.local_size})` : "MISSING";

            // Show alternatives badge if missing but alternatives exist
            let alternativesBadge = '';
            if (!model.exists && model.alternatives && model.alternatives.length > 0) {
                alternativesBadge = `
                    <span class="wmd-alternatives-badge"
                          onclick="window.wmdInstance.showAlternatives(${index})"
                          title="Click to see ${model.alternatives.length} alternative format(s) available">
                        ${model.alternatives.length} alt
                    </span>
                `;
            }

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

            // Build info icons for filename cell
            const infoIcon = this.buildMetadataInfoIcon(model);
            const suggestionsIcon = this.buildSuggestionsInfoIcon(model);

            // Action cell
            let actionCell = "";
            if (model.url) {
                // Has URL - show download button
                const btnClass = model.exists ? "wmd-btn-warning" : "wmd-btn-primary";
                const btnText = model.exists ? "Re-download" : "Download";
                actionCell = `
                    <div class="wmd-action-cell">
                        <div class="wmd-action-buttons">
                            <button class="wmd-btn ${btnClass} wmd-btn-small"
                                    id="wmd-dl-btn-${index}"
                                    onclick="window.wmdInstance.downloadModel(${index})">
                                ${btnText}
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

                actionCell = `
                    <div class="wmd-action-cell">
                        <div class="wmd-action-buttons">
                            <button class="wmd-btn wmd-btn-secondary wmd-btn-small"
                                    id="wmd-fuzzy-btn-${index}"
                                    onclick="window.wmdInstance.fuzzyMatch(${index})"
                                    title="Find similar models using fuzzy matching (70% threshold)">
                                Fuzzy Match
                            </button>
                            <button class="wmd-btn ${searchBtnClass} wmd-btn-small"
                                    id="wmd-search-btn-${index}"
                                    onclick="window.wmdInstance.${searchBtnHandler}(${index})">
                                ${searchBtnText}
                            </button>
                            ${hashLookupBtn}
                        </div>
                        <div class="wmd-url-input-row" id="wmd-url-row-${index}">
                            <input type="text" class="wmd-url-input"
                                   id="wmd-url-input-${index}"
                                   placeholder="Paste URL or CivitAI URN (urn:air:...)..."
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

            // Determine homepage URL for the filename link
            let homepageUrl = null;
            if (model.hf_repo) {
                homepageUrl = `https://huggingface.co/${model.hf_repo}`;
            } else if (model.civitai_url) {
                homepageUrl = model.civitai_url;
            }

            const filenameHtml = homepageUrl
                ? `<a href="${homepageUrl}" target="_blank" class="wmd-filename-link" title="Open model page">${model.filename}</a>`
                : `<span class="wmd-filename-text">${model.filename}</span>`;

            return `
                <tr id="wmd-row-${index}">
                    <td class="wmd-filename-cell">
                        <span class="wmd-filename-wrapper">${filenameHtml}</span>
                        <span class="wmd-filename-icons" id="wmd-filename-icons-${index}">
                            <button class="wmd-copy-btn" onclick="window.wmdInstance.copyModelMetadata(${index})" title="Copy model info">📋</button>
                            ${infoIcon}${suggestionsIcon}
                        </span>
                    </td>
                    <td><span class="wmd-type-badge">${model.type}</span></td>
                    <td>${dirDropdown}</td>
                    <td class="${statusClass}" id="wmd-status-cell-${index}">${statusText} ${alternativesBadge}</td>
                    <td>${hfLink}</td>
                    <td>${actionCell}</td>
                </tr>
            `;
        }).join("");

        modelsContent.innerHTML = `
            ${filterHtml}
            ${summaryHtml}
            <div style="flex: 1; overflow-y: auto;">
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
            </div>
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

    // Auto-resolve all 100% confidence matches
    async autoResolveMatches() {
        const downloadable = this.models.filter(m => !m.exists && m.url);

        if (downloadable.length === 0) {
            this.showNotification('No models ready for download', 'info');
            return;
        }

        if (!confirm(`Download ${downloadable.length} models that have URLs?`)) return;

        // Queue all downloads
        for (let i = 0; i < this.models.length; i++) {
            const model = this.models[i];
            if (!model.exists && model.url) {
                await this.downloadModel(i);
                // Small delay between downloads to avoid overwhelming
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }
    }

    showAlternatives(index) {
        const model = this.models[index];
        if (!model || !model.alternatives || model.alternatives.length === 0) {
            this.showNotification('No alternatives found', 'info');
            return;
        }

        // Remove existing popup if any
        const existingPopup = document.querySelector('.wmd-alternatives-popup');
        if (existingPopup) existingPopup.remove();

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'wmd-modal-overlay';
        overlay.style.zIndex = '10000';
        overlay.onclick = (e) => {
            if (e.target === overlay) overlay.remove();
        };

        // Create popup
        const popup = document.createElement('div');
        popup.className = 'wmd-alternatives-popup';
        popup.innerHTML = `
            <h3>Alternative Formats Available</h3>
            <p style="color: #888; margin-bottom: 16px;">
                Looking for: <strong>${model.filename}</strong>
            </p>
            <div class="wmd-alternatives-list">
                ${model.alternatives.map((alt, i) => `
                    <div class="wmd-alternative-item">
                        <div class="wmd-alternative-info">
                            <div class="wmd-alternative-name">${alt.filename}</div>
                            <div class="wmd-alternative-meta">
                                <span class="wmd-format-badge">${alt.format}</span>
                                ${alt.size || ''} | ${alt.directory}
                            </div>
                        </div>
                        <button class="wmd-btn wmd-btn-info wmd-btn-small"
                                onclick="window.wmdInstance.useAlternative(${index}, ${i}); this.closest('.wmd-modal-overlay').remove();">
                            Use This
                        </button>
                    </div>
                `).join('')}
            </div>
            <div style="margin-top: 16px; text-align: right;">
                <button class="wmd-btn wmd-btn-secondary" onclick="this.closest('.wmd-modal-overlay').remove();">
                    Close
                </button>
            </div>
        `;

        overlay.appendChild(popup);
        document.body.appendChild(overlay);
    }

    useAlternative(modelIndex, altIndex) {
        const model = this.models[modelIndex];
        const alt = model?.alternatives?.[altIndex];

        if (!model || !alt) {
            this.showNotification('Alternative not found', 'error');
            return;
        }

        // Copy the alternative filename to clipboard with a helpful message
        navigator.clipboard.writeText(alt.filename).then(() => {
            this.showNotification(
                `Alternative "${alt.filename}" copied to clipboard. Update your workflow node to use this file.`,
                'success'
            );
        }).catch(() => {
            this.showNotification(
                `Use "${alt.filename}" from ${alt.directory}/ in your workflow`,
                'info'
            );
        });
    }

    async fuzzyMatch(index) {
        const model = this.models[index];
        if (!model) return;

        const fuzzyBtn = document.getElementById(`wmd-fuzzy-btn-${index}`);
        if (fuzzyBtn) {
            fuzzyBtn.disabled = true;
            fuzzyBtn.textContent = "Matching...";
        }

        try {
            const response = await api.fetchApi("/workflow-models/fuzzy-match", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename: model.filename, threshold: 0.70 })
            });

            const result = await response.json();

            if (result.success && result.matches && result.matches.length > 0) {
                // Find best match with URL
                const bestMatch = result.matches.find(m => m.url) || result.matches[0];

                if (bestMatch && bestMatch.url) {
                    // Update model with found URL and confidence
                    model.url = bestMatch.url;
                    model.url_source = bestMatch.source || 'fuzzy_match';
                    model.confidence = bestMatch.confidence;
                    model.match_type = bestMatch.match_type;

                    // Extract HF info if applicable
                    if (bestMatch.url.includes('huggingface.co')) {
                        const hfMatch = bestMatch.url.match(/huggingface\.co\/([^/]+\/[^/]+)/);
                        if (hfMatch) model.hf_repo = hfMatch[1];
                    }

                    this.showNotification(`Found ${bestMatch.confidence}% match: ${bestMatch.filename}`, 'success');
                    this.updateRowWithUrl(index);
                } else {
                    // Show matches without URLs
                    const matchList = result.matches.map(m =>
                        `${m.filename || m.matched_name} (${m.confidence}% - ${m.match_type})`
                    ).join('\n');
                    this.showNotification(`Found similar models but no URLs:\n${matchList}`, 'info');
                    if (fuzzyBtn) {
                        fuzzyBtn.disabled = false;
                        fuzzyBtn.textContent = "Fuzzy Match";
                    }
                }
            } else {
                this.showNotification(`No similar models found for ${model.filename}`, 'info');
                if (fuzzyBtn) {
                    fuzzyBtn.disabled = false;
                    fuzzyBtn.textContent = "Fuzzy Match";
                }
            }
        } catch (error) {
            console.error("[WMD] Fuzzy match error:", error);
            this.showNotification(`Fuzzy match error: ${error.message}`, 'error');
            if (fuzzyBtn) {
                fuzzyBtn.disabled = false;
                fuzzyBtn.textContent = "Fuzzy Match";
            }
        }
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
                model.confidence = 100; // Exact match

                // Re-render the row
                this.updateRowWithUrl(index);
            } else {
                this.showNotification(`No URL found. Try Fuzzy Match or paste a URL manually.`, 'info');
                if (searchBtn) {
                    searchBtn.disabled = false;
                    searchBtn.textContent = "Search URL";
                }
            }
        } catch (error) {
            console.error("[WMD] Search URL error:", error);
            this.showNotification(`Error searching for URL: ${error.message}`, 'error');
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
        const filenameIcons = document.getElementById(`wmd-filename-icons-${index}`);
        if (!filenameIcons) return;

        // Remove existing suggestions icon if any
        const existingIcon = filenameIcons.querySelector('.wmd-info-icon');
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

        filenameIcons.appendChild(infoIcon);
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

        // Update filename to be a link if homepage URL is available
        const filenameWrapper = row.querySelector('.wmd-filename-wrapper');
        if (filenameWrapper) {
            let homepageUrl = null;
            if (model.hf_repo) {
                homepageUrl = `https://huggingface.co/${model.hf_repo}`;
            } else if (model.civitai_url) {
                homepageUrl = model.civitai_url;
            }

            if (homepageUrl) {
                filenameWrapper.innerHTML = `<a href="${homepageUrl}" target="_blank" class="wmd-filename-link" title="Open model page">${model.filename}</a>`;
            }
        }

        // Update source column
        const sourceCell = row.cells[4];
        const sourceBadge = this.getSourceBadge(model);
        if (model.hf_repo) {
            sourceCell.innerHTML = `<a href="https://huggingface.co/${model.hf_repo}" target="_blank" class="wmd-hf-link">${model.hf_repo}</a>${sourceBadge}`;
        } else {
            sourceCell.innerHTML = `<span style="color:#888;">Direct URL</span>${sourceBadge}`;
        }

        // Build info icon if metadata exists and update filename icons
        const infoIcon = this.buildMetadataInfoIcon(model);
        const filenameIcons = document.getElementById(`wmd-filename-icons-${index}`);
        if (filenameIcons) {
            filenameIcons.innerHTML = `
                <button class="wmd-copy-btn" onclick="window.wmdInstance.copyModelMetadata(${index})" title="Copy model info">📋</button>
                ${infoIcon}
            `;
        }

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

        // Validate URL format - accept http(s) URLs or CivitAI URN format
        const isCivitAiUrn = url.startsWith('urn:') && url.includes(':civitai:');
        if (!url.startsWith('http://') && !url.startsWith('https://') && !isCivitAiUrn) {
            alert("Please enter a valid URL (http://, https://) or CivitAI URN (urn:air:...)");
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

    // Load Downloads tab content
    async loadDownloadsTab() {
        const content = document.getElementById("wmd-content-downloads");
        if (!content) return;

        try {
            // Fetch both current progress and persistent history
            const [progressResponse, historyResponse] = await Promise.all([
                api.fetchApi("/workflow-models/progress"),
                api.fetchApi("/workflow-models/download-history")
            ]);

            if (!progressResponse.ok) {
                throw new Error(`HTTP ${progressResponse.status}: ${progressResponse.statusText}`);
            }

            const allProgress = await progressResponse.json();
            const historyData = historyResponse.ok ? await historyResponse.json() : { history: [] };
            const history = historyData.history || [];

            // Separate active downloads from current progress
            const active = [];
            const activeFilenames = new Set();

            for (const [id, progress] of Object.entries(allProgress)) {
                if (progress.status === 'downloading' || progress.status === 'starting') {
                    active.push({ id, ...progress });
                    activeFilenames.add(progress.filename);
                }
            }

            // Get completed and failed from history (excluding currently active ones)
            const completed = history
                .filter(h => h.status === 'completed' && !activeFilenames.has(h.filename))
                .map(h => ({ ...h, id: h.id || h.filename }));
            const failed = history
                .filter(h => h.status === 'error' && !activeFilenames.has(h.filename))
                .map(h => ({ ...h, id: h.id || h.filename }));

            // Update badge
            this.updateDownloadsBadge(active.length);

            const hasHistory = completed.length > 0 || failed.length > 0;

            content.innerHTML = `
                <!-- Raw Download Section -->
                <div class="wmd-raw-download-section">
                    <div class="wmd-downloads-section-title">Direct URL Download</div>
                    <div class="wmd-raw-download-input-row">
                        <input type="text" class="wmd-url-input" id="wmd-raw-url-input"
                               placeholder="Paste URL (HuggingFace, CivitAI) or CivitAI URN (urn:air:...)..."
                               style="flex: 1;"
                               onkeypress="if(event.key==='Enter') window.wmdInstance.analyzeRawUrl()">
                        <button class="wmd-btn wmd-btn-info wmd-btn-small" onclick="window.wmdInstance.analyzeRawUrl()">
                            Check URL
                        </button>
                    </div>
                    <div id="wmd-raw-download-preview" style="display: none;"></div>
                </div>

                <div class="wmd-downloads-header">
                    <div class="wmd-downloads-stats">
                        <div class="wmd-downloads-stat">
                            <span class="wmd-downloads-stat-value">${active.length}</span>
                            <span>Active</span>
                        </div>
                        <div class="wmd-downloads-stat">
                            <span class="wmd-downloads-stat-value">${completed.length}</span>
                            <span>Completed</span>
                        </div>
                        <div class="wmd-downloads-stat">
                            <span class="wmd-downloads-stat-value">${failed.length}</span>
                            <span>Failed</span>
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px;">
                        ${hasHistory ? `
                            <button class="wmd-btn wmd-btn-danger wmd-btn-small"
                                    onclick="window.wmdInstance.clearDownloadHistory()">
                                Clear History
                            </button>
                        ` : ''}
                        <button class="wmd-btn wmd-btn-secondary wmd-btn-small"
                                onclick="window.wmdInstance.loadDownloadsTab()">
                            Refresh
                        </button>
                    </div>
                </div>

                ${active.length > 0 ? `
                    <div class="wmd-downloads-section">
                        <div class="wmd-downloads-section-title">Active Downloads</div>
                        ${active.map(d => this.renderDownloadItem(d, 'active')).join('')}
                    </div>
                ` : ''}

                ${completed.length > 0 ? `
                    <div class="wmd-downloads-section">
                        <div class="wmd-downloads-section-title">Completed (${completed.length})</div>
                        ${completed.map(d => this.renderDownloadItem(d, 'completed')).join('')}
                    </div>
                ` : ''}

                ${failed.length > 0 ? `
                    <div class="wmd-downloads-section">
                        <div class="wmd-downloads-section-title">Failed (${failed.length})</div>
                        ${failed.map(d => this.renderDownloadItem(d, 'failed')).join('')}
                    </div>
                ` : ''}

                ${active.length === 0 && completed.length === 0 && failed.length === 0 ? `
                    <div class="wmd-browser-empty">
                        <p>No downloads yet</p>
                        <p style="font-size: 13px; margin-top: 8px;">Start downloading models from the Models tab</p>
                    </div>
                ` : ''}
            `;

            // Auto-refresh if there are active downloads
            if (active.length > 0 && this.currentTab === 'downloads') {
                setTimeout(() => {
                    if (this.currentTab === 'downloads') {
                        this.loadDownloadsTab();
                    }
                }, 2000);
            }
        } catch (error) {
            console.error("[WMD] Error loading downloads:", error);
            content.innerHTML = `
                <div class="wmd-browser-empty">
                    Error loading downloads: ${error.message}
                    <br><br>
                    <button class="wmd-btn wmd-btn-secondary wmd-btn-small"
                            onclick="window.wmdInstance.loadDownloadsTab()">
                        Retry
                    </button>
                </div>`;
        }
    }

    async clearDownloadHistory() {
        if (!confirm('Clear all download history? This cannot be undone.')) {
            return;
        }

        try {
            const response = await api.fetchApi("/workflow-models/clear-download-history", {
                method: "POST"
            });

            if (response.ok) {
                this.showNotification('Download history cleared', 'success');
                this.loadDownloadsTab();
            } else {
                this.showNotification('Failed to clear history', 'error');
            }
        } catch (error) {
            console.error("[WMD] Error clearing history:", error);
            this.showNotification('Error clearing history', 'error');
        }
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    renderDownloadItem(download, status) {
        const progressPercent = download.progress || 0;
        const sizeInfo = download.total_size > 0
            ? this.formatBytes(download.total_size)
            : '';

        let statusBadge = '';
        let actionBtn = '';
        let timeInfo = '';

        // Format timestamp if available (from history)
        if (download.timestamp) {
            const date = new Date(download.timestamp);
            timeInfo = date.toLocaleString();
        }

        if (status === 'active') {
            const activeSize = download.total_size > 0
                ? `${this.formatBytes(download.downloaded || 0)} / ${this.formatBytes(download.total_size)}`
                : 'Calculating...';
            statusBadge = `<span style="color: #2196F3;">Downloading... ${progressPercent}%</span>`;
            actionBtn = `<button class="wmd-btn wmd-btn-danger wmd-btn-small"
                                 onclick="window.wmdInstance.cancelDownloadById('${download.id}')">Cancel</button>`;
            return `
                <div class="wmd-download-item">
                    <div class="wmd-download-item-info">
                        <div class="wmd-download-item-name">${download.filename || download.id}</div>
                        <div class="wmd-download-item-meta">${activeSize} ${statusBadge}</div>
                    </div>
                    <div class="wmd-download-item-progress">
                        <div class="wmd-progress-bar">
                            <div class="wmd-progress-fill" style="width: ${progressPercent}%"></div>
                        </div>
                    </div>
                    <div class="wmd-download-item-actions">
                        ${actionBtn}
                    </div>
                </div>
            `;
        } else if (status === 'completed') {
            statusBadge = `<span style="color: #4CAF50;">✓ Completed</span>`;
            actionBtn = `
                <button class="wmd-copy-btn" onclick="window.wmdInstance.copyDownloadInfo('${download.filename}', 'completed')" title="Copy info">📋</button>
                <button class="wmd-btn wmd-btn-secondary wmd-btn-small" style="padding: 4px 8px; font-size: 11px;"
                         onclick="window.wmdInstance.deleteHistoryItem('${download.filename}')">Remove</button>`;
        } else if (status === 'failed') {
            const escapedError = (download.error || 'Failed').replace(/'/g, "\\'").replace(/"/g, '\\"');
            statusBadge = `<span style="color: #f44336;">✗ ${download.error || 'Failed'}</span>
                <button class="wmd-copy-btn" onclick="window.wmdInstance.copyError('${escapedError}')" title="Copy error">📋</button>`;
            actionBtn = `
                <button class="wmd-btn wmd-btn-secondary wmd-btn-small" style="padding: 4px 8px; font-size: 11px;"
                         onclick="window.wmdInstance.deleteHistoryItem('${download.filename}')">Remove</button>`;
        }

        return `
            <div class="wmd-download-item">
                <div class="wmd-download-item-info">
                    <div class="wmd-download-item-name">
                        ${download.filename || download.id}
                        <button class="wmd-copy-btn" onclick="window.wmdInstance.copyDownloadInfo('${download.filename}', '${status}', '${(download.error || '').replace(/'/g, "\\'")}')" title="Copy info">📋</button>
                    </div>
                    <div class="wmd-download-item-meta">
                        ${sizeInfo ? `<span style="color: #888;">${sizeInfo}</span>` : ''}
                        ${timeInfo ? `<span style="color: #666; margin-left: 8px;">${timeInfo}</span>` : ''}
                        <span style="margin-left: 8px;">${statusBadge}</span>
                    </div>
                </div>
                <div class="wmd-download-item-actions">
                    ${actionBtn}
                </div>
            </div>
        `;
    }

    async deleteHistoryItem(filename) {
        try {
            const response = await api.fetchApi("/workflow-models/delete-history-item", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename })
            });

            if (response.ok) {
                this.loadDownloadsTab();
            }
        } catch (error) {
            console.error("[WMD] Error deleting history item:", error);
        }
    }

    async cancelDownloadById(downloadId) {
        try {
            await api.fetchApi(`/workflow-models/cancel/${downloadId}`, { method: 'POST' });
            this.showNotification('Download cancelled', 'info');
            this.loadDownloadsTab();
        } catch (error) {
            console.error("[WMD] Error cancelling download:", error);
        }
    }

    async analyzeRawUrl() {
        const urlInput = document.getElementById('wmd-raw-url-input');
        const previewDiv = document.getElementById('wmd-raw-download-preview');

        if (!urlInput || !previewDiv) return;

        const url = urlInput.value.trim();
        if (!url) {
            this.showNotification('Please enter a URL', 'error');
            return;
        }

        previewDiv.style.display = 'block';
        previewDiv.innerHTML = `<div style="padding: 12px; color: #888;">Analyzing URL...</div>`;

        try {
            const response = await api.fetchApi('/workflow-models/analyze-url', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const result = await response.json();

            if (result.success) {
                this.rawDownloadInfo = result;

                // Use fetched directories or fall back to hardcoded list
                const dirs = this.availableDirectories.length > 0 ? this.availableDirectories : MODEL_DIRECTORIES;
                const dirOptions = dirs.map(dir =>
                    `<option value="${dir}" ${dir === result.suggested_directory ? 'selected' : ''}>models/${dir}/</option>`
                ).join('');

                previewDiv.innerHTML = `
                    <div class="wmd-raw-preview-card">
                        <div class="wmd-raw-preview-row">
                            <span class="wmd-raw-preview-label">Filename:</span>
                            <input type="text" class="wmd-url-input" id="wmd-raw-filename"
                                   value="${result.filename}" style="flex: 1;">
                        </div>
                        <div class="wmd-raw-preview-row">
                            <span class="wmd-raw-preview-label">Type:</span>
                            <span class="wmd-type-badge">${result.model_type || 'Unknown'}</span>
                            ${result.size ? `<span style="color: #888; margin-left: 12px;">${result.size}</span>` : ''}
                        </div>
                        <div class="wmd-raw-preview-row">
                            <span class="wmd-raw-preview-label">Save to:</span>
                            <select class="wmd-dir-select" id="wmd-raw-directory" style="flex: 1;">
                                ${dirOptions}
                            </select>
                        </div>
                        <div class="wmd-raw-preview-row">
                            <span class="wmd-raw-preview-label">Source:</span>
                            <span style="color: #888;">${result.source || 'Direct URL'}</span>
                        </div>
                        <div class="wmd-raw-preview-actions">
                            <button class="wmd-btn wmd-btn-secondary" onclick="window.wmdInstance.cancelRawDownload()">
                                Cancel
                            </button>
                            <button class="wmd-btn wmd-btn-primary" onclick="window.wmdInstance.startRawDownload()">
                                Download
                            </button>
                        </div>
                    </div>
                `;
            } else {
                previewDiv.innerHTML = `
                    <div style="padding: 12px; color: #f44336;">
                        Error: ${result.error || 'Could not analyze URL'}
                    </div>
                `;
            }
        } catch (error) {
            console.error('[WMD] Analyze URL error:', error);
            previewDiv.innerHTML = `
                <div style="padding: 12px; color: #f44336;">
                    Error: ${error.message}
                </div>
            `;
        }
    }

    cancelRawDownload() {
        const previewDiv = document.getElementById('wmd-raw-download-preview');
        const urlInput = document.getElementById('wmd-raw-url-input');

        if (previewDiv) {
            previewDiv.style.display = 'none';
            previewDiv.innerHTML = '';
        }
        if (urlInput) urlInput.value = '';
        this.rawDownloadInfo = null;
    }

    async startRawDownload() {
        if (!this.rawDownloadInfo) {
            this.showNotification('No URL analyzed', 'error');
            return;
        }

        const filename = document.getElementById('wmd-raw-filename')?.value.trim();
        const directory = document.getElementById('wmd-raw-directory')?.value;

        if (!filename) {
            this.showNotification('Please enter a filename', 'error');
            return;
        }

        const previewDiv = document.getElementById('wmd-raw-download-preview');
        if (previewDiv) {
            previewDiv.innerHTML = `<div style="padding: 12px; color: #2196F3;">Starting download...</div>`;
        }

        try {
            const response = await api.fetchApi('/workflow-models/queue-download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: this.rawDownloadInfo.url,
                    filename: filename,
                    directory: directory
                })
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification(`Download started: ${filename}`, 'success');
                this.cancelRawDownload();
                // Refresh to show the new download
                setTimeout(() => this.loadDownloadsTab(), 500);
            } else {
                this.showNotification(`Failed to start download: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('[WMD] Start raw download error:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }

    updateDownloadsBadge(count) {
        const badge = document.getElementById("wmd-downloads-badge");
        if (badge) {
            badge.textContent = count.toString();
            badge.style.display = count > 0 ? "inline-block" : "none";
        }
        this.activeDownloadCount = count;
    }

    // Load Browser tab content
    async loadBrowserTab() {
        const content = document.getElementById("wmd-content-browser");
        if (!content) return;

        // Initialize state
        this.installedModels = [];
        this.selectedBrowserModel = null;
        this.selectedModelReadme = null;
        this.browserFilter = this.browserFilter || '';
        this.browserType = this.browserType || '';

        content.innerHTML = `
            <div class="wmd-loading">
                <div class="wmd-spinner"></div>
                <div>Loading models...</div>
            </div>
        `;

        try {
            const response = await api.fetchApi("/workflow-models/installed");
            const data = await response.json();
            this.installedModels = data.models || [];
            this.renderBrowserTab();
        } catch (error) {
            console.error("[WMD] Error loading browser tab:", error);
            content.innerHTML = `
                <div class="wmd-workflows-layout">
                    <div style="padding: 40px; text-align: center; color: #f87171;">
                        <div style="font-size: 24px; margin-bottom: 10px;">⚠️</div>
                        <div>Error loading models</div>
                        <div style="font-size: 12px; margin-top: 5px;">${error.message || 'Unknown error'}</div>
                    </div>
                </div>
            `;
        }
    }

    renderBrowserTab() {
        const content = document.getElementById("wmd-content-browser");
        if (!content) return;

        try {
            this.installedModels = this.installedModels || [];
            this.browserFilter = this.browserFilter || '';
            this.browserType = this.browserType || '';

            // Get unique types for dropdown
            const types = [...new Set(this.installedModels.map(m => m.type))].sort();

            // Filter models
            const filteredModels = this.installedModels.filter(m => {
                const matchesSearch = !this.browserFilter ||
                    m.filename.toLowerCase().includes(this.browserFilter.toLowerCase());
                const matchesType = !this.browserType || m.type === this.browserType;
                return matchesSearch && matchesType;
            });

            content.innerHTML = `
                <div style="display: flex; flex-direction: column; height: 100%;">
                    <!-- Header with search and filter -->
                    <div style="padding: 12px; border-bottom: 1px solid #333; display: flex; gap: 10px; align-items: center;">
                        <input type="text" placeholder="Search models..."
                               value="${this.browserFilter}"
                               onkeyup="window.wmdInstance.onBrowserSearch(this.value)"
                               style="flex: 1; padding: 8px 12px; background: #333; border: 1px solid #444; border-radius: 4px; color: #fff;">
                        <select onchange="window.wmdInstance.onBrowserTypeChange(this.value)"
                                style="padding: 8px 12px; background: #333; border: 1px solid #444; border-radius: 4px; color: #fff;">
                            <option value="" ${!this.browserType ? 'selected' : ''}>All Types (${this.installedModels.length})</option>
                            ${types.map(t => {
                                const count = this.installedModels.filter(m => m.type === t).length;
                                return `<option value="${t}" ${this.browserType === t ? 'selected' : ''}>${t} (${count})</option>`;
                            }).join('')}
                        </select>
                        <button class="wmd-btn wmd-btn-secondary" onclick="window.wmdInstance.loadBrowserTab()" title="Refresh">🔄</button>
                    </div>

                    <!-- Models list -->
                    <div style="flex: 1; overflow-y: auto; padding: 8px;">
                        ${filteredModels.length > 0 ? `
                            <table style="width: 100%; border-collapse: collapse;">
                                <thead>
                                    <tr style="border-bottom: 1px solid #444; color: #888; font-size: 11px; text-transform: uppercase;">
                                        <th style="text-align: left; padding: 8px;">Filename</th>
                                        <th style="text-align: left; padding: 8px; width: 100px;">Type</th>
                                        <th style="text-align: right; padding: 8px; width: 80px;">Size</th>
                                        <th style="text-align: center; padding: 8px; width: 60px;">Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${filteredModels.map(m => {
                                        const escapedPath = m.path.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
                                        return `
                                            <tr style="border-bottom: 1px solid #333;">
                                                <td style="padding: 8px; font-size: 12px; word-break: break-all;">${m.filename}</td>
                                                <td style="padding: 8px; font-size: 11px; color: #888;">${m.type}</td>
                                                <td style="padding: 8px; font-size: 11px; color: #888; text-align: right;">${m.size_human}</td>
                                                <td style="padding: 8px; text-align: center;">
                                                    <button class="wmd-btn wmd-btn-small"
                                                            onclick="window.wmdInstance.deleteModel('${escapedPath}')"
                                                            style="background: #dc2626; padding: 4px 8px;"
                                                            title="Delete">🗑️</button>
                                                </td>
                                            </tr>
                                        `;
                                    }).join('')}
                                </tbody>
                            </table>
                        ` : `
                            <div style="padding: 40px; text-align: center; color: #666;">
                                No models found
                            </div>
                        `}
                    </div>

                    <!-- Footer -->
                    <div style="padding: 8px 12px; border-top: 1px solid #333; color: #888; font-size: 11px;">
                        Showing ${filteredModels.length} of ${this.installedModels.length} models
                    </div>
                </div>
            `;

            window.wmdInstance = this;
        } catch (error) {
            console.error("[WMD] Error rendering browser tab:", error);
            content.innerHTML = `<div style="padding: 40px; text-align: center; color: #f87171;">Error loading models</div>`;
        }
    }

    async selectBrowserModel(filename) {
        this.selectedBrowserModel = this.installedModels.find(m => m.filename === filename) || null;
        this.selectedModelInfo = null;
        this.selectedModelReadme = null;

        if (this.selectedBrowserModel) {
            // Load model URL info from cache/metadata
            try {
                const response = await api.fetchApi(`/workflow-models/model-url?filename=${encodeURIComponent(filename)}`);
                if (response.ok) {
                    this.selectedModelInfo = await response.json();
                }
            } catch (e) {
                console.error("[WMD] Error loading model URL info:", e);
            }
        }

        this.renderBrowserTab();
    }

    async findModelUrl(filename) {
        this.showNotification('Searching HuggingFace & CivitAI...', 'info');

        try {
            const response = await api.fetchApi('/workflow-models/find-model-url', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename })
            });

            const result = await response.json();

            if (result.success && result.url) {
                const source = result.source === 'huggingface_api' ? 'HuggingFace' :
                               result.source === 'civitai_api' ? 'CivitAI' : result.source;
                this.showNotification(`Found on ${source}!`, 'success');
                // Reload model info to show the URL
                await this.selectBrowserModel(filename);
            } else {
                this.showNotification('Not found on HuggingFace or CivitAI', 'error');
            }
        } catch (e) {
            console.error("[WMD] Error finding model URL:", e);
            this.showNotification('Error searching for URL', 'error');
        }
    }

    async saveModelUrl(filename) {
        const input = document.getElementById('wmd-model-url-input');
        if (!input) return;

        const url = input.value.trim();
        if (!url) {
            this.showNotification('Please enter a URL', 'error');
            return;
        }

        // Validate URL
        if (!url.startsWith('http://') && !url.startsWith('https://')) {
            this.showNotification('Please enter a valid URL', 'error');
            return;
        }

        try {
            const response = await api.fetchApi('/workflow-models/save-model-url', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename, url })
            });

            if (response.ok) {
                this.showNotification('URL saved', 'success');
                // Reload model info
                await this.selectBrowserModel(filename);
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to save URL', 'error');
            }
        } catch (e) {
            console.error("[WMD] Error saving model URL:", e);
            this.showNotification('Error saving URL', 'error');
        }
    }

    async loadModelReadme(url) {
        if (!url || !url.includes('huggingface.co')) return;

        try {
            const response = await api.fetchApi(`/workflow-models/hf-readme?url=${encodeURIComponent(url)}`);
            if (response.ok) {
                const data = await response.json();
                this.selectedModelReadme = data.readme || '<div style="color: #666;">No README available</div>';
            } else {
                this.selectedModelReadme = '<div style="color: #666;">Could not load README</div>';
            }
        } catch (e) {
            console.error("[WMD] Error loading README:", e);
            this.selectedModelReadme = '<div style="color: #666;">Error loading README</div>';
        }

        // Update just the README section
        const readmeEl = document.getElementById('wmd-model-readme');
        if (readmeEl) {
            readmeEl.innerHTML = this.selectedModelReadme;
        }
    }

    async scanModelMetadata() {
        this.showNotification('Scanning model metadata...', 'info');

        try {
            const response = await api.fetchApi('/workflow-models/scan-model-metadata', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ force: false })
            });

            if (response.ok) {
                const result = await response.json();
                const sources = [];
                if (result.from_safetensors > 0) sources.push(`${result.from_safetensors} from files`);
                if (result.from_model_list > 0) sources.push(`${result.from_model_list} from model-list`);
                const sourceInfo = sources.length > 0 ? ` (${sources.join(', ')})` : '';

                this.showNotification(
                    `Scanned ${result.scanned} models, found URLs for ${result.updated}${sourceInfo}`,
                    'success'
                );
                // Reload to show updated info
                await this.loadBrowserTab();
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to scan metadata', 'error');
            }
        } catch (e) {
            console.error("[WMD] Error scanning metadata:", e);
            this.showNotification('Error scanning metadata', 'error');
        }
    }

    getFilteredBrowserModels() {
        let models = [...(this.installedModels || [])];

        // Filter by search
        if (this.browserFilter) {
            const search = this.browserFilter.toLowerCase();
            models = models.filter(m => m.filename.toLowerCase().includes(search));
        }

        // Filter by type
        if (this.browserType) {
            models = models.filter(m => m.type === this.browserType);
        }

        // Sort by name
        models.sort((a, b) => a.filename.localeCompare(b.filename));

        return models;
    }

    onBrowserSearch(value) {
        this.browserFilter = value;
        this.renderBrowserTab();
    }

    onBrowserTypeChange(value) {
        this.browserType = value;
        this.selectedBrowserModel = null; // Clear selection when changing folder
        this.renderBrowserTab();
    }

    async trackModelUsage(models) {
        try {
            await api.fetchApi("/workflow-models/track-usage", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    models: models.filter(m => m.exists).map(m => ({
                        filename: m.filename,
                        directory: m.directory
                    }))
                })
            });
            console.log("[WMD] Tracked usage for", models.filter(m => m.exists).length, "models");
        } catch (error) {
            console.error("[WMD] Error tracking usage:", error);
        }
    }

    async copyModelPath(path) {
        try {
            await navigator.clipboard.writeText(path);
            this.showNotification('Path copied to clipboard', 'success');
        } catch (error) {
            console.error("[WMD] Error copying path:", error);
            this.showNotification('Failed to copy path', 'error');
        }
    }

    async viewModelMetadata(path) {
        try {
            const response = await api.fetchApi(`/workflow-models/model/metadata?path=${encodeURIComponent(path)}`);
            const metadata = await response.json();

            // Create metadata modal
            const overlay = document.createElement('div');
            overlay.className = 'wmd-metadata-overlay';
            overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };

            overlay.innerHTML = `
                <div class="wmd-metadata-modal">
                    <div class="wmd-metadata-header">
                        <div class="wmd-metadata-title">Model Details</div>
                        <button class="wmd-modal-close" onclick="this.closest('.wmd-metadata-overlay').remove()">×</button>
                    </div>
                    <div class="wmd-metadata-body">
                        <div class="wmd-metadata-row">
                            <div class="wmd-metadata-label">Filename</div>
                            <div class="wmd-metadata-value">${metadata.filename}</div>
                        </div>
                        <div class="wmd-metadata-row">
                            <div class="wmd-metadata-label">Type</div>
                            <div class="wmd-metadata-value">${metadata.type}</div>
                        </div>
                        <div class="wmd-metadata-row">
                            <div class="wmd-metadata-label">Size</div>
                            <div class="wmd-metadata-value">${metadata.size_human}</div>
                        </div>
                        <div class="wmd-metadata-row">
                            <div class="wmd-metadata-label">Path</div>
                            <div class="wmd-metadata-value mono">${metadata.path}</div>
                        </div>
                        ${metadata.hash ? `
                            <div class="wmd-metadata-row">
                                <div class="wmd-metadata-label">SHA256</div>
                                <div class="wmd-metadata-value mono">${metadata.hash}</div>
                            </div>
                        ` : ''}
                        ${metadata.modified ? `
                            <div class="wmd-metadata-row">
                                <div class="wmd-metadata-label">Modified</div>
                                <div class="wmd-metadata-value">${new Date(metadata.modified * 1000).toLocaleString()}</div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;

            document.body.appendChild(overlay);
        } catch (error) {
            console.error("[WMD] Error fetching metadata:", error);
            this.showNotification('Error loading model details', 'error');
        }
    }

    async deleteModel(path) {
        const filename = path.split(/[/\\]/).pop();
        if (!confirm(`Are you sure you want to delete "${filename}"?\n\nThis cannot be undone.`)) return;

        try {
            const response = await api.fetchApi("/workflow-models/model/delete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ path })
            });

            if (response.ok) {
                this.showNotification('Model deleted successfully', 'success');
                this.loadBrowserTab();
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Failed to delete model', 'error');
            }
        } catch (error) {
            console.error("[WMD] Error deleting model:", error);
            this.showNotification('Error deleting model', 'error');
        }
    }

    // Load Help tab content
    async loadHelpTab() {
        const content = document.getElementById("wmd-content-help");
        if (!content) return;

        // Load version info first
        let versionInfo = { installed: 'unknown', latest: null, update_available: false, github_url: '', registry_url: '' };
        try {
            const response = await api.fetchApi("/workflow-models/version");
            if (response.ok) {
                versionInfo = await response.json();
            }
        } catch (e) {
            console.error("[WMD] Error loading version info:", e);
        }

        const helpPanel = this.createHelpPanel(versionInfo);
        helpPanel.style.margin = '0';
        helpPanel.style.border = 'none';
        helpPanel.style.borderRadius = '0';

        content.innerHTML = '';
        content.appendChild(helpPanel);
    }

    // Switch to help tab
    toggleHelp() {
        this.selectTab('help');
    }

    createHelpPanel(versionInfo = {}) {
        const panel = document.createElement('div');
        panel.id = 'wmd-help-panel';
        panel.className = 'wmd-help-panel';

        // Build version card
        const updateButton = versionInfo.update_available
            ? `<a href="${versionInfo.registry_url}" target="_blank" class="wmd-btn wmd-btn-warning wmd-btn-small" style="margin-left: 12px;">Update Available</a>`
            : '';

        const latestInfo = versionInfo.latest
            ? `<span style="color: #888; margin-left: 8px;">(Latest: ${versionInfo.latest})</span>`
            : '';

        const versionCard = `
            <div class="wmd-version-card" style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border: 1px solid #0f3460; border-radius: 8px; padding: 16px; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 24px;">📦</span>
                    <div>
                        <div style="font-weight: bold; font-size: 16px; color: #e94560;">Workflow Models Downloader</div>
                        <div style="color: #888; font-size: 12px; margin-top: 4px;">
                            Version: <span style="color: #4CAF50; font-weight: bold;">${versionInfo.installed || 'unknown'}</span>
                            ${latestInfo}
                        </div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <a href="${versionInfo.github_url || 'https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader'}" target="_blank" class="wmd-btn wmd-btn-secondary wmd-btn-small" title="View on GitHub">
                        GitHub
                    </a>
                    ${updateButton}
                </div>
            </div>
        `;

        panel.innerHTML = `
            ${versionCard}
            <div class="wmd-help-title">
                <span style="color: #2196F3;">?</span> Help & FAQ
            </div>

            <div class="wmd-help-section">
                <div class="wmd-help-section-title">
                    <span>🔑</span> How to Get a HuggingFace Token
                </div>
                <div class="wmd-help-section-content">
                    <ol>
                        <li>Go to <a href="https://huggingface.co/settings/tokens" target="_blank" class="wmd-help-link">huggingface.co/settings/tokens</a></li>
                        <li>Click "New token" or "Create new token"</li>
                        <li>Give it a name (e.g., "ComfyUI") and select "Read" access</li>
                        <li>Copy the token and paste it in <strong>ComfyUI Menu > Settings > Workflow Models Downloader</strong></li>
                    </ol>
                    <div class="wmd-help-note">
                        <strong>Note:</strong> HuggingFace tokens are required for gated models like Flux, SD3, etc.
                        You must also accept the model's license on its HuggingFace page before downloading.
                    </div>
                </div>
            </div>

            <div class="wmd-help-section">
                <div class="wmd-help-section-title">
                    <span>🎨</span> How to Get a CivitAI API Key
                </div>
                <div class="wmd-help-section-content">
                    <ol>
                        <li>Go to <a href="https://civitai.com/user/account" target="_blank" class="wmd-help-link">civitai.com/user/account</a></li>
                        <li>Scroll down to "API Keys" section</li>
                        <li>Click "Add API Key" and give it a name</li>
                        <li>Copy the key and paste it in <strong>ComfyUI Menu > Settings > Workflow Models Downloader</strong></li>
                    </ol>
                    <div class="wmd-help-note">
                        <strong>Note:</strong> CivitAI API keys are required for downloading models from CivitAI,
                        including early access models.
                    </div>
                </div>
            </div>

            <div class="wmd-help-section">
                <div class="wmd-help-section-title">
                    <span>⚠️</span> "Security Error" When Installing from Registry
                </div>
                <div class="wmd-help-section-content">
                    If you see <strong>"only custom nodes from default channel"</strong> error when installing:
                    <ol>
                        <li>This is a <strong>ComfyUI Manager</strong> security setting, not an issue with this extension</li>
                        <li>Open ComfyUI Manager (click "Manager" button in ComfyUI)</li>
                        <li>Go to <strong>Manager Settings</strong></li>
                        <li>Find "Security Level" and change it from "Strong" to "Normal" or "Weak"</li>
                        <li>Restart ComfyUI and try installing again</li>
                    </ol>
                    <div class="wmd-help-warning">
                        <strong>Alternative:</strong> You can also install manually by cloning the repository:<br>
                        <code>git clone https://github.com/slahiri/ComfyUI-Workflow-Models-Downloader</code><br>
                        into your <code>ComfyUI/custom_nodes/</code> folder.
                    </div>
                </div>
            </div>

            <div class="wmd-help-section">
                <div class="wmd-help-section-title">
                    <span>📁</span> Custom Model Directories (extra_model_paths.yaml)
                </div>
                <div class="wmd-help-section-content">
                    If you store models in custom directories outside the default <code>models/</code> folder:
                    <ol>
                        <li>This extension now supports <code>extra_model_paths.yaml</code></li>
                        <li>Your custom paths configured in ComfyUI will be searched automatically</li>
                        <li>Edit <code>ComfyUI/extra_model_paths.yaml</code> to add custom paths</li>
                    </ol>
                    <div class="wmd-help-note">
                        <strong>Example extra_model_paths.yaml:</strong><br>
                        <code>
                        mymodels:<br>
                        &nbsp;&nbsp;base_path: D:/AI/Models<br>
                        &nbsp;&nbsp;checkpoints: checkpoints<br>
                        &nbsp;&nbsp;loras: loras
                        </code>
                    </div>
                </div>
            </div>

            <div class="wmd-help-section">
                <div class="wmd-help-section-title">
                    <span>🔎</span> How to Get a Tavily API Key
                </div>
                <div class="wmd-help-section-content">
                    Tavily enables AI-powered web search to find model sources:
                    <ol>
                        <li>Go to <a href="https://tavily.com" target="_blank" class="wmd-help-link">tavily.com</a></li>
                        <li>Sign up for a free account</li>
                        <li>Go to your dashboard and copy your API key</li>
                        <li>Paste it in <strong>Settings tab > Tavily API Key</strong></li>
                    </ol>
                    <div class="wmd-help-note">
                        <strong>Note:</strong> Tavily offers 1,000 free searches/month. Search results are cached locally
                        so repeated searches for the same model don't use additional quota.
                    </div>
                </div>
            </div>

            <div class="wmd-help-section">
                <div class="wmd-help-section-title">
                    <span>📂</span> Workflows Tab - Browse Saved Workflows
                </div>
                <div class="wmd-help-section-content">
                    The Workflows tab lets you browse all your saved workflow files:
                    <ol>
                        <li><strong>Left column:</strong> Lists all workflow files from your configured folders</li>
                        <li><strong>Middle column:</strong> Shows models used in the selected workflow</li>
                        <li><strong>Right column:</strong> Shows details for the selected model</li>
                    </ol>
                    <div class="wmd-help-note">
                        <strong>Manual Source Entry:</strong> If a model has no source URL, you'll see a text input field.
                        Paste the download URL (HuggingFace, CivitAI, or direct link) and click <strong>Save</strong>.
                        The URL is automatically parsed and saved for future use.
                    </div>
                </div>
            </div>

            <div class="wmd-help-section">
                <div class="wmd-help-section-title">
                    <span>🔍</span> Model Not Found / Unknown URLs
                </div>
                <div class="wmd-help-section-content">
                    If a model shows "Missing URLs / Unknown":
                    <ol>
                        <li><strong>Search URL:</strong> Click to search HuggingFace and CivitAI APIs</li>
                        <li><strong>Lookup Hash:</strong> If you have the file, calculates SHA256 and searches CivitAI</li>
                        <li><strong>Advanced Search:</strong> Uses AI-powered web search (requires Tavily API key)</li>
                        <li><strong>Manual Entry:</strong> In Workflows tab, paste URL directly into the Source field</li>
                    </ol>
                    <div class="wmd-help-note">
                        <strong>Tip:</strong> Search results are cached and persist across restarts.
                        Use Advanced Search to find sources, then copy the URL to the Source field.
                    </div>
                </div>
            </div>

            <div class="wmd-help-section">
                <div class="wmd-help-section-title">
                    <span>🚀</span> Quick Tips
                </div>
                <div class="wmd-help-section-content">
                    <ul style="list-style-type: disc; padding-left: 20px;">
                        <li><strong>Downloads continue in background</strong> - You can close this dialog and downloads will keep running</li>
                        <li><strong>Change directories</strong> - Use the dropdown to change where a model will be saved</li>
                        <li><strong>Filter models</strong> - Use the dropdown in header to show only missing, existing, etc.</li>
                        <li><strong>Settings persist</strong> - API keys are saved and remembered across sessions</li>
                    </ul>
                </div>
            </div>
        `;

        return panel;
    }

    async loadSettings() {
        try {
            const response = await api.fetchApi("/workflow-models/settings");
            this.settings = await response.json();

            // Also load queue status for parallel setting and aria2
            const queueResponse = await api.fetchApi("/workflow-models/queue-status");
            const queueStatus = await queueResponse.json();
            this.settings.max_parallel_downloads = queueStatus.max_parallel || 3;
            this.settings.aria2_available = queueStatus.aria2_available || false;
        } catch (error) {
            console.error("[WMD] Error loading settings:", error);
            this.settings = {
                huggingface_token: '',
                civitai_api_key: '',
                huggingface_token_set: false,
                civitai_api_key_set: false,
                max_parallel_downloads: 3,
                aria2_available: false
            };
        }
    }

    async copyToClipboard(text, successMsg = 'Copied to clipboard') {
        try {
            await navigator.clipboard.writeText(text);
            this.showNotification(successMsg, 'success');
        } catch (error) {
            console.error("[WMD] Copy failed:", error);
            this.showNotification('Failed to copy', 'error');
        }
    }

    copyModelMetadata(index) {
        const model = this.models[index];
        if (!model) return;

        const metadata = {
            filename: model.filename,
            type: model.type,
            directory: model.directory,
            status: model.exists ? 'EXISTS' : 'MISSING',
            url: model.url || 'No URL',
            hf_repo: model.hf_repo || '',
            hf_path: model.hf_path || '',
            source: model.source || ''
        };

        this.copyToClipboard(JSON.stringify(metadata, null, 2), 'Model info copied');
    }

    copyDownloadInfo(filename, status, error = '') {
        const info = {
            filename: filename,
            status: status,
            error: error || undefined,
            timestamp: new Date().toISOString()
        };

        this.copyToClipboard(JSON.stringify(info, null, 2), 'Download info copied');
    }

    copyError(error) {
        this.copyToClipboard(error, 'Error copied');
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

    // ==================== Workflows Tab ====================

    async loadWorkflowsTab() {
        const content = document.getElementById("wmd-content-workflows");
        if (!content) return;

        // Initialize state
        this.workflowsList = [];
        this.selectedWorkflow = null;
        this.workflowModels = [];
        this.selectedWorkflowModel = null;
        this.workflowsFilter = '';

        try {
            // Load workflows list from default directories
            const response = await api.fetchApi("/workflow-models/list-workflows");
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.workflowsList = data.workflows || [];
                }
            }

            this.renderWorkflowsTab();
        } catch (error) {
            console.error("[WMD] Error loading workflows tab:", error);
            // Show error state instead of stuck spinner
            content.innerHTML = `
                <div class="wmd-workflows-layout">
                    <div style="padding: 40px; text-align: center; color: #f87171;">
                        <div style="font-size: 24px; margin-bottom: 10px;">⚠️</div>
                        <div>Error loading workflows</div>
                        <div style="font-size: 12px; margin-top: 5px;">${error.message || 'Unknown error'}</div>
                    </div>
                </div>
            `;
        }
    }

    renderWorkflowsTab() {
        const content = document.getElementById("wmd-content-workflows");
        if (!content) return;

        try {
            // Ensure arrays are always valid
            this.workflowsList = this.workflowsList || [];
            this.workflowModels = this.workflowModels || [];
            this.workflowsFilter = this.workflowsFilter || '';

            const filteredWorkflows = this.workflowsList.filter(w =>
                w && w.name && w.name.toLowerCase().includes(this.workflowsFilter.toLowerCase())
            );

        // Build workflows list HTML
        const workflowsHtml = filteredWorkflows.length > 0
            ? filteredWorkflows.map((w, i) => `
                <div class="wmd-workflow-item ${this.selectedWorkflow?.path === w.path ? 'active' : ''}"
                     onclick="window.wmdInstance.selectWorkflowItem('${w.path.replace(/\\/g, '\\\\').replace(/'/g, "\\'")}')">
                    <span class="wmd-workflow-item-icon">📄</span>
                    <div class="wmd-workflow-item-info">
                        <div class="wmd-workflow-item-name">${w.name}</div>
                        <div class="wmd-workflow-item-path">${w.folder}/${w.relative_path}</div>
                    </div>
                </div>
            `).join('')
            : '<div class="wmd-workflows-empty">No workflows found</div>';

        // Build models list HTML
        let modelsHtml = '<div class="wmd-workflows-empty">Select a workflow to see models</div>';
        if (this.selectedWorkflow && this.workflowModels.length > 0) {
            modelsHtml = this.workflowModels.map((m, i) => `
                <div class="wmd-model-item ${!m.exists ? 'missing' : ''} ${this.selectedWorkflowModel?.filename === m.filename ? 'active' : ''}"
                     onclick="window.wmdInstance.selectWorkflowModelItem(${i})">
                    <div class="wmd-model-item-info">
                        <div class="wmd-model-item-name">${m.filename}</div>
                        <div class="wmd-model-item-type">${m.type} • ${m.node_class || 'Unknown Node'}</div>
                    </div>
                    <span class="wmd-model-item-status ${m.exists ? 'exists' : 'missing'}">
                        ${m.exists ? 'OK' : 'MISSING'}
                    </span>
                </div>
            `).join('');
        } else if (this.selectedWorkflow && this.workflowModels.length === 0) {
            modelsHtml = '<div class="wmd-workflows-empty">No models in this workflow</div>';
        }

        // Build model details HTML
        let detailsHtml = '<div class="wmd-workflows-empty">Select a model to see details</div>';
        if (this.selectedWorkflowModel) {
            const m = this.selectedWorkflowModel;

            // Build source link or input
            let sourceHtml = '';
            const hasSource = m.hf_repo || m.civitai_url || m.url;
            if (m.hf_repo) {
                sourceHtml = `<a href="https://huggingface.co/${m.hf_repo}" target="_blank">${m.hf_repo}</a>`;
            } else if (m.civitai_url) {
                sourceHtml = `<a href="${m.civitai_url}" target="_blank">View on CivitAI</a>`;
            } else if (m.url) {
                sourceHtml = `<a href="${m.url}" target="_blank">Direct URL</a>`;
            } else {
                // No source - show input field
                sourceHtml = `
                    <div style="display: flex; gap: 6px; align-items: center; width: 100%;">
                        <input type="text" id="wmd-source-url-input"
                               placeholder="Enter source URL..."
                               style="flex: 1; padding: 4px 8px; font-size: 11px; background: #333; border: 1px solid #555; border-radius: 4px; color: #fff;">
                        <button class="wmd-btn wmd-btn-secondary wmd-btn-small"
                                onclick="window.wmdInstance.saveModelSource()"
                                style="font-size: 10px; padding: 4px 8px; white-space: nowrap;">
                            Save
                        </button>
                    </div>
                `;
            }

            // Build advanced search section
            const advancedSearchEnabled = this.settings?.enable_advanced_search && this.settings?.tavily_api_key_set;
            const isDiffusionModel = m.type === 'diffusion_model' || m.type === 'checkpoint' || m.type === 'unet';
            const isSafetensor = m.filename?.endsWith('.safetensors');

            let advancedSearchHtml = '';
            if (advancedSearchEnabled) {
                // Check for cached results (from memory cache first)
                const cachedResults = this.searchCache[m.filename];
                const cachedHtml = cachedResults ? this.formatSearchResults(cachedResults) : '';

                advancedSearchHtml = `
                    <div class="wmd-model-details-section">
                        <div class="wmd-model-details-section-title" style="display: flex; justify-content: space-between; align-items: center;">
                            <span>Advanced Search</span>
                            <button class="wmd-btn wmd-btn-secondary wmd-btn-small"
                                    onclick="window.wmdInstance.searchModelAlternatives()"
                                    id="wmd-adv-search-btn"
                                    style="font-size: 11px; padding: 4px 8px;">
                                ${cachedResults ? 'Refresh' : 'Search'}
                            </button>
                        </div>
                        <div id="wmd-adv-search-results" style="padding: 10px;">${cachedHtml || '<div style="color: #666; font-size: 11px;">Loading...</div>'}</div>
                    </div>
                `;

                // Load cached results from backend if not in memory
                if (!cachedResults) {
                    this.loadCachedSearchResults(m.filename);
                }
            } else {
                advancedSearchHtml = `
                    <div class="wmd-model-details-section">
                        <div class="wmd-model-details-section-title">Advanced Search</div>
                        <div style="padding: 20px; color: #888; font-size: 12px; text-align: center;">
                            <p>Enable Advanced Search using Tavily for:</p>
                            <ul style="text-align: left; margin: 10px 0; padding-left: 20px;">
                                <li>Find possible download sources</li>
                                <li>Discover alternative versions</li>
                                ${isDiffusionModel && isSafetensor ? '<li>Find GGUF quantized versions</li>' : ''}
                            </ul>
                            <p style="margin-top: 10px;">
                                <a href="#" onclick="window.wmdInstance.selectTab('help'); return false;" style="color: #4a9eff;">
                                    Update Tavily API key in Settings
                                </a>
                            </p>
                        </div>
                    </div>
                `;
            }

            detailsHtml = `
                <div class="wmd-model-details-section">
                    <div class="wmd-model-details-section-title">Model Information</div>
                    <div class="wmd-model-details-row">
                        <div class="wmd-model-details-label">Filename</div>
                        <div class="wmd-model-details-value">${m.filename}</div>
                    </div>
                    <div class="wmd-model-details-row">
                        <div class="wmd-model-details-label">Type</div>
                        <div class="wmd-model-details-value">${m.type}</div>
                    </div>
                    <div class="wmd-model-details-row">
                        <div class="wmd-model-details-label">Directory</div>
                        <div class="wmd-model-details-value">${m.directory}</div>
                    </div>
                    <div class="wmd-model-details-row">
                        <div class="wmd-model-details-label">Status</div>
                        <div class="wmd-model-details-value" style="color: ${m.exists ? '#4CAF50' : '#f87171'}">
                            ${m.exists ? `EXISTS (${m.local_size || 'unknown size'})` : 'MISSING'}
                        </div>
                    </div>
                    <div class="wmd-model-details-row">
                        <div class="wmd-model-details-label">Node</div>
                        <div class="wmd-model-details-value">${m.node_class || 'Unknown'}</div>
                    </div>
                    <div class="wmd-model-details-row">
                        <div class="wmd-model-details-label">Source</div>
                        <div class="wmd-model-details-value" style="${!hasSource ? 'flex: 1;' : ''}">${sourceHtml}</div>
                    </div>
                </div>
                ${advancedSearchHtml}
            `;
        }

        // Count stats
        const existsCount = this.workflowModels.filter(m => m.exists).length;
        const missingCount = this.workflowModels.filter(m => !m.exists).length;

        content.innerHTML = `
            <div class="wmd-workflows-layout">
                <!-- Column 1: Workflows List -->
                <div class="wmd-workflows-column workflows-list">
                    <div class="wmd-workflows-column-header">
                        <span>Workflows</span>
                        <button class="wmd-refresh-btn" onclick="window.wmdInstance.loadWorkflowsTab()" title="Refresh">🔄</button>
                    </div>
                    <div class="wmd-workflows-search">
                        <input type="text" placeholder="Search workflows..."
                               value="${this.workflowsFilter}"
                               onkeyup="window.wmdInstance.onWorkflowsFilterChange(this.value)">
                    </div>
                    <div class="wmd-workflows-column-content">
                        ${workflowsHtml}
                    </div>
                </div>

                <!-- Column 2: Models List -->
                <div class="wmd-workflows-column models-list">
                    <div class="wmd-workflows-column-header">
                        <span>Models ${this.selectedWorkflow ? `(${this.workflowModels.length})` : ''}</span>
                        ${this.selectedWorkflow ? `
                            <span style="font-size: 10px; color: #888; font-weight: normal;">
                                <span style="color: #4CAF50;">${existsCount} OK</span> /
                                <span style="color: #f87171;">${missingCount} Missing</span>
                            </span>
                        ` : ''}
                    </div>
                    <div class="wmd-workflows-column-content">
                        ${modelsHtml}
                    </div>
                </div>

                <!-- Column 3: Model Details -->
                <div class="wmd-workflows-column model-details">
                    <div class="wmd-workflows-column-header">
                        <span>Model Details</span>
                    </div>
                    <div class="wmd-model-details-content">
                        ${detailsHtml}
                    </div>
                </div>
            </div>
        `;

            window.wmdInstance = this;
        } catch (error) {
            console.error("[WMD] Error rendering workflows tab:", error);
            content.innerHTML = `
                <div class="wmd-workflows-layout">
                    <div style="padding: 40px; text-align: center; color: #f87171;">
                        <div style="font-size: 24px; margin-bottom: 10px;">⚠️</div>
                        <div>Error rendering workflows</div>
                        <div style="font-size: 12px; margin-top: 5px;">${error.message || 'Unknown error'}</div>
                    </div>
                </div>
            `;
        }
    }

    async selectWorkflowItem(path) {
        // Find workflow
        const workflow = this.workflowsList.find(w => w.path === path);
        if (!workflow) return;

        this.selectedWorkflow = workflow;
        this.selectedWorkflowModel = null;
        this.workflowModels = [];

        // Temporarily show loading
        this.renderWorkflowsTab();

        // Parse workflow to get models
        try {
            const response = await api.fetchApi("/workflow-models/parse-workflow", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ path: workflow.path })
            });

            const data = await response.json();
            if (data.success) {
                this.workflowModels = data.models || [];
            }
        } catch (error) {
            console.error("[WMD] Error parsing workflow:", error);
        }

        this.renderWorkflowsTab();
    }

    selectWorkflowModelItem(index) {
        this.selectedWorkflowModel = this.workflowModels[index];
        this.renderWorkflowsTab();
    }

    onWorkflowsFilterChange(value) {
        this.workflowsFilter = value;
        this.renderWorkflowsTab();
    }

    // Helper to format time ago
    getTimeAgo(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        if (seconds < 60) return 'just now';
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        if (days < 7) return `${days}d ago`;
        return date.toLocaleDateString();
    }

    // Load cached search results from backend
    async loadCachedSearchResults(filename) {
        try {
            const response = await api.fetchApi(`/workflow-models/tavily-cache/${encodeURIComponent(filename)}`);
            const data = await response.json();

            if (data.success && data.results) {
                // Store in memory cache
                this.searchCache[filename] = data;

                // Update the results div if it exists
                const resultsDiv = document.getElementById('wmd-adv-search-results');
                const btn = document.getElementById('wmd-adv-search-btn');
                if (resultsDiv) {
                    resultsDiv.innerHTML = this.formatSearchResults(data);
                }
                if (btn) {
                    btn.textContent = 'Refresh';
                }
            } else {
                // No cached results
                const resultsDiv = document.getElementById('wmd-adv-search-results');
                if (resultsDiv) {
                    resultsDiv.innerHTML = '<div style="color: #666; font-size: 11px;">Click Search to find sources and alternatives</div>';
                }
            }
        } catch (error) {
            console.error('[WMD] Error loading cached search results:', error);
            const resultsDiv = document.getElementById('wmd-adv-search-results');
            if (resultsDiv) {
                resultsDiv.innerHTML = '<div style="color: #666; font-size: 11px;">Click Search to find sources and alternatives</div>';
            }
        }
    }

    // Save manually entered source URL
    async saveModelSource() {
        if (!this.selectedWorkflowModel) return;

        const input = document.getElementById('wmd-source-url-input');
        if (!input || !input.value.trim()) {
            alert('Please enter a source URL');
            return;
        }

        const url = input.value.trim();
        const m = this.selectedWorkflowModel;
        const filename = m.filename;

        try {
            const response = await api.fetchApi('/workflow-models/save-model-source', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: filename,
                    url: url,
                    model_type: m.type,
                    directory: m.directory
                })
            });

            const data = await response.json();

            if (data.success) {
                // Update the model in our list
                m.url = data.metadata?.url || url;
                m.hf_repo = data.metadata?.hf_repo;
                m.hf_path = data.metadata?.hf_path;
                m.civitai_url = data.metadata?.civitai_url;

                // Re-render to show updated source
                this.renderWorkflowsTab();
            } else {
                alert(data.error || 'Failed to save source');
            }
        } catch (error) {
            console.error('[WMD] Save source error:', error);
            alert('Error saving source: ' + error.message);
        }
    }

    // Extract best source from search results and update metadata
    async extractSourceFromResults() {
        if (!this.selectedWorkflowModel) return;

        const m = this.selectedWorkflowModel;
        const fullPath = m.filename;
        const searchName = fullPath.split(/[\\\/]/).pop();
        const cachedData = this.searchCache[fullPath];

        if (!cachedData || !cachedData.results || cachedData.results.length === 0) {
            alert('No search results to extract from. Please search first.');
            return;
        }

        const btn = document.getElementById('wmd-extract-btn');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Extracting...';
        }

        try {
            const response = await api.fetchApi('/workflow-models/extract-source', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: searchName,
                    original_filename: fullPath,
                    results: cachedData.results,
                    model_type: m.type,
                    directory: m.directory
                })
            });

            const data = await response.json();

            if (data.success) {
                // Update the model in our list
                if (data.metadata) {
                    m.url = data.metadata.url;
                    m.hf_repo = data.metadata.hf_repo;
                    m.hf_path = data.metadata.hf_path;
                    m.civitai_url = data.metadata.civitai_url;
                }

                // Show success and re-render
                if (btn) {
                    btn.textContent = 'Source Updated!';
                    btn.style.background = '#4CAF50';
                }

                // Re-render to show updated source
                setTimeout(() => this.renderWorkflowsTab(), 1500);
            } else {
                if (btn) {
                    btn.textContent = data.message || 'No source found';
                    btn.style.background = '#666';
                }
            }
        } catch (error) {
            console.error('[WMD] Extract source error:', error);
            if (btn) {
                btn.textContent = 'Error';
                btn.style.background = '#f44336';
            }
        }
    }

    // Format search results into HTML
    formatSearchResults(data) {
        const results = data.results || [];
        let html = '';

        // Show cache info if available
        if (data.cached_at) {
            const cachedDate = new Date(data.cached_at);
            const timeAgo = this.getTimeAgo(cachedDate);
            html += `<div style="color: #555; font-size: 9px; margin-bottom: 6px;">Cached ${timeAgo}</div>`;
        }

        // Show what was searched
        if (data.query) {
            html += `<div style="color: #666; font-size: 10px; margin-bottom: 8px;">Query: "${data.query}"</div>`;
        }

        if (results.length > 0) {
            // Helper to get source icon/label based on URL
            const getSourceStyle = (url) => {
                if (url.includes('huggingface.co')) return { icon: '🤗', label: 'HuggingFace' };
                if (url.includes('civitai.com')) return { icon: '🎨', label: 'CivitAI' };
                if (url.includes('github.com')) return { icon: '📦', label: 'GitHub' };
                return { icon: '🔗', label: 'Web' };
            };

            html += `<div style="color: #888; font-size: 11px; margin-bottom: 8px;">${results.length} results found</div>`;

            results.forEach((r, idx) => {
                const source = getSourceStyle(r.url);
                const content = r.content ? r.content.substring(0, 120) + (r.content.length > 120 ? '...' : '') : '';

                html += `
                    <div style="margin-bottom: 8px; padding: 8px; background: #2a2a2a; border-radius: 4px; border-left: 3px solid #555;">
                        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
                            <span style="font-size: 12px;">${source.icon}</span>
                            <span style="font-size: 9px; color: #888; background: #333; padding: 1px 4px; border-radius: 2px;">${source.label}</span>
                        </div>
                        <a href="${r.url}" target="_blank" style="color: #7aa2f7; font-size: 12px; word-break: break-word; text-decoration: none;">
                            ${r.title || r.url}
                        </a>
                        ${content ? `<div style="color: #666; font-size: 10px; margin-top: 4px; line-height: 1.3;">${content}</div>` : ''}
                        <div style="margin-top: 4px;">
                            <a href="${r.url}" target="_blank" style="color: #555; font-size: 9px; word-break: break-all;">${r.url}</a>
                        </div>
                    </div>
                `;
            });
        } else {
            html = '<div style="color: #666; font-size: 11px;">No results found</div>';
        }

        return html;
    }

    async searchModelAlternatives() {
        const resultsDiv = document.getElementById('wmd-adv-search-results');
        const btn = document.getElementById('wmd-adv-search-btn');

        if (!resultsDiv || !this.selectedWorkflowModel) return;

        // Get filename from selected model
        const fullPath = this.selectedWorkflowModel.filename;

        // Extract just the filename, removing any folder path
        const searchName = fullPath.split(/[\\\/]/).pop();

        // Check if it's a diffusion model safetensor for GGUF search
        const m = this.selectedWorkflowModel;
        const isDiffusionModel = m.type === 'diffusion_model' || m.type === 'checkpoint' || m.type === 'unet';
        const isSafetensor = fullPath?.endsWith('.safetensors');
        const searchGguf = isDiffusionModel && isSafetensor;

        // Show loading
        resultsDiv.innerHTML = '<div style="color: #888; font-size: 11px;">Searching...</div>';
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Searching...';
        }

        try {
            const response = await api.fetchApi('/workflow-models/search-alternatives', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: searchName, original_filename: fullPath, search_gguf: searchGguf })
            });

            const data = await response.json();

            if (!data.success) {
                resultsDiv.innerHTML = `<div style="color: #f87171; font-size: 11px;">${data.error || 'Search failed'}</div>`;
                return;
            }

            // Cache the results
            this.searchCache[fullPath] = data;

            // Format and display results
            resultsDiv.innerHTML = this.formatSearchResults(data);

        } catch (error) {
            console.error('[WMD] Search alternatives error:', error);
            resultsDiv.innerHTML = `<div style="color: #f87171; font-size: 11px;">Error: ${error.message}</div>`;
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = 'Refresh';
            }
        }
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

        app.ui.settings.addSetting({
            id: "WorkflowModelsDownloader.MaxParallelDownloads",
            category: ["Workflow Models Downloader", "Downloads"],
            name: "Max Parallel Downloads",
            tooltip: "Maximum number of simultaneous downloads (1-10). Higher values may speed up batch downloads but use more bandwidth.",
            type: "slider",
            attrs: {
                min: 1,
                max: 10,
                step: 1
            },
            defaultValue: 3,
            onChange: async (value) => {
                try {
                    await api.fetchApi("/workflow-models/settings", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ max_parallel_downloads: parseInt(value) })
                    });
                } catch (e) {
                    console.error("[WMD] Failed to save Max Parallel Downloads setting:", e);
                }
            }
        });

        // Try new-style menu first
        try {
            const { ComfyButton } = await import("../../scripts/ui/components/button.js");

            const wmdButton = new ComfyButton({
                icon: "download",
                action: showMissingModelsDialog,
                tooltip: "Scan workflow for required models and download them",
                content: "Workflow Models",
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
            button.textContent = "Workflow Models";
            button.onclick = showMissingModelsDialog;
            menu.append(button);

            console.log("[Workflow-Models-Downloader] Added button to old-style menu");
        }

        console.log(`[Workflow-Models-Downloader] v${VERSION} loaded successfully`);
    }
});
