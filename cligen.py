import streamlit as st
import asyncio
import aiohttp
import random
import time
import pandas as pd
from datetime import datetime

# 1. Конфигурация страницы (ДОЛЖНА БЫТЬ ПЕРВОЙ СТРОКОЙ)
st.set_page_config(
    page_title="Roblox Scanner Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS для строгого дизайна
st.markdown("""
    <style>
        .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
        .stMetric { background-color: #262730; padding: 10px; border-radius: 5px; }
        /* Скрываем стандартное меню для чистоты */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 3. Инициализация состояния (память браузера)
if 'data' not in st.session_state:
    st.session_state.data = []
if 'is_running' not in st.session_state:
    st.session_state.is_running = False

# --- ФУНКЦИИ (Они не выполняются при старте, только определяются) ---

async def fetch_thumbnails(session, batch_ids):
    """Быстрая проверка 100 ID через сервер картинок"""
    ids_str = ",".join(map(str, batch_ids))
    url = f"https://thumbnails.roblox.com/v1/places/gameicons?placeIds={ids_str}&returnPolicy=PlaceHolder&size=50x50&format=Png&isCircular=false"
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                # Возвращаем только ID тех игр, у которых есть иконка (Completed)
                return [item['targetId'] for item in data.get('data', []) if item.get('state') == 'Completed']
            elif resp.status == 429:
                return "RATELIMIT"
    except:
        return []
    return []

async def fetch_details(session, place_id):
    """Получение имени игры"""
    url = f"https://economy.roblox.com/v2/assets/{place_id}/details"
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        pass
    return None

async def runner(placeholder_log, placeholder_metrics, start_id, end_id, speed_delay):
    """Главный цикл сканирования"""
    async with aiohttp.ClientSession() as session:
        total_checked = 0
        found_count = 0
        start_time = time.time()

        # Цикл работает, пока включен флаг is_running
        while st.session_state.is_running:
            # 1. Генерируем пачку 100 ID
            batch = [random.randint(start_id, end_id) for _ in range(100)]
            
            # 2. Асинхронный запрос
            valid_ids = await fetch_thumbnails(session, batch)
            
            if valid_ids == "RATELIMIT":
                placeholder_log.warning("⚠️ Rate Limit (429). Ждем 3 секунды...")
                await asyncio.sleep(3)
                continue
            
            total_checked += 100
            
            # 3. Если нашли живые ID, узнаем детали
            if valid_ids:
                for vid in valid_ids:
                    details = await fetch_details(session, vid)
                    if details and details.get("AssetTypeId") == 9: # 9 = Place (Игра)
                        name = details.get("Name", "Unknown")
                        link = f"https://www.roblox.com/games/{vid}"
                        
                        # Добавляем в начало списка
                        st.session_state.data.insert(0, {
                            "Time": datetime.now().strftime("%H:%M:%S"),
                            "ID": str(vid),
                            "Name": name,
                            "Link": link
                        })
                        found_count += 1
                        placeholder_log.success(f"✅ Найдено: {name}")

            # 4. Обновляем метрики
            elapsed = time.time() - start_time
            speed = int(total_checked / elapsed) if elapsed > 0 else 0
            
            with placeholder_metrics.container():
                c1, c2, c3 = st.columns(3)
                c1.metric("Проверено ID", f"{total_checked:,}")
                c2.metric("Найдено", found_count)
                c3.metric("Скорость", f"{speed} ID/sec")

            # 5. Пауза, чтобы не убить сервер Streamlit
            await asyncio.sleep(speed_delay)

# --- ИНТЕРФЕЙС (UI) ---

st.title("⚡ Roblox Fast Scanner")

# Сайдбар с настройками
with st.sidebar:
    st.header("Настройки")
    
    start_input = st.number_input("Начало диапазона", value=1000000000, step=1000000)
    end_input = st.number_input("Конец диапазона", value=5000000000, step=1000000)
    
    speed_mode = st.select_slider("Скорость / Риск", options=["Медленно", "Нормально", "Быстро"], value="Нормально")
    
    delay_map = {"Медленно": 1.0, "Нормально": 0.5, "Быстро": 0.1}
    current_delay = delay_map[speed_mode]
    
    st.markdown("---")
    
    # КНОПКИ УПРАВЛЕНИЯ
    col1, col2 = st.columns(2)
    if col1.button("▶ СТАРТ", type="primary"):
        st.session_state.is_running = True
        
    if col2.button("⏹ СТОП"):
        st.session_state.is_running = False
        st.rerun() # Перезагрузить страницу, чтобы обновить состояние кнопок

    if st.button("🗑 Очистить таблицу"):
        st.session_state.data = []
        st.rerun()

# --- ОСНОВНАЯ ЧАСТЬ ---

# Место для логов и метрик
metrics_area = st.empty()
log_area = st.empty()

# Таблица результатов (всегда видна, если есть данные)
if st.session_state.data:
    st.markdown("### 📋 Результаты")
    st.dataframe(
        pd.DataFrame(st.session_state.data), 
        column_config={"Link": st.column_config.LinkColumn("Ссылка")},
        use_container_width=True
    )
else:
    st.info("Нажмите СТАРТ для начала поиска.")

# --- ЗАПУСК ЛОГИКИ ---
# Этот блок выполнится только если мы нажали Старт и is_running = True
if st.session_state.is_running:
    try:
        asyncio.run(runner(log_area, metrics_area, start_input, end_input, current_delay))
    except Exception as e:
        st.error(f"Ошибка выполнения: {e}")
        st.session_state.is_running = False
