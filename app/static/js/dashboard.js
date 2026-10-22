/**
 * CloudResource Scheduler - Client-side Controller
 * Dynamic data synchronization, real-time metrics, and sidebar routing
 */

let currentResources = [];
let currentSchedules = [];
let autoRefreshTimer = null;

document.addEventListener('DOMContentLoaded', () => {
  fetchAllData();
  // Auto-refresh smoothly every 20 seconds in the background
  autoRefreshTimer = setInterval(() => fetchAllData(false), 20000);
});

async function fetchAllData(showLoading = true) {
  try {
    // Prioritize immediate UI metrics and resources first
    await Promise.all([
      loadStats(),
      loadResources(showLoading)
    ]);
    // Non-blocking background sync for auxiliary tables
    Promise.all([
      loadSchedules(),
      loadAlerts(),
      loadAuditLogs()
    ]).catch(() => {});
  } catch (err) {
    console.error('Error fetching dashboard telemetry:', err);
  }
}

// ==============================================================================
// Sidebar View Routing
// ==============================================================================
const VIEW_METADATA = {
  'dashboard-view': {
    title: 'Dashboard',
    desc: 'A clear view of your cloud resources and operations.'
  },
  'resources-view': {
    title: 'Cloud Resources',
    desc: 'Real-time telemetry and state management for EC2 compute instances.'
  },
  'schedules-view': {
    title: 'Operating Schedules',
    desc: 'Permitted execution windows and runtime thresholds per instance.'
  },
  'alerts-view': {
    title: 'Multi-Channel Alerts',
    desc: 'Outbound dispatch logs for SMS, WhatsApp, and SMTP Email.'
  },
  'audit-view': {
    title: 'Audit Ledger',
    desc: 'Tamper-evident record of user commands and automated shutdowns.'
  },
  'settings-view': {
    title: 'Settings & FinOps',
    desc: 'Cloud provider configuration and cost optimization metrics.'
  }
};

function switchSidebarView(viewId) {
  // Update sidebar active buttons
  document.querySelectorAll('.nav-item-btn').forEach(btn => btn.classList.remove('active'));
  const activeBtn = document.querySelector(`.nav-item-btn[onclick*="${viewId}"]`);
  if (activeBtn) activeBtn.classList.add('active');

  // Toggle visible section
  document.querySelectorAll('.tab-page-view').forEach(view => view.classList.remove('active'));
  const targetView = document.getElementById(viewId);
  if (targetView) targetView.classList.add('active');

  // Update Top Bar Header
  const meta = VIEW_METADATA[viewId] || { title: 'Dashboard', desc: '' };
  const titleEl = document.getElementById('topbar-page-title');
  const descEl = document.getElementById('topbar-page-desc');
  if (titleEl) titleEl.innerText = meta.title;
  if (descEl) descEl.innerText = meta.desc;
}

// ==============================================================================
// 1. Stats & KPI Metrics (5 Metric Cards)
// ==============================================================================
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    if (!data.success) return;

    const m = data.metrics;
    // 5 Metric Cards in Row (safe null checks)
    const elTotal = document.getElementById('dash-total-resources');
    const elRunning = document.getElementById('dash-running-resources');
    const elStopped = document.getElementById('dash-stopped-resources');
    const elSched = document.getElementById('dash-scheduled-actions');
    const elAlerts = document.getElementById('dash-failed-alerts');

    if (elTotal) elTotal.innerText = m.total_resources;
    if (elRunning) elRunning.innerText = m.running_resources;
    if (elStopped) elStopped.innerText = m.stopped_resources;
    if (elSched) elSched.innerText = m.active_schedules;
    if (elAlerts) elAlerts.innerText = m.auto_shutdowns || 0;

    // Dashboard view FinOps savings cards
    const dashSavingsUsd = document.getElementById('dash-savings-usd');
    if (dashSavingsUsd) dashSavingsUsd.innerText = `$${(m.estimated_savings_usd || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;

    const dashSavingsInr = document.getElementById('dash-savings-inr');
    if (dashSavingsInr) dashSavingsInr.innerText = `₹${(m.estimated_savings_inr || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} saved`;

    const finopsAvoided = document.getElementById('finops-avoided-hours');
    if (finopsAvoided) finopsAvoided.innerText = `${(m.estimated_avoided_hours || 0).toFixed(1)} hrs`;

    const finopsBurn = document.getElementById('finops-burn-rate');
    if (finopsBurn) finopsBurn.innerText = `$${(m.current_burn_rate_usd || 0).toFixed(3)} / hr`;

    const finopsTotal = document.getElementById('finops-total-savings');
    if (finopsTotal) finopsTotal.innerText = `$${(m.estimated_savings_usd || 0).toFixed(2)} (₹${(m.estimated_savings_inr || 0).toFixed(2)})`;

    // Settings view FinOps savings
    const finopsEl = document.getElementById('settings-finops-savings');
    if (finopsEl) {
      finopsEl.innerText = `$${m.estimated_savings_usd.toLocaleString()} (₹${m.estimated_savings_inr.toLocaleString()})`;
    }
  } catch (err) {
    console.error('Error fetching statistics:', err);
  }
}

// ==============================================================================
// 2. Cloud Resources (Overview & Full Inventory)
// ==============================================================================
async function loadResources(showLoading = true) {
  const overviewTbody = document.getElementById('dash-overview-tbody');
  const fullTbody = document.getElementById('full-resources-tbody');
  const emptyBox = document.getElementById('resource-overview-empty');
  const tableWrap = document.getElementById('resource-overview-table-wrap');
  const alertSelect = document.getElementById('alert-target-select');

  try {
    const res = await fetch('/api/resources');
    const data = await res.json();
    if (!data.success) throw new Error(data.error);

    currentResources = data.resources || [];

    // If custom overview renderer is present on page (e.g. dashboard.html with 6 cols, filter search & provider badges)
    if (typeof renderDashboardOverviewTable === 'function') {
      renderDashboardOverviewTable();
    } else {
      // If 0 resources found -> show clean empty state
      if (currentResources.length === 0) {
        if (emptyBox) emptyBox.style.display = 'flex';
        if (tableWrap) tableWrap.style.display = 'none';
        if (fullTbody) fullTbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No cloud resources found. Click "Discover Resources" to scan.</td></tr>`;
        return;
      }

      if (emptyBox) emptyBox.style.display = 'none';
      if (tableWrap) tableWrap.style.display = 'block';

      // Populate Overview Preview Table (Dashboard View)
      if (overviewTbody) {
        overviewTbody.innerHTML = currentResources.slice(0, 5).map(r => {
          const isRunning = r.state === 'running';
          const isTerminated = r.state === 'terminated';
          let stateBadge = '';
          if (isRunning) {
            stateBadge = `<span class="badge-state-pill badge-state-running"><span class="dot-green"></span> Running</span>`;
          } else if (isTerminated) {
            stateBadge = `<span class="badge-state-pill" style="background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5;"><span style="width:6px; height:6px; border-radius:50%; background:#ef4444; display:inline-block; margin-right:4px;"></span> Terminated</span>`;
          } else {
            stateBadge = `<span class="badge-state-pill badge-state-stopped"><span class="dot-gray"></span> Stopped</span>`;
          }

          let actionButtons = '';
          if (isRunning) {
            actionButtons = `<button class="btn-table-action btn-tbl-stop" onclick="stopInstance(${r.id})">Stop</button>
                             <button class="btn-table-action btn-tbl-extend" onclick="extendInstance(${r.id}, 60)">+60m</button>`;
          } else if (isTerminated) {
            actionButtons = `<span style="font-size: 11px; color: #9ca3af; font-style: italic;">Terminated in AWS</span>`;
          } else {
            actionButtons = `<button class="btn-table-action btn-tbl-start" onclick="startInstance(${r.id})">Start</button>`;
          }

          return `
            <tr>
              <td>
                <div class="instance-title-text">${escapeHtml(r.instance_name)}</div>
                <div class="instance-id-sub">${r.instance_id}</div>
              </td>
              <td>
                <div>${r.region}</div>
                <div style="font-size: 11px; color: #6b7280;">${r.instance_type}</div>
              </td>
              <td>${stateBadge}</td>
              <td>
                <span style="font-family: var(--font-mono); font-size: 12px;">${isRunning ? r.uptime_hours + ' hrs' : '0.0 hrs'}</span>
              </td>
              <td>
                <div style="display: flex; gap: 6px; align-items: center;">
                  ${actionButtons}
                </div>
              </td>
            </tr>
          `;
        }).join('');
      }
    }

    // Populate Full Inventory Table (Resources View)
    renderFullResourcesTable(currentResources);

    // Update simulation select dropdown
    if (alertSelect) {
      alertSelect.innerHTML = '';
      currentResources.forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.id;
        opt.innerText = `${r.instance_name} (${r.instance_id}) - [${r.state.toUpperCase()}]`;
        alertSelect.appendChild(opt);
      });
    }

  } catch (err) {
    if (overviewTbody) {
      overviewTbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">Error loading inventory: ${err.message}</td></tr>`;
    }
  }
}

function renderFullResourcesTable(resources) {
  const tbody = document.getElementById('full-resources-tbody');
  if (!tbody) return;

  if (resources.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">No cloud resources match your filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = resources.map(r => {
    const isRunning = r.state === 'running';
    const isTerminated = r.state === 'terminated';
    let stateBadge = '';
    if (isRunning) {
      stateBadge = `<span class="badge-state-pill badge-state-running"><span class="dot-green"></span> Running</span>`;
    } else if (isTerminated) {
      stateBadge = `<span class="badge-state-pill" style="background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5;"><span style="width:6px; height:6px; border-radius:50%; background:#ef4444; display:inline-block; margin-right:4px;"></span> Terminated</span>`;
    } else {
      stateBadge = `<span class="badge-state-pill badge-state-stopped"><span class="dot-gray"></span> Stopped</span>`;
    }

    const schedInfo = r.schedule
      ? `<span style="font-family: var(--font-mono); font-size: 11px;">${r.schedule.start_time}-${r.schedule.end_time}</span>`
      : `<span style="color: #9ca3af;">None</span>`;

    const leaseInfo = r.is_lease_active
      ? `<span style="color: #059669; font-family: var(--font-mono); font-size: 11px;">Active (${formatDate(r.lease_expires_at)})</span>`
      : `<span style="color: #9ca3af;">None</span>`;

    let actionButtons = '';
    if (isRunning) {
      actionButtons = `
        <button class="btn-table-action btn-tbl-stop" onclick="stopInstance(${r.id})">Stop</button>
        <button class="btn-table-action btn-tbl-extend" onclick="extendInstance(${r.id}, 60)">+60m</button>
        <button class="btn-table-action btn-tbl-alert" onclick="triggerAlert(${r.id})" title="Trigger Breach Alert">Alert</button>
      `;
    } else if (isTerminated) {
      actionButtons = `<span style="font-size: 11px; color: #9ca3af; font-style: italic;">Terminated in AWS</span>`;
    } else {
      actionButtons = `
        <button class="btn-table-action btn-tbl-start" onclick="startInstance(${r.id})">Start</button>
      `;
    }

    return `
      <tr>
        <td>
          <div class="instance-title-text">${escapeHtml(r.instance_name)}</div>
          <div class="instance-id-sub">${r.instance_id}</div>
        </td>
        <td>
          <div>${r.region}</div>
          <div style="font-size: 11px; color: #6b7280;">${r.instance_type}</div>
        </td>
        <td>${stateBadge}</td>
        <td>
          <div style="font-family: var(--font-mono); font-size: 11px;">Pub: ${r.public_ip || 'None'}</div>
          <div style="font-family: var(--font-mono); font-size: 11px; color: #6b7280;">Priv: ${r.private_ip || 'None'}</div>
        </td>
        <td>
          <span style="font-family: var(--font-mono); font-size: 12px;">${isRunning ? r.uptime_hours + ' hrs' : '0.0 hrs'}</span>
        </td>
        <td>${schedInfo}</td>
        <td>${leaseInfo}</td>
        <td>
          <div style="display: flex; gap: 6px; align-items: center;">
            ${actionButtons}
            <button class="btn-cancel-modal" style="padding: 4px 8px; font-size: 11px;" onclick="openScheduleModal(${r.id})">Policy</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function filterFullResources() {
  const query = (document.getElementById('full-resource-search')?.value || '').toLowerCase().trim();
  if (!query) {
    renderFullResourcesTable(currentResources);
    return;
  }
  const filtered = currentResources.filter(r => 
    r.instance_name.toLowerCase().includes(query) ||
    r.instance_id.toLowerCase().includes(query) ||
    r.region.toLowerCase().includes(query) ||
    r.state.toLowerCase().includes(query)
  );
  renderFullResourcesTable(filtered);
}

// ==============================================================================
// 3. Operational Actions (Start, Stop, Extend, Sync, Audit)
// ==============================================================================
async function startInstance(resourceId) {
  try {
    showToast('Starting EC2 instance...', 'info');
    const res = await fetch(`/api/resources/${resourceId}/start`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      fetchAllData(false);
    } else {
      showToast(`Error: ${data.error}`, 'error');
    }
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

async function stopInstance(resourceId) {
  try {
    showToast('Stopping EC2 instance...', 'info');
    const res = await fetch(`/api/resources/${resourceId}/stop`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      fetchAllData(false);
    } else {
      showToast(`Error: ${data.error}`, 'error');
    }
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

async function stopAllRunningInstances() {
  if (!confirm('Are you sure you want to shut down all running cloud instances? This will terminate compute cost burn immediately.')) return;
  try {
    showToast('Shutting down all running instances...', 'info');
    const res = await fetch('/api/resources/stop-all', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      if (typeof showDashboardBanner === 'function') {
        showDashboardBanner(data.message, 'success');
      }
      fetchAllData(false);
    } else {
      showToast(`Error: ${data.error}`, 'error');
    }
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

async function extendInstance(resourceId, minutes = 60) {
  try {
    showToast(`Extending operational lease by ${minutes} minutes...`, 'info');
    const res = await fetch(`/api/resources/${resourceId}/extend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ minutes })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      fetchAllData(false);
    } else {
      showToast(`Error: ${data.error}`, 'error');
    }
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

async function triggerAlert(resourceId) {
  try {
    showToast('Dispatching alert across phone (ntfy), SMS, WhatsApp, and Email...', 'info');
    const res = await fetch(`/api/resources/${resourceId}/trigger-alert`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      displaySimLinks(data.stop_url, data.extend_url, data.whatsapp_link);
      fetchAllData(false);
    } else {
      showToast(`Alert Failed: ${data.error}`, 'error');
    }
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

function simulateAlertFromDropdown() {
  const sel = document.getElementById('alert-target-select');
  if (!sel || !sel.value) {
    showToast('Select a target instance first.', 'error');
    return;
  }
  triggerAlert(sel.value);
}

function displaySimLinks(stopUrl, extendUrl, whatsappUrl) {
  const box = document.getElementById('sim-active-links-box');
  if (!box) return;
  const waHtml = whatsappUrl ? `
    <div style="margin-bottom: 8px;">
      <a href="${whatsappUrl}" target="_blank" style="display:inline-block; padding: 6px 12px; background-color: #25d366; color:white; border-radius: 6px; font-weight: 700; text-decoration: none; font-size: 11.5px; box-shadow: 0 2px 4px rgba(37,211,102,0.3);">💬 Open Alert in WhatsApp →</a>
    </div>
  ` : '';
  box.innerHTML = `
    <div style="background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; margin-top: 10px;">
      <div style="font-weight: 600; color: #0f584c; margin-bottom: 6px;">Single-Click Actions &amp; Webhook Links (TTL: 15 mins):</div>
      ${waHtml}
      <div style="margin-bottom: 6px;">
        <a href="${stopUrl}" target="_blank" style="display:inline-block; padding: 4px 10px; background-color: #ef4444; color:white; border-radius: 4px; font-weight: 600; text-decoration: none; font-size: 11px;">🛑 Test STOP Webhook</a>
        <span style="font-family: var(--font-mono); font-size: 10px; color: #6b7280; display: block; word-break: break-all; margin-top: 2px;">${stopUrl}</span>
      </div>
      <div>
        <a href="${extendUrl}" target="_blank" style="display:inline-block; padding: 4px 10px; background-color: #0ea5e9; color:white; border-radius: 4px; font-weight: 600; text-decoration: none; font-size: 11px;">⏳ Test EXTEND LEASE (+60m)</a>
        <span style="font-family: var(--font-mono); font-size: 10px; color: #6b7280; display: block; word-break: break-all; margin-top: 2px;">${extendUrl}</span>
      </div>
    </div>
  `;
}

async function syncCloudResources() {
  showToast('Discovering cloud instances in AWS region...', 'info');
  try {
    const res = await fetch('/api/resources/scan', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      fetchAllData(false);
    } else {
      showToast(`Scan Error: ${data.error}`, 'error');
    }
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

async function clearDiscoveredInventory() {
  if (!confirm('Are you sure you want to purge all discovered cloud resources from the database? This will reset the dashboard to a clean empty state.')) return;
  showToast('Purging discovered cloud inventory...', 'info');
  try {
    const res = await fetch('/api/resources/clear', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      fetchAllData(false);
    } else {
      showToast(`Error: ${data.error}`, 'error');
    }
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

async function triggerPolicyAudit() {
  showToast('Running periodic compliance audit cycle...', 'info');
  try {
    const res = await fetch('/api/audit/trigger', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      const r = data.results;
      showToast(`Audit Completed: ${r.violations_detected} breaches, ${r.alerts_dispatched} alerts, ${r.shutdowns_executed} auto-shutdowns.`, 'success');
      fetchAllData(false);
    } else {
      showToast(`Audit Error: ${data.error}`, 'error');
    }
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

// ==============================================================================
// 4. Schedules Management
// ==============================================================================
async function loadSchedules() {
  const container = document.getElementById('full-schedules-container');
  if (!container) return;

  try {
    const res = await fetch('/api/schedules');
    const data = await res.json();
    if (!data.success) return;

    currentSchedules = data.schedules || [];
    if (currentSchedules.length === 0) {
      container.innerHTML = `<div class="text-muted py-4">No schedules configured yet.</div>`;
      return;
    }

    container.innerHTML = currentSchedules.map(s => {
      const resObj = currentResources.find(r => r.id === s.resource_id);
      const instName = resObj ? resObj.instance_name : `Resource #${s.resource_id}`;
      const instId = resObj ? resObj.instance_id : '';

      return `
        <div style="background-color: #f8faf9; border: 1px solid var(--border-light); border-radius: 10px; padding: 18px;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
            <div>
              <div style="font-weight: 700; color: #111827; font-size: 14px;">${escapeHtml(instName)}</div>
              <div style="font-family: var(--font-mono); font-size: 11px; color: #059669;">${instId}</div>
            </div>
            <button class="btn-cancel-modal" style="padding: 4px 8px; font-size: 11px;" onclick="openScheduleModal(${s.resource_id})">Edit Policy</button>
          </div>
          <div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid var(--border-subtle); font-size: 12px;">
            <span style="color: #6b7280;">Operating Hours:</span>
            <span style="font-family: var(--font-mono); font-weight: 600;">${s.start_time} - ${s.end_time} UTC</span>
          </div>
          <div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid var(--border-subtle); font-size: 12px;">
            <span style="color: #6b7280;">Max Continuous Cap:</span>
            <span style="font-family: var(--font-mono); font-weight: 600;">${s.max_runtime_hours} Hours</span>
          </div>
          <div style="display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid var(--border-subtle); font-size: 12px;">
            <span style="color: #6b7280;">Permitted Days:</span>
            <span>${s.days_of_week}</span>
          </div>
          <div style="display: flex; justify-content: space-between; padding: 5px 0; font-size: 12px;">
            <span style="color: #6b7280;">Policy State:</span>
            <span>${s.is_active ? '<span style="color:#059669; font-weight:600;">Active</span>' : '<span style="color:#9ca3af;">Paused</span>'}</span>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error('Error loading schedules:', err);
  }
}

function openScheduleModalForFirstResource() {
  if (currentResources.length > 0) {
    openScheduleModal(currentResources[0].id);
  } else {
    showToast('Scan cloud resources first to configure schedules.', 'info');
    syncCloudResources();
  }
}

function openScheduleModal(resourceId) {
  const resObj = currentResources.find(r => r.id === resourceId);
  const schedObj = currentSchedules.find(s => s.resource_id === resourceId);

  document.getElementById('modal-resource-id').value = resourceId;
  document.getElementById('modal-instance-name').value = resObj ? `${resObj.instance_name} (${resObj.instance_id})` : `Resource #${resourceId}`;

  if (schedObj) {
    document.getElementById('modal-start-time').value = schedObj.start_time || '09:00';
    document.getElementById('modal-end-time').value = schedObj.end_time || '19:00';
    document.getElementById('modal-max-hours').value = schedObj.max_runtime_hours || 8.0;
    document.getElementById('modal-days').value = schedObj.days_of_week || 'MON,TUE,WED,THU,FRI';
    document.getElementById('modal-is-active').checked = schedObj.is_active;
  } else {
    document.getElementById('modal-start-time').value = '09:00';
    document.getElementById('modal-end-time').value = '19:00';
    document.getElementById('modal-max-hours').value = 8.0;
    document.getElementById('modal-days').value = 'MON,TUE,WED,THU,FRI';
    document.getElementById('modal-is-active').checked = true;
  }

  document.getElementById('schedule-modal').classList.add('show');
}

function closeScheduleModal() {
  document.getElementById('schedule-modal').classList.remove('show');
}

async function submitScheduleForm(e) {
  e.preventDefault();
  const resourceId = parseInt(document.getElementById('modal-resource-id').value);
  const payload = {
    resource_id: resourceId,
    start_time: document.getElementById('modal-start-time').value,
    end_time: document.getElementById('modal-end-time').value,
    max_runtime_hours: parseFloat(document.getElementById('modal-max-hours').value),
    days_of_week: document.getElementById('modal-days').value,
    is_active: document.getElementById('modal-is-active').checked
  };

  try {
    const res = await fetch('/api/schedules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      showToast('Operating schedule saved successfully!', 'success');
      closeScheduleModal();
      fetchAllData(false);
    } else {
      showToast(`Error: ${data.error}`, 'error');
    }
  } catch (err) {
    showToast(`Failed: ${err.message}`, 'error');
  }
}

// ==============================================================================
// 5. Alert & Audit Logs
// ==============================================================================
async function loadAlerts() {
  const tbody = document.getElementById('full-alerts-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/alerts?limit=25');
    const data = await res.json();
    if (!data.success) return;

    const alerts = data.alerts || [];
    if (alerts.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center py-4 text-muted">No outbound alerts dispatched yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = alerts.map(a => `
      <tr>
        <td style="font-family: var(--font-mono); font-size: 11px;">${formatDate(a.sent_at)}</td>
        <td>
          <div style="font-weight: 600;">${escapeHtml(a.instance_name || 'N/A')}</div>
          <div style="font-family: var(--font-mono); font-size: 11px; color: #059669;">${a.instance_id || ''}</div>
        </td>
        <td><span style="font-weight:600; color: #0f584c;">${a.channel}</span></td>
        <td style="font-family: var(--font-mono); font-size: 11px;">${escapeHtml(a.recipient)}</td>
        <td>
          <span class="badge-state-pill ${a.status === 'SENT' ? 'badge-state-running' : 'badge-state-stopped'}">
            ${a.status}
          </span>
        </td>
        <td style="font-size: 12px; color: #4b5563;">${escapeHtml(a.details || '')}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Error loading alerts:', err);
  }
}

async function loadAuditLogs() {
  const tbody = document.getElementById('full-audit-tbody');
  const dashAuditList = document.getElementById('dash-recent-audits-list');

  try {
    const res = await fetch('/api/audit-logs?limit=30');
    const data = await res.json();
    if (!data.success) return;

    const logs = data.audit_logs || [];

    // Populate Dashboard Recent Audits Feed if present
    if (dashAuditList) {
      if (logs.length === 0) {
        dashAuditList.innerHTML = '<div style="font-size: 12px; color: #9ca3af; text-align: center; padding: 12px 0;">No recent audit events recorded.</div>';
      } else {
        dashAuditList.innerHTML = logs.slice(0, 5).map(l => {
          const act = (l.action_taken || '').toUpperCase();
          const isStop = act.includes('STOP') || act.includes('SHUTDOWN');
          const isAlert = act.includes('ALERT');
          const isGrace = act.includes('GRACE') || act.includes('EXTEND');

          let cardBg, cardBorder, accentBorder, badgeBg, badgeColor;
          if (isStop) {
            cardBg = 'linear-gradient(135deg, #fff5f5 0%, #ffffff 100%)';
            cardBorder = '#fecaca';
            accentBorder = '#ef4444';
            badgeBg = '#fee2e2';
            badgeColor = '#b91c1c';
          } else if (isAlert) {
            cardBg = 'linear-gradient(135deg, #fffdf0 0%, #ffffff 100%)';
            cardBorder = '#fde68a';
            accentBorder = '#f59e0b';
            badgeBg = '#fef3c7';
            badgeColor = '#b45309';
          } else if (isGrace) {
            cardBg = 'linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%)';
            cardBorder = '#bae6fd';
            accentBorder = '#0284c7';
            badgeBg = '#e0f2fe';
            badgeColor = '#0369a1';
          } else {
            cardBg = 'linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%)';
            cardBorder = '#bbf7d0';
            accentBorder = '#10b981';
            badgeBg = '#ecfdf5';
            badgeColor = '#047857';
          }

          return `
            <div style="background:${cardBg}; border:1.5px solid ${cardBorder}; border-left:4px solid ${accentBorder}; border-radius:8px; padding:10px 12px; font-size:11.5px; transition:all 0.2s cubic-bezier(0.16, 1, 0.3, 1); box-shadow:0 1px 3px rgba(0,0,0,0.03);" onmouseenter="this.style.transform='translateX(4px)'; this.style.boxShadow='0 4px 12px rgba(0,0,0,0.07)';" onmouseleave="this.style.transform='none'; this.style.boxShadow='0 1px 3px rgba(0,0,0,0.03)';">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                <span style="padding:2px 7px; border-radius:4px; font-weight:800; font-size:10px; background:${badgeBg}; color:${badgeColor}; letter-spacing:0.04em;">${escapeHtml(l.action_taken)}</span>
                <span style="color:#64748b; font-family:var(--font-mono); font-size:10.5px;">${formatDate(l.timestamp)}</span>
              </div>
              <div style="color:#334155; font-size:11.5px; line-height:1.45; font-weight:500;">${escapeHtml(l.details || '')}</div>
            </div>
          `;
        }).join('');
      }
    }

    if (!tbody) return;

    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center py-4 text-muted">Audit ledger is empty.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => `
      <tr>
        <td style="font-family: var(--font-mono); font-size: 11px;">${formatDate(l.timestamp)}</td>
        <td><span style="font-family: var(--font-mono); font-size: 11px; color: #059669;">${escapeHtml(l.triggered_by)}</span></td>
        <td>
          <span style="padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 700; ${l.action_taken.includes('STOP') || l.action_taken.includes('SHUTDOWN') ? 'background-color:#fee2e2; color:#b91c1c;' : 'background-color:#e0f2fe; color:#0369a1;'}">
            ${l.action_taken}
          </span>
        </td>
        <td>
          <div style="font-weight: 500;">${escapeHtml(l.instance_name || 'N/A')}</div>
          <div style="font-family: var(--font-mono); font-size: 10px; color: #6b7280;">${l.instance_id || ''}</div>
        </td>
        <td style="font-size: 12px; color: #4b5563;">${escapeHtml(l.details || '')}</td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Error loading audit logs:', err);
  }
}

// ==============================================================================
// Utilities (Toast, Date, Escaping)
// ==============================================================================
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function formatDate(isoStr) {
  if (!isoStr) return 'N/A';
  try {
    const d = new Date(isoStr);
    return d.toISOString().replace('T', ' ').substring(0, 19);
  } catch (e) {
    return isoStr;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
