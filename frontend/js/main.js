// ==========================================
// MAIN.JS - Global/Shared Functions
// ==========================================

function startEfficientScheduler(task, delaySeconds = 0) {
    function scheduleNext() {
        const now = new Date();
        // Hitung sisa detik sampai detik target berikutnya
        let secondsUntilTarget = delaySeconds - now.getSeconds();
        if (secondsUntilTarget <= 0) {
            secondsUntilTarget += 60;
        }
        const msUntilTarget = secondsUntilTarget * 1000 - now.getMilliseconds();

        setTimeout(() => {
            const runTime = new Date();
            task(runTime); // Jalankan task tepat di detik yang ditentukan
            scheduleNext(); // Jadwalkan task berikutnya
        }, msUntilTarget);
    }

    scheduleNext();
}

// ==========================================
// REAL-TIME CLOCK
// ==========================================

function updateRealTimeClock() {
    const clockElement = document.getElementById('current-time');
    if (clockElement) {
        const now = new Date();
        
        // Format: YYYY-MM-DD HH:MM:SS
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        
        const timeString = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
        clockElement.textContent = timeString;
    }
}

function startRealTimeClock() {
    // Update clock immediately
    updateRealTimeClock();
    
    // Set interval to update every 1000ms (1 second)
    setInterval(updateRealTimeClock, 1000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    refreshDashboardData();

    // Dashboard stats at second 0 every minute
    startEfficientScheduler(() => {
        if (typeof refreshStats === 'function') refreshStats();
    }, 0);

    // Note: DataTables will auto-refresh based on user interaction
    // loadDashboard() is called from index.html's loadComponents()
    // after all components and sections are loaded
});

// ==========================================
// AUTHENTICATION & LOGOUT
// ==========================================

async function checkAuth() {
    try {
        const response = await fetch('/api/check-auth');
        const data = await response.json();
        if (!data.authenticated) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Auth check error:', error);
    }
}

async function logout() {
    Swal.fire({
        title: 'Logout',
        text: 'Yakin ingin logout dari sistem?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#4f46e5',
        cancelButtonColor: '#9ca3af',
        confirmButtonText: 'Ya, Logout',
        cancelButtonText: 'Batal'
    }).then(async (result) => {
        if (result.isConfirmed) {
            try {
                const response = await fetch('/api/logout', { method: 'POST' });
                if (response.ok) {
                    Swal.fire({
                        title: 'Berhasil',
                        text: 'Anda berhasil logout',
                        icon: 'success',
                        timer: 1500,
                        didClose: () => {
                            window.location.href = '/login';
                        }
                    });
                }
            } catch (error) {
                console.error('Logout error:', error);
                Swal.fire('Error', 'Gagal logout: ' + error.message, 'error');
            }
        }
    });
}

// ==========================================
// SIDEBAR TOGGLE
// ==========================================

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (sidebar) sidebar.classList.toggle('active');
    if (overlay) overlay.classList.toggle('active');
}

// ==========================================
// SECTION NAVIGATION
// ==========================================

function showSection(sectionName) {
    try {
        // Stop auto-refresh for logs if switching away from logs
        if (sectionName !== 'logs' && typeof logAutoRefreshInterval !== 'undefined' && logAutoRefreshInterval) {
            clearInterval(logAutoRefreshInterval);
            logAutoRefreshInterval = null;
        }
        
        // Hide all sections
        const sections = [
            'dashboard-section',
            'config-section'
        ];
        
        sections.forEach(sectionId => {
            const section = document.getElementById(sectionId);
            if (section) {
                section.style.display = 'none';
            }
        });
        
        // Remove active class from all nav items
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Show selected section and mark nav item as active
        const navItems = document.querySelectorAll('.nav-item');
        let activeItem = null;
        
        if (sectionName === 'dashboard') {
            const section = document.getElementById('dashboard-section');
            if (section) section.style.display = 'block';
            activeItem = document.querySelector('[data-section="dashboard"]');
            if (typeof refreshDashboardData === 'function') refreshDashboardData();
            if (typeof refreshVisibleSectionData === 'function') refreshVisibleSectionData();

            
        } else if (sectionName === 'logs') {
            // Redirect to standalone logs page
            window.location.href = '/logs.html';
            return;
        } else if (sectionName === 'config') {
            const section = document.getElementById('config-section');
            if (section) section.style.display = 'block';
            activeItem = document.querySelector('[data-section="config"]');
            if (typeof loadConfiguration === 'function') loadConfiguration();
        }
        
        // Add active class to the selected nav item
        if (activeItem) {
            activeItem.classList.add('active');
        }

        // Close sidebar on mobile after selection
        if (window.innerWidth <= 768) {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebarOverlay');
            if (sidebar) sidebar.classList.remove('active');
            if (overlay) overlay.classList.remove('active');
        }

    } catch (error) {
        console.error('Error in showSection:', error);
    }
}

// ==========================================
// HELPER FUNCTIONS
// ==========================================

function getFieldValue(row, fieldName) {
    const fieldMapping = {
        'datetime': 'date',
        'date': 'date',
        'ph': 'pH',
        'pH': 'pH',
        'orp': 'orp',
        'tds': 'tds',
        'do': 'do',
        'conduct': 'conduct',
        'conductivity': 'conduct',
        'flow': 'flow',
        'cod': 'cod',
        'tss': 'tss',
        'bod': 'bod',
        'nh3n': 'nh3n'
    };
    
    const actualField = fieldMapping[fieldName.toLowerCase()] || fieldName;
    return row[actualField];
}

function formatFieldValue(value, fieldName) {
    if (value === null || value === undefined) return '-';
    
    // Date fields
    if (fieldName.toLowerCase() === 'datetime' || fieldName.toLowerCase() === 'date') {
        try {
            return new Date(value).toLocaleString('id-ID');
        } catch (e) {
            return value;
        }
    }
    
    // Numeric fields
    if (typeof value === 'number' || !isNaN(parseFloat(value))) {
        const numVal = parseFloat(value);
        if (value === 0 || numVal === 0) return '-';
        return numVal.toFixed(2);
    }
    
    return value;
}

function getFieldDisplayName(fieldName) {
    const displayNames = {
        'datetime': 'Tanggal',
        'date': 'Tanggal',
        'ph': 'pH',
        'orp': 'ORP',
        'tds': 'TDS',
        'do': 'DO',
        'conduct': 'Conductivity',
        'flow': 'Flow',
        'cod': 'COD',
        'tss': 'TSS',
        'bod': 'BOD',
        'nh3n': 'NH3-N'
    };
    return displayNames[fieldName.toLowerCase()] || fieldName.toUpperCase();
}

function formatDateCustom(dateValue) {
    if (!dateValue) return '-';
    try {
        const date = new Date(dateValue);
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const hours = date.getHours().toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const year = date.getFullYear();
        return `${day}-${month}-${year} ${hours}:${minutes}`;
    } catch (e) {
        return dateValue;
    }
}

// ==========================================
// SWAL ALERT HELPER
// ==========================================

function showConfigAlert(message, type) {
    const iconMap = {
        'success': 'success',
        'danger': 'error',
        'info': 'info'
    };
    
    Swal.fire({
        title: type === 'success' ? 'Berhasil' : type === 'danger' ? 'Error' : 'Informasi',
        html: message,
        icon: iconMap[type] || 'info',
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer)
            toast.addEventListener('mouseleave', Swal.resumeTimer)
        }
    });
}
