import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="Ottimizzatore Tagli Multi-Pannello", layout="wide")

st.title("🪚 Ottimizzatore Multi-Pannello")
st.write("L'app userà tutti i pannelli necessari per completare l'ordine.")

# --- SIDEBAR ---
st.sidebar.header("1. Dimensioni Pannello Grezzo")
bin_w = st.sidebar.number_input("Lunghezza Pannello (mm)", value=2440)
bin_h = st.sidebar.number_input("Altezza Pannello (mm)", value=1220)
kerf = st.sidebar.number_input("Spessore Lama (mm)", value=3)

# --- LISTA PEZZI ---
if 'num_rows' not in st.session_state:
    st.session_state.num_rows = 1

st.header("2. Lista Pezzi")
pezzi_input = []
for i in range(st.session_state.num_rows):
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    nome = c1.text_input(f"Nome pezzo {i+1}", f"Pezzo {i+1}", key=f"n_{i}")
    w = c2.number_input(f"Largh. (mm)", value=400, key=f"w_{i}")
    h = c3.number_input(f"Alt. (mm)", value=300, key=f"h_{i}")
    qta = c4.number_input(f"Q.tà", value=1, key=f"q_{i}", min_value=1)
    for _ in range(qta):
        pezzi_input.append((w + kerf, h + kerf, nome))

if st.button("➕ Aggiungi riga"):
    st.session_state.num_rows += 1
    st.rerun()

# --- CALCOLO ---
if st.button("🚀 CALCOLA E DISEGNA"):
    if not pezzi_input:
        st.warning("Inserisci almeno un pezzo!")
    else:
        # Usiamo un packer che apre nuovi "bin" (pannelli) se necessario
        packer = newPacker(rotation=True)
        for p in pezzi_input:
            packer.add_rect(p[0], p[1], rid=p[2])
        
        # Aggiungiamo un numero potenzialmente infinito di pannelli
        packer.add_bin(bin_w, bin_h, count=float("inf"))
        packer.pack()

        # Risultati
        nbins = len(packer)
        st.metric("Pannelli totali necessari", nbins)

        # Disegniamo ogni pannello utilizzato
        for i, bin_rects in enumerate(packer):
            st.subheader(f"Pannello n. {i+1}")
            
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.set_xlim(0, bin_w)
            ax.set_ylim(0, bin_h)
            ax.set_aspect('equal')
            
            # Colore di sfondo (sfrido)
            ax.add_patch(patches.Rectangle((0, 0), bin_w, bin_h, color="#dfe6e9"))

            for rect in bin_rects:
                # rect = [bin_index, x, y, width, height, rid]
                x, y, w, h, rid = rect.x, rect.y, rect.width, rect.height, rect.rid
                
                # Disegno pezzo
                ax.add_patch(patches.Rectangle((x, y), w-kerf, h-kerf, 
                                             facecolor="#0984e3", edgecolor="black", linewidth=0.5))
                # Testo
                ax.text(x + w/2, y + h/2, f"{rid}\n{int(w-kerf)}x{int(h-kerf)}", 
                        ha='center', va='center', fontsize=6, color='white', fontweight='bold')

            plt.title(f"Schema Taglio Pannello {i+1}")
            st.pyplot(fig)
            st.divider()

        st.success(f"Tutti i pezzi sono stati posizionati su {nbins} pannelli.")
