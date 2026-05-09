import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="Ottimizzatore Tagli con Venatura", layout="wide")

st.title("🪚 Ottimizzatore con Gestione Venatura")
st.write("Seleziona 'Rispetta Venatura' per evitare la rotazione dei pezzi.")

# --- SIDEBAR ---
st.sidebar.header("1. Impostazioni Pannello")
bin_w = st.sidebar.number_input("Lunghezza Pannello (mm) - Lungo venatura", value=2440)
bin_h = st.sidebar.number_input("Altezza Pannello (mm) - Traverso venatura", value=1220)
kerf = st.sidebar.number_input("Spessore Lama (mm)", value=3)
# INTERRUTTORE VENATURA
rispetta_venatura = st.sidebar.toggle("Rispetta Venatura (No Rotazione)", value=True)

# --- LISTA PEZZI ---
if 'num_rows' not in st.session_state:
    st.session_state.num_rows = 1

st.header("2. Lista Pezzi")
pezzi_input = []
for i in range(st.session_state.num_rows):
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    nome = c1.text_input(f"Nome pezzo {i+1}", f"Pezzo {i+1}", key=f"n_{i}")
    w = c2.number_input(f"Lungo V. (mm)", value=400, key=f"w_{i}")
    h = c3.number_input(f"Trasv. V. (mm)", value=300, key=f"h_{i}")
    qta = c4.number_input(f"Q.tà", value=1, key=f"q_{i}", min_value=1)
    for _ in range(qta):
        pezzi_input.append((w + kerf, h + kerf, nome))

if st.button("➕ Aggiungi riga"):
    st.session_state.num_rows += 1
    st.rerun()

# --- CALCOLO ---
if st.button("🚀 GENERA SCHEMA"):
    if not pezzi_input:
        st.warning("Inserisci almeno un pezzo!")
    else:
        # Se 'rispetta_venatura' è True, disabilitiamo la rotazione
        packer = newPacker(rotation=(not rispetta_venatura))
        
        for p in pezzi_input:
            packer.add_rect(p, p, rid=p)
        
        packer.add_bin(bin_w, bin_h, count=float("inf"))
        packer.pack()

        nbins = len(packer)
        st.metric("Pannelli totali necessari", nbins)
        if rispetta_venatura:
            st.info("ℹ️ Modalità Venatura ATTIVA: i pezzi non sono stati ruotati.")

        for i, bin_rects in enumerate(packer):
            st.subheader(f"Pannello n. {i+1}")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.set_xlim(0, bin_w)
            ax.set_ylim(0, bin_h)
            ax.set_aspect('equal')
            
            # Sfondo (mostriamo delle linee leggere per simulare la venatura)
            ax.add_patch(patches.Rectangle((0, 0), bin_w, bin_h, color="#f3e5ab", alpha=0.3))
            for line in range(0, bin_h, 50):
                ax.axhline(y=line, color='#dcdde1', linestyle='-', linewidth=0.5, alpha=0.3)

            for rect in bin_rects:
                x, y, w, h, rid = rect.x, rect.y, rect.width, rect.height, rect.rid
                ax.add_patch(patches.Rectangle((x, y), w-kerf, h-kerf, 
                                             facecolor="#d35400", edgecolor="black", linewidth=0.8))
                ax.text(x + w/2, y + h/2, f"{rid}\n{int(w-kerf)}x{int(h-kerf)}", 
                        ha='center', va='center', fontsize=7, color='white', fontweight='bold')

            plt.title(f"Schema Taglio Pannello {i+1}")
            st.pyplot(fig)
            st.divider()

