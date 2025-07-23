from flask import Flask, render_template, jsonify, send_file
import serial
import threading
import time
from datetime import datetime
import pandas as pd
import os
import re 
app = Flask(__name__)
data_buffer = []
arduino_connected = False
BUZZER_PIN = 4
STATUS_LED_PIN = 3
TEMP_THRESHOLD = 40
HUM_THRESHOLD = 70
GAS_THRESHOLD = 800
EXCEL_FILE = "readings.xlsx"

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
                raw = arduino.readline().decode('utf-8', errors='ignore').strip()
                print(f"Raw data received: {raw}")  # للتصحيح
                
                if raw:
                    try:
                        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", raw)
                        
                        if len(numbers) >= 3:
                            temp = float(numbers[0])
                            hum = float(numbers[1])
                            gas = float(numbers[2])
                            quality = determine_air_quality(gas)
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            alert = ''

                            # التحقق من تجاوز الحدود
                            alert_condition = (temp > TEMP_THRESHOLD or 
                                             hum > HUM_THRESHOLD or 
                                             gas > GAS_THRESHOLD)

                            if alert_condition:
                                arduino.write(b'1\n')  # تشغيل الإنذار
                                if temp > TEMP_THRESHOLD:
                                    alert = f"⚠️ درجة الحرارة مرتفعة ({temp}°C)"
                                if hum > HUM_THRESHOLD:
                                    alert = f"⚠️ الرطوبة مرتفعة ({hum}%)"
                                if gas > GAS_THRESHOLD:
                                    alert = f"⚠️ مستوى الغاز مرتفع ({gas} PPM)"
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
                            
                            # حفظ البيانات كل 10 قراءات
                            if len(data_buffer) % 10 == 0:
                                save_to_excel()

                            if len(data_buffer) > 100:
                                data_buffer.pop(0)
                    except ValueError as e:
                        print(f"خطأ في تحويل البيانات: {e}، البيانات الخام: {raw}")
                    except Exception as e:
                        print(f"خطأ غير متوقع: {e}")
            except Exception as err:
                print("خطأ أثناء قراءة البيانات:", err)
                arduino_connected = False
        else:
            arduino_connected = False
            print("الأردوينو غير متصل")
        time.sleep(2)

@app.route('/')
def home():
    return render_template('index.html', connected=arduino_connected)

@app.route('/data')
def get_data():
    return jsonify(data_buffer)

@app.route('/export')
def export_data():
    try:
        df = pd.DataFrame(data_buffer)
        excel_path = "exported_data.xlsx"
        df.to_excel(excel_path, index=False)
        return send_file(excel_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    if os.path.exists(EXCEL_FILE):
        os.remove(EXCEL_FILE)
    pd.DataFrame().to_excel(EXCEL_FILE)
    
    threading.Thread(target=read_serial, daemon=True).start()
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
