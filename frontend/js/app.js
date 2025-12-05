// API Base URL
const API_BASE = '/api';

// Global state
const state = {
    token: localStorage.getItem('dns_manager_token') || null,
    user: null,
    currentZone: null,
    zoneData: null,
    allZones: [], // Store for search filtering
    users: [] // Store for user management
};

// ===========================
// API Functions
// ===========================

const api = {
    // Authentication
    async login(username, password) {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        return await response.json();
    },

    async logout() {
        const response = await fetch(`${API_BASE}/auth/logout`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });
        return await response.json();
    },

    async verify() {
        const response = await fetch(`${API_BASE}/auth/verify`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });
        return await response.json();
    },

    // Users (Admin Only)
    async getUsers() {
        const response = await fetch(`${API_BASE}/users`, {
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        return await response.json();
    },

    async createUser(username, password, role) {
        const response = await fetch(`${API_BASE}/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ username, password, role })
        });
        return await response.json();
    },

    async deleteUser(username) {
        const response = await fetch(`${API_BASE}/users/${username}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${state.token}` }
        });
        return await response.json();
    },

    // Zones
    async getZones() {
        const response = await fetch(`${API_BASE}/zones`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });
        return await response.json();
    },

    async getZoneRecords(zoneFile) {
        const response = await fetch(`${API_BASE}/zones/${zoneFile}/records`, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });
        return await response.json();
    },

    // Records
    async addRecord(zoneFile, record) {
        const response = await fetch(`${API_BASE}/zones/${zoneFile}/records`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ record })
        });
        return await response.json();
    },

    async updateRecord(zoneFile, oldRecord, newRecord) {
        const response = await fetch(`${API_BASE}/zones/${zoneFile}/records`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ old_record: oldRecord, new_record: newRecord })
        });
        return await response.json();
    },

    async deleteRecord(zoneFile, record) {
        const response = await fetch(`${API_BASE}/zones/${zoneFile}/records`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({ record })
        });
        return await response.json();
    },

    // Service operations
    async reloadZone(zoneName) {
        const response = await fetch(`${API_BASE}/reload/${zoneName}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });
        return await response.json();
    },

    async restartService() {
        const response = await fetch(`${API_BASE}/restart`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });
        return await response.json();
    },

    // Logs
    async getLogs(filters = {}) {
        let url = `${API_BASE}/logs`;
        const params = new URLSearchParams(filters);
        if (params.toString()) url += `?${params}`;

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${state.token}`
            }
        });
        return await response.json();
    },

    async createZone(name, type, allowTransfer, alsoNotify) {
        const response = await fetch(`${API_BASE}/zones`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${state.token}`
            },
            body: JSON.stringify({
                name,
                type,
                allow_transfer_ips: allowTransfer,
                also_notify_ips: alsoNotify
            })
        });
        return await response.json();
    }
};

// ===========================
// UI Functions & Logic
// ===========================

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');
}

function showView(viewId) {
    document.querySelectorAll('.view').forEach(view => view.classList.remove('active'));
    document.getElementById(viewId).classList.add('active');
}

function showLoading(show = true) {
    const overlay = document.getElementById('loading-overlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = '';
    if (type === 'success') {
        icon = '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
    } else if (type === 'error') {
        icon = '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
    } else {
        icon = '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>';
    }

    toast.innerHTML = `${icon}<div class="toast-message">${message}</div>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideInRight 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function showError(elementId, message) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.classList.add('active');
}

function hideError(elementId) {
    const element = document.getElementById(elementId);
    element.classList.remove('active');
}

// ===========================
// Login Functionality
// ===========================

document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const submitBtn = e.target.querySelector('button[type="submit"]');

    submitBtn.classList.add('loading');
    hideError('login-error');

    try {
        const result = await api.login(username, password);

        if (result.success) {
            state.token = result.token;
            state.user = result.user;
            localStorage.setItem('dns_manager_token', result.token);

            showToast('Login successful!', 'success');
            initDashboard();
            showPage('dashboard-page');
        } else {
            showError('login-error', result.error || 'Login failed');
        }
    } catch (error) {
        showError('login-error', 'Network error. Please try again.');
    } finally {
        submitBtn.classList.remove('loading');
    }
});

// ===========================
// Dashboard Initialization
// ===========================

async function initDashboard() {
    // Set user info
    document.getElementById('user-name').textContent = state.user.username;
    document.getElementById('user-role').textContent = state.user.role;

    // Handle Admin Permissions
    const adminSection = document.getElementById('admin-section');
    if (state.user.role !== 'admin') {
        adminSection.style.display = 'none';
        // If user is on an admin view, switch to default
        if (['users-view'].some(id => document.getElementById(id).classList.contains('active'))) {
            document.querySelector('[data-view="zones"]').click();
        }
    } else {
        adminSection.style.display = 'block';
    }

    // Load zones
    await loadZones();
}

// ===========================
// Zone Management
// ===========================

async function loadZones() {
    try {
        const result = await api.getZones();
        if (result.success) {
            state.allZones = result.zones;
            renderZoneSelector(state.allZones);
        } else {
            showToast('Failed to load zones', 'error');
        }
    } catch (error) {
        showToast('Failed to load zones', 'error');
    }
}

// Zone Modal Events
const zoneModal = document.getElementById('zone-modal');
if (document.getElementById('create-zone-btn')) {
    document.getElementById('create-zone-btn').addEventListener('click', () => zoneModal.classList.add('active'));
    document.getElementById('close-zone-modal-btn')?.addEventListener('click', () => zoneModal.classList.remove('active'));
    document.getElementById('cancel-zone-btn')?.addEventListener('click', () => zoneModal.classList.remove('active'));

    document.getElementById('zone-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const name = fd.get('name');
        const type = fd.get('type');
        const allowTransfer = fd.get('allow_transfer_ips');
        const alsoNotify = fd.get('also_notify_ips');

        showLoading(true);
        try {
            const res = await api.createZone(name, type, allowTransfer, alsoNotify);
            if (res.success) {
                showToast(`Zone ${name} created`, 'success');
                zoneModal.classList.remove('active');
                e.target.reset();
                await loadZones(); // Refresh list to show new zone
            } else {
                showToast(res.error || 'Failed to create zone', 'error');
            }
        } catch (err) {
            showToast('Network error', 'error');
        } finally {
            showLoading(false);
        }
    });
}

function renderZoneSelector(zones) {
    const selector = document.getElementById('zone-selector');

    if (zones.length === 0) {
        selector.innerHTML = '<option value="">No zones found</option>';
        return;
    }

    selector.innerHTML = '<option value="">Select a zone...</option>';
    zones.forEach(zone => {
        const option = document.createElement('option');
        option.value = zone.file;
        option.textContent = `${zone.name} (${zone.type})`;
        option.dataset.zoneName = zone.name;
        selector.appendChild(option);
    });
}

// Zone Search Filter
document.getElementById('zone-search-input').addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    const filtered = state.allZones.filter(z =>
        z.name.toLowerCase().includes(term) || z.file.toLowerCase().includes(term)
    );
    renderZoneSelector(filtered);

    // Auto-select first if only one match
    if (filtered.length === 1) {
        const selector = document.getElementById('zone-selector');
        selector.value = filtered[0].file;
        selector.dispatchEvent(new Event('change'));
    }
});

document.getElementById('zone-selector').addEventListener('change', async (e) => {
    const zoneFile = e.target.value;
    if (!zoneFile) {
        document.getElementById('zone-content').innerHTML = '<div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg><p>Select a zone to manage DNS records</p></div>';
        document.getElementById('records-section').style.display = 'none';
        return;
    }

    const zoneName = e.target.options[e.target.selectedIndex].dataset.zoneName;
    state.currentZone = { file: zoneFile, name: zoneName };
    await loadZoneRecords(zoneFile);
});

async function loadZoneRecords(zoneFile) {
    showLoading(true);
    try {
        const result = await api.getZoneRecords(zoneFile);
        if (result.success) {
            state.zoneData = result.data;
            displayZoneRecords(result.data.records);
        } else {
            showToast(result.error || 'Failed to load zone records', 'error');
        }
    } catch (error) {
        console.error('Load zone records error:', error);
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// Record Search Filter
document.getElementById('record-search-input').addEventListener('input', (e) => {
    if (!state.zoneData) return;

    const term = e.target.value.toLowerCase();
    const records = state.zoneData.records;

    const filtered = records.filter(r => {
        const name = getRecordName(r).toLowerCase();
        const value = getRecordValue(r).toLowerCase();
        const type = r.type.toLowerCase();
        return name.includes(term) || value.includes(term) || type.includes(term);
    });

    displayZoneRecords(filtered);
});


// ===========================
// Record Display & Management
// ===========================

function getRecordValue(record) {
    switch (record.type) {
        case 'A': return record.ipv4;
        case 'AAAA': return record.ipv6;
        case 'MX': return `${record.priority} ${record.mailserver}`;
        case 'CNAME': return record.target;
        case 'TXT': return record.text;
        case 'SRV': return `${record.priority} ${record.weight} ${record.port} ${record.target}`;
        case 'PTR': return record.fqdn;
        case 'NS': return record.nameserver;
        default: return JSON.stringify(record);
    }
}

function getRecordName(record) {
    return record.name || record.ip_octet || '@';
}

function displayZoneRecords(records) {
    const data = state.zoneData;
    document.getElementById('zone-content').innerHTML = '';
    document.getElementById('records-section').style.display = 'block';
    document.getElementById('zone-title').textContent = `${state.currentZone.name} Records`;

    if (data.soa) {
        document.getElementById('soa-info-content').innerHTML = `
            <div class="soa-item">
                <div class="soa-label">Serial</div>
                <div class="soa-value">${data.soa.serial}</div>
            </div>
            <div class="soa-item">
                <div class="soa-label">Primary NS</div>
                <div class="soa-value">${data.soa.primary_ns}</div>
            </div>
            <div class="soa-item">
                <div class="soa-label">Admin Email</div>
                <div class="soa-value">${data.soa.admin_email}</div>
            </div>
        `;
    }

    const tbody = document.getElementById('records-tbody');
    tbody.innerHTML = '';

    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--color-text-muted);">No records found</td></tr>';
        return;
    }

    records.forEach(record => {
        const row = document.createElement('tr');
        const commentText = record.comment || '';
        const commentDisplay = commentText ? `<span title="${commentText}">${commentText}</span>` : '<span style="color: var(--color-text-muted);">-</span>';

        row.innerHTML = `
            <td><span class="record-type-badge">${record.type}</span></td>
            <td class="record-value">${getRecordName(record)}</td>
            <td class="record-value">${getRecordValue(record)}</td>
            <td class="comment-cell comment-column">${commentDisplay}</td>
            <td style="text-align: right;">
                <button class="btn-icon" onclick="editRecord(${JSON.stringify(record).replace(/"/g, '&quot;')})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" style="width: 18px; height: 18px;">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                </button>
                <button class="btn-icon danger" onclick="deleteRecordConfirm(${JSON.stringify(record).replace(/"/g, '&quot;')})">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" style="width: 18px; height: 18px;">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });

    updateCommentVisibility();
}

function updateCommentVisibility() {
    const showComments = document.getElementById('show-comments-toggle')?.checked ?? true;
    document.querySelectorAll('.comment-column').forEach(el => {
        el.style.display = showComments ? '' : 'none';
    });
}

document.getElementById('show-comments-toggle').addEventListener('change', updateCommentVisibility);

// ===========================
// User Management Logic
// ===========================

async function loadUsers() {
    if (state.user.role !== 'admin') return;

    showLoading(true);
    try {
        const result = await api.getUsers();
        if (result.success) {
            state.users = result.users;
            displayUsers(result.users);
        } else {
            showToast('Failed to load users', 'error');
        }
    } catch (e) {
        showToast('Error loading users', 'error');
    } finally {
        showLoading(false);
    }
}

function displayUsers(users) {
    const tbody = document.getElementById('users-tbody');
    tbody.innerHTML = '';

    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong style="color: var(--color-primary);">${user.username}</strong></td>
            <td><span class="user-role-badge">${user.role}</span></td>
            <td>${user.created_at || '-'}</td>
            <td>${user.last_login || 'Never'}</td>
            <td style="text-align: right;">
                ${user.username !== 'admin' && user.username !== state.user.username ? `
                <button class="btn-icon danger" onclick="deleteUserConfirm('${user.username}')">
                     <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>` : '<span style="color:var(--color-text-muted); font-size: 0.8rem;">Protected</span>'}
            </td>
        `;
        tbody.appendChild(row);
    });
}

// User Modal Events
const userModal = document.getElementById('user-modal');
document.getElementById('add-user-btn').addEventListener('click', () => userModal.classList.add('active'));
document.getElementById('close-user-modal-btn').addEventListener('click', () => userModal.classList.remove('active'));
document.getElementById('cancel-user-btn').addEventListener('click', () => userModal.classList.remove('active'));

document.getElementById('user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);

    showLoading(true);
    try {
        const res = await api.createUser(fd.get('username'), fd.get('password'), fd.get('role'));
        if (res.success) {
            showToast('User created successfully', 'success');
            userModal.classList.remove('active');
            e.target.reset();
            loadUsers();
        } else {
            showToast(res.error, 'error');
        }
    } catch (err) {
        showToast('Failed to create user', 'error');
    } finally {
        showLoading(false);
    }
});

window.deleteUserConfirm = async (username) => {
    if (!confirm(`Are you sure you want to delete user "${username}"? This cannot be undone.`)) return;

    showLoading(true);
    try {
        const res = await api.deleteUser(username);
        if (res.success) {
            showToast('User deleted', 'success');
            loadUsers();
        } else {
            showToast(res.error, 'error');
        }
    } catch (err) {
        showToast('Error deleting user', 'error');
    } finally {
        showLoading(false);
    }
};

// ===========================
// Modal & Action Logic (Records)
// ===========================

let currentEditRecord = null;

document.getElementById('add-record-btn').addEventListener('click', () => {
    currentEditRecord = null;
    document.getElementById('modal-title').textContent = 'Add DNS Record';
    document.getElementById('submit-btn-text').textContent = 'Add Record';
    document.getElementById('record-form').reset();
    updateRecordForm();
    showRecordModal();
});

document.getElementById('record-type').addEventListener('change', updateRecordForm);

function updateRecordForm() {
    const type = document.getElementById('record-type').value;
    const container = document.getElementById('dynamic-fields');
    container.innerHTML = '';

    const fields = getFieldsForRecordType(type);
    fields.forEach(field => {
        const div = document.createElement('div');
        div.className = 'form-group';
        div.innerHTML = `
            <label for="${field.name}">${field.label}</label>
            <input type="${field.type}" id="${field.name}" name="${field.name}" 
                   placeholder="${field.placeholder}" ${field.required ? 'required' : ''} 
                   value="${currentEditRecord ? (currentEditRecord[field.name] || '') : ''}">
        `;
        container.appendChild(div);
    });

    const commentDiv = document.createElement('div');
    commentDiv.className = 'form-group';
    commentDiv.innerHTML = `
        <label for="comment">Comment (Optional)</label>
        <input type="text" id="comment" name="comment" 
               placeholder="Optional comment for this record" 
               value="${currentEditRecord ? (currentEditRecord.comment || '') : ''}">
    `;
    container.appendChild(commentDiv);
}

function getFieldsForRecordType(type) {
    const fieldSets = {
        'A': [
            { name: 'name', label: 'Name', type: 'text', placeholder: 'www', required: true },
            { name: 'ipv4', label: 'IPv4 Address', type: 'text', placeholder: '192.168.1.1', required: true }
        ],
        'AAAA': [
            { name: 'name', label: 'Name', type: 'text', placeholder: 'www', required: true },
            { name: 'ipv6', label: 'IPv6 Address', type: 'text', placeholder: '2001:db8::1', required: true }
        ],
        'MX': [
            { name: 'name', label: 'Name', type: 'text', placeholder: '@', required: true },
            { name: 'priority', label: 'Priority', type: 'number', placeholder: '10', required: true },
            { name: 'mailserver', label: 'Mail Server', type: 'text', placeholder: 'mail.example.com.', required: true }
        ],
        'CNAME': [
            { name: 'name', label: 'Name', type: 'text', placeholder: 'www', required: true },
            { name: 'target', label: 'Target', type: 'text', placeholder: 'example.com.', required: true }
        ],
        'TXT': [
            { name: 'name', label: 'Name', type: 'text', placeholder: '@', required: true },
            { name: 'text', label: 'Text Value', type: 'text', placeholder: 'v=spf1 mx -all', required: true }
        ],
        'SRV': [
            { name: 'name', label: 'Service Name', type: 'text', placeholder: '_service._tcp', required: true },
            { name: 'priority', label: 'Priority', type: 'number', placeholder: '0', required: true },
            { name: 'weight', label: 'Weight', type: 'number', placeholder: '1', required: true },
            { name: 'port', label: 'Port', type: 'number', placeholder: '443', required: true },
            { name: 'target', label: 'Target', type: 'text', placeholder: 'server.example.com.', required: true }
        ],
        'PTR': [
            { name: 'ip_octet', label: 'IP Last Octet', type: 'text', placeholder: '10', required: true },
            { name: 'fqdn', label: 'FQDN', type: 'text', placeholder: 'host.example.com.', required: true }
        ],
        'NS': [
            { name: 'name', label: 'Name', type: 'text', placeholder: '@', required: true },
            { name: 'nameserver', label: 'Name Server', type: 'text', placeholder: 'ns1.example.com.', required: true }
        ]
    };
    return fieldSets[type] || [];
}

document.getElementById('record-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const record = { type: formData.get('type') };

    for (let [key, value] of formData.entries()) {
        if (key !== 'type') {
            if (key === 'comment' && !value) continue;
            if (['priority', 'weight', 'port'].includes(key)) {
                record[key] = parseInt(value);
            } else {
                record[key] = value;
            }
        }
    }

    showLoading(true);
    try {
        let result;
        if (currentEditRecord) {
            result = await api.updateRecord(state.currentZone.file, currentEditRecord, record);
        } else {
            result = await api.addRecord(state.currentZone.file, record);
        }

        if (result.success) {
            showToast(currentEditRecord ? 'Record updated' : 'Record added', 'success');
            hideRecordModal();
            await loadZoneRecords(state.currentZone.file);
        } else {
            showToast(result.error || 'Operation failed', 'error');
        }
    } catch (error) {
        showToast('Network error', 'error');
    } finally {
        showLoading(false);
    }
});

window.editRecord = function (record) {
    currentEditRecord = record;
    document.getElementById('modal-title').textContent = 'Edit DNS Record';
    document.getElementById('submit-btn-text').textContent = 'Update Record';
    document.getElementById('record-type').value = record.type;
    updateRecordForm();
    showRecordModal();
};

window.deleteRecordConfirm = async function (record) {
    if (!confirm(`Delete ${record.type} record for ${getRecordName(record)}?`)) return;
    showLoading(true);
    try {
        const result = await api.deleteRecord(state.currentZone.file, record);
        if (result.success) {
            showToast('Record deleted', 'success');
            await loadZoneRecords(state.currentZone.file);
        } else {
            showToast(result.error || 'Delete failed', 'error');
        }
    } catch (e) { showToast('Network error', 'error'); }
    finally { showLoading(false); }
};

function showRecordModal() { document.getElementById('record-modal').classList.add('active'); }
function hideRecordModal() { document.getElementById('record-modal').classList.remove('active'); }

document.getElementById('close-modal-btn').addEventListener('click', hideRecordModal);
document.getElementById('cancel-record-btn').addEventListener('click', hideRecordModal);

// Reload & Restart
document.getElementById('reload-zone-btn').addEventListener('click', async () => {
    if (!state.currentZone) return;
    showLoading(true);
    try {
        const res = await api.reloadZone(state.currentZone.name);
        if (res.success) {
            showToast('Zone reloaded', 'success');
            // Refresh zone records from file to show latest Serial/Changes
            await loadZoneRecords(state.currentZone.file);
        } else {
            showToast(res.error, 'error');
        }
    } catch (e) { showToast('Network error', 'error'); }
    finally { showLoading(false); }
});

document.getElementById('restart-service-btn').addEventListener('click', async () => {
    if (!confirm('Restart named service?')) return;
    showLoading(true);
    try {
        const res = await api.restartService();
        if (res.success) showToast('Service restarted', 'success');
        else showToast(res.error, 'error');
    } catch (e) { showToast('Network error', 'error'); }
    finally { showLoading(false); }
});

// Navigation
document.querySelectorAll('.sidebar-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const viewId = btn.dataset.view;
        if (!viewId) return; // e.g., restart service btn

        showView(viewId + '-view');
        document.querySelectorAll('.sidebar-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        if (viewId === 'users') loadUsers();
        if (viewId === 'logs') loadEventLogs();
    });
});

// Logs
async function loadEventLogs() {
    try {
        const result = await api.getLogs();
        if (result.success) {
            const tbody = document.getElementById('logs-tbody');
            tbody.innerHTML = '';
            result.logs.forEach(log => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${new Date(log.timestamp).toLocaleString()}</td>
                    <td>${log.user}</td>
                    <td>${log.action}</td>
                    <td><span class="status-badge ${log.status === 'success' ? 'status-success' : 'status-failure'}">${log.status}</span></td>
                    <td>${log.details ? JSON.stringify(log.details) : '-'}</td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (e) { console.error(e); }
}

document.getElementById('logout-btn').addEventListener('click', async () => {
    await api.logout();
    state.token = null;
    state.user = null;
    localStorage.removeItem('dns_manager_token');
    showPage('login-page');
});

// Auto-check auth
async function checkAuth() {
    if (state.token) {
        try {
            const res = await api.verify();
            if (res.success) {
                state.user = res.user;
                initDashboard();
                showPage('dashboard-page');
            } else {
                throw new Error('Invalid token');
            }
        } catch (e) {
            state.token = null;
            localStorage.removeItem('dns_manager_token');
            showPage('login-page');
        }
    } else {
        showPage('login-page');
    }
}
checkAuth();
