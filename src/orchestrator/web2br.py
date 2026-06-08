import subprocess

# Chạy file script2.py
result = subprocess.run(['python', 'script2.py'], capture_output=True, text=True)

# In kết quả trả về từ script2
print("Kết quả:", result.stdout)