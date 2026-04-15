// ==========================================
// DASHBOARD.JS - Dashboard Functions
// ==========================================

// Store parameter fields for table loading
let parameterFields = [];

// Refresh dashboard data
async function refreshDashboardData() {
  if (typeof refreshStats === "function") await refreshStats();
  if (typeof loadAllData === "function") await loadAllData();
}

// Load dashboard data
async function loadDashboard() {
  // Load stats and data (Fire and forget based on original logic)
  refreshStats();
  loadAllData();
}

// Helper: Generate Badge HTML
const getStatusBadge = (status) => {
  return status === 1 
    ? '<span class="badge badge-success">Sent</span>' 
    : '<span class="badge badge-pending">Pending</span>';
};

// Load all data with dynamic headers
async function loadAllData() {
  try {
    const response = await fetch('/api/data/all');
    const data = await response.json();

    if (!data.success) {
      return Swal.fire('Error', data.error || 'Gagal memfilter data', 'error');
    }

    // Process parameters
    const dashParams = (data.params || 'datetime,pH,cod,tss,nh3n,flow')
      .split(',')
      .map(f => f.trim())
      .filter(f => f && f.toLowerCase() !== 'datetime');

    // Build Table Headers
    const headerHtml = [
      '<th>No</th>',
      '<th>Tanggal</th>',
      ...dashParams.map(field => `<th>${getFieldDisplayName(field)}</th>`),
      '<th>DLH</th>',
      '<th>HAS</th>',
      '<th>Sent At</th>',
      '<th>Keterangan</th>'
    ].join('');

    // Build Table Body
    let bodyHtml = '';

    if (data.data.length === 0) {
      const colSpan = dashParams.length + 4;
      bodyHtml = `<tr><td colspan="${colSpan}" class="text-center text-muted">Tidak ada data pada rentang tanggal ini</td></tr>`;
    } else {
      bodyHtml = data.data.map((row, idx) => {
        const datetimeValue = getFieldValue(row, 'datetime') || getFieldValue(row, 'date');
        const tanggal = formatDateCustom(datetimeValue);

        // Generate dynamic columns
        const paramsHtml = dashParams.map(field => {
          const value = getFieldValue(row, field);
          return `<td>${formatFieldValue(value, field)}</td>`;
        }).join('');

        // Generate status columns
        const dlhBadge = getStatusBadge(row.dlh);
        const hasBadge = getStatusBadge(row.has);
        
        const sentAt = row.dlh_sent_at 
          ? formatDateCustom(new Date(row.dlh_sent_at)) 
          : '-';

        return `
          <tr>
            <td>${idx + 1}</td>
            <td>${tanggal}</td>
            ${paramsHtml}
            <td>${dlhBadge}</td>
            <td>${hasBadge}</td>
            <td>${sentAt}</td>
            <td>${row.dlh_response || '-'}</td>

          </tr>
        `;
      }).join('');
    }

    // Update DOM
    const table = document.getElementById('all-data-table');
    if (!table) {
      console.warn('⚠️  Table element "all-data-table" not found in DOM');
      return;
    }

    table.innerHTML = `
      <thead>
        <tr>${headerHtml}</tr>
      </thead>
      <tbody id="all-data-body">${bodyHtml}</tbody>
    `;

    Swal.fire({
      title: 'Berhasil',
      text: `Data berhasil difilter. Total: ${data.data.length} records`,
      icon: 'success',
      timer: 2000
    });

  } catch (error) {
    console.error('Filter error:', error);
    Swal.fire('Error', 'Gagal memfilter data: ' + error.message, 'error');
  }
}

// Refresh statistics
async function refreshStats() {
  try {
    const response = await fetch("/api/data/stats");
    const data = await response.json();

    if (!data.success) return;

    const { stats } = data;
    
    // DOM Elements
    const elements = {
      total: document.getElementById("stat-total"),
      pending: document.getElementById("stat-pending"),
      sent: document.getElementById("stat-sent"),
      dlh: document.getElementById("stat-dlh"),
      lastSync: document.getElementById("last-sync")
    };

    // Update Text Content
    if (elements.total) elements.total.textContent = stats.total_data.toLocaleString();
    if (elements.pending) elements.pending.textContent = stats.pending_data.toLocaleString();
    if (elements.sent) elements.sent.textContent = stats.sent_dlh.toLocaleString();
    if (elements.dlh) elements.dlh.textContent = stats.sent_has.toLocaleString();

    // Update Last Sync
    if (elements.lastSync) {
      const now = stats.dlh_sent_at ? new Date(stats.dlh_sent_at) : null;
      elements.lastSync.textContent = now ? formatDateCustom(now) : 'Belum pernah sinkron';
    }
  } catch (error) {
    console.error("Error loading stats:", error);
  }
}

// ==========================================
// MANUAL SEND FUNCTION
// ==========================================

async function sendPendingData() {
  const confirmResult = await Swal.fire({
    title: 'Konfirmasi Pengiriman Manual',
    text: 'Apakah Anda yakin ingin mengirim data sekarang ke API?',
    icon: 'question',
    showCancelButton: true,
    confirmButtonColor: '#28a745',
    cancelButtonColor: '#dc3545',
    confirmButtonText: 'Ya, Kirim',
    cancelButtonText: 'Batal'
  });

  if (!confirmResult.isConfirmed) return;

  // Show loading
  Swal.fire({
    title: 'Mengirim Data',
    text: 'Mohon tunggu...',
    icon: 'info',
    allowOutsideClick: false,
    allowEscapeKey: false,
    didOpen: () => Swal.showLoading()
  });

  try {
    const response = await fetch('/api/send/manual', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });

    const result = await response.json();

    if (result.results) {
      const { results } = result;
      const messages = [];

      // Format DLH Message
      if (results.dlh_sent) {
        messages.push(`✅ DLH: ${results.dlh_message}`);
      } else if (results.dlh_message) {
        messages.push(`ℹ️ DLH: ${results.dlh_message}`);
      }

      // Format HAS Message
      if (results.has_sent) {
        messages.push(`✅ HAS: ${results.has_message}`);
      } else if (results.has_message) {
        messages.push(`ℹ️ HAS: ${results.has_message}`);
      }

      const hasAnyData = results.dlh_sent || results.has_sent;
      const alertType = hasAnyData ? 'success' : 'info';
      const alertTitle = hasAnyData ? 'Data Terkirim' : 'Informasi';

      await Swal.fire(
        alertTitle,
        messages.join('\n\n') || 'Permintaan selesai diproses',
        alertType
      );

      // Refresh after sending
      refreshStats();
      loadAllData();

    } else {
      Swal.fire('Gagal', result.error || 'Gagal mengirim data', 'error');
    }

  } catch (error) {
    console.error('Send error:', error);
    Swal.fire('Error', 'Terjadi kesalahan: ' + error.message, 'error');
  }
}