import streamlit as st
import subprocess
import os
import tempfile
import shutil
import zipfile
from pathlib import Path

# Konfiguracja strony
st.set_page_config(page_title="EXIF Spoofer RAW Web", layout="centered")

st.title("📷 EXIF Spoofer v2.3.2 (Web Edition)")
st.markdown("### Narzędzie do zmiany Make/Model w plikach RAW i JPG")
st.warning("Ta aplikacja działa w chmurze. Uruchamia prawdziwego ExifTool'a, więc obsługuje pliki RAW (NEF, DNG, ARW itp.).")

# --- SPRAWDZANIE EXIFTOOL ---
def get_exiftool_path():
    # W środowisku Streamlit Cloud (Linux) exiftool będzie zainstalowany w /usr/bin/exiftool
    if shutil.which("exiftool"):
        return "exiftool"
    return None

EXIFTOOL_PATH = get_exiftool_path()

if not EXIFTOOL_PATH:
    st.error("❌ Nie znaleziono ExifTool w systemie! Upewnij się, że plik packages.txt zawiera 'libimage-exiftool-perl'.")
    st.stop()

# --- GUI ---
col1, col2 = st.columns(2)
with col1:
    make_input = st.text_input("Make (Producent)", value="NIKON CORPORATION")
with col2:
    model_input = st.text_input("Model (Aparat)", value="Coolpix P1000")

uploaded_files = st.file_uploader(
    "Wybierz pliki (RAW lub JPG)", 
    accept_multiple_files=True,
    help="Obsługiwane formaty: DNG, NRW, NEF, CR2, ARW, JPG, PNG i inne wspierane przez ExifTool."
)

# --- LOGIKA PRZETWARZANIA ---
if st.button("Start Processing", type="primary", disabled=not uploaded_files):
    if not make_input or not model_input:
        st.error("Uzupełnij pola Make i Model!")
    else:
        # Pasek postępu
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Katalog tymczasowy na sesję
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            processed_files = []
            
            total_files = len(uploaded_files)
            
            for i, uploaded_file in enumerate(uploaded_files):
                # 1. Zapisz przesłany plik na dysku serwera
                file_path = temp_path / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                status_text.text(f"Przetwarzanie: {uploaded_file.name}...")
                
                # 2. Uruchom ExifTool (to samo co w Twoim skrypcie)
                try:
                    cmd = [
                        EXIFTOOL_PATH,
                        "-api", "Validate=0",
                        f"-Make={make_input}",
                        f"-Model={model_input}",
                        f"-UniqueCameraModel={model_input}",
                        "-overwrite_original",
                        "-m",  # ignoruj drobne błędy
                        str(file_path)
                    ]
                    # Uruchom proces
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    processed_files.append(file_path)
                    
                except subprocess.CalledProcessError:
                    st.error(f"Błąd przy przetwarzaniu pliku: {uploaded_file.name}")
                
                # Aktualizacja paska
                progress_bar.progress((i + 1) / total_files)

            # 3. Pakowanie do ZIP
            if processed_files:
                status_text.text("Generowanie pliku ZIP...")
                zip_path = temp_path / "spoofed_photos.zip"
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file in processed_files:
                        zipf.write(file, file.name)
                
                # 4. Przycisk pobierania
                with open(zip_path, "rb") as f:
                    st.success(f"Gotowe! Przetworzono {len(processed_files)} plików.")
                    st.download_button(
                        label="📥 Pobierz ZIP",
                        data=f,
                        file_name="spoofed_photos.zip",
                        mime="application/zip"
                    )
            else:
                st.warning("Nie udało się przetworzyć żadnych plików.")