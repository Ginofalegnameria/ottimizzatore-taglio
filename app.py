import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import io
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Taglio Pro - Falegnameria", layout="wide")

# --- INIZIALIZZAZIONE STATO ---
if 'num_rows' not in st.session_state:
    st.session_state.num_rows = 1

def reset_app():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.session_state.num_rows = 1

# --- INTERFACCIA ---
st.title("🪚 Ottimizzatore Taglio Professionale")

st.sidebar.header("📋 Dati Commessa")
cliente = st.sidebar.text_input("Nome Cliente / Commessa", "Cliente Generico")
materiale = st.sidebar.text_input("Tipo Materiale", "Multistrato 18mm")

st.sidebar.header("📏 Impostazioni Pannello")
bin_w = st.sidebar.number_input("Lunghezza Pannello (mm)", value=2440)
bin_h = st.sidebar.number_input("Altezza Pannello (mm)", value=1220)
kerf = st.sidebar.number_input("Spessore Lama (mm)", value=3)
rispetta_venatura = st.sidebar.toggle("Rispetta Venatura (No Rotazione)", value=True)

st.sidebar.divider()
st.sidebar.button("🗑️ Reset Totale", on_click=reset_app, type="secondary")

st.header(f"📦 Lista Pezzi: {cliente}")
lista_per_tabella = []
pezzi_input = []

for i in range(st.session_state.num_rows):
    c1, c2, c3, c4 = st.columns(4)
    nome = c1.text_input(f"Pezzo {i+1}", f"Pezzo {i+1}", key=f"n_{i}")
    w = c2.number_input(f"Lungo V. (mm)", value=400, key=f"w_{i}", min_value=1)
    h = c3.number_input(f"Trasv. V. (mm)", value=300, key=f"h_{i}", min_value=1)
    qta = c4.number_input(f"Q.tà", value=1, key=f"q_{i}", min_value=1)
    
    lista_per_tabella.append({"Nome": nome, "Lungo V. (mm)": w, "Trasv. V. (mm)": h, "Q.tà": qta})
    for _ in range(qta):
        pezzi_input.append({"width": w + kerf, "height": h + kerf, "name": nome})

st.button("➕ Aggiungi riga", on_click=lambda: st.session_state.update(num_rows=st.session_state.num_rows + 1))

# --- CALCOLO E GENERAZIONE PDF ---
if st.button("🚀 GENERA SCHEMI E PDF", type="primary"):
    if not pezzi_input:
        st.warning("Inserisci almeno un pezzo!")
    else:
        packer = newPacker(rotation=(not rispetta_venatura))
        for p in pezzi_input:
            packer.add_rect(p["width"], p["height"], rid=p["name"])
        packer.add_bin(bin_w, bin_h, count=float("inf"))
        packer.pack()

        st.metric("Pannelli totali necessari", len(packer))
        
        # Mostra tabella riassuntiva nell'app
        df = pd.DataFrame(lista_per_tabella)
        st.table(df)

        pdf_buffer = io.BytesIO()
        data_oggi = datetime.now().strftime("%d/%m/%Y")

        # Generazione Grafici per ogni Pannello
        for i, bin_rects in enumerate(packer):
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.set_xlim(0, bin_w)
            ax.set_ylim(0, bin_h)
            ax.set_aspect('equal')
            ax.add_patch(patches.Rectangle((0, 0), bin_w, bin_h, color="#f3e5ab", alpha=0.1))
            
            if rispetta_venatura:
                for line in range(0, int(bin_h), 100):
                    ax.axhline(y=line, color='#dcdde1', linewidth=0.5, alpha=0.2)

            for rect in bin_rects:
                x, y, w, h, rid = rect.x, rect.y, rect.width, rect.height, rect.rid
                ax.add_patch(patches.Rectangle((x, y), w-kerf, h-kerf, facecolor="#e67e22", edgecolor="black", linewidth=1))
                ax.text(x + w/2, y + h/2, f"{rid}\n{int(w-kerf)}x{int(h-kerf)}", ha='center', va='center', fontsize=8, color='white', fontweight='bold')

            plt.title(f"COMMESSA: {cliente} | MAT: {materiale}\nPANNELLO {i+1}/{len(packer)} ({bin_w}x{bin_h}mm) - {data_oggi}")
            st.pyplot(fig)
            fig.savefig(pdf_buffer, format='pdf', bbox_inches='tight')
            plt.close(fig)

        # Aggiunta tabella dati in fondo al PDF (come immagine per semplicità tecnica)
        fig_tab, ax_tab = plt.subplots(figsize=(8, len(df)*0.5 + 1))
        ax_tab.axis('off')
        tab = ax_tab.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
        tab.auto_set_font_size(False)
        tab.set_fontsize(10)
        plt.title(f"LISTA TAGLI - {cliente}", pad=20)
        fig_tab.savefig(pdf_buffer, format='pdf', bbox_inches='tight')
        plt.close(fig_tab)

        st.download_button(
            label="📄 SCARICA PDF COMPLETO (Schemi + Lista)",
            data=pdf_buffer.getvalue(),
            file_name=f"Ordine_Taglio_{cliente.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
