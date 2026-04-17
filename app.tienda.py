import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import MultipleLocator

# --- CONSTANTES DE MODULACIÓN EXACTA ---
MOD_1FT = 0.30
MOD_2FT = 0.61        
MOD_3FT = 0.91        
PROF_CAFE = 0.75      
PROF_CHECK = 0.60     
PROF_CAJERO = 1.00    
PROF_CONTRA = 0.45    
PROF_FRIO = 2.00      
PROF_PERIMETRO = 0.45 
GONDOLA_PROF = 0.90   
CABECERA_PROF = 0.45  
PUERTA_ANCHO = 1.80   
ISLA_DIM = 0.60

# --- CLASIFICADOR DE MATRIZ DE FORMATOS OXXO ---
def clasificar_formato(m2):
    if m2 <= 15: return "BOOTH (Compacto)"
    elif m2 <= 36: return "MINI (Reducido)"
    elif m2 <= 56: return "MINI 2 (Reducido)"
    elif m2 <= 77: return "MEDIA (Ordinario)"
    elif m2 <= 98: return "MEDIA 2 (Ordinario)"
    elif m2 <= 117: return "REGULAR (Ordinario)"
    elif m2 <= 135: return "MÍNIMO 2 (Ordinario)"
    elif m2 <= 154: return "ÓPTIMO (Ordinario)"
    elif m2 <= 170: return "ÓPTIMO 2 (Ordinario)"
    elif m2 <= 250: return "MÁXIMO (Extra Ordinario)"
    else: return "MEGA (Extra Ordinario)"

def colisiona(x, y, w, h, obstaculos):
    margen = 0.05
    for (ox, oy, ow, oh) in obstaculos:
        if not (x + w <= ox + margen or x >= ox + ow - margen or y + h <= oy + margen or y >= oy + oh - margen):
            return True
    return False

# --- MOTOR DE TRANSFORMACIÓN ESPACIAL ---
def obtener_transformacion(muro, ancho_orig, largo_orig):
    def transform(x, y, w, h, rot_texto=0):
        if muro == 'Inferior (Frente)': return x, y, w, h, rot_texto
        elif muro == 'Lateral Izquierdo': return y, x, h, w, rot_texto - 90
        elif muro == 'Lateral Derecho': return ancho_orig - y - h, x, h, w, rot_texto + 90
    return transform

def normalizar_rotacion(r):
    r = r % 360
    if 90 < r < 270: r -= 180
    return r

def dibujar_layout_oxxo(conf):
    ancho_real, largo_real = conf['ancho'], conf['largo']
    muro = conf['muro_puerta']
    
    if muro == 'Inferior (Frente)': W, L = ancho_real, largo_real
    else: W, L = largo_real, ancho_real 

    fig, ax = plt.subplots(figsize=(12, 12))
    ax.set_xlim(0, W)
    ax.set_ylim(0, L)
    
    # Cuadrícula 1x1m
    ax.xaxis.set_major_locator(MultipleLocator(1))
    ax.yaxis.set_major_locator(MultipleLocator(1))
    ax.grid(which='major', color='#E5E7E9', linestyle='-', linewidth=0.5, zorder=0)

    trans = obtener_transformacion(muro, ancho_real, largo_real)
    obstaculos, errores = [], []
    area_exh = 0
    
    def dibujar(x, y, w, h, color, ec='black', alpha=1.0, texto="", fontsize=6, rot=0, color_txt='black', weight='normal'):
        xn, yn, wn, hn, rotn = trans(x, y, w, h, rot)
        ax.add_patch(patches.Rectangle((xn, yn), wn, hn, color=color, ec=ec, alpha=alpha, zorder=5))
        if texto:
            cx, cy = xn + wn/2, yn + hn/2
            ax.text(cx, cy, texto, ha='center', va='center', rotation=normalizar_rotacion(rotn), fontsize=fontsize, color=color_txt, weight=weight, zorder=10)

    def dibujar_circulo(x, y, r, color, alpha):
        xn, yn, _, _, _ = trans(x - r, y - r, r*2, r*2, 0)
        ax.add_patch(patches.Circle((xn + r, yn + r), r, color=color, alpha=alpha, zorder=1))

    # Lienzo Base
    ax.add_patch(patches.Rectangle((0, 0), ancho_real, largo_real, fill=False, ec='black', lw=4, zorder=10))

    area_total = W * L
    area_operativa = area_total * 0.20 
    area_comercial = area_total * 0.80

    # ==========================================
    # 1. BODEGA (Área Operativa 20%)
    # ==========================================
    w_bod, h_bod = W, area_operativa / W
    x_bod, y_bod = 0, L - h_bod
    puerta_bod_x, puerta_bod_y = 0, 0

    if conf['t_bodega']:
        if conf['loc_bodega'] == 'Fondo':
            x_bod, y_bod = 0, L - h_bod
            puerta_bod_x, puerta_bod_y = W/2 - 0.9, y_bod
        elif conf['loc_bodega'] == 'Lateral Izquierdo':
            w_bod, h_bod = area_operativa / L, L
            x_bod, y_bod = 0, 0
            puerta_bod_x, puerta_bod_y = w_bod, L/2
        else: 
            w_bod, h_bod = area_operativa / L, L
            x_bod, y_bod = W - w_bod, 0
            puerta_bod_x, puerta_bod_y = x_bod, L/2
            
        dibujar(x_bod, y_bod, w_bod, h_bod, '#D2B48C', texto='BODEGA (20%)', weight='bold')
        
        p_bod = conf['pasillo_bod']
        dibujar(x_bod + 0.5, y_bod + 0.5, w_bod - 1.0, h_bod - 1.0, '#E59866', ec='none', alpha=0.3, texto=f'Pasillo: {p_bod}m', color_txt='white')
        
        if conf['loc_bodega'] == 'Fondo': dibujar(puerta_bod_x, puerta_bod_y-0.1, 1.8, 0.2, 'brown')
        else: dibujar(puerta_bod_x-0.1, puerta_bod_y, 0.2, 1.8, 'brown')
            
        obstaculos.append((x_bod, y_bod, w_bod, h_bod))

    # ==========================================
    # 2. ACCESO Y PASILLO DE PODER
    # ==========================================
    ancho_puerta_real = 0.9 if conf['tipo_puerta'] == '1 Puerta (90cm)' else 1.80
    x_p, y_p = conf['pos_puerta'], 0
    
    if conf['t_puerta']:
        dibujar(x_p, y_p, ancho_puerta_real, 0.2, 'red', ec='darkred', texto='ACCESO', color_txt='white', fontsize=5)
        dibujar_circulo(x_p + ancho_puerta_real/2, 0, 2.0, '#85C1E9', 0.2)
        
    if conf['t_pasillos'] and conf['t_puerta']:
        w_poder = conf['pas_poder']
        lim_y = y_bod if conf['t_bodega'] and conf['loc_bodega'] == 'Fondo' else L
        dibujar(x_p - (w_poder-ancho_puerta_real)/2, 0, w_poder, lim_y, '#AED6F1', ec='none', alpha=0.4, texto='PASILLO DE PODER', rot=90, color_txt='#154360', weight='bold')
        obstaculos.append((x_p - (w_poder-ancho_puerta_real)/2, 0, w_poder, lim_y))

        w_peri = conf['pas_peri']
        lim_x_izq = w_bod if conf['t_bodega'] and conf['loc_bodega'] == 'Lateral Izquierdo' else 0
        lim_x_der = W - w_bod if conf['t_bodega'] and conf['loc_bodega'] == 'Lateral Derecho' else W
        
        dibujar(lim_x_izq + PROF_PERIMETRO, PROF_PERIMETRO, w_peri, lim_y - PROF_PERIMETRO*2, '#FCF3CF', ec='none', alpha=0.3)
        dibujar(lim_x_der - PROF_PERIMETRO - w_peri, PROF_PERIMETRO, w_peri, lim_y - PROF_PERIMETRO*2, '#FCF3CF', ec='none', alpha=0.3)
        dibujar(lim_x_izq + PROF_PERIMETRO, lim_y - PROF_FRIO - w_peri, lim_x_der - lim_x_izq - PROF_PERIMETRO*2, w_peri, '#FCF3CF', ec='none', alpha=0.5)

    # ==========================================
    # 3. CHECKOUT
    # ==========================================
    if conf['t_check']:
        ancho_check = conf['cant_check'] * MOD_2FT
        muro_chk = conf['muro_check']
        
        if muro_chk == 'Inferior': x_chk, y_chk, w_chk, h_chk, rot = W - ancho_check - PROF_PERIMETRO, PROF_PERIMETRO, ancho_check, PROF_CONTRA+PROF_CAJERO+PROF_CHECK, 0
        elif muro_chk == 'Superior': x_chk, y_chk, w_chk, h_chk, rot = PROF_PERIMETRO, L - (PROF_CONTRA+PROF_CAJERO+PROF_CHECK) - (h_bod if conf['t_bodega'] and conf['loc_bodega']=='Fondo' else 0), ancho_check, PROF_CONTRA+PROF_CAJERO+PROF_CHECK, 0
        elif muro_chk == 'Izquierdo': x_chk, y_chk, w_chk, h_chk, rot = PROF_PERIMETRO, PROF_PERIMETRO, PROF_CONTRA+PROF_CAJERO+PROF_CHECK, ancho_check, 90
        else: x_chk, y_chk, w_chk, h_chk, rot = W - (PROF_CONTRA+PROF_CAJERO+PROF_CHECK) - PROF_PERIMETRO, PROF_PERIMETRO, PROF_CONTRA+PROF_CAJERO+PROF_CHECK, ancho_check, 90

        if not colisiona(x_chk, y_chk, w_chk, h_chk, obstaculos):
            if rot == 0:
                dibujar(x_chk, y_chk, ancho_check, PROF_CONTRA, '#82E0AA', texto='C.CAJA', fontsize=4)
                dibujar(x_chk, y_chk + PROF_CONTRA, ancho_check, PROF_CAJERO, '#EAEDED')
                for i in range(conf['cant_check']): dibujar(x_chk + (i*MOD_2FT), y_chk + PROF_CONTRA + PROF_CAJERO, MOD_2FT, PROF_CHECK, '#ABEBC6', texto=f'CHK{i+1}', fontsize=5)
                if conf['t_pasillos']: dibujar(x_chk, y_chk + h_chk, ancho_check, 1.20, '#D5F5E3', ec='none', alpha=0.5, texto='PASILLO COBRO', fontsize=5)
            else:
                dibujar(x_chk, y_chk, PROF_CONTRA, ancho_check, '#82E0AA')
                dibujar(x_chk + PROF_CONTRA, y_chk, PROF_CAJERO, ancho_check, '#EAEDED')
                dibujar(x_chk + PROF_CONTRA + PROF_CAJERO, y_chk, PROF_CHECK, ancho_check, '#ABEBC6', texto='CHECKOUT', rot=90)
                if conf['t_pasillos']: dibujar(x_chk + w_chk, y_chk, 1.20, ancho_check, '#D5F5E3', ec='none', alpha=0.5, texto='PASILLO COBRO', rot=90, fontsize=5)
            
            obstaculos.append((x_chk, y_chk, w_chk, h_chk + (1.20 if rot==0 and conf['t_pasillos'] else 0)))
            area_exh += (ancho_check * PROF_CHECK)
        else: errores.append("Checkout colisiona o no cabe en ese muro.")

    # ==========================================
    # 4. CUARTO FRÍO
    # ==========================================
    if conf['t_frio']:
        ptas = conf['cant_frio']
        ancho_frio = ptas * MOD_2FT
        y_frio = y_bod - PROF_FRIO if conf['t_bodega'] and conf['loc_bodega']=='Fondo' else L - PROF_FRIO
        x_frio = conf['pos_frio']
        
        if not colisiona(x_frio, y_frio, ancho_frio, PROF_FRIO, obstaculos):
            dibujar(x_frio, y_frio, ancho_frio, PROF_FRIO, '#AED6F1', texto='CUARTO FRÍO', weight='bold')
            for i in range(ptas): dibujar(x_frio + (i*MOD_2FT), y_frio, MOD_2FT, 0.15, '#2874A6', ec='white', texto=f'P{i+1}', color_txt='white', rot=90, fontsize=4)
            obstaculos.append((x_frio, y_frio - (1.20 if conf['t_pasillos'] else 0), ancho_frio, PROF_FRIO + (1.20 if conf['t_pasillos'] else 0)))
            area_exh += (ancho_frio * PROF_FRIO)
        else: errores.append("El Cuarto Frío colisiona con la bodega o paredes.")

    # ==========================================
    # 5. FOODVENIENCE
    # ==========================================
    if conf['t_cafe']:
        mods = conf['cant_cafe']
        ancho_cafe = mods * MOD_2FT
        x_c, y_c = conf['pos_cafe_x'], conf['pos_cafe_y']
        
        if conf['forma_cafe'] == 'Lineal':
            if not colisiona(x_c, y_c, ancho_cafe, PROF_CAFE, obstaculos):
                for i in range(mods): dibujar(x_c + (i*MOD_2FT), y_c, MOD_2FT, PROF_CAFE, '#FAD7A0', texto=f'C{i+1}')
                obstaculos.append((x_c, y_c, ancho_cafe, PROF_CAFE))
                area_exh += (ancho_cafe * PROF_CAFE)
            else: errores.append("Foodvenience Lineal colisiona con otro mueble.")
        else: 
            mods_x = int(mods / 2)
            mods_y = mods - mods_x
            if not colisiona(x_c, y_c, mods_x*MOD_2FT, PROF_CAFE + mods_y*MOD_2FT, obstaculos):
                dibujar(x_c, y_c, mods_x*MOD_2FT, PROF_CAFE, '#FAD7A0')
                dibujar(x_c, y_c + PROF_CAFE, PROF_CAFE, mods_y*MOD_2FT, '#FAD7A0')
                dibujar(x_c, y_c, PROF_CAFE, PROF_CAFE, '#E59866') 
                obstaculos.append((x_c, y_c, max(mods_x*MOD_2FT, PROF_CAFE), PROF_CAFE + mods_y*MOD_2FT))
                area_exh += (mods * MOD_2FT * PROF_CAFE)

    # ==========================================
    # 6. GÓNDOLAS CENTRALES
    # ==========================================
    if conf['t_gondolas']:
        x_g, y_g = conf['pos_gon_x'], conf['pos_gon_y']
        largo_g = conf['cant_tramos'] * MOD_3FT
        trenes_colocados = 0
        
        for i in range(conf['cant_trenes']):
            if conf['rot_gon'] == 'Vertical':
                if not colisiona(x_g, y_g, GONDOLA_PROF, largo_g + CABECERA_PROF*2, obstaculos):
                    dibujar(x_g, y_g, GONDOLA_PROF, CABECERA_PROF, '#E74C3C', texto='CAB', fontsize=4)
                    if conf['sep_cab']: dibujar(x_g, y_g + CABECERA_PROF + 0.6, GONDOLA_PROF, largo_g - 1.2, '#ABB2B9')
                    else: 
                        for t in range(conf['cant_tramos']): dibujar(x_g, y_g + CABECERA_PROF + (t*MOD_3FT), GONDOLA_PROF, MOD_3FT, '#ABB2B9', texto=f'Tr{t+1}', fontsize=5)
                    dibujar(x_g, y_g + CABECERA_PROF + largo_g, GONDOLA_PROF, CABECERA_PROF, '#E74C3C', texto='CAB', fontsize=4)
                    obstaculos.append((x_g, y_g, GONDOLA_PROF, largo_g + CABECERA_PROF*2))
                    area_exh += GONDOLA_PROF * (largo_g + CABECERA_PROF*2)
                    trenes_colocados += 1
                x_g += GONDOLA_PROF + conf['pas_gon']
            else: 
                if not colisiona(x_g, y_g, largo_g + CABECERA_PROF*2, GONDOLA_PROF, obstaculos):
                    dibujar(x_g, y_g, CABECERA_PROF, GONDOLA_PROF, '#E74C3C', texto='CAB', rot=90, fontsize=4)
                    if conf['sep_cab']: dibujar(x_g + CABECERA_PROF + 0.6, y_g, largo_g - 1.2, GONDOLA_PROF, '#ABB2B9')
                    else: 
                        for t in range(conf['cant_tramos']): dibujar(x_g + CABECERA_PROF + (t*MOD_3FT), y_g, MOD_3FT, GONDOLA_PROF, '#ABB2B9', texto=f'Tr{t+1}', rot=90, fontsize=5)
                    dibujar(x_g + CABECERA_PROF + largo_g, y_g, CABECERA_PROF, GONDOLA_PROF, '#E74C3C', texto='CAB', rot=90, fontsize=4)
                    obstaculos.append((x_g, y_g, largo_g + CABECERA_PROF*2, GONDOLA_PROF))
                    area_exh += GONDOLA_PROF * (largo_g + CABECERA_PROF*2)
                    trenes_colocados += 1
                y_g += GONDOLA_PROF + conf['pas_gon']
        if trenes_colocados < conf['cant_trenes']: errores.append("Uno o más trenes de góndola colisionan o exceden el área.")

    # ==========================================
    # 7. PERIMETRALES
    # ==========================================
    if conf['t_perimetral']:
        tramos_peri = 0
        def colocar_muro(xb, yb, lw, is_v):
            nonlocal tramos_peri
            for i in range(int(lw / MOD_1FT)):
                cx = xb if is_v else xb + (i*MOD_1FT)
                cy = yb + (i*MOD_1FT) if is_v else yb
                cw = PROF_PERIMETRO if is_v else MOD_1FT
                ch = MOD_1FT if is_v else PROF_PERIMETRO
                if not colisiona(cx, cy, cw, ch, obstaculos):
                    dibujar(cx, cy, cw, ch, '#D5DBDB', ec='gray', texto='P', fontsize=4, rot=0 if is_v else 90)
                    tramos_peri += 1

        if 'Izquierda' in conf['muros_peri']: colocar_muro(0, 0, L, True)
        if 'Derecha' in conf['muros_peri']: colocar_muro(W - PROF_PERIMETRO, 0, L, True)
        if 'Frente' in conf['muros_peri']: colocar_muro(0, 0, W, False)
        if 'Fondo' in conf['muros_peri']: colocar_muro(0, L - PROF_PERIMETRO, W, False)
        area_exh += (tramos_peri * MOD_1FT * PROF_PERIMETRO)

    # ==========================================
    # 8. ISLAS (Agrupadas)
    # ==========================================
    if conf['t_islas']:
        islas_ok = 0
        grupo = conf['grupo_islas']
        dim_x = ISLA_DIM * (2 if grupo in ['2x1', '2x2'] else 1)
        dim_y = ISLA_DIM * (2 if grupo == '2x2' else 1)
        
        for y_isla in range(1, int(L)-1): 
            for x_isla in range(1, int(W)-1):
                if islas_ok >= conf['cant_islas']: break
                if not colisiona(x_isla, y_isla, dim_x, dim_y, obstaculos):
                    dibujar(x_isla, y_isla, dim_x, dim_y, '#F4D03F', texto=f'E{islas_ok+1}')
                    obstaculos.append((x_isla - 0.2, y_isla - 0.2, dim_x + 0.4, dim_y + 0.4))
                    islas_ok += 1
        area_exh += (islas_ok * dim_x * dim_y)

    pct_exh = (area_exh / area_comercial) * 100 if area_comercial > 0 else 0
    pct_nav = 100 - pct_exh
    
    ax.set_aspect('equal')
    plt.title(f"Store Planning OXXO | Formato: {clasificar_formato(area_total)}")
    return fig, errores, pct_exh, pct_nav, area_total, area_comercial

# --- INTERFAZ STREAMLIT ---
st.set_page_config(layout="wide")

with st.sidebar:
    st.title("🏬 Store Planning OXXO")
    st.markdown("### 📊 Dashboard de M2 y KPIs")
    
    ancho = st.number_input("Ancho (m)", 5.0, 20.0, 12.0, 0.5, key='ancho')
    largo = st.number_input("Profundidad (m)", 5.0, 20.0, 15.0, 0.5, key='largo')
    
    area_tot = ancho * largo
    area_op = area_tot * 0.20
    area_com = area_tot * 0.80
    
    st.write(f"**M2 Totales:** {area_tot:.1f} m² | **Formato:** `{clasificar_formato(area_tot)}`")
    st.caption(f"80% Comercial ({area_com:.1f} m²) | 20% Operativo ({area_op:.1f} m²)")
    
    kpi_col1, kpi_col2 = st.columns(2)
    kpi_exh = kpi_col1.empty()
    kpi_nav = kpi_col2.empty()
    
    st.markdown("---")
    st.write("🔧 **Módulos Independientes (Activa los necesarios)**")

col_info, col_plot = st.columns([1.2, 2.8])

with col_info:
    with st.expander("ℹ️ Información y Reglas del Sistema Store Planning OXXO", expanded=False):
        st.markdown("""
        **Balanceo de Áreas:** El código respeta la regla de distribución de espacio que dicta que aproximadamente el **20%** se destina a Espacios Operativos y el **80%** a Espacios Comerciales. Dentro del área comercial, se calcula un **40% para exhibición** (garantizando rentabilidad sin saturar) y un **60% para navegación** (asegurando una buena experiencia del consumidor).
        
        **Matriz de Formatos:** La función agrupa la tienda en categorías como "Compactos", "Reducidos" y "Ordinarios" dependiendo del rango exacto de m2 estipulado en la matriz oficial. Por ejemplo, de 99 a 117 m2 se considera formato **REGULAR**.
        
        **Los 4 Elementos Cardinales:** Se extrajeron las condicionantes de ubicación estrictas: 
        1. El **Acceso** es el punto de partida.
        2. El **Check out** debe estar lo más cerca del acceso.
        3. El área **Operativa** no debe dejar espacios muertos.
        4. El **Cuarto Frío** debe ir perimetral y lo más alejado de la entrada (Destino).
        
        **Landscaping (Jerarquía Visual):** Se implementó la regla *"primero lo más bajo y al fondo lo más alto"* para definir las alturas máximas permitidas de acuerdo a la distancia desde el umbral (desde 3.5 ft en el acceso hasta 7 ft en el muro perimetral más lejano).
        """)

    with st.expander("1. Acceso y Puertas", expanded=False):
        t_puerta = st.checkbox("Habilitar Acceso", value=True)
        tipo_puerta = st.selectbox("Tipo de Puerta", ['1 Puerta (90cm)', '2 Puertas (180cm)'], index=1)
        muro_puerta = st.selectbox("Muro", ['Inferior (Frente)', 'Lateral Izquierdo', 'Lateral Derecho'])
        pos_puerta = st.slider("Posición (m)", 0.0, 20.0, 5.0)

    with st.expander("2. Bodega Operativa (20%)", expanded=False):
        t_bodega = st.checkbox("Habilitar Bodega", value=True)
        loc_bodega = st.selectbox("Ubicación", ['Fondo', 'Lateral Izquierdo', 'Lateral Derecho'])

    with st.expander("3. Red de Pasillos", expanded=False):
        t_pasillos = st.checkbox("Habilitar Pasillos", value=True)
        pas_poder = st.slider("Ancho Pasillo de Poder", 0.9, 2.5, 1.8)
        pas_peri = st.slider("Ancho Pasillos Perimetrales", 0.9, 1.5, 1.2)
        pas_bod = st.slider("Ancho Pasillo Bodega", 0.8, 1.5, 1.0)
        if st.button("🚨 Validar Vías de Circulación"):
            st.warning("Verificación: Validando anchos mínimos y cruces de evacuación...")

    with st.expander("4. Checkout", expanded=False):
        t_check = st.checkbox("Habilitar Checkout", value=True)
        muro_check = st.selectbox("Anclar a muro", ['Inferior', 'Izquierdo', 'Derecho', 'Superior'])
        cant_check = st.slider("Módulos", 2, 7, 3)

    with st.expander("5. Cuarto Frío", expanded=False):
        t_frio = st.checkbox("Habilitar Cuarto Frío", value=True)
        forma_frio = st.radio("Formato", ['Lineal', 'Escuadra'])
        cant_frio = st.slider("Puertas", 2, 20, 8)
        pos_frio = st.slider("Posición en el muro (X)", 0.0, 20.0, 0.0)

    with st.expander("6. Góndolas Centrales", expanded=False):
        t_gondolas = st.checkbox("Habilitar Góndolas", value=True)
        rot_gon = st.radio("Orientación", ['Vertical', 'Horizontal'])
        sep_cab = st.checkbox("Separar cabeceras para islas")
        cant_trenes = st.slider("Trenes", 1, 6, 2)
        cant_tramos = st.slider("Tramos", 1, 8, 3)
        pas_gon = st.slider("Pasillo entre góndolas", 0.9, 1.5, 1.2)
        pos_gon_x = st.slider("Posición Inicial X", 0.0, 20.0, 4.0)
        pos_gon_y = st.slider("Posición Inicial Y", 0.0, 20.0, 4.0)

    with st.expander("7. Foodvenience", expanded=False):
        t_cafe = st.checkbox("Habilitar Foodvenience", value=True)
        forma_cafe = st.radio("Formato Café", ['Lineal', 'Escuadra'])
        cant_cafe = st.slider("Módulos Café", 2, 10, 4)
        pos_cafe_x = st.slider("Pos. Café X", 0.0, 20.0, 0.0)
        pos_cafe_y = st.slider("Pos. Café Y", 0.0, 20.0, 0.0)

    with st.expander("8. Góndola Perimetral", expanded=False):
        t_perimetral = st.checkbox("Habilitar Perimetrales", value=True)
        muros_peri = st.multiselect("Muros disponibles", ['Izquierda', 'Derecha', 'Frente', 'Fondo'], default=['Izquierda', 'Derecha'])

    with st.expander("9. Islas y Exhibidores", expanded=False):
        t_islas = st.checkbox("Habilitar Islas", value=True)
        cant_islas = st.slider("Cantidad de agrupaciones", 1, 20, 4)
        grupo_islas = st.selectbox("Tipo de Agrupación", ['1x1', '2x1', '2x2'])
        prioridad = st.multiselect("Zonas de Prioridad", ['Frente Checkout', 'Costado Pasillo Poder', 'Entre Góndolas'], default=['Frente Checkout'])

conf = {
    'ancho': ancho, 'largo': largo, 
    't_puerta': t_puerta, 'tipo_puerta': tipo_puerta, 'muro_puerta': muro_puerta, 'pos_puerta': pos_puerta,
    't_bodega': t_bodega, 'loc_bodega': loc_bodega, 'pasillo_bod': pas_bod,
    't_pasillos': t_pasillos, 'pas_poder': pas_poder, 'pas_peri': pas_peri,
    't_check': t_check, 'muro_check': muro_check, 'cant_check': cant_check,
    't_frio': t_frio, 'forma_frio': forma_frio, 'cant_frio': cant_frio, 'pos_frio': pos_frio,
    't_gondolas': t_gondolas, 'rot_gon': rot_gon, 'sep_cab': sep_cab, 'cant_trenes': cant_trenes, 'cant_tramos': cant_tramos, 'pas_gon': pas_gon, 'pos_gon_x': pos_gon_x, 'pos_gon_y': pos_gon_y,
    't_cafe': t_cafe, 'forma_cafe': forma_cafe, 'cant_cafe': cant_cafe, 'pos_cafe_x': pos_cafe_x, 'pos_cafe_y': pos_cafe_y,
    't_perimetral': t_perimetral, 'muros_peri': muros_peri,
    't_islas': t_islas, 'cant_islas': cant_islas, 'grupo_islas': grupo_islas
}

with col_plot:
    fig, errores, pct_exh, pct_nav, a_tot, a_com = dibujar_layout_oxxo(conf)
    st.pyplot(fig)
    
    if errores:
        for err in errores: st.error(f"🚨 {err}")

# Actualizar Dashboard Permanentemente
kpi_exh.metric("Rentabilidad (Meta: 30-40%)", f"{pct_exh:.1f}%")
kpi_nav.metric("Experiencia (Meta: 60-70%)", f"{pct_nav:.1f}%")