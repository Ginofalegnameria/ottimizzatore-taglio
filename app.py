import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configurazione Pagina
st.set_page_config(page_title="Taglio Pannelli Falegnameria", layout="wide")

st.title("🪚 Ottimizzatore di Taglio per Falegnami")
st.write("Inserisci le misure e genera lo schema di taglio ottimizzato.")

# --- INPUT DIMENSIONI PANNELLO ---
st.sidebar.header("1. Dimensioni Pannello Grezzo")
bin_w = st.sidebar.number_input("Lunghezza Pannello (mm)", value=2440)
bin_h = st.sidebar.number_input("Altezza Pannello (mm)", value=1220)
kerf = st.sidebar.number_input("Spessore Lama / Sfrido (mm)", value=3)

# --- GESTIONE LISTA PEZZI ---
if 'num_rows' not in st.session_state:
    st.session_state.num_rows = 1

st.header("2. Lista Pezzi da Ricavare")
pezzi_da_tagliare = []

for i in range(st.session_state.num_rows):
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    nome = c1.text_input(f"Nome pezzo {i+1}", f"Pezzo {i+1}", key=f"n_{i}")
    w = c2.number_input(f"Largh. (mm)", value=400, key=f"w_{i}")
    h = c3.number_input(f"Alt. (mm)", value=300, key=f"h_{i}")
    qta = c4.number_input(f"Q.tà", value=1, key=f"q_{i}")
    for _ in range(qta):
        # Aggiungiamo il kerf alla misura per riservare lo spazio della lama
        pezzi_da_tagliare.append((w + kerf, h + kerf, nome))

if st.button("➕ Aggiungi altra tipologia di pezzo"):
    st.session_state.num_rows += 1
    st.rerun()

# --- CALCOLO E VISUALIZZAZIONE ---
if st.button("🚀 GENERA SCHEMA DI TAGLIO"):
    if not pezzi_da_tagliare:
        st.warning("Aggiungi almeno un pezzo!")
    else:
        packer = newPacker(rotation=True)
        for p in pezzi_da_tagliare:
            # Carichiamo i pezzi nel sistema
            packer.add_rect(p[0], p[1], rid=p[2])
        
        packer.add_bin(bin_w, bin_h)
        packer.pack()

        all_rects = packer.rect_list()

        if len(all_rects) < len(pezzi_da_tagliare):
            st.error(f"Attenzione: Solo {len(all_rects)} su {len(pezzi_da_tagliare)} pezzi entrano nel pannello!")
        
        st.subheader("Schema di posizionamento:")
        
        # Disegno grafico
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_xlim(0, bin_w)
        ax.set_ylim(0, bin_h)
        ax.set_aspect('equal')
        
        # Sfondo del pannello
        ax.add_patch(patches.Rectangle((0, 0), bin_w, bin_h, color="#dfe6e9", label="Scarto"))

        for rect in all_rects:
            b, x, y, w, h, rid = rect
            # Disegniamo il pezzo (togliendo visivamente lo spazio lama per chiarezza)
            ax.add_patch(patches.Rectangle((x, y), w-kerf, h-kerf, facecolor="#0984e3", edgecolor="black", linewidth=1))
            ax.text(x + w/2, y + h/2, f"{rid}\n{int(w-kerf)}x{int(h-kerf)}", 
                    ha='center', va='center', fontsize=7, color='white', fontweight='bold')

        plt.title(f"Pannello {bin_w}x{bin_h} mm")
        st.pyplot(fig)
        
        st.success("Ottimizzazione completata. Puoi fare uno screenshot e inviarlo ai colleghi!")
