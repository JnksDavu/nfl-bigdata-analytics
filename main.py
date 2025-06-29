import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide")
st.title("NFL Big Data Bowl 2025 - Análise Interativa")

st.markdown("""
Esta aplicação interativa permite a análise de dados da competição NFL Big Data Bowl 2025, utilizando os datasets de jogos, jogadas, jogadores, participação em jogadas e rastreamento de movimentos.
""")

# Carregando os arquivos da pasta 'dataset'
games_df = pd.read_csv("dataset/games.csv")
plays_df = pd.read_csv("dataset/plays.csv")
players_df = pd.read_csv("dataset/players.csv")
player_play_df = pd.read_csv("dataset/player_play.csv")
tracking_df = pd.read_csv("dataset/tracking_week_1.csv")

# Convertendo a data para datetime e formatando para pt-BR
games_df['gameDate'] = pd.to_datetime(games_df['gameDate'], format="%m/%d/%Y")
games_df['gameDateBr'] = games_df['gameDate'].dt.strftime("%d/%m/%Y")

st.sidebar.header("Filtros")

# Cria coluna de descrição do jogo
games_df['jogo_str'] = games_df['gameDateBr'] + " - " + games_df['homeTeamAbbr'] + " x " + games_df['visitorTeamAbbr']

# Filtro único para seleção do jogo
jogo_escolhido = st.sidebar.selectbox("Escolha o jogo", ["Selecione..."] + list(games_df['jogo_str']))

if jogo_escolhido != "Selecione...":
    jogo_final = games_df[games_df['jogo_str'] == jogo_escolhido]
    if not jogo_final.empty:
        game_id = jogo_final['gameId'].values[0]
        time_casa = jogo_final['homeTeamAbbr'].values[0]
        time_visitante = jogo_final['visitorTeamAbbr'].values[0]
        data_escolhida = jogo_final['gameDateBr'].values[0]

        # Filtro de jogada só é habilitado após escolha do jogo
        game_plays = plays_df[plays_df['gameId'] == game_id]
        play_ids = sorted(game_plays['playId'].unique())
        play_id = st.sidebar.selectbox("Escolha uma jogada (playId)", play_ids, disabled=False)

        # Filtro de jogador só é habilitado após escolha do jogo e jogada
        track_play = tracking_df[(tracking_df['gameId'] == game_id) & (tracking_df['playId'] == play_id)]
        jogadores_disponiveis = track_play['displayName'].unique()
        jogador_escolhido = st.sidebar.selectbox("Filtrar por jogador (opcional)", ["Todos"] + list(jogadores_disponiveis), disabled=False)

        st.subheader("Visualização da Jogada Selecionada")

        # Filtra tracking se jogador for selecionado
        if jogador_escolhido != "Todos":
            track_play = track_play[track_play['displayName'] == jogador_escolhido]

        # Mostrar o campo com os jogadores
        if not track_play.empty and 'frameId' in track_play.columns:
            track_play = track_play.sort_values(by='frameId')
            fig = px.scatter(
                track_play,
                x="x",
                y="y",
                color="club",
                animation_frame="frameId",
                animation_group="nflId",
                hover_name="displayName",
                title=f"Movimento da jogada - Jogo: {time_casa} x {time_visitante} ({data_escolhida})",
                range_x=[0, 120],
                range_y=[0, 53.3],
                height=600
            )
            fig.update_yaxes(scaleanchor="x", scaleratio=1)
            st.plotly_chart(fig, use_container_width=True, key=f"plot_{game_id}_{play_id}_{jogador_escolhido}")
        else:
            st.warning("Nenhum dado disponível para gerar a animação.")

        # Análise estatística
        st.subheader("Resumo estatístico da jogada")
        merged = pd.merge(player_play_df, players_df, on="nflId", how="left")
        merged_play = merged[(merged['gameId'] == game_id) & (merged['playId'] == play_id)]
        st.dataframe(merged_play[[
            'displayName', 'position', 'rushingYards', 'passingYards', 'receivingYards',
            'soloTackle', 'tackleForALoss', 'interceptionYards'
        ]].fillna(0))
    else:
        st.warning("Nenhum jogo encontrado para a seleção.")
else:
    # Bloqueia filtros de jogada e jogador até seleção do jogo
    st.sidebar.selectbox("Escolha uma jogada (playId)", ["Selecione um jogo primeiro"], disabled=True)
    st.sidebar.selectbox("Filtrar por jogador (opcional)", ["Selecione um jogo primeiro"], disabled=True)
    st.info("Selecione um jogo na barra lateral para liberar os filtros de jogada e jogador.")
