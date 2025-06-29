import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from mapping import team_mapping

st.set_page_config(layout="wide")
st.title("NFL Big Data Bowl 2025 - Análise Interativa")

# Carregando os arquivos da pasta 'dataset'
games_df = pd.read_csv("dataset/games.csv")
plays_df = pd.read_csv("dataset/plays.csv")
players_df = pd.read_csv("dataset/players.csv")
player_play_df = pd.read_csv("dataset/player_play.csv")
tracking_df = pd.read_csv("dataset/tracking_week_1.csv")

# Convertendo a data para datetime e formatando para pt-BR
games_df['gameDate'] = pd.to_datetime(games_df['gameDate'], format="%m/%d/%Y")
games_df['gameDateBr'] = games_df['gameDate'].dt.strftime("%d/%m/%Y")

# Criar colunas com nome completo dos times
games_df['homeTeamFull'] = games_df['homeTeamAbbr'].map(lambda x: team_mapping.get(x, {}).get('nome', x))
games_df['visitorTeamFull'] = games_df['visitorTeamAbbr'].map(lambda x: team_mapping.get(x, {}).get('nome', x))
games_df['jogo_str'] = games_df['gameDateBr'] + " - " + games_df['homeTeamFull'] + " x " + games_df['visitorTeamFull']

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

        # Filtro de jogada
        game_plays = plays_df[plays_df['gameId'] == game_id]
        play_ids = sorted(game_plays['playId'].unique())
        play_id = st.sidebar.selectbox("Escolha uma jogada (playId)", play_ids)

        # Tracking e filtro de jogador
        track_play = tracking_df[(tracking_df['gameId'] == game_id) & (tracking_df['playId'] == play_id)]
        jogadores_disponiveis = track_play['displayName'].dropna().unique()
        jogador_escolhido = st.sidebar.selectbox("Filtrar por jogador (opcional)", ["Todos"] + list(jogadores_disponiveis))

        # ----------------- CARDS -----------------
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Time Visitante", value=nome_visitante)
        with col2:
            st.metric(label="Time da Casa", value=nome_casa)
        with col3:
            principal = track_play['displayName'].value_counts().idxmax() if not track_play.empty else "N/A"
            st.metric(label="Jogador com mais frames", value=principal)

        st.subheader("Visualização da Jogada Selecionada")

        if jogador_escolhido != "Todos":
            track_play = track_play[track_play['displayName'] == jogador_escolhido]

        # Preparar cores customizadas
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
    st.sidebar.selectbox("Escolha uma jogada (playId)", ["Selecione um jogo primeiro"], disabled=True)
    st.sidebar.selectbox("Filtrar por jogador (opcional)", ["Selecione um jogo primeiro"], disabled=True)
    st.info("Selecione um jogo na barra lateral para liberar os filtros de jogada e jogador.")
