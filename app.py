import streamlit as st
from streamlit_sheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")

@st.cache_data(ttl=300)
def load_data():
    conn = st.experimental_connection("gsheets", type=GSheetsConnection)
    data = conn.read(worksheet="daftar_nama", usecols=list(range(5)))
    data = data.dropna(how="all")
    return data

data = load_data()
calon_mitra = data
calon_mitra["nik"] = calon_mitra["nik"].astype(str)

# Tambahkan kolom checkbox
calon_mitra["Check"] = [False] * len(calon_mitra)

# Inisialisasi session state
if 'data_kehadiran' not in st.session_state:
    # Filter calon_mitra yang kolom waktu tidak kosong
    data_kehadiran_init = calon_mitra[calon_mitra['waktu'].notnull()]

    # Buat DataFrame baru untuk data_kehadiran
    st.session_state.data_kehadiran = pd.DataFrame(data_kehadiran_init, columns=["nik", "nama", "posisi_daftar", "waktu", "nomor_urut"])


# Fungsi untuk menambahkan kehadiran
def tambah_kehadiran(nik, nama, posisi_daftar):
    waktu = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nomor_urut = len(st.session_state.data_kehadiran) + 1
    st.session_state.data_kehadiran.loc[len(st.session_state.data_kehadiran)] = [nik, nama, posisi_daftar, waktu, nomor_urut]
    
    # Lakukan pembaruan data waktu dan nomor urut pada calon_mitra
    calon_mitra.loc[calon_mitra["nik"] == nik, "waktu"] = waktu
    calon_mitra.loc[calon_mitra["nik"] == nik, "nomor_urut"] = nomor_urut
    conn = st.experimental_connection("gsheets", type=GSheetsConnection)
    conn.update(worksheet="daftar_nama", data=calon_mitra)


def main(): 
    st.title("Daftar Hadir Wawancara Rekrutmen Mitra Statistik BPS Kabupaten Kepulauan Sula 2024")

    cari_nama = st.text_input("Cari nama:")

    # Formulir untuk mencari nama dan menambah kehadiran
    with st.form(key="kehadiran_form", clear_on_submit = True):
        # Tampilkan daftar nama berdasarkan pencarian
        if cari_nama != "":
            daftar_nama = calon_mitra[calon_mitra["nama"].str.contains(cari_nama, case=False)]
            st.write("Daftar nama:")
            daftar_nama = st.data_editor(
                daftar_nama[["nik", "nama", "posisi_daftar", "Check"]], 
                column_config= {
                    "nama": "nama Calon Mitra",
                    "posisi_daftar": "Posisi Daftar",
                    "Check": "Pilih Calon Mitra"
                },
                use_container_width=True, 
                hide_index=True,
                disabled=["nama", "posisi_daftar"])
            
            tombol_submit = st.form_submit_button("Tambah Kehadiran")

            st.write(tombol_submit)

            # Pilih nama dari hasil pencarian
            # Pilih nama dari hasil pencarian
            if tombol_submit:
                selected_data = daftar_nama[daftar_nama["Check"]]
                if not selected_data.empty:
                    nama_berhasil_ditambahkan = []  # Inisialisasi list untuk menyimpan nama yang berhasil ditambahkan
                    for index, row in selected_data.iterrows():
                        if row["nama"] not in st.session_state.data_kehadiran["nama"].values:
                            tambah_kehadiran(row["nik"], row["nama"], row["posisi_daftar"])
                            nama_berhasil_ditambahkan.append(row["nama"])  # Tambahkan nama ke list
                    if nama_berhasil_ditambahkan:
                        st.success(f"Berhasil menambah kehadiran untuk {', '.join(nama_berhasil_ditambahkan)}. Total data kehadiran sekarang: {len(st.session_state.data_kehadiran)}")
                    else:
                        st.warning("Tidak ada nama yang ditambahkan karena sudah ada sebelumnya.")
                elif selected_data.empty:
                    st.warning("Tidak ada nama yang dipilih.")


    # Tampilkan data kehadiran
    st.write("Data Kehadiran:")
    st.dataframe(
        st.session_state.data_kehadiran.sort_values(by="nomor_urut"),
        column_config={
            "nik": "NIK",
            "nama": "Nama Calon Mitra",
            "posisi_daftar": "Posisi Daftar",
            "waktu": "Waktu",
            "nomor_urut": "Nomor Urut"
        },
        use_container_width=True, 
        hide_index=True)

if __name__ == "__main__":
    main()
