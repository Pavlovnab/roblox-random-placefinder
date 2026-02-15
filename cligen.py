import streamlit as st
import asyncio
import aiohttp
import random
import time
import pandas as pd

st.set_page_config(page_title="Ultra Fast Scanner", layout="wide")

st.title("⚡ Hyper Roblox Scanner")
st.write("Использование асинхронности для максимальной скорости.")

# Настройки в сайдбаре
with st.sidebar:
    st.header("🚀 Разгон")
    # 5000/сек в облаке не выйдет, но 200-500 попробовать можно
    concurrent_tasks = st.slider("Параллельные запросы", 10, 200, 50)
    batch_size = 50 # Фиксировано для Thumbnails API
    target_count = st.number_input("Сколько ID проверить всего?", value=10000)

if 'results' not in st.session_state:
    st.session_state.results = []

# --- Асинхронное ядро ---
async def check_id_batch(session, progress_bar, status_text):
    checked = 0
    found = 0
    
    while checked < target_count:
        tasks = []
        # Формируем пачки запросов
        for _ in range(concurrent_tasks):
            ids = [random.randint(1000000000, 5000000000) for _ in range(batch_size)]
            ids_str = ",".join(map(str, ids))
            url = f"https://thumbnails.roblox.com/v1/places/gameicons?placeIds={ids_str}&returnPolicy=PlaceHolder&size=50x50&format=Png&isCircular=false"
            tasks.append(session.get(url))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for resp in responses:
            if isinstance(resp, aiohttp.ClientResponse) and resp.status == 200:
                data = await resp.json()
                items = data.get("data", [])
                for item in items:
                    if item.get("state") == "Completed":
                        t_id = item.get("targetId")
                        # Быстрая проверка деталей
                        async with session.get(f"https://economy.roblox.com/v2/assets/{t_id}/details") as det_resp:
                            if det_resp.status == 200:
                                d = await det_resp.json()
                                if d.get("AssetTypeId") == 9:
                                    res = {"ID": t_id, "Name": d.get("Name"), "Time": time.strftime("%H:%M:%S")}
                                    st.session_state.results.append(res)
                                    found += 1
            elif isinstance(resp, aiohttp.ClientResponse) and resp.status == 429:
                status_text.warning("⚠️ Rate limit hit! Slowing down...")
                await asyncio.sleep(2)
        
        checked += (concurrent_tasks * batch_size)
        progress_bar.progress(min(checked / target_count, 1.0))
        status_text.text(f"Проверено: {checked:,} | Найдено: {found}")
        
        # Минимальная пауза, чтобы интерфейс Streamlit не "умер"
        await asyncio.sleep(0.01)

# --- Кнопка запуска ---
if st.button("🔥 ЗАПУСК НА МАКСИМУМ"):
    async def run_scanner():
        async with aiohttp.ClientSession() as session:
            await check_id_batch(session, progress_bar, status_text)

    progress_bar = st.progress(0)
    status_text = st.empty()
    
    asyncio.run(run_scanner())
    st.balloons()

# Вывод результатов
if st.session_state.results:
    st.write("### 🏆 Находки")
    df = pd.DataFrame(st.session_state.results)
    st.dataframe(df, use_container_width=True)
