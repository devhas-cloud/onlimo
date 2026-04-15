import sqlite3
import os
import time
from datetime import date, datetime

CONFIG_DIR = "../config"
CONFIG_DB_NAME = "database.db"
CONFIG_DB_PATH = os.path.join(CONFIG_DIR, CONFIG_DB_NAME)


def defaultConfig():
    config_dir = CONFIG_DIR
    db_path = CONFIG_DB_PATH

    # Pastikan folder config ada
    os.makedirs(config_dir, exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Buat tabel config
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY,

            -- general
            parameter TEXT,
                       

            -- dlh api
            dlh_status TEXT,
            dlh_api_url TEXT,
            dlh_api_key TEXT,
            dlh_api_secret TEXT,
            dlh_uid TEXT,

            -- has api
            has_status TEXT,
            has_api_url TEXT,
            has_logs_api_url TEXT,
            has_token_api TEXT,
            has_fields TEXT,


            -- device info
            device_id TEXT,
            location_name TEXT,
            software_version TEXT,
            geo_latitude TEXT,
            geo_longitude TEXT
        )
        """)

        configurations = {
        
            # general
            "parameter": "pH, orp, tds, conduct, do, salinity, nh3n, battery, depth, flow, tflow, turb, tss, cod, bod, no3, wtemp, wpress",

            # dlh api
            "dlh_status": "inactive",
            "dlh_api_url": "https://onlimo.kemenlh.go.id/api/connect/Pengukuran",
            "dlh_api_key": "connect@hasenvironmental",
            "dlh_api_secret": "2wsx3edc!@#QWE",
            "dlh_uid": "",

            # has api
            "has_status": "inactive",
            "has_api_url": "https://api.hasportal.com/api/v1/data",
            "has_logs_api_url": "https://api.hasportal.com/api/v1/logs",
            "has_token_api": "",
            "has_fields": "datetime,pH,cod,tss,nh3n,flow,wtemp,orp,turb,tds,conduct,do,depth,bod,wpress",

     
            # device info
            "device_id": "HSP-xxxxxx",
            "location_name": "PT. Has Environmental",
            "software_version": "1.0.0",
            "geo_latitude": "-6.5224399",
            "geo_longitude": "106.8384747"
        }

        # Check if config with id=1 already exists
        cursor.execute("SELECT COUNT(*) as count FROM config WHERE id=1")
        exists = cursor.fetchone()[0] > 0
        
        # Only insert default values if config doesn't exist
        if not exists:
            columns = ", ".join(configurations.keys())
            placeholders = ", ".join(["?"] * len(configurations))
            values = list(configurations.values())

            cursor.execute(f"""
            INSERT INTO config (id, {columns})
            VALUES (1, {placeholders})
            """, values)

        conn.commit()

    except Exception as e:
        print("Error pada defaultConfig:", e)

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def loadConfig():
    defaultConfig()
    conn = sqlite3.connect(CONFIG_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM config WHERE id=1")
    row = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    config = dict(zip(columns, row))
    cursor.close()
    conn.close()
    return config


def ambilDateAll():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return timestamp

def ambilDate():
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return date

def ambilDateTime():
    Interval_Timestamp = datetime.strptime(ambilDateAll(), '%Y-%m-%d %H:%M:%S')
    unix_dt = int(time.mktime(Interval_Timestamp.timetuple()))
    return unix_dt
      

def cek_table():

    conn = sqlite3.connect(CONFIG_DB_PATH)
    cursor = conn.cursor()

        # Buat table data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device TEXT,
            date DATETIME,
            datetime BIGINT DEFAULT 0,
            pH FLOAT DEFAULT 0,
            orp FLOAT DEFAULT 0,
            tds FLOAT DEFAULT 0,
            conduct FLOAT DEFAULT 0,
            do FLOAT DEFAULT 0,
            salinity FLOAT DEFAULT 0,
            nh3n FLOAT DEFAULT 0,
            battery FLOAT DEFAULT 0,
            depth FLOAT DEFAULT 0,
            kedalaman FLOAT DEFAULT 0,
            flow FLOAT DEFAULT 0,
            tflow FLOAT DEFAULT 0,
            turb FLOAT DEFAULT 0,
            turbidity FLOAT DEFAULT 0,
            tss FLOAT DEFAULT 0,
            cod FLOAT DEFAULT 0,
            bod FLOAT DEFAULT 0,
            no3 FLOAT DEFAULT 0,
            wtemp FLOAT DEFAULT 0,
            wpress FLOAT DEFAULT 0,
            dlh BOOLEAN DEFAULT 0,
            dlh_response TEXT,
            dlh_sent_at DATETIME DEFAULT NULL,
            has BOOLEAN DEFAULT 0
        )
        """)
    conn.commit()
    cursor.close()
    conn.close()


def check_duplicate_data(device, date):
    """
    Cek apakah data dengan device dan date yang sama sudah ada di database.
    Mengabaikan detik dalam perbandingan (hanya membandingkan sampai menit).
    
    Args:
        device: ID device
        date: Datetime object atau string dalam format '%Y-%m-%d %H:%M:%S'
    
    Returns:
        True jika data sudah ada, False jika belum ada
    """
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()

        # Normalisasi date agar bisa menerima string maupun datetime object
        if isinstance(date, datetime):
            date_str = date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            date_str = str(date)
        
        # Cek di tabel tmp dan data
        for tbl in ['data']:
            query = f"""
                SELECT COUNT(*) FROM {tbl}
                WHERE device = ? AND date LIKE ?
            """
            # Format: YYYY-MM-DD HH:MM (tanpa detik)
            date_pattern = date_str[:16] + '%'
            cursor.execute(query, (device, date_pattern))
            result = cursor.fetchone()
            
            if result and result[0] > 0:
                cursor.close()
                conn.close()
                return True
        
        cursor.close()
        conn.close()
        return False
        
    except Exception as e:
        print(f"[ERROR] Gagal mengecek duplicate data: {e}")
        return False


def insert_data(date, datetime_val, ph, orp, tds, conduct, do, salinity, nh3n, battery, depth, flow, tflow, turb, tss, cod, bod, no3, wtemp, wpress):
  
    # buat table data
    cek_table()

    device = loadConfig()['device_id']

    # Cek apakah data dengan device dan date yang sama sudah ada
    if check_duplicate_data(device, date):
        print(f"[SKIP] Data dengan device '{device}' dan date '{date}' sudah ada di database. Pembacaan dilewati.")
        return False
    
    query = """
        INSERT INTO data (device, date, datetime, pH, orp, tds, conduct, do, salinity, nh3n, battery, depth, flow, tflow,
                          turb, tss, cod, bod, no3, wtemp, wpress)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()

        values = (
            device, date, datetime_val, ph, orp, tds, conduct, do, salinity, nh3n, battery, depth, flow, tflow,
            turb, tss, cod, bod, no3, wtemp, wpress
        )
        
        cursor.execute(query, values)
        conn.commit()

        print(f"[INFO] Data berhasil dimasukkan ke data: device='{device}', date='{date}'")
        return True
        
    except Exception as e:
        print(f"[ERROR] Gagal memasukkan data ke database: {e}")
        return False
        
    finally:
        # Tutup koneksi
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()



# ============ Function DLH ==================
def ambilDataDlh(fields, date):
    """Ambil data dari tabel 'data' yang belum dikirim (dlh = '0')"""
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        field_str = ", ".join(fields)
        cursor.execute(f"SELECT {field_str} FROM data WHERE dlh = '0' AND date <= ?", (date,))
        rows = cursor.fetchall()
        
        if rows:
            return rows
        else:
            return None
        
    except Exception as e:
        print(f"[ERROR] Gagal mengambil data: {e}")
        return None
        
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()


def UpdateDataDlh(date,dlh,dlh_response, dlh_sent_at):
    """Update data yang sudah dikirim dengan dlh = '1'"""
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        # Update dlh menjadi '1' untuk data dengan datetime tersebut
        cursor.execute("UPDATE data SET dlh = ?, dlh_response = ?, dlh_sent_at = ? WHERE date = ?", (dlh, dlh_response, dlh_sent_at, date))
        conn.commit()
        return True
    
    except Exception as e:
        print(f"[ERROR] Gagal mengupdate data: {e}")
        return False
    
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# ============ Function HAS ==================

def ambilDataHas(fields, date_str):
    """Ambil data dari tabel 'data' yang belum dikirim (has = '0')"""
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        field_str = ", ".join(fields)
        cursor.execute(f"SELECT {field_str} FROM data WHERE has = '0' AND date <= ?", (date_str,))
        rows = cursor.fetchall()
        
        if rows:
            return rows
        else:
            return None
        
    except Exception as e:
        print(f"[ERROR] Gagal mengambil data: {e}")
        return None
        
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

def prosesDataHas(rows, FIELDS):
    """
    Proses data dari database ke format yang sesuai dengan API HAS.
    Contoh output yang diharapkan:
    [
        {
            "recorded_at": "2024-12-14T10:30:00Z",
            "timestamp": 1702548600,
            "parameter_name": "temperature",
            "value": 25.5
        },
        ...
    ]
    """
    data_list = []
    if not rows:
        return data_list
    
    for row in rows:
        recorded_at = None
        timestamp = None
        
        # First pass: extract datetime
        for idx, field in enumerate(FIELDS):
            field = field.strip()
            if field == 'datetime':
                timestamp = row[idx]
                recorded_at = datetime.fromtimestamp(timestamp).isoformat()
                break
        
        # Second pass: create records for each parameter
        for idx, field in enumerate(FIELDS):
            field = field.strip()
            if field != 'datetime':
                record = {
                    'recorded_at': recorded_at,
                    'timestamp': timestamp,
                    'parameter_name': field,
                    'value': row[idx]
                }
                data_list.append(record)
    
    return data_list


def updateDataSentHas(FIELDS, date_str):
    """Update data yang sudah dikirim dengan has = '1'"""
    try:
        conn = sqlite3.connect(CONFIG_DB_PATH)
        cursor = conn.cursor()
        # Update has menjadi '1' untuk data dengan datetime tersebut
        cursor.execute("UPDATE data SET has = '1' WHERE datetime <= ?", (date_str,)) 
        conn.commit()
        return True
    
    except Exception as e:
        print(f"[ERROR] Gagal mengupdate data: {e}")
        return False
    
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
