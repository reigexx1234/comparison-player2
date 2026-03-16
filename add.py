import streamlit as st
import pandas as pd
import soccerdata as sd

st.set_page_config(page_title="Football Scout Pro", layout="wide")

# Функция для безопасного создания объекта FBref
@st.cache_resource
def get_fbref_connection():
    try:
        # Пытаемся инициализировать библиотеку
        return sd.FBref()
    except Exception as e:
        st.error(f"Ошибка подключения к базе данных: {e}")
        return None

# Функция загрузки списка игроков
@st.cache_data(ttl=86400)
def load_all_players():
    fb = get_fbref_connection()
    if fb is None:
        return {"Lionel Messi (Inter Miami)": "d70ce98e", "Kylian Mbappé (Real Madrid)": "42fd4c3c"}
    try:
        df = fb.read_player_season_stats(stat_type="standard")
        df = df.reset_index()
        df['display_name'] = df['player'] + " (" + df['Squad'].astype(str) + ")"
        return pd.Series(df.player_id.values, index=df.display_name).to_dict()
    except:
        return {"Lionel Messi (Inter Miami)": "d70ce98e", "Kylian Mbappé (Real Madrid)": "42fd4c3c"}

# Функция получения статистики
@st.cache_data(ttl=3600)
def get_player_stats(p_id, mode="Season"):
    fb = get_fbref_connection()
    if fb is None: return None
    try:
        if mode == "Matches":
            df = fb.read_player_match_logs(stat_type="summary")
            df = df.reset_index()
            return df[df['player_id'] == p_id].tail(5)
        else:
            df = fb.read_player_season_stats(stat_type="standard")
            df = df.reset_index()
            return df[df['player_id'] == p_id].iloc[-1]
    except:
        return None

# --- ИНТЕРФЕЙС ---
st.title("⚽ Football Scout Professional")

with st.spinner("Синхронизация данных..."):
    PLAYER_DB = load_all_players()
    player_names = sorted(list(PLAYER_DB.keys()))

st.sidebar.header("Параметры")
p1_name = st.sidebar.selectbox("Игрок №1:", player_names, index=0)
p2_name = st.sidebar.selectbox("Игрок №2:", player_names, index=min(1, len(player_names)-1))

analysis_mode = st.sidebar.radio("Данные:", ["Итоги сезона", "Последние 5 игр"])

if st.sidebar.button("Анализировать"):
    id1, id2 = PLAYER_DB[p1_name], PLAYER_DB[p2_name]
    
    if analysis_mode == "Итоги сезона":
        d1, d2 = get_player_stats(id1, "Season"), get_player_stats(id2, "Season")
        if d1 is not None and d2 is not None:
            metrics = {
                "Показатель": ["Команда", "Матчи", "Голы", "xG"],
                p1_name: [d1['Squad'], d1['MP'], d1['Gls'], d1['xG']],
                p2_name: [d2['Squad'], d2['MP'], d2['Gls'], d2['xG']]
            }
            st.table(pd.DataFrame(metrics))
        else:
            st.warning("Сервер статистики временно недоступен. Попробуйте позже.")
    else:
        l1, l2 = get_player_stats(id1, "Matches"), get_player_stats(id2, "Matches")
        c1, c2 = st.columns(2)
        for col, log, name in zip([c1, c2], [l1, l2], [p1_name, p2_name]):
            with col:
                st.subheader(name)
                if log is not None: st.dataframe(log[['Date', 'Opponent', 'Gls', 'xG']], hide_index=True)
