import streamlit as st
import pandas as pd
import soccerdata as sd

st.set_page_config(page_title="Football Scout Pro", layout="wide")

@st.cache_resource
def get_fbref_connection():
    try:
        return sd.FBref()
    except Exception as e:
        return None

@st.cache_data(ttl=86400)
def load_all_players():
    fb = get_fbref_connection()
    if fb is None:
        return {"Загрузка не удалась (введите ID вручную)": "none"}
    try:
        df = fb.read_player_season_stats(stat_type="standard")
        df = df.reset_index()
        df['display_name'] = df['player'] + " (" + df['Squad'].astype(str) + ")"
        return pd.Series(df.player_id.values, index=df.display_name).to_dict()
    except:
        return {"Поиск временно недоступен": "none"}

# --- ИНТЕРФЕЙС ---
st.title("⚽ Football Scout Professional")

PLAYER_DB = load_all_players()
player_names = sorted(list(PLAYER_DB.keys()))

st.sidebar.header("Параметры поиска")

# Способ 1: Выбор из списка
p1_select = st.sidebar.selectbox("Игрок №1 (Поиск):", player_names)
# Способ 2: Ручной ввод ID (если поиск не нашел игрока)
p1_manual = st.sidebar.text_input("Или введите ID №1 вручную (например, 42fd4c3c):")

st.sidebar.markdown("---")

p2_select = st.sidebar.selectbox("Игрок №2 (Поиск):", player_names, index=min(1, len(player_names)-1))
p2_manual = st.sidebar.text_input("Или введите ID №2 вручную:")

# Логика выбора ID
id1 = p1_manual if p1_manual else PLAYER_DB.get(p1_select)
id2 = p2_manual if p2_manual else PLAYER_DB.get(p2_select)

analysis_mode = st.sidebar.radio("Данные:", ["Итоги сезона", "Последние 5 игр"])

if st.sidebar.button("Анализировать"):
    if not id1 or id1 == "none" or not id2 or id2 == "none":
        st.error("Пожалуйста, выберите игрока из списка или введите ID вручную.")
    else:
        fb = get_fbref_connection()
        if fb is None:
            st.error("Проблема с подключением к FBref. Попробуйте обновить страницу.")
        else:
            with st.spinner("Получение данных..."):
                try:
                    if analysis_mode == "Итоги сезона":
                        # Загружаем данные сезона
                        df_s = fb.read_player_season_stats(stat_type="standard").reset_index()
                        d1 = df_s[df_s['player_id'] == id1].iloc[-1]
                        d2 = df_s[df_s['player_id'] == id2].iloc[-1]
                        
                        st.subheader("📊 Сравнение показателей")
                        res = pd.DataFrame({
                            "Параметр": ["Команда", "Матчи", "Голы", "xG"],
                            "Игрок 1": [d1['Squad'], d1['MP'], d1['Gls'], d1['xG']],
                            "Игрок 2": [d2['Squad'], d2['MP'], d2['Gls'], d2['xG']]
                        })
                        st.table(res)
                    else:
                        # Логи матчей
                        df_m = fb.read_player_match_logs(stat_type="summary").reset_index()
                        l1 = df_m[df_m['player_id'] == id1].tail(5)
                        l2 = df_m[df_m['player_id'] == id2].tail(5)
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            st.subheader("Игрок 1")
                            st.dataframe(l1[['Date', 'Opponent', 'Gls', 'xG']], hide_index=True)
                        with c2:
                            st.subheader("Игрок 2")
                            st.dataframe(l2[['Date', 'Opponent', 'Gls', 'xG']], hide_index=True)
                except Exception as e:
                    st.error(f"Данные для этих ID не найдены или сервер перегружен.")
