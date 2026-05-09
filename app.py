import streamlit as st
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import io
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Taglio Pro - Falegnameria", layout="wide")

# --- GESTIONE LOGO ---
LOGO_PATH = "logo.png"

# --- STATO DELL'APP ---
if 'num_rows' not in st.session_state:
    st.session_state.num_rows = 1

def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.num_rows = 1

# --- INTERFACCIA ---
c_header1, c_header2 = st.columns([1, 4])
with c_header1:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=120)
with c_header2:
    st.title("🪚 Ottimizzatore Professionale")

with st.expander("📝 IMPOSTAZIONI COMMESSA E PANNELLO", expanded=True):
    c_comm1, c_comm2 = st.columns(2)
    cliente = c_comm1.text_input("Nome Cliente", "Cliente Generico")
    materiale = c_comm2.text_input("Materiale", "Multistrato 18mm")
    
    c_pan1, c_pan2, c_pan3 = st.columns(3)
    bin_w = c_pan1.number_input("Lunghezza Pannello REALE (mm)", value=2440)
    bin_h = c_pan2.number_input("Altezza Pannello REALE (mm)", value=1220)
    kerf = c_pan3.number_input("Spessore Lama (mm)", value=3)
    
    rispetta_venatura = st.toggle("Rispetta Venatura (No Rotazione)", value=True)
    if st.button("🗑️ Reset Totale"):
        reset_app()
        st.rerun()

st.divider()

# --- LISTA PEZZI ---
st.header(f"📦 Pezzi da Tagliare (Misure Reali)")
lista_tabella = []
pezzi_input = []

for i in range(st.session_state.num_rows):
    c1, c2, c3, c4 = st.columns(4)
    nome = c1.text_input(f"Pezzo {i+1}", f"P. {i+1}", key=f"n_{i}")
    w = c2.number_input(f"Lungo (mm)", value=400, key=f"w_{i}", min_value=1)
    h = c3.number_input(f"Trasv (mm)", value=300, key=f"h_{i}", min_value=1)
    qta = c4.number_input(f"Q.tà", value=1, key=f"q_{i}", min_value=1)
    
    lista_tabella.append({"Pezzo": nome, "Lungo (mm)": w, "Trasv (mm)": h, "Q.tà": qta})
    for _ in range(qta):
        # Aggiungiamo il kerf per il calcolo, ma terremo traccia della misura netta
        pezzi_input.append({"w_net": w, "h_net": h, "name": nome})

st.button("➕ Aggiungi riga", on_click=lambda: st.session_state.update(num_rows=st.session_state.num_rows + 1))

# --- CALCOLO E PDF ---
if st.button("🚀 GENERA DOCUMENTO COMPLETO", type="primary", use_container_width=True):
    if not pezzi_input:
        st.warning("Inserisci i pezzi!")
    else:
        packer = newPacker(rotation=(not rispetta_venatura))
        for p in pezzi_input:
            packer.add_rect(p["w_net"] + kerf, p["h_net"] + kerf, rid=p["name"])
        packer.add_bin(bin_w, bin_h, count=float("inf"))
        packer.pack()

        st.metric("Pannelli necessari", len(packer))
        df = pd.DataFrame(lista_tabella)

        pdf_buffer = io.BytesIO()
        with PdfPages(pdf_buffer) as pdf:
            data_oggi = datetime.now().strftime("%d/%m/%Y")

            for i, bin_rects in enumerate(packer):
                fig, ax = plt.subplots(figsize=(11.69, 8.27))
                ax.set_xlim(0, bin_w)
                ax.set_ylim(0, bin_h)
                ax.set_aspect('equal')
                
                # Sfondo pannello con misura reale
                ax.add_patch(patches.Rectangle((0, 0), bin_w, bin_h, color="#f3e5ab", alpha=0.1))
                ax.text(bin_w/2, -50, f"LUNGHEZZA PANNELLO REALE: {bin_w} mm", ha='center', fontsize=9, fontweight='bold')
                ax.text(-50, bin_h/2, f"ALTEZZA: {bin_h} mm", va='center', rotation=90, fontsize=9, fontweight='bold')

                for rect in bin_rects:
                    x, y, w, h, rid = rect.x, rect.y, rect.width, rect.height, rect.rid
                    # Disegniamo la misura NETTA (senza kerf) per chiarezza visiva
                    ax.add_patch(patches.Rectangle((x, y), w-kerf, h-kerf, facecolor="#e67e22", edgecolor="black"))
                    # Etichetta con MISURA REALE da tagliare
                    ax.text(x + (w-kerf)/2, y + (h-kerf)/2, f"{rid}\n{int(w-kerf)} x {int(h-kerf)}", 
                            ha='center', va='center', fontsize=7, color='white', fontweight='bold')

                plt.title(f"SCHEMA DI TAGLIO - CLIENTE: {cliente}\nPANNELLO {i+1}/{len(packer)} ({materiale}) - {data_oggi}", pad=20)
                st.pyplot(fig)
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)

            # Pagina Lista Pezzi
            fig_tab, ax_tab = plt.subplots(figsize=(8.27, 11.69))
            ax_tab.axis('off')
            ax_tab.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center')
            plt.title(f"RIEPILOGO TAGLI REALI - {cliente}\nMateriale: {materiale}", pad=30)
            pdf.savefig(fig_tab)
            plt.close(fig_tab)

        st.download_button(
            label="📄 SCARICA PDF PER OFFICINA",
            data=pdf_buffer.getvalue(),
            file_name=f"Taglio_{cliente}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
