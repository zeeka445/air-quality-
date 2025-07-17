//app.py(python)
from flask import Flask, render_template, jsonify
import serial
import threading
import time
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)
data_buffer = []
arduino_connected = False
ALERT_LED_PIN = 13
TEMP_THRESHOLD = 40
HUM_THRESHOLD = 90
GAS_THRESHOLD = 800
EXCEL_FILE = "readings.xlsx"  # اسم ملف Excel

AIR_QUALITY_THRESHOLDS = {
    'Excellent': 200,
    'Good': 400,
    'Moderate': 600,
    'Poor': 800,
    'Very Poor': 1000,
    'Hazardous': float('inf')
}

def save_to_excel():
    try:
        df = pd.DataFrame(data_buffer)
        df.to_excel(EXCEL_FILE, index=False)
        print(f"تم حفظ البيانات في {EXCEL_FILE}")
    except Exception as e:
        print(f"خطأ في حفظ الملف: {e}")

def determine_air_quality(gas_value):
    for quality, threshold in AIR_QUALITY_THRESHOLDS.items():
        if gas_value < threshold:
            return quality
    return 'Hazardous'

try:
    arduino = serial.Serial('COM6', 9600, timeout=1)
    arduino_connected = True
    print("✅ Arduino connected on COM6")
except Exception as e:
    arduino = None
    print("❌ Arduino not connected:", e)

def read_serial():
    global arduino_connected
    while True:
        if arduino and arduino.is_open:
            try:
                raw = arduino.readline().decode('utf-8').strip()
                if raw:
                    parts = [p.strip() for p in raw.split(",")]
                    if len(parts) >= 3:
                        temp = float(parts[0])
                        hum = float(parts[1])
                        gas = float(parts[2])
                        quality = determine_air_quality(gas)
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        alert = ''

                        if temp > TEMP_THRESHOLD:
                            alert = f"⚠️ درجة الحرارة مرتفعة ({temp}°C)"
                            arduino.write(b'1\n')
                        elif hum > HUM_THRESHOLD:
                            alert = f"⚠️ الرطوبة مرتفعة ({hum}%)"
                            arduino.write(b'1\n')
                        elif gas > GAS_THRESHOLD:
                            alert = f"⚠️ مستوى الغاز مرتفع ({gas} PPM)"
                            arduino.write(b'1\n')
                        else:
                            arduino.write(b'0\n')

                        new_data = {
                            "temp": temp,
                            "hum": hum,
                            "gas": gas,
                            "quality": quality,
                            "timestamp": timestamp,
                            "alert": alert
                        }

                        data_buffer.append(new_data)
                        
                        # حفظ البيانات في Excel كل 10 قراءات
                        if len(data_buffer) % 10 == 0:
                            save_to_excel()

                        if len(data_buffer) > 100:
                            data_buffer.pop(0)
            except Exception as err:
                print("خطأ أثناء قراءة البيانات:", err)
        else:
            arduino_connected = False
        time.sleep(2)

@app.route('/')
def home():
    return render_template('index.html', connected=arduino_connected)

@app.route('/data')
def get_data():
    return jsonify(data_buffer)

if __name__ == '__main__':
    # إنشاء ملف Excel جديد عند التشغيل
    if os.path.exists(EXCEL_FILE):
        os.remove(EXCEL_FILE)
    pd.DataFrame().to_excel(EXCEL_FILE)
    
    threading.Thread(target=read_serial, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
