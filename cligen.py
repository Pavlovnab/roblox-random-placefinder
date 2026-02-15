import streamlit as st
import asyncio
import aiohttp
import random
import time
import pandas as pd
from datetime import datetime

# --- КОНФИГУРАЦИЯ СТРАНИЦЫ ---
st.set_page_config(
    page_title="Roblox Scanner Pro",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- СТИЛИЗАЦИЯ (СТРОГИЙ ДИЗАЙН) ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2129; padding: 15px; border-radius: 10px; border: 1px solid #3e424b; }
    div[data-testid="stExpander"] { border: none; background-color: #1e2129; }
    </style>
    """, unsafe_allow_html=True)

# --- ИНИЦИАЛИЗАЦИЯ ДАННЫХ ---
if 'db' not in st.session_state:
    st.session_state.db = []
if 'scanning' not in st.session_state:
    st.session_state.scanning = False

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
with st.sidebar:
    st.title("⚙️ Control Panel")
    st.markdown("---")
    
    range_start = st.number_input("Start ID", value=1300000000, step=1000000)
    range_end = st.number_input("End ID", value=1500000000, step=1000000)
    
    speed_mode = st.select_slider(
        "Scan Intensity",
        options=["Safe", "Balanced", "Aggressive", "Turbo"],
        value="Balanced"
    )
    
    intensity_map = {
        "Safe": {"tasks": 5, "delay": 1.0},
        "Balanced": {"tasks": 15, "delay": 0.5},
        "Aggressive": {"tasks": 40, "delay": 0.2},
        "Turbo": {"tasks": 80, "delay": 0.05}
    }
    
    st.markdown("---")
    if st.button("🗑️ Clear Database", use_container_width=True):
        st.session_state.db = []
        st.rerun()

# --- МЕТРИКИ ---
st.title("🛠️ Roblox Place Finder Pro")
m1, m2, m3 = st.columns(3)
total_checked_placeholder = m1.empty()
found_placeholder = m2.empty()
speed_placeholder = m3.empty()

# --- ОСНОВНОЙ БЛОК ---
col_run, col_stop = st.columns(2)
start_btn = col_run.button("🚀 START SCANNING", use_container_width=True, type="primary")
stop_btn = col_stop.button("🛑 STOP", use_container_width=True)

if stop_btn:
    st.session_state.scanning = False

log_container = st.container()

# --- АСИНХРОННЫЙ СКАНЕР ---
async def fetch_batch(session, batch_ids):
    ids_str = ",".join(map(str, batch_ids))
    url = f"https://thumbnails.roblox.com/v1/places/gameicons?placeIds={ids_str}&returnPolicy=PlaceHolder&size=50x50&format=Png&isCircular=false"
    try:
        async with session.get(url, timeout=5) as resp:
            if resp.status == 200:
                data = await resp.json()
                return [item['targetId'] for item in data.get('data', []) if item.get('state') == 'Completed']
            elif resp.status == 429:
                return "RATE_LIMIT"
    except:
        return []
    return []

async def get_details(session, target_id):
    url = f"https://economy.roblox.com/v2/assets/{target_id}/details"
    try:
        async with session.get(url, timeout=5) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        return None

async def run_scanner():
    params = intensity_map[speed_mode]
    st.session_state.scanning = True
    
    checked = 0
    found = 0
    start_time = time.time()
    
    async with aiohttp.ClientSession(headers={'User-Agent': 'Mozilla/5.0'}) as session:
        while st.session_state.scanning:
            tasks = []
            # Создаем группу задач для параллельного выполнения
            for _ in range(params["tasks"]):
                batch = [random.randint(range_start, range_end) for _ in range(100)]
                tasks.append(fetch_batch(session, batch))
            
            results = await asyncio.gather(*tasks)
            
            for live_ids in results:
                if live_ids == "RATE_LIMIT":
                    st.warning("⚠️ Rate Limit Detected. Cooling down...")
                    await asyncio.sleep(5)
                    continue
                
                checked += 100
                if live_ids:
                    for tid in live_ids:
                        details = await get_details(session, tid)
                        if details and details.get("AssetTypeId") == 9:
                            item = {
                                "Time": datetime.now().strftime("%H:%M:%S"),
                                "ID": tid,
                                "Name": details.get("Name", "N/A"),
                                "Link": f"https://www.roblox.com/games/{tid}"
                            }
                            st.session_state.db.insert(0, item)
                            found += 1
                            with log_container:
                                st.success(f"📍 Found: {item['Name']} ({tid})")

            # Обновление метрик
            elapsed = time.time() - start_time
            speed = int(checked / elapsed) if elapsed > 0 else 0
            
            total_checked_placeholder.metric("Total Checked", f"{checked:,}")
            found_placeholder.metric("Games Found", found)
            speed_placeholder.metric("Speed (ID/s)", f"{speed}/s")
            
            await asyncio.sleep(params["delay"])

if start_btn:
    asyncio.run(run_scanner())

# --- ТАБЛИЦА РЕЗУЛЬТАТОВ ---
if st.session_state.db:
    st.markdown("### 📋 Recent Discoveries")
    df = pd.DataFrame(st.session_state.db)
    st.dataframe(df, use_container_width=True, height=400)
