"""Streamlit compact debug interface for Thai ID Card Reader."""

import io
import logging
from datetime import datetime
from typing import Optional

import streamlit as st
from PIL import Image

from pythaiid.reader import ThaiIDCardReader
from pythaiid.models import ThaiIDCard, CardReaderInfo
from pythaiid.exceptions import (
    NoReaderFoundError,
    NoCardDetectedError,
    CardConnectionError,
    InvalidCardError,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Thai ID Card Reader",
    page_icon="🪪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Modern compact CSS
st.markdown("""
<style>
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Compact padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Modern dark card */
    .info-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }

    /* Info row styling */
    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 0.4rem 0;
        border-bottom: 1px solid #334155;
        font-size: 0.9rem;
    }

    .info-row:last-child {
        border-bottom: none;
    }

    .info-label {
        color: #94a3b8;
        font-weight: 500;
        min-width: 140px;
    }

    .info-value {
        color: #e2e8f0;
        font-weight: 600;
        text-align: right;
        flex: 1;
    }

    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .status-valid {
        background: #10b981;
        color: white;
    }

    .status-expired {
        background: #ef4444;
        color: white;
    }

    .status-warning {
        background: #f59e0b;
        color: white;
    }

    .status-connected {
        background: #10b981;
        color: white;
    }

    .status-disconnected {
        background: #6b7280;
        color: white;
    }

    /* Photo container */
    .photo-container {
        border: 2px solid #334155;
        border-radius: 12px;
        overflow: hidden;
        background: #0f172a;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }

    /* Compact button styling */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        border: 1px solid #334155;
        transition: all 0.2s;
    }

    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }

    /* Section headers */
    .section-header {
        color: #f1f5f9;
        font-size: 1.1rem;
        font-weight: 700;
        margin: 1rem 0 0.5rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #334155;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Control panel */
    .control-panel {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }

    /* Reader info */
    .reader-info {
        background: #0f172a;
        border-left: 3px solid #10b981;
        padding: 0.75rem 1rem;
        border-radius: 6px;
        margin: 0.5rem 0;
        font-size: 0.85rem;
    }

    .reader-name {
        color: #e2e8f0;
        font-weight: 600;
    }

    .reader-detail {
        color: #94a3b8;
        font-size: 0.8rem;
        margin-top: 0.25rem;
    }

    /* Compact tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        font-weight: 600;
    }

    /* Hide file uploader */
    [data-testid="stFileUploadDropzone"] {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'reader' not in st.session_state:
    st.session_state.reader = None
if 'card_data' not in st.session_state:
    st.session_state.card_data = None
if 'connected' not in st.session_state:
    st.session_state.connected = False
if 'readers_info' not in st.session_state:
    st.session_state.readers_info = []


def scan_readers():
    """Scan for available card readers."""
    try:
        logger.info("Scanning for card readers...")
        readers = ThaiIDCardReader.list_readers()
        st.session_state.readers_info = readers
        logger.info(f"Found {len(readers)} reader(s)")
        return readers
    except NoReaderFoundError:
        logger.error("No card readers found")
        st.error("❌ No card readers found")
        return []
    except Exception as e:
        logger.error(f"Error scanning readers: {e}")
        st.error(f"❌ Error: {e}")
        return []


def connect_to_reader(reader_index: int):
    """Connect to a card reader."""
    try:
        logger.info(f"Connecting to reader {reader_index}...")
        reader = ThaiIDCardReader(reader_index=reader_index)
        reader.connect()
        st.session_state.reader = reader
        st.session_state.connected = True
        logger.info("Connected successfully")
        st.success("✅ Connected to card reader")
    except (NoCardDetectedError, InvalidCardError, CardConnectionError) as e:
        logger.error(f"Connection error: {e}")
        st.error(f"❌ {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        st.error(f"❌ Error: {e}")


def disconnect_reader():
    """Disconnect from the card reader."""
    if st.session_state.reader:
        logger.info("Disconnecting...")
        st.session_state.reader.disconnect()
        st.session_state.reader = None
        st.session_state.connected = False
        st.session_state.card_data = None
        st.info("🔌 Disconnected")


def read_card_data(include_photo: bool = True):
    """Read data from the card."""
    if not st.session_state.connected or not st.session_state.reader:
        st.error("❌ Not connected to a card reader")
        return

    try:
        logger.info("Reading card data...")
        progress_bar = st.progress(0, text="Reading card information...")

        def photo_progress(current: int, total: int):
            progress = current / total
            progress_bar.progress(progress, text=f"Reading photo: {current}/{total} parts")

        card_data = st.session_state.reader.read_card(
            include_photo=include_photo,
            photo_progress_callback=photo_progress if include_photo else None
        )

        progress_bar.progress(100, text="✅ Card read successfully!")
        st.session_state.card_data = card_data
        logger.info(f"Card data read for CID: {card_data.cid}")
    except Exception as e:
        logger.error(f"Error reading card: {e}")
        st.error(f"❌ Error: {e}")


def copy_to_clipboard_button(text: str, label: str, key: str):
    """Create a copy button with JavaScript clipboard functionality."""
    import html
    escaped_text = html.escape(text).replace("'", "\\'")

    button_html = f"""
    <button onclick="copyToClipboard_{key}()" style="
        width: 100%;
        padding: 0.5rem;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: 1px solid #1e40af;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.85rem;
    " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.3)';"
       onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='none';">
        {label}
    </button>
    <script>
    function copyToClipboard_{key}() {{
        const text = '{escaped_text}';
        navigator.clipboard.writeText(text).then(function() {{
            console.log('Copied to clipboard: ' + text);
        }}, function(err) {{
            console.error('Could not copy text: ', err);
        }});
    }}
    </script>
    """
    st.markdown(button_html, unsafe_allow_html=True)


def render_card_info(card: ThaiIDCard):
    """Render card information in compact modern layout."""

    col1, col2 = st.columns([2, 1])

    with col1:
        # Personal Information
        st.markdown('<div class="section-header">👤 Personal Information</div>', unsafe_allow_html=True)

        # Quick copy section for key fields
        st.markdown('<div class="info-card" style="margin-bottom: 0.5rem; padding: 1rem;">', unsafe_allow_html=True)

        copy_col1, copy_col2, copy_col3 = st.columns(3)
        with copy_col1:
            copy_to_clipboard_button(card.cid, "📋 Copy CID", "cid")

        with copy_col2:
            copy_to_clipboard_button(card.thai_fullname, "📋 Copy Thai Name", "thai")

        with copy_col3:
            copy_to_clipboard_button(card.english_fullname, "📋 Copy EN Name", "en")

        st.markdown('</div>', unsafe_allow_html=True)

        # Full information display
        st.markdown(f'''
        <div class="info-card">
            <div class="info-row">
                <span class="info-label">Citizen ID</span>
                <span class="info-value">{card.cid}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Thai Name</span>
                <span class="info-value">{card.thai_fullname}</span>
            </div>
            <div class="info-row">
                <span class="info-label">English Name</span>
                <span class="info-value">{card.english_fullname}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Date of Birth</span>
                <span class="info-value">{card.date_of_birth.strftime("%d %B %Y")}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Age</span>
                <span class="info-value">{card.age} years</span>
            </div>
            <div class="info-row">
                <span class="info-label">Gender</span>
                <span class="info-value">{card.gender_text}</span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # Card Information
        st.markdown('<div class="section-header">🪪 Card Information</div>', unsafe_allow_html=True)

        status_class = "status-expired" if card.is_expired else "status-valid"
        status_text = "Expired" if card.is_expired else "Valid"

        expiry_class = "status-expired" if card.days_until_expiry < 0 else "status-warning" if card.days_until_expiry < 30 else "status-valid"

        st.markdown(f'''
        <div class="info-card">
            <div class="info-row">
                <span class="info-label">Card Issuer</span>
                <span class="info-value">{card.card_issuer}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Issue Date</span>
                <span class="info-value">{card.issue_date.strftime("%d %B %Y")}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Expire Date</span>
                <span class="info-value">{card.expire_date.strftime("%d %B %Y")}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Days Until Expiry</span>
                <span class="info-value"><span class="status-badge {expiry_class}">{card.days_until_expiry} days</span></span>
            </div>
            <div class="info-row">
                <span class="info-label">Status</span>
                <span class="info-value"><span class="status-badge {status_class}">{status_text}</span></span>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # Address
        st.markdown('<div class="section-header">📍 Address</div>', unsafe_allow_html=True)
        st.markdown(f'''
        <div class="info-card">
            <div style="color: #e2e8f0; line-height: 1.6; margin-bottom: 1rem;">{card.address}</div>
        ''', unsafe_allow_html=True)

        # Copy address button (inline in the card)
        copy_to_clipboard_button(card.address, "📋 Copy Address", "address")

        st.markdown(f'''
        </div>
        ''', unsafe_allow_html=True)

        # Export options
        st.markdown('<div class="section-header">💾 Export</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)

        with c1:
            json_data = card.model_dump_json(indent=2)
            st.download_button(
                label="📥 JSON",
                data=json_data,
                file_name=f"{card.cid}.json",
                mime="application/json",
                width='stretch'
            )

        with c2:
            csv_data = f"""Citizen ID,{card.cid}
Thai Name,{card.thai_fullname}
English Name,{card.english_fullname}
Date of Birth,{card.date_of_birth}
Gender,{card.gender_text}
Address,"{card.address}"
Issue Date,{card.issue_date}
Expire Date,{card.expire_date}
"""
            st.download_button(
                label="📥 CSV",
                data=csv_data,
                file_name=f"{card.cid}.csv",
                mime="text/csv",
                width='stretch'
            )

        with c3:
            if card.photo:
                st.download_button(
                    label="📥 Photo",
                    data=card.photo,
                    file_name=f"{card.cid}.jpg",
                    mime="image/jpeg",
                    width='stretch'
                )

    with col2:
        # Photo
        st.markdown('<div class="section-header">📸 Photo</div>', unsafe_allow_html=True)
        if card.photo:
            try:
                img = Image.open(io.BytesIO(card.photo))
                st.markdown('<div class="photo-container">', unsafe_allow_html=True)
                st.image(img, width='stretch')
                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Error displaying photo: {e}")
        else:
            st.info("No photo data")


def main():
    """Main application."""

    # Header
    st.markdown("""
    <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
        <h1 style="margin: 0; font-size: 2rem; font-weight: 800; color: #f1f5f9;">
            🪪 Thai ID Card Reader
        </h1>
        <p style="margin: 0.5rem 0 0 0; color: #94a3b8; font-size: 0.9rem;">
            Compact Debug Interface
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Control Panel
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)

    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4, ctrl_col5 = st.columns([1.5, 2, 1.5, 1.5, 1.5])

    with ctrl_col1:
        if st.button("🔍 Scan Readers", width='stretch', type="primary"):
            scan_readers()

    with ctrl_col2:
        # Reader selection
        if st.session_state.readers_info:
            reader_options = [f"Reader {r.index}: {r.name[:30]}" for r in st.session_state.readers_info]
            selected = st.selectbox("Select Reader", reader_options, label_visibility="collapsed")
            selected_idx = int(selected.split(":")[0].replace("Reader ", ""))
        else:
            st.selectbox("Select Reader", ["No readers found"], disabled=True, label_visibility="collapsed")
            selected_idx = None

    with ctrl_col3:
        if st.button("🔌 Connect", disabled=selected_idx is None or st.session_state.connected, width='stretch'):
            connect_to_reader(selected_idx)

    with ctrl_col4:
        include_photo = st.checkbox("📸 Photo", value=True)
        if st.button("📖 Read Card", disabled=not st.session_state.connected, width='stretch', type="primary"):
            read_card_data(include_photo)

    with ctrl_col5:
        if st.button("⏏️ Disconnect", disabled=not st.session_state.connected, width='stretch'):
            disconnect_reader()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Connection Status & Reader Info
    if st.session_state.readers_info:
        status_col1, status_col2 = st.columns([1, 3])

        with status_col1:
            status_class = "status-connected" if st.session_state.connected else "status-disconnected"
            status_text = "Connected" if st.session_state.connected else "Disconnected"
            st.markdown(f'''
            <div style="text-align: center; padding: 0.5rem 0;">
                <span class="status-badge {status_class}">{status_text}</span>
            </div>
            ''', unsafe_allow_html=True)

        with status_col2:
            if st.session_state.readers_info and selected_idx is not None:
                reader_info = st.session_state.readers_info[selected_idx]
                st.markdown(f'''
                <div class="reader-info">
                    <div class="reader-name">{reader_info.name}</div>
                    <div class="reader-detail">ATR: {reader_info.atr if reader_info.atr else "Not available"}</div>
                </div>
                ''', unsafe_allow_html=True)

    # Card Data Display
    if st.session_state.card_data:
        st.markdown("---")
        render_card_info(st.session_state.card_data)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 3rem 0; color: #64748b;">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🪪</div>
            <div style="font-size: 1.1rem; font-weight: 600;">No Card Data</div>
            <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                Scan readers, connect to a reader, and read the card to view data
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
