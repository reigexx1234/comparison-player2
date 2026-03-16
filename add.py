import streamlit as st
import pandas as pd
import soccerdata as sd

# Настройка страницы
st.set_page_config(page_title="Football Scout Pro", layout="wide")

# Функция безопасного подключения
@st.cache_resource
def get_fbref():
    try:
        # Добавляем параметр no_cache=True внутри, если библиотека поддерживает, 
        # или просто инициализируем
        return sd.FBref()
    except Exception as e:
        st.error(f"Сетевая ошибка сервера данных. Попробуйте нажать Reboot в меню. Ошибка: {e}")
        return None

# Функция загрузки списка
@st.cache_data(ttl=86400)
def get_player_list():
    fb = get_fbref()
    if fb is None:
        return {"Ошибка загрузки (введите ID вручную)": "none"}
    try:
        # Ограничиваем выборку только топ-лигами для стабильности
        df = fb.read_player_season_stats(stat_type="standard")
        df = df.reset_index()
        df['display_name'] = df['player'].astype(str) + " (" + df['Squad'].astype(str) + ")"
        return pd.Series(df.player_id.values, index=df.display_name).to_dict()
    except:
        return {"Список пуст (используйте ручной ввод)": "none"}

# --- ИНТЕРФЕЙС ---
st.title("⚽ Football Scout Professional")

PLAYER_DB = get_player_list()
player_names = sorted(list(PLAYER_DB.keys()))

st.sidebar.header("Поиск")

# Поле выбора и ручной ввод
p1_sel = st.sidebar.selectbox("Игрок №1:", player_names)
p1_id_manual = st.sidebar.text_input("Или ID №1 (например, 42fd4c3c):")

st.sidebar.markdown("---")

p2_sel = st.sidebar.selectbox("Игрок №2:", player_names, index=min(1, len(player_names)-1))
p2_id_manual = st.sidebar.text_input("Или ID №2:")

# Выбор итогового ID
id1 = p1_id_manual.strip() if p1_id_manual else PLAYER_DB.get(p1_sel)
id2 = p2_id_manual.strip() if p2_id_manual else PLAYER_DB.get(p2_sel)

mode = st.sidebar.radio("Режим:", ["Сезон", "Матчи"])

if st.sidebar.button("Сравнить"):
    if not id1 or id1 == "none" or not id2 or id2 == "none":
        st.warning("Выберите игроков или введите их ID.")
    else:
        fb = get_fbref()
        if fb:
            with st.spinner("Сбор данных..."):
                try:
                    if mode == "Сезон":
                        stats = fb.read_player_season_stats(stat_type="standard").reset_index()
                        # Фильтруем через loc для надежности
                        d1 = stats[stats['player_id'] == id1].iloc[-1]
                        d2 = stats[stats['player_id'] == id2].iloc[-1]
                        
                        st.subheader("📊 Результаты")
                        col1, col2 = st.columns(2)
                        col1.metric(f"Голы {d1['player']}", int(d1['Gls']))
                        col2.metric(f"Голы {d2['player']}", int(d2['Gls']))
                        
                        res = pd.DataFrame({
                            "Метрика": ["Клуб", "Матчи", "xG"],
                            "Игрок 1": [d1['Squad'], d1['MP'], d1['xG']],
                            "Игrow 2": [d2['Squad'], d2['MP'], d2['xG']]
                        })
                        st.table(res)
                    else:
                        logs = fb.read_player_match_logs(stat_type="summary").reset_index()
                        l1 = logs[logs['player_id'] == id1].tail(5)
                        l2 = logs[logs['player_id'] == id2].tail(5)
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"**Последние игры игрока 1**")
                            st.dataframe(l1[['Date', 'Opponent', 'Gls', 'xG']], hide_index=True)
                        with c2:
                            st.write(f"**Последние игры игрока 2**")
                            st.dataframe(l2[['Date', 'Opponent', 'Gls', 'xG']], hide_index=True)
                except Exception as e:
                    st.error(f"Данные не найдены. Проверьте правильность ID или попробуйте позже. (Ошибка: {e})")
