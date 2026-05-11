const API_BASE = window.location.origin;
const SITES_URL = window.SITES_URL || 'https://nodify-sites.azirar.ovh';

async function loadSites() {
    const grid = document.getElementById('sitesGrid');
    if (!grid) return;
    
    grid.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i><p>Loading sites...</p></div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/sites`);
        if (!response.ok) throw new Error('Failed to fetch sites');
        const sites = await response.json();
        
        updateStats(sites);
        displaySites(sites);
    } catch (error) {
        console.error('Error loading sites:', error);
        grid.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Error loading sites</p></div>';
    }
}

function updateStats(sites) {
    const totalSitesEl = document.getElementById('totalSites');
    const totalSizeEl = document.getElementById('totalSize');
    
    if (totalSitesEl) totalSitesEl.textContent = sites.length;
    if (totalSizeEl) {
        const totalSize = sites.reduce((sum, site) => sum + (site.size || 0), 0);
        totalSizeEl.textContent = formatSize(totalSize);
    }
}

function displaySites(sites) {
    const grid = document.getElementById('sitesGrid');
    if (!grid) return;
    
    const searchTerm = document.getElementById('searchInput')?.value.toLowerCase() || '';
    const filteredSites = sites.filter(site => site.name.toLowerCase().includes(searchTerm));
    
    if (filteredSites.length === 0) {
        grid.innerHTML = '<div class="empty-state"><i class="fas fa-folder-open"></i><p>No sites found</p></div>';
        return;
    }
    
    grid.innerHTML = filteredSites.map(site => `
        <div class="site-card" data-name="${escapeHtml(site.name)}">
            <div class="site-header">
                <div class="site-icon">
                    <i class="fas fa-globe"></i>
                </div>
                <div class="site-info">
                    <h3>${escapeHtml(site.name)}</h3>
                    <p><i class="fas fa-calendar-alt"></i> Generated</p>
                </div>
            </div>
            <div class="site-size">
                <i class="fas fa-hdd"></i> ${formatSize(site.size)} KB
            </div>
            <div class="site-actions">
                 <a href="${SITES_URL}/${site.name}/" target="_blank" class="btn-view">
		    <i class="fas fa-external-link-alt"></i> View
                </a>
                <button class="btn-delete" onclick="deleteSite('${site.name}')">
                    <i class="fas fa-trash-alt"></i> Delete
                </button>
            </div>
        </div>
    `).join('');
}

async function deleteSite(siteName) {
    if (!confirm(`Delete "${siteName}"? This action cannot be undone.`)) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/delete/${siteName}`, { method: 'DELETE' });
        if (response.ok) {
            loadSites();
        } else {
            const error = await response.json();
            alert(`Error: ${error.error || 'Failed to delete site'}`);
        }
    } catch (error) {
        console.error('Error deleting site:', error);
        alert('Error deleting site');
    }
}

function formatSize(kb) {
    if (kb >= 1024) return (kb / 1024).toFixed(1) + ' MB';
    return kb.toFixed(1);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Webhook URL display
const webhookUrlEl = document.getElementById('webhookUrl');
if (webhookUrlEl) {
    const fullUrl = `${window.location.protocol}//${window.location.host}/webhook`;
    webhookUrlEl.textContent = fullUrl;
}

// Search input
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', () => loadSites());
}

// Auto-refresh every 30 seconds
setInterval(() => {
    if (document.visibilityState === 'visible') loadSites();
}, 5000);

// Initial load
loadSites();
