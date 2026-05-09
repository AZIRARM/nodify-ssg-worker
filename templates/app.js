* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    min-height: 100vh;
    color: #f1f5f9;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 40px 24px;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 48px;
    flex-wrap: wrap;
    gap: 20px;
}

.logo h1 {
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.logo p {
    font-size: 14px;
    color: #94a3b8;
    margin-top: 4px;
}

.stats {
    display: flex;
    gap: 24px;
}

.stat-card {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 16px 24px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-card i {
    font-size: 24px;
    color: #60a5fa;
    margin-right: 12px;
}

.stat-card .label {
    font-size: 12px;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.stat-card .value {
    font-size: 32px;
    font-weight: 700;
    margin-top: 4px;
}

.webhook-info {
    background: rgba(96, 165, 250, 0.1);
    border-left: 4px solid #60a5fa;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 32px;
}

.webhook-info h3 {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 12px;
    color: #60a5fa;
}

.webhook-info code {
    background: #0f172a;
    padding: 8px 12px;
    border-radius: 8px;
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    display: inline-block;
}

.webhook-info .endpoint {
    background: #0f172a;
    padding: 8px 12px;
    border-radius: 8px;
    font-family: monospace;
    font-size: 13px;
    margin-top: 8px;
}

.controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;
}

.search-box {
    position: relative;
}

.search-box i {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: #64748b;
}

.search-box input {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 10px 12px 10px 36px;
    color: #f1f5f9;
    font-size: 14px;
    width: 250px;
}

.search-box input::placeholder {
    color: #64748b;
}

.refresh-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 10px 20px;
    color: #f1f5f9;
    cursor: pointer;
    transition: all 0.3s;
}

.refresh-btn:hover {
    background: rgba(255, 255, 255, 0.1);
}

.sites-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
}

.site-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 20px;
    transition: all 0.3s;
}

.site-card:hover {
    transform: translateY(-4px);
    border-color: rgba(96, 165, 250, 0.3);
    background: rgba(255, 255, 255, 0.05);
}

.site-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
}

.site-icon {
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.site-icon i {
    font-size: 24px;
    color: white;
}

.site-info h3 {
    font-size: 18px;
    font-weight: 600;
    word-break: break-all;
}

.site-info p {
    font-size: 12px;
    color: #94a3b8;
    margin-top: 4px;
}

.site-size {
    margin-bottom: 16px;
    font-size: 13px;
    color: #cbd5e1;
}

.site-size i {
    margin-right: 6px;
    color: #60a5fa;
}

.site-actions {
    display: flex;
    gap: 12px;
}

.btn-view {
    flex: 1;
    background: rgba(96, 165, 250, 0.2);
    border: 1px solid rgba(96, 165, 250, 0.3);
    border-radius: 10px;
    padding: 10px;
    color: #60a5fa;
    text-decoration: none;
    text-align: center;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.3s;
}

.btn-view:hover {
    background: rgba(96, 165, 250, 0.3);
}

.btn-delete {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.3);
border-radius: 10px;
padding: 10px;
color: #ef4444;
cursor: pointer;
font-size: 13px;
font-weight: 500;
transition: all 0.3s;
}

.btn-delete:hover {
    background: rgba(239, 68, 68, 0.3);
}

.empty-state {
    text-align: center;
    padding: 80px 20px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 24px;
    border: 1px dashed rgba(255, 255, 255, 0.1);
}

.empty-state i {
    font-size: 64px;
    color: #475569;
    margin-bottom: 16px;
}

.empty-state p {
    color: #94a3b8;
}

.loading {
    text-align: center;
    padding: 60px;
}

.loading i {
    font-size: 32px;
    color: #60a5fa;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.footer {
    text-align: center;
    padding: 40px 20px 20px;
    color: #64748b;
    font-size: 12px;
}

.footer a {
    color: #60a5fa;
    text-decoration: none;
}