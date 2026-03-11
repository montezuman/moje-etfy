import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Konfiguracja wyglądu strony
st.set_page_config(page_title="Analiza ETF", layout="wide")
st.title("📈 Analiza ETF: SWDA, EMIM, 3USL (w PLN)")
st.write("Interwał 30-minutowy. Punkt zero: 23.02.2026 r.")

# Przycisk do ręcznego odświeżania
if st.button('Odśwież dane now!'):
    st.cache_data.clear()

# Funkcja pobierająca dane z "cache" żeby strona nie ładowała się bez sensu przy każdej akcji
@st.cache_data(ttl=900) # Dane odświeżają się max co 15 minut (900 sekund)
def load_data():
    etfs = {'SWDA': 'SWDA.L', 'EMIM': 'EMIM.L', '3USL': '3USL.L'}
    fx_ticker = 'PLN=X'
    start_date = '2026-02-23'
    
    data = yf.download(list(etfs.values()) + [fx_ticker], start=start_date, interval='30m')['Close']
    data = data.ffill()
    
    pln_prices = pd.DataFrame(index=data.index)
    for name, ticker in etfs.items():
        pln_prices[name] = data[ticker] * data[fx_ticker]
        
    percent_growth = pd.DataFrame(index=pln_prices.index)
    for name in etfs.keys():
        first_valid_idx = pln_prices[name].first_valid_index()
        if first_valid_idx is not None:
            first_price = pln_prices[name].loc[first_valid_idx]
            percent_growth[name] = ((pln_prices[name] - first_price) / first_price) * 100
            
    return pln_prices, percent_growth, etfs

# Renderowanie z paskiem postępu
with st.spinner('Pobieranie najświeższych danych z giełdy...'):
    pln_prices, percent_growth, etfs = load_data()

    # Pobieranie aktualnych wartości
    cur_swda_p = pln_prices['SWDA'].iloc[-1]
    cur_swda_g = percent_growth['SWDA'].iloc[-1]
    cur_emim_p = pln_prices['EMIM'].iloc[-1]
    cur_emim_g = percent_growth['EMIM'].iloc[-1]
    cur_3usl_p = pln_prices['3USL'].iloc[-1]
    cur_3usl_g = percent_growth['3USL'].iloc[-1]

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
        # Wykresy cen (nieparzyste wiersze: 1, 3, 5)
        fig.add_trace(go.Scatter(x=pln_prices.index, y=pln_prices[name], mode='lines', name=f'{name} PLN', line=dict(color=colors[name])), row=2*i+1, col=1)
        # Wykresy procentowe (parzyste wiersze: 2, 4, 6)
        fig.add_trace(go.Scatter(x=percent_growth.index, y=percent_growth[name], mode='lines', name=f'{name} %', line=dict(color=colors[name], dash='dot')), row=2*i+2, col=1)

    fig.update_layout(height=1800, showlegend=False, hovermode='x unified', margin=dict(t=50, b=50, l=50, r=50))
    
    # Wyświetlenie interaktywnego wykresu na stronie
    st.plotly_chart(fig, use_container_width=True)
