import os
import zipfile
import gdown
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from mapping import team_mapping

# ===== CONFIGURAÇÃO =====
dataset_folder = "dataset"
zip_path = "dataset.zip"
file_id = "1yz7vn71tUKTU7scd_6nf6vvRXKxAVCA6"
zip_url = f"https://drive.google.com/uc?id={file_id}"

os.makedirs(dataset_folder, exist_ok=True)

# ===== VERIFICAR E BAIXAR DATASET =====
def verificar_e_baixar_dataset():
    expected_files = ["games.csv", "plays.csv", "players.csv", "player_play.csv", "tracking_week_1.csv"]
    missing_files = [f for f in expected_files if not os.path.exists(os.path.join(dataset_folder, f))]

    if missing_files:
        st.write("\U0001F4C2 Arquivos ausentes. Iniciando download...")
        with st.spinner("\U0001F4E5 Baixando e extraindo o dataset... Isso pode levar alguns minutos."):
            st.write("\U0001F517 Baixando do Google Drive...")
            gdown.download(zip_url, zip_path, quiet=False)
            st.write("✅ Download concluído. Extraindo...")

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(".")
            os.remove(zip_path)

        st.success("✅ Dataset baixado e extraído com sucesso!")

verificar_e_baixar_dataset()

st.set_page_config(layout="wide")
st.title("NFL Big Data Bowl 2025 - Análise Interativa")

# ====== CARREGAR DADOS ======
games_df = pd.read_csv(os.path.join(dataset_folder, "games.csv"))
plays_df = pd.read_csv(os.path.join(dataset_folder, "plays.csv"))
players_df = pd.read_csv(os.path.join(dataset_folder, "players.csv"))
player_play_df = pd.read_csv(os.path.join(dataset_folder, "player_play.csv"))
tracking_df = pd.read_csv(os.path.join(dataset_folder, "tracking_week_1.csv"))

# ====== FORMATAR DADOS ======
games_df['gameDate'] = pd.to_datetime(games_df['gameDate'], format="%m/%d/%Y")
games_df['gameDateBr'] = games_df['gameDate'].dt.strftime("%d/%m/%Y")
games_df['homeTeamFull'] = games_df['homeTeamAbbr'].map(lambda x: team_mapping.get(x, {}).get('nome', x))
games_df['visitorTeamFull'] = games_df['visitorTeamAbbr'].map(lambda x: team_mapping.get(x, {}).get('nome', x))
games_df['jogo_str'] = games_df['gameDateBr'] + " - " + games_df['homeTeamFull'] + " x " + games_df['visitorTeamFull']

# ====== FILTROS ======
st.sidebar.header("Filtros")
jogo_escolhido = st.sidebar.selectbox("Escolha o jogo", ["Selecione..."] + list(games_df['jogo_str']))

if jogo_escolhido != "Selecione...":
    jogo_final = games_df[games_df['jogo_str'] == jogo_escolhido]
    if not jogo_final.empty:
        game_id = jogo_final['gameId'].values[0]
        time_casa = jogo_final['homeTeamAbbr'].values[0]
        time_visitante = jogo_final['visitorTeamAbbr'].values[0]
        nome_casa = team_mapping.get(time_casa, {}).get('nome', time_casa)
        nome_visitante = team_mapping.get(time_visitante, {}).get('nome', time_visitante)
        data_escolhida = jogo_final['gameDateBr'].values[0]

        game_plays = plays_df[plays_df['gameId'] == game_id]
        play_ids = sorted(game_plays['playId'].unique())
        play_id = st.sidebar.selectbox("Escolha uma jogada (playId)", play_ids)

        track_play = tracking_df[(tracking_df['gameId'] == game_id) & (tracking_df['playId'] == play_id)]
        jogadores_disponiveis = track_play['displayName'].dropna().unique()
        jogador_escolhido = st.sidebar.selectbox("Filtrar por jogador (opcional)", ["Todos"] + list(jogadores_disponiveis))

        merged = pd.merge(player_play_df, players_df, on="nflId", how="left")
        merged = pd.merge(merged, track_play[['nflId', 'club']].drop_duplicates(), on="nflId", how="left")
        merged_play = merged[(merged['gameId'] == game_id) & (merged['playId'] == play_id)]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"<div style='font-size: 0.9rem;'>🏈 <strong>Time Visitante:</strong> {nome_visitante}</div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='font-size: 0.9rem;'>🏠 <strong>Time da Casa:</strong> {nome_casa}</div>", unsafe_allow_html=True)
        with col3:
            principal = merged_play.loc[merged_play['rushingYards'].idxmax(), 'displayName'] if not merged_play.empty else "N/A"
            st.markdown(f"<div style='font-size: 0.9rem;'>🏃‍♂️ <strong>Jogador com mais jardas corridas:</strong> {principal}</div>", unsafe_allow_html=True)
        with col4:
            total_jogadores = track_play['nflId'].nunique()
            st.markdown(f"<div style='font-size: 0.9rem;'>👥 <strong>Jogadores na jogada:</strong> {total_jogadores}</div>", unsafe_allow_html=True)

        col5, col6 = st.columns(2)
        with col5:
            j_passe = merged_play['passingYards'].sum()
            st.markdown(f"<div style='font-size: 0.9rem;'>🎯 <strong>Total Jardas de Passe:</strong> {j_passe if j_passe > 0 else 'Nenhuma'}</div>", unsafe_allow_html=True)
        with col6:
            j_receb = merged_play['receivingYards'].sum()
            st.markdown(f"<div style='font-size: 0.9rem;'>📥 <strong>Total Jardas Recebidas:</strong> {j_receb if j_receb > 0 else 'Nenhuma'}</div>", unsafe_allow_html=True)

        st.subheader("Visualização da Jogada Selecionada")
        if jogador_escolhido != "Todos":
            track_play = pd.concat([
                track_play[track_play['displayName'] == jogador_escolhido],
                track_play[track_play['club'] == 'BALL']
            ])

        color_map = {
            abbr: team_mapping[abbr]['cor'] for abbr in track_play['club'].dropna().unique() if abbr in team_mapping
        }
        track_play['club'] = track_play['club'].fillna('BALL')

        if not track_play.empty and 'frameId' in track_play.columns:
            track_play = track_play.sort_values(by='frameId')
            fig = px.scatter(
                track_play[track_play['club'] != 'BALL'],
                x="x", y="y",
                color="club",
                color_discrete_map=color_map,
                animation_frame="frameId",
                animation_group="nflId",
                hover_name="displayName",
                title=f"Movimento da jogada - Jogo: {nome_casa} x {nome_visitante} ({data_escolhida})",
                range_x=[0, 120],
                range_y=[0, 53.3],
                height=600
            )

            fig.layout.updatemenus[0].buttons[0].args[1]['frame']['duration'] = 100

            bola = track_play[track_play['club'] == 'BALL']
            if not bola.empty:
                for frame in bola['frameId'].unique():
                    bola_frame = bola[bola['frameId'] == frame].iloc[0]
                    fig.add_layout_image(
                        dict(
                            source="src/assets/icons/ball.png",
                            x=bola_frame['x'],
                            y=bola_frame['y'],
                            xref="x",
                            yref="y",
                            sizex=2,
                            sizey=2,
                            xanchor="center",
                            yanchor="middle",
                            layer="above"
                        )
                    )

            for jarda in range(10, 110, 10):
                fig.add_shape(type="line", x0=jarda, x1=jarda, y0=0, y1=53.3,
                              line=dict(color="lightgray", width=1, dash="dot"))

            fig.update_yaxes(scaleanchor="x", scaleratio=1)
            st.plotly_chart(fig, use_container_width=True, key=f"plot_{game_id}_{play_id}_{jogador_escolhido}")
        else:
            st.warning("Nenhum dado disponível para gerar a animação.")

        st.subheader("Resumo estatístico da jogada")

        stats_cols = {
            'displayName': 'Jogador',
            'position': 'Posição',
            'club': 'Time',
            'rushingYards': 'Jardas Corridas',
            'passingYards': 'Jardas de Passe',
            'receivingYards': 'Jardas Recebidas',
            'soloTackle': 'Tackles Individuais',
            'tackleForALoss': 'Tackles para Perda',
            'interceptionYards': 'Jardas de Interceptação'
        }

        full_stats = merged_play[list(stats_cols.keys())].fillna(0)
        full_stats.rename(columns=stats_cols, inplace=True)

        if not full_stats.empty:
            st.dataframe(full_stats)
        else:
            st.info("Nenhuma estatística encontrada para essa jogada.")
    else:
        st.warning("Nenhum jogo encontrado para a seleção.")
else:
    st.sidebar.selectbox("Escolha uma jogada (playId)", ["Selecione um jogo primeiro"], disabled=True)
    st.sidebar.selectbox("Filtrar por jogador (opcional)", ["Selecione um jogo primeiro"], disabled=True)
    st.info("Selecione um jogo na barra lateral para liberar os filtros de jogada e jogador.")