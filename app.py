import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from datetime import datetime
from streamlit_extras.metric_cards import style_metric_cards
from streamlit_extras.grid import grid


def build_sidebar():
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

        if isinstance(prices, pd.Series):
            prices = prices.to_frame()
            prices.columns = [tickers[0].rstrip(".SA")]

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

    # Layout configurado com grid
    mygrid = grid(5, 5, 5, 5, 5, 5, vertical_align="top")
    for i, t in enumerate(prices.columns):
        c = mygrid[i % 5]  # Ajustando para exibir corretamente nas colunas
        with c:
            st.markdown(
                f"""
                <div style="
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-radius: 10px;
                    box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
                    display: flex;
                    align-items: center;
                    justify-content: space-around;">
                    <div style="text-align: center;">
                        <img src="{'https://raw.githubusercontent.com/thefintz/icones-b3/main/icones/' + t + '.png' if t not in ['IBOV', 'portfolio'] else 'images/pie-chart-svgrepo-com.svg' if t == 'IBOV' else 'images/pie-chart-dollar-svgrepo-com.svg'}" width="60" style="margin-right: 10px;"/>
                        <h4 style="color: #007bff; margin: 5px 0 0;">{t}</h4>
                    </div>
                    <div style="display: flex; flex-direction: column;">
                        <span style="font-size: 0.9em; font-weight: bold;">Retorno</span>
                        <span style="color: #28a745; font-size: 1.2em;">{rets[t]:.0%}</span>
                    </div>
                    <div style="display: flex; flex-direction: column;">
                        <span style="font-size: 0.9em; font-weight: bold;">Volatilidade</span>
                        <span style="color: #dc3545; font-size: 1.2em;">{vols[t]:.0%}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
    style_metric_cards(background_color='rgba(255,255,255,0)')

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
