const API = 'http://localhost:8000';
let employees = [];
let leaveRequests = [];
let uploadTargetId = null;

//Navigation
function showPage(name) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('page-' + name).classList.add('active');
    if (btn) btn.classList.add('active');
    if (name == 'dashboard') loadDashboard();
    if (name == 'employees') loadEmployees();
    if (name == 'leave') loadLeave();
}

//Modal
function openModal(id) {
    if (id == 'modal-submit-leave') populateEmployeeSelect();
    document.getElementById(id).classList.add('open');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('open');
}

//Toast
function toast(msg, type = '') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'show' + type;
    setTimeout(() => t.className = '', 3000);
}

//API Helpers
async function get(path) {
    try {
        const r = await fetch(API + path);
        if (!r.ok) throw new Error(await r.text());
        return await r.json();
    } catch (e) {
        toast('Error: ' + e.message, 'error');
        return null;
    }
}

async function post(path, body) {
    try {
        const r = await fetch(API + path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || JSON.stringify(data));
        return data;
    } catch (e) {
        toast('Error: ' + e.message, 'error');
        return null;
    }
}

async function patch(path, body) {
    try {
        const r = await fetch(API + path, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail || JSON.stringify(data));
        return data;
    } catch (e) {
        toast('Error: ' + e.message, 'error');
        return null
    }
}

//Employee Name Lookup
function empName(id) {
    const e = employees.find(e => e.id === id);
    return e ? e.name : '#' + id;
}

//Badge
function badge(val, cls) {
    return `<span class="badge badge-${(val || '').toLowerCase()}">${val || '—'}</span>`;
}

//Dashboard
async function loadDashboard() {
    const [emps, reqs] = await Promise.all([get('/employees'), get('/leave-requests')]);
    if (!emps || !reqs) return;
    employees = emps; leaveRequests = reqs;

    document.getElementById('stat-employees').textContent = emps.length;
    document.getElementById('stat-pending').textContent = reqs.filter(r => r.status === 'pending').length;
    document.getElementById('stat-approved').textContent = reqs.filter(r => r.status === 'approved').length;
    document.getElementById('stat-rejected').textContent = reqs.filter(r => r.status === 'rejected').length;

    const recent = [...reqs].reverse().slice(0, 8);
    const tbody = document.getElementById('dashboard-table');
    if (!recent.length) { tbody.innerHTML = '<tr><td colspan="5" class="empty">No Requests Yet.</td></tr>'; return; }
    tbody.innerHTML = recent.map(r => `
                    <tr>
                        <td>${empName(r.employee_id)}</td>
                        <td>${badge(r.leave_type)}</td>
                        <td class="mono">${r.start_date} → ${r.end_date}</td>
                        <td>${r.days_requested}</td>
                        <td>${badge(r.status)}</td>
                    </tr>`).join('');
}

//Employees
async function loadEmployees() {
    const data = await get('/employees');
    if (!data) return;
    employees = data;
    const tbody = document.getElementById('employees-table');
    if (!data.length) { tbody.innerHTML = '<tr><td colspan="7" class="empty">No Employees Found.</td></tr>'; return; }

    const balances = await get('/leave-balances') || [];
    const balMap = {};
    balances.forEach(b => {
        if (!balMap[b.employee_id]) balMap[b.employee_id] = {};
        balMap[b.employee_id][b.leave_type] = b.remaining_days;
    })

    tbody.innerHTML = data.map(e => `
                    <tr>
                        <td class="mono">${e.id}</td>
                        <td><strong>${e.name}</strong></td>
                        <td>${e.email}</td>
                        <td>${badge(e.type)}</td>
                        <td class="mono">${e.date_hired}</td>
                        <td>${balMap[e.id]?.vacation ?? '—'}</td>
                        <td>${balMap[e.id]?.sick ?? '—'}</td>
                    </tr>`).join('');
}

async function addEmployee() {
    const body = {
        name: document.getElementById('emp-name').value,
        email: document.getElementById('emp-email').value,
        type: document.getElementById('emp-type').value,
        date_hired: document.getElementById('emp-date').value
    };
    if (!body.name || !body.email || !body.date_hired) { toast('Please fill in all fields.', 'error'); return; }
    const res = await post('/employees', body);
    if (res) {
        toast('Employee Added - ID ' + res.employee_id, 'success');
        closeModal('modal-add-employee');
        loadEmployees();
    }
}

function populateEmployeeSelect() {
    const sel = document.getElementById('leave-employee-id');
    sel.innerHTML = employees.map(e => `<option value="${e.id}">${e.name} (${e.type})</option>`).join('');
}

//Leave Requests
async function loadLeave() {
    const [emps, reqs] = await Promise.all([get('/employees'), get('/leave-requests')]);
    if (!emps || !reqs) return;
    employees = emps; leaveRequests = reqs;

    const tbody = document.getElementById('leave-table');
    if (!reqs.length) { tbody.innerHTML = '<tr><td colspan="9" class="empty">No Leave Requests Found.</td></tr>'; return; }

    tbody.innerHTML = [...reqs].reverse().map(r => {
        const isPending = r.status === 'pending';
        const isSick = r.leave_type === 'sick';
        const needsDoc = isSick && r.days_requested > 2 && !r.sick_document_id;

        let actions = '';
        if (isPending) {
            actions += `<button class="btn btn-approve btn-sm" onclick="updateStatus(${r.id}, 'approved')">Approve</button>`;
            actions += `<button class="btn btn-reject btn-sm" onclick="updateStatus(${r.id}, 'rejected')">Reject</button>`;
        }
        if (needsDoc) {
            actions += `<button class="btn btn-ghost btn-sm" onclick="openUpload(${r.id})">Upload</button>`;
        }

        return `<tr>
                        <td class="mono">${r.id}</td>
                        <td>${empName(r.employee_id)}</td>
                        <td>${badge(r.leave_type)}</td>
                        <td class="mono">${r.start_date}</td>
                        <td class="mono">${r.end_date}</td>
                        <td>${r.days_requested}</td>
                        <td>${badge(r.status)}</td>
                        <td>${r.sick_document_id ? "Yes" : needsDoc ? "No" : '-'}</td>
                        <td><div class="actions-cell">${actions || '<span style="color:var(--muted); font-size:12px">-</span>'}</div></td>
                    </tr>`;
    }).join('')
}

async function submitLeave() {
    const body = {
        employee_id: parseInt(document.getElementById('leave-employee-id').value),
        leave_type: document.getElementById('leave-type').value,
        start_date: document.getElementById('leave-start').value,
        end_date: document.getElementById('leave-end').value
    };
    if (!body.start_date || !body.end_date) { toast('Please fill in all fields', 'error'); return; }
    const res = await post('/leave-requests', body);
    if (res) {
        toast(`Request Submitted - ${res.days_requested} Day(s) Requested`, 'success');
        closeModal('modal-submit-leave');
        loadLeave();
        loadDashboard();
    }
}

//Approve / Reject
async function updateStatus(id, status) {
    const res = await patch(`/leave-requests/${id}/status`, { status });
    if (res) {
        toast(`Request ${status}`, 'success');
        loadLeave();
        loadDashboard();
    }
}

//Sick Note Upload
function openUpload(id) {
    uploadTargetId = id;
    openModal('modal-upload-sick');
}

async function uploadSickNote() {
    const file = document.getElementById('sick-file').files[0];
    if (!file) { toast('Please Select a File', 'error'); return; }
    const form = new FormData();
    form.append('file', file);
    try {
        const r = await fetch(`${API}/leave-requests/${uploadTargetID}/upload-sick-note`, {
            method: 'POST', body: form
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.detail);
        toast('Sick Note Uploaded', 'success');
        closeModal('modal-upload-sick');
        loadLeave();
    } catch (e) {
        toast('Error: ' + e.message, 'error');
    }
}

//Init
loadDashboard();