import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
from datetime import datetime

st.set_page_config(page_title="Taglio Pro - Falegnameria", layout="wide")

st.title("🪚 Ottimizzatore Taglio Professionale")

# --- SIDEBAR: DATI COMMESSA E PANNELLO ---
st.sidebar.header("📋 Dati Commessa")
cliente = st.sidebar.text_input("Nome Cliente / Commessa", "Cliente Generico")
materiale = st.sidebar.text_input("Tipo Materiale", "Multistrato 18mm")

st.sidebar.header("📏 Impostazioni Pannello")
bin_w = st.sidebar.number_input("Lunghezza Pannello (mm)", value=2440)
bin_h = st.sidebar.number_input("Altezza Pannello (mm)", value=1220)
kerf = st.sidebar.number_input("Spessore Lama (mm)", value=3)
rispetta_venatura = st.sidebar.toggle("Rispetta Venatura (No Rotazione)", value=True)

# --- LISTA PEZZI ---
if 'num_rows' not in st.session_state:
    st.session_state.num_rows = 1

st.header(f"📦 Lista Pezzi: {cliente}")
pezzi_input = []
for i in range(st.session_state.num_rows):
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    nome = c1.text_input(f"Pezzo {i+1}", f"Pezzo {i+1}", key=f"n_{i}")
    w = c2.number_input(f"Lungo V. (mm)", value=400, key=f"w_{i}")
    h = c3.number_input(f"Trasv. V. (mm)", value=300, key=f"h_{i}")
    qta = c4.number_input(f"Q.tà", value=1, key=f"q_{i}", min_value=1)
    for _ in range(qta):
        pezzi_input.append((w + kerf, h + kerf, nome))

if st.button("➕ Aggiungi riga"):
    st.session_state.num_rows += 1
    st.rerun()

# --- CALCOLO E PDF ---
if st.button("🚀 GENERA SCHEMI E PDF"):
    if not pezzi_input:
        st.warning("Inserisci almeno un pezzo!")
    else:
        packer = newPacker(rotation=(not rispetta_venatura))
        for p in pezzi_input:
            packer.add_rect(p, p, rid=p)
        packer.add_bin(bin_w, bin_h, count=float("inf"))
        packer.pack()

        nbins = len(packer)
        st.metric("Pannelli totali", nbins)
        
        pdf_buffer = io.BytesIO()
        data_oggi = datetime.now().strftime("%d/%m/%Y")

        for i, bin_rects in enumerate(packer):
            st.subheader(f"Pannello n. {i+1}")
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.set_xlim(0, bin_w)
            ax.set_ylim(0, bin_h)
            ax.set_aspect('equal')
            
            # Sfondo e grafica venatura
            ax.add_patch(patches.Rectangle((0, 0), bin_w, bin_h, color="#f3e5ab", alpha=0.1))
            if rispetta_venatura:
                for line in range(0, bin_h, 100):
                    ax.axhline(y=line, color='#dcdde1', linewidth=0.5, alpha=0.2)

            for rect in bin_rects:
                x, y, w, h, rid = rect.x, rect.y, rect.width, rect.height, rect.rid
                ax.add_patch(patches.Rectangle((x, y), w-kerf, h-kerf, 
                                             facecolor="#e67e22", edgecolor="black", linewidth=1))
                ax.text(x + w/2, y + h/2, f"{rid}\n{int(w-kerf)}x{int(h-kerf)}", 
                        ha='center', va='center', fontsize=8, color='white', fontweight='bold')

            # Intestazione sul disegno
            plt.title(f"CLIENTE: {cliente} | MAT: {materiale}\nPannello {i+1} di {nbins} ({bin_w}x{bin_h}mm) - {data_oggi}", 
                      fontsize=10, pad=20)
            
            st.pyplot(fig)
            fig.savefig(pdf_buffer, format='pdf', bbox_inches='tight')
            st.divider()

        # Download button
        st.download_button(
            label="📄 SCARICA PDF PER L'OFFICINA",
            data=pdf_buffer.getvalue(),
            file_name=f"Taglio_{cliente.replace(' ', '_')}_{materiale.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

