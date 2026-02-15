import sys
import time
import random
import threading
import os
from datetime import datetime

try:
    import requests
    from colorama import Fore, Back, Style, init
except ImportError:
    print("Ошибка! Выполни: pip install requests colorama")
    sys.exit()

init(autoreset=True)

class RobloxHybridScanner:
    def __init__(self):
        # --- НАСТРОЙКИ ---
        self.THREADS = 20
        self.BATCH_SIZE = 50
        
        # Файлы для сохранения
        self.FILE_GAMES = "found_games.txt"
        self.FILE_ASSETS = "found_assets.txt"
        
        # --- СТАТИСТИКА ---
        self.running = True
        self.total_checked = 0
        self.games_count = 0
        self.assets_count = 0
        self.start_time = time.time()
        
        self.print_lock = threading.Lock()
        self.data_lock = threading.Lock()
        self.spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.spin_idx = 0

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_banner(self):
        self.clear_screen()
        print(Fore.CYAN + Style.BRIGHT + r"""
   _____   ____  ____  _      ___  __  __ 
  |  __ \ / __ \|  _ \| |    / _ \ \ \/ / 
  | |__) | |  | | |_) | |   | | | | \  /  
  |  _  /| |  | |  _ <| |___| |_| | /  \  
  |_| \_\ \____/|_| \_\_____|\___/ /_/\_\ 
        HYBRID SCANNER v5.0
        """)
        print(Fore.WHITE + f" [INFO] Games  -> {Fore.GREEN}{self.FILE_GAMES} (Link: /games/)")
        print(Fore.WHITE + f" [INFO] Assets -> {Fore.YELLOW}{self.FILE_ASSETS} (Link: /catalog/)")
        print(Fore.LIGHTBLACK_EX + "-" * 60 + "\n")

    def get_timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def log_item(self, name, url, item_type):
        """Умный вывод: Игры ярко, Ассеты тускло"""
        with self.print_lock:
            # Очистка строки статус-бара
            sys.stdout.write('\r' + ' ' * 100 + '\r')
            
            ts = self.get_timestamp()
            
            if item_type == "GAME":
                # --- ВЫВОД ИГРЫ (ЯРКО-ЗЕЛЕНЫЙ) ---
                print(f"{Fore.WHITE}[{ts}] {Fore.GREEN}{Style.BRIGHT}[GAME FOUND] {name}")
                print(f"{Fore.GREEN}           LINK: {url}")
                print(Fore.LIGHTBLACK_EX + "-" * 40)
                # Сохраняем в файл игр
                with open(self.FILE_GAMES, "a", encoding="utf-8") as f:
                    f.write(f"[{ts}] {name} - {url}\n")
            
            else:
                # --- ВЫВОД АССЕТА (ЖЕЛТЫЙ/СЕРЫЙ) ---
                print(f"{Fore.LIGHTBLACK_EX}[{ts}] {Fore.YELLOW}[ASSET: {item_type}] {name}")
                print(f"{Fore.LIGHTBLACK_EX}           LINK: {url}")
                # Сохраняем в файл ассетов
                with open(self.FILE_ASSETS, "a", encoding="utf-8") as f:
                    f.write(f"[{ts}] [{item_type}] {name} - {url}\n")

    def update_progress_bar(self):
        if not self.running: return

        elapsed = time.time() - self.start_time
        speed = int(self.total_checked / elapsed) if elapsed > 0.1 else 0
        spin = self.spinner[self.spin_idx % len(self.spinner)]
        self.spin_idx += 1

        # Статус бар показывает и игры, и ассеты
        status = (
            f"{Fore.MAGENTA}{spin} "
            f"{Fore.WHITE}Scan: {Fore.CYAN}{self.total_checked:,} "
            f"{Fore.WHITE}| {Fore.GREEN}Games: {self.games_count} "
            f"{Fore.WHITE}| {Fore.YELLOW}Assets: {self.assets_count} "
            f"{Fore.LIGHTBLACK_EX}({speed}/s)"
        )

        with self.print_lock:
            sys.stdout.write(f"\r{status}")
            sys.stdout.flush()

    def analyze_id(self, place_id, session):
        try:
            url = f"https://economy.roblox.com/v2/assets/{place_id}/details"
            resp = session.get(url, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                name = data.get("Name", "")
                type_id = data.get("AssetTypeId")
                
                # Фильтр совсем плохих имен
                if not name or len(name) < 3 or "Asset" in name:
                    return

                # === ЛОГИКА РАЗДЕЛЕНИЯ ===
                if type_id == 9:
                    # ЭТО ИГРА (PLACE)
                    link = f"https://www.roblox.com/games/{place_id}"
                    with self.data_lock:
                        self.games_count += 1
                    self.log_item(name, link, "GAME")
                
                else:
                    # ЭТО ДРУГОЙ АССЕТ (Футболка, Модель, Аудио и т.д.)
                    # Генерируем ссылку на CATALOG, чтобы не было 404
                    link = f"https://www.roblox.com/catalog/{place_id}"
                    
                    # Определяем тип для лога
                    types = {2: "T-Shirt", 11: "Shirt", 12: "Pants", 10: "Model", 3: "Audio"}
                    type_str = types.get(type_id, "Other")
                    
                    with self.data_lock:
                        self.assets_count += 1
                    self.log_item(name, link, type_str)

        except:
            pass

    def worker(self):
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0'})

        while self.running:
            ids = [random.randint(1000000000, 5000000000) for _ in range(self.BATCH_SIZE)]
            ids_str = ",".join(map(str, ids))
            
            try:
                # 1. Проверяем иконки (фильтр пустышек)
                url = f"https://thumbnails.roblox.com/v1/places/gameicons?placeIds={ids_str}&returnPolicy=PlaceHolder&size=50x50&format=Png&isCircular=false"
                resp = session.get(url, timeout=5)
                
                with self.data_lock:
                    self.total_checked += self.BATCH_SIZE

                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    for item in data:
                        if item.get("state") == "Completed":
                            # Если иконка есть, узнаем что это за предмет
                            self.analyze_id(item.get("targetId"), session)
                            
                elif resp.status_code == 429:
                    time.sleep(2)
            except:
                pass
            time.sleep(0.1)

    def start(self):
        self.print_banner()
        threads = []
        for _ in range(self.THREADS):
            t = threading.Thread(target=self.worker, daemon=True)
            t.start()
            threads.append(t)

        try:
            while True:
                self.update_progress_bar()
                time.sleep(0.15)
        except KeyboardInterrupt:
            self.running = False
            print(f"\n{Fore.RED}[STOP] Скрипт остановлен.")
            sys.exit()

if __name__ == "__main__":
    app = RobloxHybridScanner()
    app.start()