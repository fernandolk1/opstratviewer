import streamlit as st
import yfinance as yf
from datetime import datetime
import pandas as pd
import plotly.graph_objs as go

def calculate_max_profit(strategy, premium, strike, spot_price):
    if strategy == "Long Call":
        return "Ilimitado"  # Ganancia máxima para Long Call es ilimitada si sube el precio
    elif strategy == "Short Call":
        return premium  # La ganancia máxima es la prima recibida para Short Call
    elif strategy == "Long Put":
        return max(strike - spot_price, 0) - premium  # Máxima ganancia limitada por la diferencia strike - spot
    elif strategy == "Short Put":
        return premium  # La ganancia máxima es la prima recibida para Short Put
    return 0

def calculate_chance_of_profit(strategy):
    if strategy in ["Long Call", "Short Put"]:
        return "50%"  # Ejemplo genérico
    elif strategy in ["Long Put", "Short Call"]:
        return "50%"  # Ejemplo genérico
    return "N/A"

def calculate_estimated_margin(strategy, premium, strike):
    if strategy in ["Short Put", "Short Call"]:
        return premium + (0.1 * strike * 100 * 1)  # 100 es el multiplicador y 1 es el número de contratos
    elif strategy in ["Long Call", "Long Put"]:
        return premium  # Para Long Call/Put, el margen es igual al net debit
    return "N/A"

def calculate_payoff(strategy, strike, premium, spot_prices):
    if strategy == "Long Call":
        return [max(price - strike, 0) - premium for price in spot_prices]
    elif strategy == "Short Call":
        return [premium - max(price - strike, 0) for price in spot_prices]
    elif strategy == "Long Put":
        return [max(strike - price, 0) - premium for price in spot_prices]
    elif strategy == "Short Put":
        return [premium - max(strike - price, 0) for price in spot_prices]
    return [0] * len(spot_prices)

def main():
    st.set_page_config(
        page_title="Visualizador de Estrategias de Opciones",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("📊 Visualizador de Estrategias de Opciones")
    st.caption('Creado por Fernando Guzman')
    df = None
    
    with st.sidebar:
        st.title("📊 Visualizador de Estrategias de Opciones")
        st.caption('Creado por Fernando Guzman')
        ticker = st.text_input("Ingresa el ticker:")
        
        if ticker:
            try:
                stock = yf.Ticker(ticker)
                precio_actual = stock.history(period="1d")['Close'].iloc[-1]
                st.sidebar.write(f"Precio del activo: ${precio_actual:.2f}")

                expirations = stock.options
                if expirations:
                    expirations_in_days = [
                        f"{(datetime.strptime(exp, '%Y-%m-%d') - datetime.now()).days}d ({exp})" 
                        for exp in expirations
                    ]
                    expiration_selection = st.sidebar.selectbox("Selecciona la fecha de expiración:", expirations_in_days)
                    selected_expiration = expiration_selection.split(' ')[1].strip('()')
                    options_chain = stock.option_chain(selected_expiration)
                    all_strikes = sorted(options_chain.calls['strike'].tolist())
                    strikes_above = [strike for strike in all_strikes if strike > precio_actual][:20]
                    strikes_below = [strike for strike in reversed(all_strikes) if strike < precio_actual][:20]
                    filtered_strikes = sorted(strikes_below + strikes_above)
                    selected_strike = st.sidebar.selectbox("Selecciona el strike:", filtered_strikes)
                    strategies = ["Long Call", "Long Put", "Short Call", "Short Put"]
                    selected_strategy = st.sidebar.selectbox("Selecciona una estrategia:", strategies)

                    premium = 0
                    theta_value = "N/A"
                    net_credit_debit = ""
                    if selected_strategy and selected_strike:
                        calls = options_chain.calls
                        puts = options_chain.puts
                        call_option = calls[calls['strike'] == selected_strike]
                        put_option = puts[puts['strike'] == selected_strike]

                        if selected_strategy in ["Long Call", "Short Call"]:
                            if not call_option.empty:
                                premium = call_option['lastPrice'].iloc[0]
                                theta_value = call_option['theta'].iloc[0] if 'theta' in call_option.columns else "N/A"
                        elif selected_strategy in ["Long Put", "Short Put"]:
                            if not put_option.empty:
                                premium = put_option['lastPrice'].iloc[0]
                                theta_value = put_option['theta'].iloc[0] if 'theta' in put_option.columns else "N/A"

                        if selected_strategy in ["Long Call", "Long Put"]:
                            net_credit_debit = f"Net Debit: ${premium:.2f}"
                        elif selected_strategy in ["Short Call", "Short Put"]:
                            net_credit_debit = f"Net Credit: ${premium:.2f}"

                        max_profit = calculate_max_profit(selected_strategy, premium, selected_strike, precio_actual)
                        chance_of_profit = calculate_chance_of_profit(selected_strategy)
                        estimated_margin = calculate_estimated_margin(selected_strategy, premium, selected_strike)

                        data = {
                            "Ticker": [ticker],
                            "Net Debit / Net Credit": [net_credit_debit],
                            "Max Profit": [max_profit],
                            "Chance of Profit": [chance_of_profit],
                            "Estimated Margin": [estimated_margin],
                            "Theta": [theta_value]
                        }
                        df = pd.DataFrame(data)
            except Exception as e:
                st.write("No se pudo obtener el precio o las fechas de expiración. Verifica el ticker.")

    if df is not None:
        st.write("### Resumen de la Estrategia Seleccionada")
        st.dataframe(df)

        # Generar gráfico de la estrategia después de mostrar el DataFrame
        st.write("### Visualización de la Estrategia")
        spot_prices = list(range(int(precio_actual * 0.5), int(precio_actual * 1.5)))
        payoff = calculate_payoff(selected_strategy, selected_strike, premium, spot_prices)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=spot_prices, y=payoff, mode='lines', name='Payoff', line=dict(color='royalblue', width=2)))
        
        # Agregar línea punteada continua para el strike price
        fig.add_trace(go.Scatter(
            x=[selected_strike] * len(spot_prices),
            y=[min(payoff) - 10, max(payoff) + 10],  # Extensión para que la línea sea continua
            mode='lines',
            line=dict(dash='dot', color='red', width=2),
            name='Strike Price'
        ))

        # Agregar línea blanca tenue continua para el precio spot
        fig.add_trace(go.Scatter(
            x=[precio_actual] * len(spot_prices),
            y=[min(payoff) - 10, max(payoff) + 10],  # Extensión para que la línea sea continua
            mode='lines',
            line=dict(dash='dot', color='rgba(255, 255, 255, 0.6)', width=2),
            name='Spot Price'
        ))
        fig.update_layout(
            xaxis_title="Precio",
            yaxis_title="Ganancia/Pérdida",
            legend_title="Estrategia",
            height= 600,
            width= 1200
        )
        st.plotly_chart(fig)

if __name__ == '__main__':
    main()
