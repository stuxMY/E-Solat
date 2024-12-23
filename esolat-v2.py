#!/usr/bin/env python3
import requests
import json
import datetime
import os
from tabulate import tabulate
import subprocess
from plyer import notification

def colored_text(text, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'reset': '\033[0m'
    }
    return f"{colors.get(color, colors['reset'])}{text}{colors['reset']}"

def read_zones(file_path):
    zones = {}
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.strip():
                zone_code, zone_name = line.split(':')
                zones[zone_code.strip()] = zone_name.strip()
    return zones

def select_zone(zones):
    print(colored_text("\n🌍 Select Zone By Number:", 'blue'))
    for index, (zone_code, zone_name) in enumerate(zones.items(), 1):
        print(colored_text(f"{index}. {zone_name} ({zone_code})", 'cyan'))

    while True:
        try:
            choice = int(input(colored_text("\nNumber Of Your Zone: ", 'yellow')))
            if 1 <= choice <= len(zones):
                return list(zones.keys())[choice - 1]
            else:
                print(colored_text("❌ Invalid Number, try again.", 'red'))
        except ValueError:
            print(colored_text("❌ Invalid input, Enter a number.", 'red'))

def get_prayer_times(zone, period='today', start_date=None, end_date=None):
    url = 'https://www.e-solat.gov.my/index.php?r=esolatApi/takwimsolat'

    if period == 'duration':
        if not start_date or not end_date:
            start_date = input("Start date (yyyy-mm-dd): ")
            end_date = input("End date (yyyy-mm-dd): ")
        data = {'datestart': start_date, 'dateend': end_date}
        response = requests.post(url, data=data, params={'period': period, 'zone': zone})
    else:
        response = requests.get(url, params={'period': period, 'zone': zone})

    if response.status_code == 200:
        return response.json()
    else:
        return None

def display_prayer_times(data):
    if data and data['status'] == 'OK!':
        current_year = datetime.datetime.now().year
        print(f"\n🕌 SELAMAT MENUNAIKAN IBADAH SOLAT DAN PUASA BAGI TAHUN {current_year}")
        print(colored_text(f"\n🕌 Prayer Times for {data['zone']} on {data['prayerTime'][0]['date']}", 'green'))

        table_data = []
        headers = ['Hijri 📅', 'Date 📅', 'Imsak 🌅', 'Fajr 🌅', 'Syuruk ☀️', 'Dhuhr 🌞', 'Asr 🌇', 'Maghrib 🌆', 'Isha 🌃']

        for prayer in data['prayerTime']:
            row = [
                prayer['hijri'],
                prayer['date'],
                prayer['imsak'],
                prayer['fajr'],
                prayer['syuruk'],
                prayer['dhuhr'],
                prayer['asr'],
                prayer['maghrib'],
                prayer['isha']
            ]
            table_data.append(row)

        print(tabulate(table_data, headers, tablefmt="heavy_grid"))
    else:
        print(colored_text("❌ Failed to fetch prayer times.", 'red'))

def send_os_notification(title, message):
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=10
        )
    except Exception as e:
        print(f"Failed send notification using plyer: {e}")
        try:
            subprocess.run(['notify-send', title, message])
        except Exception as e:
            print(f"Failed send notification using notify-send: {e}")

def send_telegram_notification(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': message}
    response = requests.post(url, data=payload)
    return response.status_code == 200

def configure_telegram():
    bot_token = input(colored_text("Telegram bot token: ", 'yellow'))
    chat_id = input(colored_text("Telegram chat ID: ", 'yellow'))
    return bot_token, chat_id

def main():
    zones = read_zones('zone.txt')
    selected_zone = select_zone(zones)

    while True:
        print(colored_text("\nChoose Notification Type:", 'blue'))
        print(colored_text("1. OS Notification", 'cyan'))
        print(colored_text("2. Telegram Notification", 'cyan'))
        print(colored_text("3. Skip Notifications", 'cyan'))

        try:
            notification_choice = int(input(colored_text("Enter your choice: ", 'yellow')))

            if notification_choice == 1:
                print(colored_text("\n✅ OS notifications enabled.", 'green'))
                break

            elif notification_choice == 2:
                bot_token, chat_id = configure_telegram()
                print(colored_text("\n✅ Telegram notifications configured.", 'green'))
                break

            elif notification_choice == 3:
                print(colored_text("\nNotifications disabled.", 'yellow'))
                bot_token, chat_id = None, None
                break

            else:
                print(colored_text("❌ Invalid choice, please try again.", 'red'))
        except ValueError:
            print(colored_text("❌ Invalid input, please enter a number.", 'red'))

    data = get_prayer_times(selected_zone)
    display_prayer_times(data)

    if data and data['status'] == 'OK!' and notification_choice in [1, 2]:
        for prayer in data['prayerTime']:
            times = f"Imsak: {prayer['imsak']}, Fajr: {prayer['fajr']}, Syuruk: {prayer['syuruk']}, Dhuhr: {prayer['dhuhr']}, Asr: {prayer['asr']}, Maghrib: {prayer['maghrib']}, Isha: {prayer['isha']}"
            if notification_choice == 1:
                send_os_notification("Prayer Times", times)
            elif notification_choice == 2:
                send_telegram_notification(bot_token, chat_id, times)

if __name__ == "__main__":
    main()

