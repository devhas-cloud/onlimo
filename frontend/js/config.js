// ==========================================
// CONFIG.JS - Configuration Functions
// ==========================================

async function loadConfiguration() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        
        // General
        if (document.getElementById('config-parameter')) {
            document.getElementById('config-parameter').value = config.parameter || '';
        }
       
        if (document.getElementById('config-device-id')) {
            document.getElementById('config-device-id').value = config.device_id || '';
        }
        
       
        // DLH
        if (document.getElementById('config-dlh-status')) {
            document.getElementById('config-dlh-status').value = config.dlh_status || 'inactive';
        }
        if (document.getElementById('config-dlh-api-url')) {
            document.getElementById('config-dlh-api-url').value = config.dlh_api_url || '';
        }
        if (document.getElementById('config-dlh-api-key')) {
            document.getElementById('config-dlh-api-key').value = config.dlh_api_key || '';
        }
        if (document.getElementById('config-dlh-api-secret')) {
            document.getElementById('config-dlh-api-secret').value = config.dlh_api_secret || '';
        }
        if (document.getElementById('config-dlh-uid')) {
            document.getElementById('config-dlh-uid').value = config.dlh_uid || '';
        }
       
        
        // HAS
        if (document.getElementById('config-has-status')) {
            document.getElementById('config-has-status').value = config.has_status || 'inactive';
        }
        if (document.getElementById('config-has-api-url')) {
            document.getElementById('config-has-api-url').value = config.has_api_url || '';
        }
        if (document.getElementById('config-has-token-api')) {
            document.getElementById('config-has-token-api').value = config.has_token_api || '';
        }
        if (document.getElementById('config-has-fields')) {
            document.getElementById('config-has-fields').value = config.has_fields || '';
        }
        if (document.getElementById('config-has-logs-api-url')) {
            document.getElementById('config-has-logs-api-url').value = config.has_logs_api_url || '';
        }
        
        showConfigAlert('✅ Konfigurasi berhasil dimuat', 'success');
    } catch (error) {
        console.error('Error loading configuration:', error);
        showConfigAlert('❌ Gagal memuat konfigurasi', 'danger');
    }
}

async function saveConfiguration() {
    Swal.fire({
        title: 'Konfirmasi Penyimpanan',
        text: 'Apakah Anda yakin ingin menyimpan konfigurasi ini?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#4f46e5',
        cancelButtonColor: '#9ca3af',
        confirmButtonText: 'Ya, Simpan',
        cancelButtonText: 'Batal'
    }).then(async (result) => {
        if (!result.isConfirmed) return;
        
        try {
            const configData = {
                // General
                device_id: document.getElementById('config-device-id')?.value || '',
                parameter: document.getElementById('config-parameter')?.value || '',
                
                // DLH API
                dlh_status: document.getElementById('config-dlh-status')?.value || 'inactive',
                dlh_api_url: document.getElementById('config-dlh-api-url')?.value || '',
                dlh_api_key: document.getElementById('config-dlh-api-key')?.value || '',
                dlh_api_secret: document.getElementById('config-dlh-api-secret')?.value || '',
                dlh_uid: document.getElementById('config-dlh-uid')?.value || '',
                
                // HAS API
                has_status: document.getElementById('config-has-status')?.value || 'inactive',
                has_api_url: document.getElementById('config-has-api-url')?.value || '',
                has_token_api: document.getElementById('config-has-token-api')?.value || '',
                has_fields: document.getElementById('config-has-fields')?.value || '',
                has_logs_api_url: document.getElementById('config-has-logs-api-url')?.value || '',
            };
            
            console.log('Sending config data:', configData);
            
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(configData)
            });
                
                const result = await response.json();
                console.log('Response:', result);
                
                if (result.success) {
                    showConfigAlert('✅ Konfigurasi berhasil disimpan', 'success');
                    setTimeout(() => {
                        loadConfiguration();
                    }, 500);
                } else {
                    showConfigAlert('❌ Error: ' + (result.error || 'Unknown error'), 'danger');
                }
        } catch (error) {
            console.error('Error saving configuration:', error);
            showConfigAlert('❌ Error: ' + error.message, 'danger');
        }
    });
}
