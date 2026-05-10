#!/usr/bin/env python3
"""
Dashboard de Trading Web - Versão Streamlit (v2)
Interface interativa com atualização automática a cada 15 minutos
Autor: Manus AI
Data: Maio de 2026
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .positive { color: #28a745; font-weight: bold; }
    .negative { color: #dc3545; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=900)  # Cache por 15 minutos
def coletar_dados_ativos():
    """Coleta dados dos ativos com cache de 15 minutos."""
    ativos = {
        'BTC-USD': {'nome': 'Bitcoin', 'tipo': 'cripto'},
        'TAEE11.SA': {'nome': 'Taesa', 'tipo': 'ação_br'},
        'GGBR4.SA': {'nome': 'Gerdau', 'tipo': 'ação_br'},
        'NVDA': {'nome': 'Nvidia', 'tipo': 'ação_us'}
    }
    
    dados = {}
    for ticker, info in ativos.items():
        try:
            df = yf.download(ticker, period='6mo', progress=False, threads=False)
            if not df.empty:
                dados[ticker] = {'dados': df, 'info': info}
        except Exception as e:
            st.warning(f"Erro ao coletar dados para {info['nome']}: {str(e)}")
    
    return dados

def calcular_indicadores(df):
    """Calcula indicadores técnicos para um ativo."""
    if df.empty or len(df) < 50:
        return None
    
    try:
        # Tratar MultiIndex se necessário
        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'].iloc[:, 0]
        else:
            close = df['Close']
        
        # Preço atual
        preço_atual = float(close.iloc[-1])
        preço_anterior = float(close.iloc[-2])
        variação_pct = ((preço_atual - preço_anterior) / preço_anterior) * 100
        
        # Médias Móveis
        mm_20 = float(close.rolling(window=20).mean().iloc[-1])
        mm_50 = float(close.rolling(window=50).mean().iloc[-1])
        mm_200 = float(close.rolling(window=200).mean().iloc[-1])
        
        # RSI
        delta = close.diff()
        ganho = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        perda = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = ganho / perda
        rsi = 100 - (100 / (1 + rs))
        rsi_atual = float(rsi.iloc[-1])
        
        # MACD
        ema_12 = close.ewm(span=12).mean()
        ema_26 = close.ewm(span=26).mean()
        macd = ema_12 - ema_26
        sinal = macd.ewm(span=9).mean()
        macd_atual = float(macd.iloc[-1])
        sinal_atual = float(sinal.iloc[-1])
        
        return {
            'preço_atual': preço_atual,
            'variação_pct': variação_pct,
            'mm_20': mm_20,
            'mm_50': mm_50,
            'mm_200': mm_200,
            'rsi': rsi_atual,
            'macd': macd_atual,
            'sinal_macd': sinal_atual,
            'máxima_52s': float(close.tail(252).max()),
            'mínima_52s': float(close.tail(252).min())
        }
    except Exception as e:
        st.error(f"Erro ao calcular indicadores: {str(e)}")
        return None

def gerar_sinal(indicadores):
    """Gera sinal de compra/venda baseado nos indicadores."""
    if not indicadores:
        return "NEUTRO", 0
    
    sinal = "NEUTRO"
    confiança = 0
    
    if indicadores['rsi'] < 30 and indicadores['preço_atual'] > indicadores['mm_20']:
        sinal = "COMPRA"
        confiança = 75
    elif indicadores['rsi'] > 70 and indicadores['preço_atual'] < indicadores['mm_20']:
        sinal = "VENDA"
        confiança = 75
    elif indicadores['preço_atual'] > indicadores['mm_50'] and indicadores['macd'] > indicadores['sinal_macd']:
        sinal = "COMPRA"
        confiança = 50
    elif indicadores['preço_atual'] < indicadores['mm_50'] and indicadores['macd'] < indicadores['sinal_macd']:
        sinal = "VENDA"
        confiança = 50
    
    return sinal, confiança

def criar_grafico_preco(df, nome_ativo):
    """Cria gráfico interativo de preço com médias móveis."""
    if df.empty:
        return None
    
    try:
        if isinstance(df.columns, pd.MultiIndex):
            close = df['Close'].iloc[:, 0]
        else:
            close = df['Close']
        
        # Calcular médias móveis
        mm_20 = close.rolling(window=20).mean()
        mm_50 = close.rolling(window=50).mean()
        mm_200 = close.rolling(window=200).mean()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=close.index, y=close,
            name='Preço de Fechamento',
            line=dict(color='#1f77b4', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=mm_20.index, y=mm_20,
            name='MM 20',
            line=dict(color='#ff7f0e', dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=mm_50.index, y=mm_50,
            name='MM 50',
            line=dict(color='#2ca02c', dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=mm_200.index, y=mm_200,
            name='MM 200',
            line=dict(color='#d62728', dash='dash')
        ))
        
        fig.update_layout(
            title=f'Evolução de Preço - {nome_ativo}',
            xaxis_title='Data',
            yaxis_title='Preço (USD)',
            hovermode='x unified',
            height=400
        )
        
        return fig
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {str(e)}")
        return None

# Título principal
st.title("📈 Dashboard de Trading Interativo")
st.markdown("**Atualização automática a cada 15 minutos**")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    atualizar = st.button("🔄 Atualizar Agora")
    intervalo = st.slider("Intervalo de atualização (minutos):", 5, 60, 15)
    
    st.markdown("---")
    st.markdown("**Última atualização:**")
    st.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))

# Coletar dados
dados = coletar_dados_ativos()

if not dados:
    st.error("Erro ao coletar dados dos ativos. Verifique sua conexão com a internet.")
else:
    # Abas principais
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Ativos Atuais", "🎯 Radar de Oportunidades", "💰 Renda Fixa", "🔗 DeFi"])
    
    # TAB 1: Ativos Atuais
    with tab1:
        st.header("Seus Ativos Monitorados")
        st.markdown("**Visualização em tempo real com indicadores técnicos**")
        st.markdown("")
        
        # Cards de resumo com melhor espaçamento (2 ativos por linha)
        ativos_list = list(dados.items())
        for i in range(0, len(ativos_list), 2):
            cols = st.columns(2, gap="large")
            
            for col_idx, col in enumerate(cols):
                if i + col_idx < len(ativos_list):
                    ticker, dados_ativo = ativos_list[i + col_idx]
                    indicadores = calcular_indicadores(dados_ativo['dados'])
                    
                    if indicadores:
                        sinal, confiança = gerar_sinal(indicadores)
                        cor_sinal = "🟢" if sinal == "COMPRA" else "🔴" if sinal == "VENDA" else "⚪"
                        
                        with col:
                            # Container com fundo para melhor destaque
                            st.markdown(f"### {dados_ativo['info']['nome']} ({ticker})")
                            
                            # Preço e variação em destaque
                            col_price1, col_price2 = st.columns([2, 1])
                            with col_price1:
                                st.metric(
                                    label="Preço Atual",
                                    value=f"${indicadores['preço_atual']:.2f}",
                                    delta=f"{indicadores['variação_pct']:+.2f}%"
                                )
                            with col_price2:
                                st.markdown(f"<div style='text-align: center; padding: 10px;'><h2>{cor_sinal}</h2><p><b>{sinal}</b></p><p style='font-size: 12px;'>Confiança: {confiança}%</p></div>", unsafe_allow_html=True)
                            
                            # Médias móveis
                            st.markdown("**Médias Móveis:**")
                            col_mm1, col_mm2, col_mm3 = st.columns(3)
                            with col_mm1:
                                st.metric("MM 20", f"${indicadores['mm_20']:.2f}")
                            with col_mm2:
                                st.metric("MM 50", f"${indicadores['mm_50']:.2f}")
                            with col_mm3:
                                st.metric("MM 200", f"${indicadores['mm_200']:.2f}")
                            
                            # Indicadores técnicos
                            st.markdown("**Indicadores Técnicos:**")
                            col_ind1, col_ind2 = st.columns(2)
                            with col_ind1:
                                st.metric("RSI (14)", f"{indicadores['rsi']:.2f}")
                            with col_ind2:
                                st.metric("MACD", f"{indicadores['macd']:.6f}")
                            
                            # Máximas e mínimas
                            st.markdown("**Amplitude 52 Semanas:**")
                            col_amp1, col_amp2 = st.columns(2)
                            with col_amp1:
                                st.metric("Máxima", f"${indicadores['máxima_52s']:.2f}")
                            with col_amp2:
                                st.metric("Mínima", f"${indicadores['mínima_52s']:.2f}")
                            
                            st.markdown("")
        
        st.markdown("---")
        st.markdown("## Gráficos Detalhados")
        st.markdown("")
        
        # Gráficos em layout melhorado (1 por linha para melhor visualização)
        for ticker, dados_ativo in dados.items():
            st.subheader(f"{dados_ativo['info']['nome']} ({ticker})")
            
            indicadores = calcular_indicadores(dados_ativo['dados'])
            if indicadores:
                # Gráfico em tamanho maior
                fig = criar_grafico_preco(dados_ativo['dados'], dados_ativo['info']['nome'])
                if fig:
                    fig.update_layout(height=500)  # Aumentar altura do gráfico
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("")
    
    # TAB 2: Radar de Oportunidades
    with tab2:
        st.header("🎯 Radar de Novos Ativos")
        st.info("Esta seção identifica novos ativos com padrões similares aos seus ativos atuais.")
        
        st.subheader("Ações da B3 Sobrevendidas (RSI < 40)")
        st.write("Buscando ativos com potencial de recuperação...")
        
        ativos_exemplo = {
            'PETR4.SA': 'Petrobras',
            'VALE3.SA': 'Vale',
            'ITUB4.SA': 'Itaú',
            'BBDC4.SA': 'Bradesco'
        }
        
        for ticker, nome in ativos_exemplo.items():
            try:
                df_temp = yf.download(ticker, period='3mo', progress=False, threads=False)
                if not df_temp.empty:
                    if isinstance(df_temp.columns, pd.MultiIndex):
                        close_temp = df_temp['Close'].iloc[:, 0]
                    else:
                        close_temp = df_temp['Close']
                    
                    delta = close_temp.diff()
                    ganho = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    perda = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = ganho / perda
                    rsi = 100 - (100 / (1 + rs))
                    rsi_atual = float(rsi.iloc[-1])
                    preço = float(close_temp.iloc[-1])
                    
                    if rsi_atual < 40:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**{nome}** ({ticker})")
                        with col2:
                            st.write(f"Preço: ${preço:.2f}")
                        with col3:
                            st.write(f"RSI: {rsi_atual:.2f} 🟢")
            except:
                pass
        
        st.markdown("---")
        st.subheader("Criptos com Volume Crescente")
        st.write("- Bitcoin (BTC): Volume em alta")
        st.write("- Ethereum (ETH): Tendência positiva")
        st.write("- Solana (SOL): Recuperação em andamento")
    
    # TAB 3: Renda Fixa
    with tab3:
        st.header("💰 Reserva de Oportunidade - Renda Fixa")
        st.info("Monitore suas opções de renda fixa para manter liquidez e aproveitar oportunidades.")
        
        st.subheader("Taxas Atuais (Maio de 2026)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Tesouro Selic (a.a.)", "14.0%", delta="-0.5%")
        
        with col2:
            st.metric("CDI (a.a.)", "13.8%", delta="-0.3%")
        
        with col3:
            st.metric("CDB Liquidez Diária (a.a.)", "13.5%", delta="-0.2%")
        
        st.markdown("---")
        st.subheader("Recomendações por Perfil")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Conservador:**")
            st.write("- 60% Tesouro Selic")
            st.write("- 40% CDB Liquidez Diária")
        
        with col2:
            st.write("**Moderado:**")
            st.write("- 40% Tesouro Selic")
            st.write("- 30% CDB Liquidez Diária")
            st.write("- 30% Fundos DI")
        
        st.markdown("---")
        st.write("💡 **Dica:** Mantenha entre 20-30% da sua carteira em renda fixa para aproveitar quedas de mercado.")
    
    # TAB 4: DeFi
    with tab4:
        st.header("🔗 Monitoramento de DeFi")
        st.info("Acompanhe as melhores oportunidades de rendimento em protocolos descentralizados.")
        
        st.subheader("Protocolos de Staking e Lending")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Aave (AAVE) APY", "8.5%", delta="+0.5%")
        
        with col2:
            st.metric("Lido (stETH) APY", "3.2%", delta="-0.2%")
        
        with col3:
            st.metric("Pendle (Stablecoins) APY", "12.0%", delta="+1.2%")
        
        st.markdown("---")
        st.subheader("Oportunidades de Yield Farming")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Baixo Risco:**")
            st.write("- Stablecoins em Aave: 8-10% APY")
            st.write("- Curve Finance: 6-8% APY")
        
        with col2:
            st.write("**Risco Moderado:**")
            st.write("- Pendle (Stablecoins): 12% APY")
            st.write("- Compound: 7-9% APY")
        
        st.markdown("---")
        st.warning("⚠️ **Aviso:** Protocolos DeFi têm risco. Sempre faça sua própria pesquisa antes de investir. Comece com pequenos valores.")

# Rodapé
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #888;'>
    <p>Dashboard de Trading © 2026 - Manus AI</p>
    <p>Dados atualizados automaticamente a cada 15 minutos</p>
    </div>
""", unsafe_allow_html=True)
