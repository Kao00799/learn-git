import serial
import time
import requests

# ตั้งค่าการเชื่อมต่อกับ Arduino
ser = serial.Serial('COM3', 9600, timeout=1)

# ตั้งค่า Telegram Bot
TOKEN = '...'
CHAT_ID = '...'
send_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
get_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

# ตัวแปรติดตามสถานะ
last_update_id = 0
last_temp = "ยังไม่มีข้อมูล"
count = 0
cooldown = False
cooldown_start = 0
cooldown_duration = 300  # 5 นาที

while True:
    current_time = time.time()

    # อ่านค่าจาก Arduino
    if ser.in_waiting > 0:
        temp = ser.readline().decode('ascii', errors='ignore').strip()
        try:
            float_temp = float(temp)
            last_temp = temp
            print(f"อุณหภูมิที่อ่านได้: {temp} ℃")

            if float_temp > 30 and not cooldown:
                if count < 3:
                    data = {
                        'chat_id': CHAT_ID,
                        'text': f' อุณหภูมิเกิน กรุณาปรับอุณหภูมิให้เหมาะสม อุณหภูมิปัจจุบัน: {temp} ℃ '
                    }
                    response = requests.post(send_url, data=data)
                    if response.status_code == 200:
                        count += 1
                        print("ส่งข้อความแจ้งเตือนแล้ว")
                    else:
                        print("ส่งข้อความไม่สำเร็จ:", response.text)

                if count >= 3:
                    cooldown = True
                    cooldown_start = current_time
                    print("cooldown 5 นาที เพื่อลดการใช้ CPU")

        except ValueError:
            print("ไม่สามารถแปลงค่าอุณหภูมิได้:", temp)

    # เช็คว่าควรออกจาก cooldown หรือยัง
    if cooldown and (current_time - cooldown_start >= cooldown_duration):
        cooldown = False
        count = 0
        print("ออกจาก cooldown แล้ว")

    # ตรวจสอบคำสั่งจาก Telegram
    try:
        response = requests.get(get_url, params={'offset': last_update_id + 1})
        updates = response.json()

        if "result" in updates:
            for update in updates["result"]:
                if "update_id" in update:
                    last_update_id = update["update_id"]

                if "message" in update:
                    message = update["message"]
                    text = message.get("text", "").strip().lower()

                    if text == "/temp":
                        reply = f"อุณหภูมิปัจจุบันคือ {last_temp} ℃" if last_temp != "ยังไม่มีข้อมูล" else " ยังไม่มีข้อมูลจาก Arduino"
                        requests.post(send_url, data={
                            'chat_id': message['chat']['id'],
                            'text': reply
                        })

    except Exception as e:
        print("เกิดข้อผิดพลาดขณะตรวจสอบ /temp:", e)

    time.sleep(5)

