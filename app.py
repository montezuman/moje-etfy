import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Konfiguracja strony
st.set_page_config(page_title="Analiza ETF", layout="wide")
st.title("📈 Analiza ETF: SWDA, EMIM, 3USL (w PLN)")
st.write("Interwał 30-minutowy. Punkt zero: 23.02.2026 r.")

if st.button('Odśwież dane now!'):
    st.cache_data.clear()

@st.cache_data(ttl=900)
def load_data():
    etfs = {'SWDA': 'SWDA.L', 'EMIM': 'EMIM.L', '3USL': '3USL.L'}
    fx_ticker = 'PLN=X'
    start_date = '2026-02-23'
    
    tickers = list(etfs.values()) + [fx_ticker]
    
    # Pobieranie danych
    df = yf.download(tickers, start=start_date, interval='30m')
    
    # Wyciąganie cen zamknięcia (bezpieczne dla nowych wersji yfinance)
    if isinstance(df.columns, pd.MultiIndex):
        if 'Close' in df.columns.levels[0]:
            data = df['Close']
        else:
            data = df.xs(df.columns.levels[0][0], level=0, axis=1)
    else:
        data = df

    # Zabezpieczenie: jeśli Yahoo Finance w ogóle nie zwróci jakiegoś tickera, tworzymy mu pustą kolumnę
    for t in tickers:
        if t not in data.columns:
            data[t] = np.nan
            
    # KLUCZOWA ZMIANA: ffill uzupełnia luki w przód, a bfill luki w tył (gdy waluta otwiera się wcześniej niż giełda)
    data = data.ffill().bfill()
    
    pln_prices = pd.DataFrame(index=data.index)
    percent_growth = pd.DataFrame(index=data.index)
    
    for name, ticker in etfs.items():
        # Zabezpieczenie, jeśli dla ETF-a nie ma absolutnie żadnych danych
        if data[ticker].isna().all() or data[fx_ticker].isna().all():
            pln_prices[name] = 0.0
            percent_growth[name] = 0.0
        else:
            pln_prices[name] = data[ticker] * data[fx_ticker]
            # Ponieważ zastosowaliśmy bfill, pierwszy wiersz to zawsze prawdziwa, startowa cena
            first_price = pln_prices[name].iloc[0] 
            percent_growth[name] = ((pln_prices[name] - first_price) / first_price) * 100
            
    return pln_prices, percent_growth

# Generowanie wykresów
try:
    with st.spinner('Pobieranie najświeższych danych z giełdy...'):
        pln_prices, percent_growth = load_data()
        
        # Bezpieczne pobieranie najnowszej ceny
        def get_last(df, col):
            return df[col].iloc[-1] if not df.empty and col in df.columns else 0.0

        cur_swda_p = get_last(pln_prices, 'SWDA')
        cur_swda_g = get_last(percent_growth, 'SWDA')
        cur_emim_p = get_last(pln_prices, 'EMIM')
        cur_emim_g = get_last(percent_growth, 'EMIM')
        cur_3usl_p = get_last(pln_prices, '3USL')
        cur_3usl_g = get_last(percent_growth, '3USL')

        titles = (
            f'1. SWDA - Cena (PLN) | Obecna: {cur_swda_p:.2f} PLN', 
            f'2. SWDA - Wzrost (%) | Obecny: {cur_swda_g:.2f}%',
            f'3. EMIM - Cena (PLN) | Obecna: {cur_emim_p:.2f} PLN', 
            f'4. EMIM - Wzrost (%) | Obecny: {cur_emim_g:.2f}%',
            f'5. 3USL - Cena (PLN) | Obecna: {cur_3usl_p:.2f} PLN', 
            f'6. 3USL - Wzrost (%) | Obecny: {cur_3usl_g:.2f}%'
        )

        fig = make_subplots(rows=6, cols=1, subplot_titles=titles, vertical_spacing=0.04)
        colors = {'SWDA': 'blue', 'EMIM': 'green', '3USL': 'red'}

        for i, name in enumerate(['SWDA', 'EMIM', '3USL']):
            fig.add_trace(go.Scatter(x=pln_prices.index, y=pln_prices[name], mode='lines', name=f'{name} PLN', line=dict(color=colors[name])), row=2*i+1, col=1)
            fig.add_trace(go.Scatter(x=percent_growth.index, y=percent_growth[name], mode='lines', name=f'{name} %', line=dict(color=colors[name], dash='dot')), row=2*i+2, col=1)

        fig.update_layout(height=1800, showlegend=False, hovermode='x unified', margin=dict(t=50, b=50, l=50, r=50))
        
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error("Napotkano problem podczas generowania aplikacji:")
    st.code(str(e))
