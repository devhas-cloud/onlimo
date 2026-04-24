import time
import os
import sys
import json
import requests
import traceback
from datetime import datetime, timedelta
from collections import defaultdict
from config import loadConfig, ambilDataDlh, UpdateDataDlh, ambilDataHas, prosesDataHas, updateDataSentHas


def write_log(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# Global configuration parameters
def initConfig():
    """Initialize global configuration from config.db"""
    global DLH_STATUS, DLH_API_URL, DLH_API_KEY, DLH_API_SECRET, DLH_UID, HAS_STATUS, HAS_API_URL, HAS_LOG_API_URL, HAS_TOKEN_API, HAS_FIELDS, DEVICE_ID, RUN_MINUTES
    
    try:
        config = loadConfig()
        
        # Load configuration values with validation
        DLH_STATUS = config.get('dlh_status', 'inactive')
        DLH_API_URL = config.get('dlh_api_url', '')
        DLH_API_KEY = config.get('dlh_api_key', '')
        DLH_API_SECRET = config.get('dlh_api_secret', '')
        DLH_UID = config.get('dlh_uid', '')

        HAS_STATUS = config.get('has_status', 'inactive')
        HAS_API_URL = config.get('has_api_url', '')
        HAS_LOG_API_URL = config.get('has_logs_api_url', '')
        HAS_TOKEN_API = config.get('has_token_api', '')

        RUN_MINUTES = [int(x) for x in config.get('run_minutes', '5,10,15').split(',') if x.isdigit()]  # fleksibel, bisa diubah dari config
        
        # Parse HAS_FIELDS safely
        has_fields_str = config.get('has_fields', '')
        HAS_FIELDS = [field.strip() for field in has_fields_str.split(',') if field.strip()] if has_fields_str else []

        DEVICE_ID = config.get('device_id', 'UNKNOWN')

        
        # Validate critical config values
        if DLH_STATUS == 'active' and not all([DLH_API_URL, DLH_API_KEY, DLH_API_SECRET, DLH_UID]):
            write_log(f"DLH API configuration incomplete. Some values are missing.")
        
        if HAS_STATUS == 'active' and not all([HAS_API_URL, HAS_TOKEN_API, HAS_FIELDS]):
            write_log(f"HAS API configuration incomplete. Some values are missing.")
    
        return True
        
    except Exception as e:
        write_log(f" Error saat inisialisasi konfigurasi: {e}")
        import traceback
        traceback.print_exc()
        return False

# Initialize configuration at startup
if not initConfig():
    write_log("Konfigurasi awal gagal, melanjutkan dengan nilai default...")
    # Don't exit, continue with defaults instead



def refreshConfig():
    """Refresh configuration from config.db - useful for dynamic reloading"""
    global  DLH_STATUS, DLH_API_URL, DLH_API_KEY, DLH_API_SECRET, DLH_UID,  HAS_STATUS, HAS_API_URL, HAS_LOG_API_URL, HAS_TOKEN_API, HAS_FIELDS, DEVICE_ID, RUN_MINUTES
    
    
    if not initConfig():
        write_log(f"Gagal me-refresh konfigurasi")
        return False
    
    write_log(f"Konfigurasi berhasil dimuat ulang dari config.db")
    return True


# ===== SEND LOGS =======


def send_logs(message):

    global HAS_LOG_API_URL, HAS_TOKEN_API, DEVICE_ID

    """
        Kirim log ke server API

        :param category: network | connection | sensor
        :param message: pesan log
        :param action: default unaction
        :return: bool
    """
    headers = {
        "X-API-Key": HAS_TOKEN_API,
        "Content-Type": "application/json"
    }
      

    payload = {
        "device_id": DEVICE_ID,
        "category": "network",
        "message": message,
        "action": 'unaction'
    }

    try:
        response = requests.post(HAS_LOG_API_URL, headers=headers, json=payload, timeout=10)
        if response.status_code in [200, 201]:
            write_log(f"Log berhasil dikirim ke HAS API: {message}")
            return True
        else:
            write_log(f" Gagal mengirim log ke HAS API: {response.status_code} {response.text[:500]}")
            return False
    except requests.Timeout:
        write_log(f" Timeout saat mengirim log ke HAS API")
        return False
    except requests.exceptions.RequestException as e:
        write_log(f" Request error saat mengirim log ke HAS API: {e}")
        return False
    except Exception as e:
        write_log(f" Unexpected error saat mengirim log ke HAS API: {e}")
        traceback.print_exc()
        return False


# ============ DLH SEND ==================

def send_dlh(dateNow):
    """Kirim data ke DLH API menggunakan konfigurasi global"""

    global DLH_STATUS, DLH_API_URL, DLH_API_KEY, DLH_API_SECRET, DLH_UID

    if DLH_STATUS != 'active':
        write_log("DLH API tidak aktif")
        return False
    
    if not all([DLH_API_URL, DLH_API_KEY, DLH_API_SECRET, DLH_UID]):
        write_log(f" Konfigurasi DLH tidak lengkap. URL: {bool(DLH_API_URL)}, Key: {bool(DLH_API_KEY)}, Secret: {bool(DLH_API_SECRET)}, UID: {bool(DLH_UID)}")
        return False

    fields = ["date", "wtemp", "tds", "do", "ph", "turb", "depth", "no3", "nh3n", "cod", "bod", "tss"]

    try:
        data_rows = ambilDataDlh(fields, dateNow)
    except Exception as e:
        write_log(f" Error ambil data DLH: {e}")
        traceback.print_exc()
        return False
    
    if not data_rows:
        write_log(f"Tidak ada data untuk {dateNow}")
        return False

    url = DLH_API_URL
    headers = {"Content-Type": "application/json"}

    for row in data_rows:
        try:
            # ✅ Validasi panjang row
            if len(row) < len(fields):
                write_log(f" Data row tidak lengkap: {row}")
                continue

            row_date = row[0]

            # ✅ Handle jika bukan datetime
            if isinstance(row_date, str):
                try:
                    row_date = datetime.fromisoformat(row_date)
                except Exception:
                    write_log(f" Format tanggal invalid: {row_date}")
                    continue

            tanggal = row_date.strftime("%Y-%m-%d")
            jam = row_date.strftime("%H:%M:%S")
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            dataJson = {
                "data": {
                    "IDStasiun": DLH_UID,
                    "Tanggal": tanggal,
                    "Jam": jam,
                    "Suhu": row[1] if isinstance(row[1], (int, float)) else 0.0,
                    "TDS": row[2] if isinstance(row[2], (int, float)) else 0.0,
                    "DO": row[3] if isinstance(row[3], (int, float)) else 0.0,
                    "PH": row[4] if isinstance(row[4], (int, float)) else 0.0,
                    "Turbidity": row[5] if isinstance(row[5], (int, float)) else 0.0,
                    "Kedalaman": row[6] if isinstance(row[6], (int, float)) else 0.0,
                    "Nitrat": row[7] if isinstance(row[7], (int, float)) else 0.0,
                    "Amonia": row[8] if isinstance(row[8], (int, float)) else 0.0,
                    "COD": row[9] if isinstance(row[9], (int, float)) else 0.0,
                    "BOD": row[10] if isinstance(row[10], (int, float)) else 0.0,
                    "TSS": row[11] if isinstance(row[11], (int, float)) else 0.0
                },
                "apikey": DLH_API_KEY,
                "apisecret": DLH_API_SECRET
            }

            write_log(f"Mengirim DLH: {tanggal} {jam}")

            try:
                response = requests.post(url, json=dataJson, headers=headers, timeout=(5, 10))
                
                # Validasi response kosong
                if not response.text:
                    write_log(f"DLH API returned empty response")
                    send_logs(f"DLH API response empty: {row_date} - {response.text}")
                    UpdateDataDlh(row_date, 0, response.text, now_str)
                    continue
                
                try:
                    json_response = response.json()
                except json.JSONDecodeError as je:
                    write_log(f"Invalid JSON response from DLH API: {response.text}")
                    send_logs(f"DLH API invalid JSON: {row_date} - {response.text}")
                    UpdateDataDlh(row_date, 0, f"Invalid JSON: {response.text}", now_str)
                    continue
                
                statusCode = json_response.get("status", {}).get("statusCode")
                statusDesc = json_response.get("status", {}).get("statusDesc", "No description")

                if response.status_code == 200 and statusCode == 200:
                    write_log(f"Sukses DLH: {json_response}")
                    UpdateDataDlh(row_date, 1, response.text, now_str)
                else:
                    write_log(f"Gagal Kirim: {response.text}")
                    send_logs(f"Gagal Kirim DLH API: {row_date} - {statusCode} {statusDesc}")
                    UpdateDataDlh(row_date, 0, f"{response.text}", now_str)

            except requests.Timeout:
                write_log("Timeout DLH API")
                UpdateDataDlh(row_date, 0, "Timeout", now_str)
                send_logs(f"Timeout DLH API: {row_date}")

            except requests.RequestException as e:
                write_log(f"Request error: {e}")
                UpdateDataDlh(row_date, 0, f"RequestException: {e}", now_str)
                send_logs(f"Request error DLH API: {row_date} - {e}")

        except Exception as e:
            write_log(f"Error proses row: {e}")
            traceback.print_exc()
            continue

    return True
    

# ============ HAS SEND ==================

def send_has(dateNow):
    """Kirim data ke HAS API menggunakan token API dan konfigurasi global"""
    
    global HAS_STATUS, HAS_API_URL, HAS_TOKEN_API, HAS_FIELDS, DEVICE_ID


    date_str = dateNow.strftime("%Y-%m-%d %H:%M")
    
    headers = {
        "X-API-Key": HAS_TOKEN_API,
        "Content-Type": "application/json"
    }
    
    try:
        # Ambil dan proses data
        data_rows = ambilDataHas(HAS_FIELDS, date_str)
        write_log(f"Mengambil data HAS: {len(data_rows) if data_rows else 0} baris")
        
        payloadData = prosesDataHas(data_rows, HAS_FIELDS) if data_rows else []
    except Exception as e:
        write_log(f" Error saat mengambil/memproses data HAS: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Gabungkan data dari kedua tabel
    payload = {
        "device_id": DEVICE_ID,
        "data": payloadData
    }

    if not payload["data"]:
        write_log(f"Tidak ada data baru untuk dikirim ke HAS API pada tanggal {date_str}.")
        return False

    try:
        write_log(f"Mengirim {len(payload['data'])} record ke HAS API")
        response = requests.post(HAS_API_URL, headers=headers, json=payload, timeout=(5, 120))
        
        if response.status_code in [200, 201]:  # 200 OK atau 201 Created
            write_log(f"Data untuk tanggal {date_str} berhasil dikirim ke HAS API.")
            
            # Update status 'has' di database
            try:
                update = updateDataSentHas(date_str)
                if update:
                    write_log(f"Status 'has' diperbarui untuk data dengan datetime <= {date_str}")
                else:
                    write_log(f"Gagal memperbarui status 'has' untuk data dengan datetime <= {date_str}")
            except Exception as ue:
                write_log(f"Error saat update status HAS: {ue}")
            return True
        else:
            write_log(f"HAS API error {response.status_code}: {response.text[:500]}")
            return False
    except requests.Timeout:
        write_log(f" Timeout saat mengirim ke HAS API")
        return False
    except requests.RequestException as e:
        write_log(f" Request error ke HAS API: {e}")
        return False
    except Exception as e:
        write_log(f" Unexpected error saat mengirim ke HAS: {e}")
        traceback.print_exc()
        return False
    


def get_next_run(now, run_minutes):
    run_minutes = sorted(run_minutes)

    for m in run_minutes:
        if m > now.minute:
            return now.replace(minute=m, second=0, microsecond=0)

    # kalau sudah lewat semua → ke jam berikutnya
    next_hour = now + timedelta(hours=1)
    return next_hour.replace(minute=run_minutes[0], second=0, microsecond=0)


def scheduler():
    write_log(f"🚀 Scheduler dimulai (menit: {RUN_MINUTES})")

    last_run = None  # proteksi double eksekusi

    try:
        while True:
            now = datetime.now()
            next_run = get_next_run(now, RUN_MINUTES)

            sleep_seconds = (next_run - now).total_seconds()

            if sleep_seconds < 0:
                sleep_seconds = 0

            write_log(f"Next run: {next_run} (sleep {sleep_seconds:.2f}s)")

            # sleep bertahap
            while sleep_seconds > 0:
                chunk = min(sleep_seconds, 60)
                time.sleep(chunk)
                sleep_seconds -= chunk

            exec_time = datetime.now().replace(second=0, microsecond=0)

            # proteksi supaya tidak jalan 2x di menit yang sama
            if last_run == exec_time:
                continue
            last_run = exec_time

            write_log(f"Eksekusi pada: {exec_time}")

            # ======================
            # REFRESH CONFIG
            # ======================
            try:
                if not refreshConfig():
                    write_log("Gagal refresh config, pakai sebelumnya")
            except Exception as e:
                write_log(f"Error refresh config: {e}")
                traceback.print_exc()

            # ======================
            # DLH PROCESS
            # ======================
            try:
                if DLH_STATUS == 'active':
                    write_log("Kirim DLH...")
                    send_dlh(exec_time)
                else:
                    write_log("DLH tidak aktif")
            except Exception as e:
                write_log(f"Error send_dlh: {e}")
                traceback.print_exc()

            # ======================
            # HAS PROCESS
            # ======================
            try:
                if HAS_STATUS == 'active':
                    write_log("Kirim HAS...")
                    send_has(exec_time)
                else:
                    write_log("HAS tidak aktif")
            except Exception as e:
                write_log(f"Error send_has: {e}")
                traceback.print_exc()

            # ======================
            # PROTEKSI DRIFT
            # ======================
            actual_delay = (datetime.now() - next_run).total_seconds()
            if actual_delay > 5:
                write_log(f"Terlambat {actual_delay:.2f} detik")

    except KeyboardInterrupt:
        write_log("Scheduler dihentikan user")
    except Exception as e:
        write_log(f"Fatal error: {e}")
        traceback.print_exc()
    finally:
        write_log("Scheduler berhenti")


if __name__ == "__main__":
    scheduler()