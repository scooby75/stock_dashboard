import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.grid import grid

def build_sidebar():
    # st.image("images/logo-250-100-transparente.png")
    ticker_list = pd.read_csv("tickers_ibra.csv", index_col=0)
    tickers = st.multiselect(label="Selecione as Empresas", options=ticker_list, placeholder='Códigos')
    tickers = [t + ".SA" for t in tickers]
    start_date = st.date_input("De", format="DD/MM/YYYY", value=datetime(2023, 1, 2))
    end_date = st.date_input("Até", format="DD/MM/YYYY", value=datetime.today())

    if tickers:
        prices = yf.download(tickers, start=start_date, end=end_date)["Adj Close"]

        if prices.empty:
            st.warning("Nenhum dado encontrado para os tickers e intervalo de datas selecionados.")
            return None, None

        # Verificar se prices é uma Series (caso apenas um ticker seja selecionado) e transformá-la em DataFrame
        if isinstance(prices, pd.Series):
            prices = prices.to_frame()
            prices.columns = [tickers[0].rstrip(".SA")]

        # Remover ".SA" dos nomes das colunas e adicionar coluna IBOV
        prices.columns = prices.columns.str.rstrip(".SA")
        prices['IBOV'] = yf.download("^BVSP", start=start_date, end=end_date)["Adj Close"]

        return tickers, prices
    return None, None

def build_main(tickers, prices):
    weights = np.ones(len(tickers)) / len(tickers)
    prices['portfolio'] = prices.drop("IBOV", axis=1) @ weights
    norm_prices = 100 * prices / prices.iloc[0]
    returns = prices.pct_change()[1:]
    vols = returns.std() * np.sqrt(252)
    rets = (norm_prices.iloc[-1] - 100) / 100

    # Exibir uma tabela interativa com dados de retorno e volatilidade
    st.subheader("Tabela de Retorno e Volatilidade")
    summary_df = pd.DataFrame({
        'Ticker': prices.columns,
        'Retorno (%)': rets.values * 100,
        'Volatilidade (%)': vols.values * 100
    }).set_index('Ticker')
    st.dataframe(summary_df.style.format({'Retorno (%)': "{:.2f}", 'Volatilidade (%)': "{:.2f}"}))

    # Ajuste do Grid
    columns_per_row = min(4, len(tickers) + 1)  # Máximo de 4 colunas por linha para melhor visualização
    mygrid = grid(*[1]*columns_per_row, vertical_align="top")
    for i, t in enumerate(prices.columns):
        c = mygrid[i % columns_per_row]
        c.subheader(t, divider="red")
        colA, colB, colC = c.columns(3)
        if t == "portfolio":
            colA.image("images/pie-chart-dollar-svgrepo-com.svg")
        elif t == "IBOV":
            colA.image("images/pie-chart-svgrepo-com.svg")
        else:
            colA.image(f'https://raw.githubusercontent.com/thefintz/icones-b3/main/icones/{t}.png', width=85)
        colB.metric(label="Retorno", value=f"{rets[t]:.0%}")
        colC.metric(label="Volatilidade", value=f"{vols[t]:.0%}")
        style_metric_cards(background_color='rgba(255,255,255,0)')

    # Exibir gráficos
    col1, col2 = st.columns(2, gap='large')
    with col1:
        st.subheader("Desempenho Relativo")
        st.line_chart(norm_prices, height=600)

    with col2:
        st.subheader("Risco-Retorno")
        fig = px.scatter(
            x=vols,
            y=rets,
            text=vols.index,
            color=rets / vols,
            color_continuous_scale=px.colors.sequential.Bluered_r
        )
        fig.update_traces(
            textfont_color='white',
            marker=dict(size=45),
            textfont_size=10,
        )
        fig.layout.yaxis.title = 'Retorno Total'
        fig.layout.xaxis.title = 'Volatilidade (anualizada)'
        fig.layout.height = 600
        fig.layout.xaxis.tickformat = ".0%"
        fig.layout.yaxis.tickformat = ".0%"
        fig.layout.coloraxis.colorbar.title = 'Sharpe'
        st.plotly_chart(fig, use_container_width=True)


st.set_page_config(layout="wide")

with st.sidebar:
    tickers, prices = build_sidebar()

st.title('Dash B3')
if tickers:
    build_main(tickers, prices)
