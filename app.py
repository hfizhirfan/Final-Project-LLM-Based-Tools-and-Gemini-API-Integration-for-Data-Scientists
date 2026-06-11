import os
import json
import re
import uuid
from datetime import datetime

import google.generativeai as genai
import streamlit as st
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

HISTORY_FILE = "chat_history.json"

generation_config = {
    "temperature": 0.7,
}

system_instruction = """
Kamu adalah TravelBuddy, asisten perjalanan virtual yang ahli tentang pariwisata.
Gaya bahasamu santai, ramah, dan menggunakan kata ganti 'aku' dan 'kamu'.
Selalu berikan rekomendasi tempat, kuliner, aktivitas, dan estimasi budget jika memungkinkan.
Kamu hanya boleh menjawab pertanyaan tentang perjalanan, wisata, itinerary, destinasi,
transportasi liburan, akomodasi, kuliner untuk perjalanan, oleh-oleh, dan budget wisata
atau pertanyaan umum tentang nama daerah, kota, pulau, provinsi, dan negara.
Jika pengguna menanyakan daerah atau negara, beri jawaban umum singkat, lalu tekankan
landmark/tempat ikoniknya dan berikan rekomendasi wisata yang relevan.
Jika pengguna membandingkan dua daerah, jelaskan perbedaannya secara natural:
lokasi administratif, karakter suasana, landmark/tempat ikonik, dan rekomendasi singkat.
Jika pengguna bertanya di luar topik itu, jangan jawab isi pertanyaannya.
Jawab persis dengan penolakan singkat dan arahkan ke pertanyaan rekomendasi wisata.
"""

model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
    system_instruction=system_instruction,
)


def load_conversations():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            conversations = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    return conversations if isinstance(conversations, list) else []


def save_conversations():
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(st.session_state.conversations, file, ensure_ascii=False, indent=2)


def new_conversation():
    conversation = {
        "id": str(uuid.uuid4()),
        "title": "Chat baru",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "messages": [],
    }
    st.session_state.conversations.insert(0, conversation)
    st.session_state.active_conversation_id = conversation["id"]
    save_conversations()


def get_active_conversation():
    for conversation in st.session_state.conversations:
        if conversation["id"] == st.session_state.active_conversation_id:
            return conversation

    if not st.session_state.conversations:
        new_conversation()
        return st.session_state.conversations[0]

    st.session_state.active_conversation_id = st.session_state.conversations[0]["id"]
    return st.session_state.conversations[0]


def gemini_history(messages):
    return [
        {
            "role": "model" if message["role"] == "assistant" else "user",
            "parts": [message["content"]],
        }
        for message in messages
    ]


def title_from_prompt(prompt):
    clean_prompt = " ".join(prompt.split())
    return clean_prompt[:42] + ("..." if len(clean_prompt) > 42 else "")


TRAVEL_KEYWORDS = {
    "akomodasi",
    "aktivitas",
    "bandara",
    "budget",
    "camping",
    "candi",
    "city tour",
    "desa wisata",
    "destinasi",
    "explore",
    "gunung",
    "healing",
    "hotel",
    "itinerary",
    "jalan-jalan",
    "jalan jalan",
    "kuliner",
    "liburan",
    "oleh-oleh",
    "pantai",
    "penginapan",
    "pesawat",
    "pulau",
    "rekomendasi",
    "rental",
    "resort",
    "staycation",
    "tempat wisata",
    "tiket",
    "tour",
    "transportasi",
    "travel",
    "trip",
    "villa",
    "wisata",
}

INDONESIA_PLACES = {
    "aceh",
    "bali",
    "bandung",
    "banyuwangi",
    "bogor",
    "bromo",
    "flores",
    "jakarta",
    "jawa",
    "jogja",
    "yogyakarta",
    "kalimantan",
    "komodo",
    "lombok",
    "malang",
    "medan",
    "padang",
    "papua",
    "purwakarta",
    "purwokerto",
    "raja ampat",
    "semarang",
    "solo",
    "sulawesi",
    "sumatra",
    "surabaya",
}


WORLD_PLACES = {
    "afrika selatan",
    "amerika serikat",
    "arab saudi",
    "argentina",
    "australia",
    "belanda",
    "brasil",
    "brunei",
    "beijing",
    "china",
    "filipina",
    "guangzhou",
    "hong kong",
    "india",
    "inggris",
    "italia",
    "jepang",
    "jerman",
    "kanada",
    "kamboja",
    "korea",
    "korea selatan",
    "laos",
    "leeds",
    "liverpool",
    "london",
    "manchester",
    "malaysia",
    "mekah",
    "mesir",
    "myanmar",
    "newcastle",
    "new york",
    "paris",
    "papua nugini",
    "perancis",
    "prancis",
    "qatar",
    "rusia",
    "selandia baru",
    "shanghai",
    "shenzhen",
    "singapura",
    "spanyol",
    "swiss",
    "taiwan",
    "thailand",
    "timor leste",
    "turki",
    "uni emirat arab",
    "vietnam",
}

PLACE_QUESTION_KEYWORDS = {
    "apa itu",
    "di mana",
    "dimana",
    "negara",
    "kota",
    "daerah",
    "provinsi",
    "pulau",
    "landmark",
    "ikonik",
}

LOCATION_QUESTION_PATTERNS = {
    "dimana letak",
    "di mana letak",
    "dimana lokasi",
    "di mana lokasi",
    "letak ",
    "lokasi ",
}

COMPARISON_QUESTION_PATTERNS = {
    "berbeda",
    "beda",
    "perbedaan",
    "sama atau",
    "bedanya",
}

NON_PLACE_TERMS = {
    "mata",
    "telinga",
    "hidung",
    "mulut",
    "otak",
    "jantung",
    "komputer",
    "internet",
}

CAPITALIZED_NON_PLACE_WORDS = {
    "Aku",
    "Apa",
    "Apakah",
    "Coba",
    "Dimana",
    "Di",
    "Itu",
    "Saya",
}


def has_place_name_hint(prompt):
    candidates = re.findall(r"\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\b", prompt)
    for candidate in candidates:
        words = candidate.split()
        if all(word in CAPITALIZED_NON_PLACE_WORDS for word in words):
            continue
        if candidate.lower() in NON_PLACE_TERMS:
            continue
        return True

    return False


def is_travel_question(prompt):
    clean_prompt = prompt.lower()
    known_places = INDONESIA_PLACES | WORLD_PLACES
    if any(keyword in clean_prompt for keyword in TRAVEL_KEYWORDS | known_places):
        return True

    if any(pattern in clean_prompt for pattern in LOCATION_QUESTION_PATTERNS):
        return True

    has_place_intent = any(keyword in clean_prompt for keyword in PLACE_QUESTION_KEYWORDS)
    has_place_context = any(place in clean_prompt for place in known_places)
    has_place_hint = has_place_name_hint(prompt)

    if (
        " dan " in clean_prompt
        and any(pattern in clean_prompt for pattern in COMPARISON_QUESTION_PATTERNS)
        and (has_place_context or has_place_hint)
    ):
        return True

    return has_place_intent and (has_place_context or has_place_hint)


def out_of_scope_response():
    return (
        "Maaf saya tidak bisa menjawab pertanyaan tersebut.\n\n"
        "Aku paling pas diajak ngobrol soal perjalanan: mengenal daerah atau negara, "
        "mencari landmark ikonik, menyusun itinerary, memilih kuliner lokal, sampai "
        "mengira-ngira budget liburan.\n\n"
        "Misalnya, kamu bisa tanya: rekomendasi akhir pekan di Purwokerto, bedanya "
        "Purwakarta dan Purwokerto untuk liburan, atau tempat ikonik di Liverpool "
        "yang enak dikunjungi pertama kali."
    )

st.set_page_config(
    page_title="TravelBuddy AI",
    page_icon="✈️",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --font: "Google Sans", "Product Sans", "Inter", Arial, sans-serif;
            --sans-font: "Google Sans", "Product Sans", "Inter", Arial, sans-serif;
        }

        *,
        *::before,
        *::after,
        html,
        body,
        body *,
        [data-testid],
        [class^="st"],
        [class*=" st"],
        .stApp,
        .stApp *,
        .stMarkdown,
        .stMarkdown *,
        p,
        span,
        div,
        h1,
        h2,
        h3,
        h4,
        h5,
        h6,
        li,
        label,
        textarea,
        input,
        button {
            font-family: "Google Sans", "Product Sans", "Inter", Arial, sans-serif !important;
        }

        .material-symbols-rounded,
        .material-symbols-outlined,
        .material-symbols-sharp,
        [class*="material-symbols"],
        [data-testid="stIconMaterial"] {
            font-family: "Material Symbols Rounded", "Material Symbols Outlined", sans-serif !important;
            font-weight: normal !important;
            font-style: normal !important;
            letter-spacing: normal !important;
            line-height: 1 !important;
            text-transform: none !important;
            white-space: nowrap !important;
            word-wrap: normal !important;
            direction: ltr !important;
            -webkit-font-feature-settings: "liga" !important;
            -webkit-font-smoothing: antialiased !important;
            font-feature-settings: "liga" !important;
        }

        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        #MainMenu,
        footer {
            display: none !important;
        }

        [data-testid="stHeader"] {
            background: transparent !important;
        }

        section[data-testid="stSidebar"],
        [data-testid="stSidebar"] {
            background: #0f172a !important;
            border-right: 1px solid rgba(148, 163, 184, 0.18) !important;
            display: block !important;
            max-width: 18rem !important;
            min-width: 18rem !important;
            transform: none !important;
            visibility: visible !important;
            width: 18rem !important;
        }

        section[data-testid="stSidebar"] > div {
            max-width: 18rem !important;
            min-width: 18rem !important;
            width: 18rem !important;
        }

        section[data-testid="stSidebar"] [aria-label*="Close"],
        section[data-testid="stSidebar"] [aria-label*="close" i],
        section[data-testid="stSidebar"] [aria-label*="collapse" i],
        section[data-testid="stSidebar"] [aria-label*="sidebar" i],
        section[data-testid="stSidebar"] [title*="Close"],
        section[data-testid="stSidebar"] [title*="close" i],
        section[data-testid="stSidebar"] [title*="collapse" i],
        section[data-testid="stSidebar"] [title*="sidebar" i],
        section[data-testid="stSidebar"] button:has([data-testid="stIconMaterial"]),
        section[data-testid="stSidebar"] button:has([class*="material-symbols"]),
        section[data-testid="stSidebar"] [data-testid*="collapse"] {
            display: none !important;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(26, 121, 255, 0.18), transparent 32rem),
                linear-gradient(135deg, #07111f 0%, #0d1726 52%, #111827 100%);
            color: #f8fafc;
        }

        .block-container {
            max-width: 920px;
            padding-top: 4.5rem;
            padding-bottom: 7rem;
        }

        .hero {
            border-bottom: 1px solid rgba(148, 163, 184, 0.24);
            margin-bottom: 1.6rem;
            padding-bottom: 1.4rem;
        }

        .hero-label {
            color: #38bdf8;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        .hero h1 {
            color: #ffffff;
            font-size: clamp(2.2rem, 5vw, 4rem);
            line-height: 1.05;
            margin: 0;
        }

        .hero p {
            color: #cbd5e1;
            font-size: 1.05rem;
            line-height: 1.7;
            max-width: 680px;
            margin: 1rem 0 0;
        }

        div[data-testid="stChatMessage"] {
            background: rgba(15, 23, 42, 0.78);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.18);
        }

        div[data-testid="stChatMessage"] p,
        div[data-testid="stChatMessage"] li {
            color: #f8fafc;
            font-size: 1rem;
            line-height: 1.7;
        }

        div[data-testid="stChatInput"] {
            background: rgba(7, 17, 31, 0.86);
            border-top: 1px solid rgba(148, 163, 184, 0.18);
        }

        div[data-testid="stChatInput"] textarea {
            color: #f8fafc;
        }

        .stButton > button {
            background: rgba(14, 165, 233, 0.12);
            border: 1px solid rgba(56, 189, 248, 0.34);
            border-radius: 8px;
            color: #e0f2fe;
            font-weight: 600;
        }

        .stButton > button:hover {
            background: rgba(14, 165, 233, 0.2);
            border-color: rgba(125, 211, 252, 0.7);
            color: #ffffff;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "conversations" not in st.session_state:
    st.session_state.conversations = load_conversations()

if "active_conversation_id" not in st.session_state:
    if st.session_state.conversations:
        st.session_state.active_conversation_id = st.session_state.conversations[0]["id"]
    else:
        new_conversation()

active_conversation = get_active_conversation()

with st.sidebar:
    st.header("Riwayat chat")

    if st.button("Chat baru", use_container_width=True):
        new_conversation()
        st.rerun()

    conversation_ids = [
        conversation["id"] for conversation in st.session_state.conversations
    ]
    conversation_labels = {
        conversation["id"]: conversation["title"]
        for conversation in st.session_state.conversations
    }
    selected_conversation = st.radio(
        "Pilih percakapan",
        conversation_ids,
        index=conversation_ids.index(st.session_state.active_conversation_id),
        format_func=lambda conversation_id: conversation_labels[conversation_id],
        label_visibility="collapsed",
    )

    if selected_conversation != st.session_state.active_conversation_id:
        st.session_state.active_conversation_id = selected_conversation
        st.rerun()

    if st.button("Hapus chat ini", use_container_width=True):
        st.session_state.conversations = [
            conversation
            for conversation in st.session_state.conversations
            if conversation["id"] != st.session_state.active_conversation_id
        ]
        if st.session_state.conversations:
            st.session_state.active_conversation_id = st.session_state.conversations[0][
                "id"
            ]
        else:
            new_conversation()
        save_conversations()
        st.rerun()

st.markdown(
    """
    <section class="hero">
        <div class="hero-label">AI travel assistant</div>
        <h1>TravelBuddy</h1>
        <p>
            Tanya rencana liburanmu di Indonesia. Aku bantu pilih destinasi,
            aktivitas, kuliner, dan estimasi budget dengan gaya ngobrol yang santai.
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

if st.button("Reset chat", type="secondary"):
    active_conversation["messages"] = []
    active_conversation["title"] = "Chat baru"
    save_conversations()
    st.rerun()

for message in active_conversation["messages"]:
    role = message["role"]
    avatar = "🧭" if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

user_input = st.chat_input("Tanya destinasi, itinerary, kuliner, atau budget liburan...")

if user_input:
    active_conversation["messages"].append({"role": "user", "content": user_input})
    if active_conversation["title"] == "Chat baru":
        active_conversation["title"] = title_from_prompt(user_input)
    save_conversations()

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🧭"):
        if not is_travel_question(user_input):
            assistant_response = out_of_scope_response()
            active_conversation["messages"].append(
                {"role": "assistant", "content": assistant_response}
            )
            save_conversations()
            st.markdown(assistant_response)
        else:
            with st.spinner("TravelBuddy lagi menyusun rekomendasi..."):
                chat_session = model.start_chat(
                    history=gemini_history(active_conversation["messages"][:-1])
                )
                response = chat_session.send_message(user_input)
                active_conversation["messages"].append(
                    {"role": "assistant", "content": response.text}
                )
                save_conversations()
                st.markdown(response.text)
