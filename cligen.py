import streamlit as st
import requests
import random
import time

# --- Настройка страницы ---
st.set_page_config(page_title="Roblox Place Finder", page_icon="🎲")

st.title("🎲 Roblox Random Place Finder")
st.markdown("Этот инструмент ищет случайные игры в Roblox, проверяя ID.")

# --- Боковая панель с настройками ---
with st.sidebar:
    st.header("⚙️ Настройки")
    min_id = st.number_input("Минимальный ID", value=10000000, step=100000)
    max_id = st.number_input("Максимальный ID", value=90000000000, step=100000)
    attempts = st.slider("Сколько ID проверять за один раз?", 1, 50, 10)
    
    st.info("⚠️ Примечание: Большинство ID могут быть пустыми или удаленными.")

# --- Кнопка запуска ---
if st.button("🚀 Начать поиск"):
    st.write("---")
    
    # Создаем контейнер для статус-бара
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    found_count = 0
    
    for i in range(attempts):
        # Обновляем прогресс
        progress = (i + 1) / attempts
        progress_bar.progress(progress)
        
        # Генерируем случайный ID
        current_id = random.randint(min_id, max_id)
        status_text.text(f"Проверяем ID: {current_id}...")
        
        try:
            # Делаем запрос к API Roblox (получение информации о плейсе)
            # Используем официальный API для мульти-get (он надежнее) или простой get
            url = f"https://games.roblox.com/v1/games/multiget-place-details?placeIds={current_id}"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Если список не пуст, значит игра найдена
                if data and len(data) > 0 and 'placeId' in data[0]:
                    game_info = data[0]
                    name = game_info.get('name', 'Без названия')
                    url = game_info.get('url', f"https://www.roblox.com/games/{current_id}/")
                    
                    st.success(f"✅ НАЙДЕНО! ID: {current_id}")
                    st.write(f"**Название:** {name}")
                    st.link_button("🎮 Открыть игру", url)
                    st.write("---")
                    found_count += 1
                else:
                    # Раскомментируй строку ниже, если хочешь видеть неудачные попытки
                    # st.warning(f"❌ Пусто: {current_id}")
                    pass
            else:
                st.error(f"Ошибка сети (Code {response.status_code})")
                
        except Exception as e:
            st.error(f"Ошибка скрипта: {e}")
        
        # Небольшая задержка, чтобы не получить бан по IP
        time.sleep(0.1)

    status_text.text("Готово!")
    
    if found_count == 0:
        st.warning("Ничего не найдено в этой попытке. Попробуйте еще раз!")
    else:
        st.balloons()
