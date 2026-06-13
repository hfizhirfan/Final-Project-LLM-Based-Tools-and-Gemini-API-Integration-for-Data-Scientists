# TravelBuddy AI

TravelBuddy AI adalah chatbot Streamlit untuk membantu rekomendasi perjalanan, destinasi, landmark, itinerary, kuliner, dan estimasi budget. Aplikasi memakai Gemini API dan menyimpan riwayat chat lokal di `chat_history.json`.

## Prasyarat

- Python 3.10 atau lebih baru
- Gemini API key dari Google AI Studio
- Koneksi internet saat aplikasi memanggil Gemini API

## Setup Project

1. Masuk ke folder project.

```powershell
cd e:\iseng\gemini_chatbot_project
```

2. Buat virtual environment.

```powershell
python -m venv env
```

3. Aktifkan virtual environment.

```powershell
.\env\Scripts\Activate.ps1
```

Jika PowerShell menolak menjalankan script, jalankan:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\env\Scripts\Activate.ps1
```

4. Install dependency.

```powershell
pip install -r requirements.txt
```

## Setup API Key

1. Salin file `.env.example` menjadi `.env`.

```powershell
Copy-Item .env.example .env
```

2. Isi `.env` dengan Gemini API key.

```env
GEMINI_API_KEY=isi_api_key_kamu_di_sini
```

API key bisa dibuat dari Google AI Studio.

## Menjalankan Aplikasi

Pastikan virtual environment aktif, lalu jalankan:

```powershell
streamlit run app.py
```

Buka aplikasi di browser:

```text
http://localhost:8501
```

## Fitur Utama

- Chatbot TravelBuddy untuk pertanyaan wisata, daerah, negara, landmark, dan rekomendasi perjalanan
- RAG dengan LangChain untuk menjawab berdasarkan dokumen PDF/TXT/MD yang diupload
- History chat di sidebar kiri
- Tombol `Chat baru`
- Tombol `Hapus chat ini`
- Tombol `Reset chat`
- Penyimpanan riwayat lokal di `chat_history.json`
- Filter pertanyaan di luar topik travel agar tidak memakai kuota Gemini

## Menggunakan RAG

1. Jalankan aplikasi seperti biasa.
2. Di sidebar kiri, buka bagian `Knowledge base`.
3. Upload satu atau beberapa file `PDF`, `TXT`, atau `MD`.
4. Klik `Proses dokumen`.
5. Setelah muncul pesan bahwa knowledge base siap, ajukan pertanyaan tentang isi dokumen.

Saat knowledge base aktif, pertanyaan akan dicari dulu ke dokumen menggunakan LangChain dan Gemini Embeddings. Konteks hasil pencarian dikirim ke Gemini agar jawabannya lebih sesuai dengan dokumen.

## Catatan Penggunaan

Jika muncul error `429 ResourceExhausted`, artinya kuota Gemini API sedang habis atau terkena rate limit. Tunggu beberapa detik sampai satu menit, lalu coba lagi.

Jika sidebar atau tampilan belum berubah setelah update kode, lakukan hard refresh di browser:

```text
Ctrl + F5
```

## Struktur File

```text
gemini_chatbot_project/
+-- app.py              # Aplikasi utama Streamlit
+-- requirements.txt    # Dependency project
+-- .env.example        # Contoh konfigurasi environment
+-- .env                # API key lokal, jangan dibagikan
+-- chat_history.json   # Riwayat chat lokal
+-- .streamlit/
    +-- config.toml     # Konfigurasi tema Streamlit
```

## Keamanan

Jangan upload atau membagikan file `.env`, karena berisi API key pribadi.
