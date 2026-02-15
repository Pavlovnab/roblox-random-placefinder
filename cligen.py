import streamlit as st
import requests
import random
import time

st.set_page_config(page_title="Roblox Place Finder", page_icon="🎲")
st.title("🎲 Roblox Random Place Finder (Fix 401)")

# --- Настройки ---
with st.sidebar:
    st.header("⚙️ Настройки")
    min_id = st.number_input("Минимальный ID", value=10000000, step=100000)
    max_id = st.number_input("Максимальный ID", value=100000000, step=100000)
    # Уменьшаем кол-во, чтобы не словить бан слишком быстро
    attempts = st.slider("Проверок за раз", 1, 20, 5) 

# --- Самое важное: Заголовки, чтобы притвориться браузером ---
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.roblox.com/',
    'Origin': 'https://www.roblox.com'
}

if st.button("🚀 Начать поиск"):
    st.write("---")
    progress_bar = st.progress(0)
    status_text = st.empty()
    found_count = 0
    
    for i in range(attempts):
        progress_bar.progress((i + 1) / attempts)
        
        # Генерируем ID
        current_id = random.randint(min_id, max_id)
        status_text.text(f"🔍 Проверяем ID: {current_id}")
        
        try:
            # Используем API получения деталей по ID
            url = f"https://games.roblox.com/v1/games/multiget-place-details?placeIds={current_id}"
            
            # ВАЖНО: передаем headers=headers
            response = requests.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                # Проверяем, что пришел не пустой список
                if data and isinstance(data, list) and len(data) > 0:
                    game = data[0]
                    # Проверяем, что это не удаленная игра (обычно у удаленных нет имени или reasonProhibited)
                    if 'name' in game and game['name'] != "[ Content Deleted ]":
                        st.success(f"✅ НАЙДЕНО! ID: {current_id}")
                        st.write(f"**Имя:** {game.get('name')}")
                        st.write(f"**Онлайн:** {game.get('playing', 0)}")
                        link = f"https://www.roblox.com/games/{current_id}/"
                        st.link_button("🎮 Открыть", link)
                        found_count += 1
            elif response.status_code == 401:
                st.warning("⚠️ Roblox требует авторизацию (Cookie). Попробуйте позже.")
                break # Останавливаем, если нас заблокировали
            elif response.status_code == 429:
                st.error("⛔ Слишком много запросов! Ждем 5 секунд...")
                time.sleep(5)
            
        except Exception as e:
            st.error(f"Ошибка: {e}")
        
        # Пауза между запросами обязательна, чтобы не банили
        time.sleep(0.5)

    status_text.text("Готово!")
    if found_count == 0:
        st.info("В этой попытке ничего интересного не найдено.")
