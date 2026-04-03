# dashboard_udare.py - Sistem AI pentru legume (udare, fertilizare, tratamente)
# Suportă multiple culturi, ajustare climatică, prognoză meteo, grafice interactive

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import json
import os
import requests

# ========== CONFIGURAȚIE PAGINĂ ==========
st.set_page_config(
    page_title="🌱 Sistem AI pentru Legume",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== FUNCȚII GENERALE ==========
@st.cache_data(ttl=3600)
def incarca_culturi():
    """Încarcă fișierul culturi.csv și returnează un DataFrame."""
    try:
        df = pd.read_csv('culturi.csv')
        # Coloanele obligatorii (dacă lipsesc, se adaugă cu valori implicite)
        required = [
            'nume', 'suprafata', 'adancime_radacina_cm', 'coeficient_evaporare',
            'temp_opt_min', 'temp_opt_max',
            'necesar_plantare', 'necesar_vegetativ', 'necesar_inflorire',
            'necesar_maturare', 'necesar_pre_recoltare', 'prag_udare_litri_mp'
        ]
        for col in required:
            if col not in df.columns:
                st.warning(f"Coloana '{col}' lipsește din culturi.csv. Se adaugă cu valoare implicită.")
                if col.startswith('necesar'):
                    df[col] = 5
                elif col == 'adancime_radacina_cm':
                    df[col] = 30
                elif col == 'coeficient_evaporare':
                    df[col] = 1.0
                elif col == 'temp_opt_min':
                    df[col] = 15
                elif col == 'temp_opt_max':
                    df[col] = 30
                elif col == 'prag_udare_litri_mp':
                    df[col] = 20
                else:
                    df[col] = 0

        # Coloane opționale pentru fertilizare/tratamente
        optional = [
            'fertilizare_frecventa_zile', 'fertilizare_doza_kg_mp',
            'fertilizare_produs', 'tratamente_fungicide', 'tratamente_insecticide'
        ]
        for col in optional:
            if col not in df.columns:
                df[col] = None
        return df
    except FileNotFoundError:
        st.error("Fișierul `culturi.csv` nu a fost găsit. Creează-l în folderul aplicației.")
        return pd.DataFrame()

def get_parametri_cultura(nume_cultura, df_culturi):
    """Returnează un dicționar cu toți parametrii specifici culturii."""
    row = df_culturi[df_culturi['nume'] == nume_cultura].iloc[0]
    return {
        'suprafata': float(row['suprafata']),
        'adancime_radacina': float(row['adancime_radacina_cm']),
        'coeficient_evaporare': float(row['coeficient_evaporare']),
        'temp_opt_min': float(row['temp_opt_min']),
        'temp_opt_max': float(row['temp_opt_max']),
        'necesar': {
            'Plantare': float(row['necesar_plantare']),
            'Vegetativ': float(row['necesar_vegetativ']),
            'Inflorire': float(row['necesar_inflorire']),
            'Maturare': float(row['necesar_maturare']),
            'Pre-recoltare': float(row['necesar_pre_recoltare'])
        },
        'prag_udare_litri_mp': float(row['prag_udare_litri_mp']),
        'fertilizare_frecventa_zile': row['fertilizare_frecventa_zile'] if not pd.isna(row['fertilizare_frecventa_zile']) else None,
        'fertilizare_doza_kg_mp': float(row['fertilizare_doza_kg_mp']) if not pd.isna(row['fertilizare_doza_kg_mp']) else None,
        'fertilizare_produs': row['fertilizare_produs'] if not pd.isna(row['fertilizare_produs']) else None,
        'tratamente_fungicide': row['tratamente_fungicide'] if not pd.isna(row['tratamente_fungicide']) else None,
        'tratamente_insecticide': row['tratamente_insecticide'] if not pd.isna(row['tratamente_insecticide']) else None
    }

def get_weather_forecast():
    """Obține prognoza meteo curentă folosind OpenWeatherMap API (necesită secret)."""
    try:
        api_key = st.secrets["OPENWEATHER_API_KEY"]
    except:
        return None
    city = "Bucharest"  # Poți face configurabil
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ro"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get('cod') != 200:
            return None
        return {
            'temperatura': data['main']['temp'],
            'umiditate': data['main']['humidity'],
            'descriere': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon']
        }
    except:
        return None

def ajusteaza_necesar(necesar_baza, temperatura, temp_opt_min, temp_opt_max, coeficient_evaporare):
    """
    Ajustează necesarul zilnic de apă (litri/mp) în funcție de:
    - temperatura curentă față de intervalul optim
    - coeficientul de evaporare specific culturii
    """
    if temperatura is None:
        return necesar_baza * coeficient_evaporare

    # Corecție termică
    if temperatura < temp_opt_min:
        factor_temp = 0.8   # udare redusă la frig
    elif temperatura > temp_opt_max:
        factor_temp = 1.3   # udare crescută la căldură
    else:
        factor_temp = 1.0

    return necesar_baza * factor_temp * coeficient_evaporare

def calculeaza_necesar(suprafata, necesar_pe_zi_ajustat, zile_scurse):
    return suprafata * necesar_pe_zi_ajustat * zile_scurse

def incarca_istoric(cultura):
    """Încarcă istoricul udărilor din fișierul JSON specific culturii."""
    nume_fisier = f"istoric_{cultura.lower().replace(' ', '_')}.json"
    if os.path.exists(nume_fisier):
        try:
            with open(nume_fisier, "r", encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def incarca_predictii_ai(cultura):
    """Încarcă predicțiile AI din fișierul JSON specific culturii."""
    nume_fisier = f"predictii_{cultura.lower().replace(' ', '_')}.json"
    if os.path.exists(nume_fisier):
        try:
            with open(nume_fisier, "r", encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def incarca_tratamente(cultura):
    """Încarcă istoricul tratamentelor din fișierul JSON specific culturii."""
    nume_fisier = f"tratamente_{cultura.lower().replace(' ', '_')}.json"
    if os.path.exists(nume_fisier):
        try:
            with open(nume_fisier, "r", encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def salveaza_tratament(cultura, tratament):
    """Salvează un tratament în fișierul JSON specific culturii."""
    tratamente = incarca_tratamente(cultura)
    tratamente.append(tratament)
    nume_fisier = f"tratamente_{cultura.lower().replace(' ', '_')}.json"
    with open(nume_fisier, "w", encoding='utf-8') as f:
        json.dump(tratamente, f, indent=2, ensure_ascii=False)

# ========== BARA LATERALĂ ==========
with st.sidebar:
    st.header("⚙️ Configurație")

    # Încarcă lista de culturi
    df_culturi = incarca_culturi()
    if df_culturi.empty:
        st.stop()

    nume_cultura = st.selectbox("🌿 Selectează cultura", df_culturi['nume'].tolist())
    params = get_parametri_cultura(nume_cultura, df_culturi)

    # Afișează parametrii specifici
    with st.expander("📋 Parametrii culturii"):
        st.write(f"**Suprafață:** {params['suprafata']} mp")
        st.write(f"**Adâncime rădăcină:** {params['adancime_radacina']} cm")
        st.write(f"**Coeficient evaporare:** {params['coeficient_evaporare']}")
        st.write(f"**Temperatură optimă:** {params['temp_opt_min']}°C – {params['temp_opt_max']}°C")
        st.write(f"**Prag udare:** {params['prag_udare_litri_mp']} litri/mp")
        st.write("**Necesar zilnic (litri/mp/zi):**")
        for stadiu, val in params['necesar'].items():
            st.write(f"  - {stadiu}: {val}")

    st.markdown("---")

    # Permite suprascrierea suprafeței
    suprafata = st.number_input("Suprafață (mp)", value=float(params['suprafata']), step=10.0)

    debit_pompa = st.number_input("Debit pompă (l/h)", value=5640, step=100, min_value=1)

    st.markdown("---")

    stadiu_curent = st.selectbox(
        "Stadiul curent",
        ["Plantare", "Vegetativ", "Inflorire", "Maturare", "Pre-recoltare"],
        index=2
    )

    ultima_udare = st.date_input(
        "Ultima udare",
        value=datetime.date.today() - datetime.timedelta(days=3)
    )

    st.markdown("---")

    st.subheader("🌤️ Prognoză meteo")
    if st.button("🔍 Verifică vremea acum", use_container_width=True):
        with st.spinner("Se preia prognoza..."):
            weather = get_weather_forecast()
            if weather:
                st.success(f"**{weather['temperatura']:.1f}°C** | 💧 {weather['umiditate']}%")
                st.caption(f"{weather['descriere'].capitalize()}")
                st.session_state.weather = weather
            else:
                st.error("Nu s-a putut obține prognoza. Verifică cheia API în Secrets.")
                st.session_state.weather = None
    else:
        if 'weather' not in st.session_state:
            st.session_state.weather = None
        if st.session_state.weather:
            st.success(f"**{st.session_state.weather['temperatura']:.1f}°C** | 💧 {st.session_state.weather['umiditate']}%")
            st.caption(f"{st.session_state.weather['descriere'].capitalize()}")
        else:
            st.info("Apasă butonul de mai sus pentru a vedea prognoza actualizată.")

    st.markdown("---")

    # Secțiune pentru înregistrarea tratamentelor
    st.subheader("🧪 Înregistrează tratament")
    with st.form("form_tratament"):
        tip_tratament = st.selectbox("Tip tratament", ["Fertilizare", "Fungicid", "Insecticit", "Altul"])
        produs = st.text_input("Produs")
        doza = st.number_input("Doză (kg/mp sau litri)", min_value=0.0, step=0.01, format="%.2f")
        observatii = st.text_area("Observații")
        submitted = st.form_submit_button("Salvează")
        if submitted:
            tratament = {
                "data": datetime.date.today().isoformat(),
                "tip": tip_tratament,
                "produs": produs,
                "doza": doza,
                "observatii": observatii
            }
            salveaza_tratament(nume_cultura, tratament)
            st.success(f"Tratament înregistrat pentru {nume_cultura}")

    st.markdown("---")
    st.subheader("📊 Filtre grafice")
    zile_istoric = st.slider("Perioadă istoric (zile)", 7, 90, 30)

# ========== OBȚINE DATELE METEO CURENTE ==========
weather = st.session_state.get('weather', None)
temperatura = weather['temperatura'] if weather else None

# ========== CALCULE PRINCIPALE ==========
astazi = datetime.date.today()
zile_scurse = max(0, (astazi - ultima_udare).days)

necesar_pe_zi_baza = params['necesar'][stadiu_curent]
necesar_pe_zi_ajustat = ajusteaza_necesar(
    necesar_pe_zi_baza,
    temperatura,
    params['temp_opt_min'],
    params['temp_opt_max'],
    params['coeficient_evaporare']
)
necesar_total = calculeaza_necesar(suprafata, necesar_pe_zi_ajustat, zile_scurse)
prag_udare_total = suprafata * params['prag_udare_litri_mp']
trebuie_udat = necesar_total >= prag_udare_total
if debit_pompa > 0:
    timp_udare = int((necesar_total / debit_pompa) * 60) if trebuie_udat else 0
else:
    timp_udare = 0
timp_sector = (timp_udare + 1) // 2

# Încarcă datele specifice culturii
istoric = incarca_istoric(nume_cultura)
predictii_ai = incarca_predictii_ai(nume_cultura)
tratamente = incarca_tratamente(nume_cultura)

# ========== KPI-URI ==========
st.subheader(f"📊 Starea curentă – {nume_cultura}")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📅 Zile de la ultima udare", f"{zile_scurse} zile")
with col2:
    st.metric("💧 Necesar acumulat", f"{int(necesar_total):,} litri")
with col3:
    if trebuie_udat:
        st.metric("🚨 Recomandare", "UDĂ ACUM!", delta=f"{timp_udare} min", delta_color="inverse")
    else:
        st.metric("🌱 Recomandare", "AȘTEAPTĂ")
with col4:
    st.metric("🌡️ Stadiu", stadiu_curent)

if trebuie_udat:
    st.info(f"💧 **Recomandare udare:** {timp_udare} minute total\n\n- Sector 1: {timp_sector} minute\n- Sector 2: {timp_udare - timp_sector} minute")

st.markdown("---")

# ========== GRAFICE PRINCIPALE ==========
st.subheader("📈 Evoluție și tendințe")

if istoric:
    df_istoric = pd.DataFrame(istoric)
    df_istoric['data'] = pd.to_datetime(df_istoric['data'])
    df_istoric = df_istoric.sort_values('data')
    df_istoric = df_istoric.tail(zile_istoric)

    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.line(df_istoric, x='data', y='necesar_acumulat',
                       title='Evoluția necesarului de apă',
                       labels={'data': 'Data', 'necesar_acumulat': 'Litri'})
        fig1.update_traces(line_color='#2ecc71', line_width=2)
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        fig2 = px.area(df_istoric, x='data', y='necesar_acumulat',
                       title='Necesar cumulat (arie)',
                       labels={'data': 'Data', 'necesar_acumulat': 'Litri'})
        fig2.update_traces(fillcolor='rgba(46,204,113,0.3)', line_color='#2ecc71')
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("Nu există date istorice pentru această cultură. Rulează scriptul de predicție pentru a genera istoric.")

st.markdown("---")

# ========== GRAFICE PREDICȚII AI ==========
if predictii_ai:
    st.subheader("🤖 Analiza predicțiilor AI")
    df_pred = pd.DataFrame(predictii_ai)
    df_pred['data'] = pd.to_datetime(df_pred['data'])
    df_pred = df_pred.sort_values('data')
    df_pred = df_pred.tail(zile_istoric)

    col1, col2 = st.columns(2)
    with col1:
        fig3 = px.line(df_pred, x='data', y='minute_recomandate',
                       title='Minute recomandate de AI',
                       labels={'data': 'Data', 'minute_recomandate': 'Minute'})
        fig3.update_traces(line_color='#e74c3c', line_width=2)
        st.plotly_chart(fig3, use_container_width=True)
    with col2:
        if 'temperatura' in df_pred.columns:
            fig4 = px.scatter(df_pred, x='temperatura', y='minute_recomandate',
                              title='Corelație temperatură - recomandare AI',
                              labels={'temperatura': 'Temperatură (°C)', 'minute_recomandate': 'Minute'},
                              trendline='ols')
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("Nu există date suficiente pentru corelație.")
else:
    st.info("Nu există predicții AI pentru această cultură.")

st.markdown("---")

# ========== ANALIZE AVANSATE (dacă există date) ==========
if istoric:
    st.subheader("📊 Analize avansate")
    col1, col2 = st.columns(2)
    with col1:
        if 'zile_de_la_udare' in df_istoric.columns:
            fig5 = px.bar(df_istoric, x='data', y='zile_de_la_udare',
                          title='Zile între udări',
                          labels={'data': 'Data', 'zile_de_la_udare': 'Zile'},
                          color='zile_de_la_udare', color_continuous_scale='Viridis')
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("Coloana 'zile_de_la_udare' lipsește din istoric.")
    with col2:
        fig6 = px.histogram(df_istoric, x='necesar_acumulat',
                            title='Distribuția necesarului de apă',
                            labels={'necesar_acumulat': 'Litri', 'count': 'Frecvență'},
                            nbins=20, color_discrete_sequence=['#3498db'])
        st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# ========== ANALIZĂ SEZONIERĂ ==========
if predictii_ai and len(df_pred) > 5:
    st.subheader("🌡️ Analiză sezonieră")
    col1, col2 = st.columns(2)
    with col1:
        df_pred['luna'] = pd.to_datetime(df_pred['data']).dt.month
        fig7 = px.box(df_pred, x='luna', y='minute_recomandate',
                      title='Minute recomandate pe luni',
                      labels={'luna': 'Luna', 'minute_recomandate': 'Minute'})
        st.plotly_chart(fig7, use_container_width=True)
    with col2:
        if 'temperatura' in df_pred.columns and 'minute_recomandate' in df_pred.columns and 'zile_de_la_udare' in df_pred.columns:
            df_corr = df_pred[['minute_recomandate', 'temperatura', 'zile_de_la_udare']].corr()
            fig8 = px.imshow(df_corr, text_auto=True,
                             title='Matricea de corelație',
                             color_continuous_scale='RdBu', zmin=-1, zmax=1)
            st.plotly_chart(fig8, use_container_width=True)
        else:
            st.info("Nu există suficiente date pentru matricea de corelație.")

st.markdown("---")

# ========== DASHBOARD INTEGRAT (SUBPLOT) ==========
if predictii_ai and len(df_pred) > 5:
    st.subheader("📈 Dashboard integrat")
    fig9 = make_subplots(rows=3, cols=1,
                         subplot_titles=('Temperatură', 'Minute recomandate', 'Zile de la udare'),
                         shared_xaxes=True)
    fig9.add_trace(go.Scatter(x=df_pred['data'], y=df_pred['temperatura'],
                              mode='lines+markers', name='Temperatură', line=dict(color='#f39c12')),
                   row=1, col=1)
    fig9.add_trace(go.Scatter(x=df_pred['data'], y=df_pred['minute_recomandate'],
                              mode='lines+markers', name='Minute udare', line=dict(color='#e74c3c')),
                   row=2, col=1)
    if 'zile_de_la_udare' in df_pred.columns:
        fig9.add_trace(go.Scatter(x=df_pred['data'], y=df_pred['zile_de_la_udare'],
                                  mode='lines+markers', name='Zile de la udare', line=dict(color='#2ecc71')),
                       row=3, col=1)
    fig9.update_layout(height=800, title_text="Analiza completă a culturii")
    st.plotly_chart(fig9, use_container_width=True)

st.markdown("---")

# ========== RECOMANDĂRI FERTILIZARE ȘI TRATAMENTE ==========
st.subheader("🧪 Recomandări tratamente și fertilizare")

# Calcul pentru fertilizare
frecventa_fertilizare = params.get('fertilizare_frecventa_zile')
if frecventa_fertilizare is not None and frecventa_fertilizare > 0:
    ultima_fertilizare = None
    if tratamente:
        for t in reversed(tratamente):
            if t.get('tip') == 'Fertilizare':
                try:
                    ultima_fertilizare = datetime.date.fromisoformat(t['data'])
                    break
                except:
                    pass
    if ultima_fertilizare is None:
        st.warning(f"📢 Nu s-a înregistrat nicio fertilizare pentru {nume_cultura}. Recomandare: aplică **{params['fertilizare_produs']}** (doză {params['fertilizare_doza_kg_mp']} kg/mp) la fiecare {frecventa_fertilizare} zile.")
    else:
        zile_ultima = (datetime.date.today() - ultima_fertilizare).days
        if zile_ultima >= frecventa_fertilizare:
            st.error(f"⚠️ A trecut {zile_ultima} zile de la ultima fertilizare. Aplică acum **{params['fertilizare_produs']}** (doză {params['fertilizare_doza_kg_mp']} kg/mp).")
        else:
            st.success(f"✅ Ultima fertilizare: acum {zile_ultima} zile. Următoarea peste {frecventa_fertilizare - zile_ultima} zile.")
else:
    st.info("Nu există recomandări de fertilizare configurate pentru această cultură.")

# Afișează recomandări fungicide/insecticide
if params.get('tratamente_fungicide') and not pd.isna(params['tratamente_fungicide']):
    st.info(f"🍄 **Recomandare fungicid:** {params['tratamente_fungicide']}")
if params.get('tratamente_insecticide') and not pd.isna(params['tratamente_insecticide']):
    st.info(f"🐛 **Recomandare insecticid:** {params['tratamente_insecticide']}")

# ========== ISTORIC TRATAMENTE ==========
st.subheader("📜 Istoric tratamente")
if tratamente:
    df_trat = pd.DataFrame(tratamente)
    df_trat['data'] = pd.to_datetime(df_trat['data'])
    df_trat = df_trat.sort_values('data', ascending=False)
    st.dataframe(df_trat, use_container_width=True)
else:
    st.info("Nu există tratamente înregistrate pentru această cultură.")

st.markdown("---")

# ========== ISTORIC UDĂRI ==========
st.subheader("📋 Istoric complet udări")
if istoric:
    df_afisare = pd.DataFrame(istoric).tail(20)
    df_afisare = df_afisare.sort_values('data', ascending=False)
    st.dataframe(df_afisare, use_container_width=True)
else:
    st.info("Nu există date istorice pentru această cultură. Rulează scriptul de predicție.")

st.markdown("---")

# ========== RECOMANDĂRI PERSONALIZATE (stadiu) ==========
st.subheader("💡 Recomandări personalizate")

recomandari = {
    "Plantare": "🌱 Udează zilnic sau la 2 zile pentru a asigura prinderea rădăcinilor.",
    "Vegetativ": "🌿 Udează mai rar (1-2 ori/săptămână), dar mai abundent pentru rădăcini adânci.",
    "Inflorire": "🌸 Perioada critică! Udează frecvent (2-3 ori/săptămână) pentru a preveni căderea florilor.",
    "Maturare": "🍅 Reduce udarea treptat pentru a concentra aromele.",
    "Pre-recoltare": "🔴 Oprește complet udarea cu 2-3 săptămâni înainte de recoltare!"
}
st.success(recomandari.get(stadiu_curent, ""))

# Afișează un rezumat al ajustării
if temperatura is not None:
    st.caption(f"🌡️ Ajustare necesar: {necesar_pe_zi_baza:.1f} → {necesar_pe_zi_ajustat:.1f} litri/mp/zi (temp. {temperatura:.1f}°C, evaporare x{params['coeficient_evaporare']})")
else:
    st.caption(f"🌡️ Ajustare necesar: {necesar_pe_zi_baza:.1f} → {necesar_pe_zi_ajustat:.1f} litri/mp/zi (evaporare x{params['coeficient_evaporare']})")

# ========== FOOTER ==========
st.markdown("---")
st.caption(f"📅 Ultima actualizare: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("🌱 Sistem AI pentru legume - Datele sunt salvate local în fișiere JSON specifice culturii.")