import streamlit as st
import requests
import random
import time

# Настройка страницы
st.set_page_config(page_title="Roblox Hybrid Scanner", page_icon="🔍", layout="wide")

# Кастомный CSS для стиля терминала
st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .stCodeBlock { background-color: #1e1e1e !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Roblox Hybrid Scanner v5.0")
st.caption("Адаптировано для Streamlit Cloud")

# --- Инициализация сессии ---
if 'found_items' not in st.session_state:
    st.session_state.found_items = []

# --- Боковая панель ---
with st.sidebar:
    st.header("⚙️ Настройки сканера")
    min_id = st.number_input("Минимальный ID", value=1000000000)
    max_id = st.number_input("Максимальный ID", value=5000000000)
    batch_size = st.slider("Размер пачки (batch)", 10, 100, 50)
    delay = st.slider("Задержка (сек)", 0.0, 2.0, 0.2)
    
    if st.button("🗑️ Очистить результаты"):
        st.session_state.found_items = []
        st.rerun()

# --- Основной интерфейс ---
col1, col2 = st.columns([1, 1])

with col1:
    start_btn = st.button("▶️ Запустить сканирование", use_container_width=True)
    stop_btn = st.button("⏹️ Остановить", use_container_width=True)

status_area = st.empty()
progress_bar = st.progress(0)

# --- Логика сканирования ---
if start_btn:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0'
    })
    
    st.info("Сканирование запущено. Результаты будут появляться ниже.")
    
    # В Streamlit вместо бесконечного цикла делаем фиксированное количество итераций
    # чтобы избежать зависания сервера
    for step in range(100): 
        if stop_btn:
            st.warning("Сканирование остановлено пользователем.")
            break
            
        # 1. Генерируем пачку ID
        ids = [random.randint(min_id, max_id) for _ in range(batch_size)]
        ids_str = ",".join(map(str, ids))
        
        try:
            # 2. Проверяем иконки (фильтр живых объектов)
            thumb_url = f"https://thumbnails.roblox.com/v1/places/gameicons?placeIds={ids_str}&returnPolicy=PlaceHolder&size=50x50&format=Png&isCircular=false"
            resp = session.get(thumb_url, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                for item in data:
                    if item.get("state") == "Completed":
                        target_id = item.get("targetId")
                        
                        # 3. Уточняем детали через Economy API
                        detail_url = f"https://economy.roblox.com/v2/assets/{target_id}/details"
                        det_resp = session.get(detail_url, timeout=5)
                        
                        if det_resp.status_code == 200:
                            details = det_resp.json()
                            name = details.get("Name", "Unknown")
                            type_id = details.get("AssetTypeId")
                            
                            # Фильтр мусора
                            if name and len(name) > 2 and "Asset" not in name:
                                item_type = "GAME" if type_id == 9 else "ASSET"
                                link = f"https://www.roblox.com/games/{target_id}" if type_id == 9 else f"https://www.roblox.com/catalog/{target_id}"
                                
                                result = {"id": target_id, "name": name, "type": item_type, "link": link}
                                st.session_state.found_items.insert(0, result)
                                
                                # Сразу отображаем находку
                                if item_type == "GAME":
                                    st.success(f"🎮 **GAME FOUND:** {name} ([Link]({link}))")
                                else:
                                    st.write(f"📦 **Asset:** {name} ([Link]({link}))")
            
            elif resp.status_code == 429:
                st.warning("⏳ Лимит запросов (429). Спим 5 секунд...")
                time.sleep(5)
                
        except Exception as e:
            pass # Игнорируем ошибки сети

        # Обновляем прогресс визуально
        progress_bar.progress((step + 1) / 100)
        status_area.text(f"Проверено объектов: {(step + 1) * batch_size}")
        time.sleep(delay)

# --- Таблица результатов ---
if st.session_state.found_items:
    st.write("### 📜 История находок")
    st.table(st.session_state.found_items)
