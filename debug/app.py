"""Streamlit debug interface for Thai ID Card Reader."""

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
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Thai ID Card Reader - Debug Interface",
    page_icon="🪪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .card-info {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .debug-section {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
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
if 'debug_logs' not in st.session_state:
    st.session_state.debug_logs = []


def log_debug(message: str, level: str = "INFO"):
    """Add debug log with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] [{level}] {message}"
    st.session_state.debug_logs.append(log_entry)
    logger.log(getattr(logging, level), message)


def scan_readers():
    """Scan for available card readers."""
    try:
        log_debug("Scanning for card readers...", "INFO")
        readers = ThaiIDCardReader.list_readers()
        st.session_state.readers_info = readers
        log_debug(f"Found {len(readers)} reader(s)", "INFO")
        return readers
    except NoReaderFoundError:
        log_debug("No card readers found", "ERROR")
        st.error("No card readers found. Please connect a card reader.")
        return []
    except Exception as e:
        log_debug(f"Error scanning readers: {e}", "ERROR")
        st.error(f"Error scanning readers: {e}")
        return []


def connect_to_reader(reader_index: int):
    """Connect to a card reader."""
    try:
        log_debug(f"Connecting to reader {reader_index}...", "INFO")
        reader = ThaiIDCardReader(reader_index=reader_index)
        reader.connect()

        st.session_state.reader = reader
        st.session_state.connected = True

        log_debug(f"Connected successfully. ATR: {reader.atr}", "INFO")
        st.success("Connected to card reader successfully!")

    except NoCardDetectedError:
        log_debug("No card detected in reader", "ERROR")
        st.error("No card detected. Please insert a Thai ID card.")
    except InvalidCardError as e:
        log_debug(f"Invalid card: {e}", "ERROR")
        st.error(f"Invalid card: {e}")
    except CardConnectionError as e:
        log_debug(f"Connection error: {e}", "ERROR")
        st.error(f"Connection error: {e}")
    except Exception as e:
        log_debug(f"Unexpected error: {e}", "ERROR")
        st.error(f"Unexpected error: {e}")


def disconnect_reader():
    """Disconnect from the card reader."""
    if st.session_state.reader:
        log_debug("Disconnecting from reader...", "INFO")
        st.session_state.reader.disconnect()
        st.session_state.reader = None
        st.session_state.connected = False
        st.session_state.card_data = None
        log_debug("Disconnected", "INFO")
        st.info("Disconnected from card reader.")


def read_card_data(include_photo: bool = True):
    """Read data from the card."""
    if not st.session_state.connected or not st.session_state.reader:
        st.error("Not connected to a card reader.")
        return

    try:
        log_debug("Reading card data...", "INFO")

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        def photo_progress(current: int, total: int):
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(f"Reading photo: {current}/{total} parts")

        status_text.text("Reading card information...")
        card_data = st.session_state.reader.read_card(
            include_photo=include_photo,
            photo_progress_callback=photo_progress if include_photo else None
        )

        progress_bar.progress(100)
        status_text.text("Card read successfully!")

        st.session_state.card_data = card_data
        log_debug(f"Card data read successfully for CID: {card_data.cid}", "INFO")

        st.success("Card data read successfully!")

    except Exception as e:
        log_debug(f"Error reading card: {e}", "ERROR")
        st.error(f"Error reading card: {e}")


def display_card_data(card: ThaiIDCard):
    """Display card data in a formatted way."""
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("### Personal Information")

        info_data = {
            "Citizen ID": card.cid,
            "Thai Name": card.thai_fullname,
            "English Name": card.english_fullname,
            "Date of Birth": card.date_of_birth.strftime("%d %B %Y"),
            "Age": f"{card.age} years",
            "Gender": card.gender_text,
        }

        for label, value in info_data.items():
            st.text(f"{label:.<25} {value}")

        st.markdown("### Card Information")

        card_info = {
            "Card Issuer": card.card_issuer,
            "Issue Date": card.issue_date.strftime("%d %B %Y"),
            "Expire Date": card.expire_date.strftime("%d %B %Y"),
            "Days Until Expiry": card.days_until_expiry,
            "Status": "Expired" if card.is_expired else "Valid",
        }

        for label, value in card_info.items():
            if label == "Status":
                status_class = "status-error" if card.is_expired else "status-success"
                st.markdown(f'{label:.<25} <span class="{status_class}">{value}</span>',
                          unsafe_allow_html=True)
            elif label == "Days Until Expiry":
                color = "status-error" if value < 0 else "status-warning" if value < 30 else "status-success"
                st.markdown(f'{label:.<25} <span class="{color}">{value} days</span>',
                          unsafe_allow_html=True)
            else:
                st.text(f"{label:.<25} {value}")

        st.markdown("### Address")
        st.text_area("Address", value=card.address, height=100, disabled=True, label_visibility="collapsed")

    with col2:
        st.markdown("### Photo")
        if card.photo:
            try:
                img = Image.open(io.BytesIO(card.photo))
                st.image(img, width='stretch')

                # Download button
                st.download_button(
                    label="Download Photo",
                    data=card.photo,
                    file_name=f"{card.cid}.jpg",
                    mime="image/jpeg"
                )
            except Exception as e:
                st.error(f"Error displaying photo: {e}")
        else:
            st.info("No photo data available")


def main():
    """Main application."""
    st.markdown('<div class="main-header">🪪 Thai ID Card Reader - Debug Interface</div>',
                unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("## Controls")

        # Scan readers
        if st.button("🔍 Scan Readers", width='stretch'):
            scan_readers()

        # Display available readers
        if st.session_state.readers_info:
            st.markdown("### Available Readers")
            for reader_info in st.session_state.readers_info:
                status_icon = "✅" if reader_info.connected else "❌"
                with st.expander(f"{status_icon} Reader {reader_info.index}"):
                    st.text(f"Name: {reader_info.name}")
                    if reader_info.atr:
                        st.text(f"ATR: {reader_info.atr}")
                    st.text(f"Card: {'Present' if reader_info.connected else 'Not present'}")

                    if not st.session_state.connected:
                        if st.button(f"Connect to Reader {reader_info.index}",
                                   key=f"connect_{reader_info.index}",
                                   width='stretch'):
                            connect_to_reader(reader_info.index)

        st.markdown("---")

        # Connection status
        st.markdown("### Connection Status")
        if st.session_state.connected:
            st.markdown('<span class="status-success">🟢 Connected</span>',
                       unsafe_allow_html=True)

            if st.button("🔌 Disconnect", width='stretch'):
                disconnect_reader()
                st.rerun()
        else:
            st.markdown('<span class="status-error">🔴 Not Connected</span>',
                       unsafe_allow_html=True)

        st.markdown("---")

        # Read card options
        st.markdown("### Read Card")
        include_photo = st.checkbox("Include Photo", value=True)

        if st.button("📖 Read Card",
                    disabled=not st.session_state.connected,
                    width='stretch'):
            read_card_data(include_photo)

        st.markdown("---")

        # Clear logs
        if st.button("🗑️ Clear Logs", width='stretch'):
            st.session_state.debug_logs = []
            st.rerun()

    # Main content area
    tab1, tab2, tab3 = st.tabs(["📋 Card Data", "🐛 Debug Logs", "ℹ️ About"])

    with tab1:
        if st.session_state.card_data:
            display_card_data(st.session_state.card_data)

            # Export options
            st.markdown("---")
            st.markdown("### Export Data")

            col1, col2, col3 = st.columns(3)

            with col1:
                json_data = st.session_state.card_data.model_dump_json(indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"{st.session_state.card_data.cid}.json",
                    mime="application/json",
                    width='stretch'
                )

            with col2:
                if st.session_state.card_data.photo:
                    st.download_button(
                        label="📥 Download Photo",
                        data=st.session_state.card_data.photo,
                        file_name=f"{st.session_state.card_data.cid}.jpg",
                        mime="image/jpeg",
                        width='stretch'
                    )

            with col3:
                # CSV-like text export
                csv_data = f"""Citizen ID,{st.session_state.card_data.cid}
Thai Name,{st.session_state.card_data.thai_fullname}
English Name,{st.session_state.card_data.english_fullname}
Date of Birth,{st.session_state.card_data.date_of_birth}
Gender,{st.session_state.card_data.gender_text}
Address,"{st.session_state.card_data.address}"
Issue Date,{st.session_state.card_data.issue_date}
Expire Date,{st.session_state.card_data.expire_date}
"""
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"{st.session_state.card_data.cid}.csv",
                    mime="text/csv",
                    width='stretch'
                )
        else:
            st.info("👆 Connect to a reader and read a card to display data here.")

    with tab2:
        st.markdown("### Debug Logs")

        if st.session_state.debug_logs:
            log_text = "\n".join(reversed(st.session_state.debug_logs[-100:]))  # Last 100 logs
            st.markdown(f'<div class="debug-section">{log_text}</div>',
                       unsafe_allow_html=True)
        else:
            st.info("No debug logs yet. Logs will appear here as you interact with the application.")

    with tab3:
        st.markdown("""
        ### About Thai ID Card Reader

        This is a debug interface for reading Thai National ID cards using smart card readers.

        **Features:**
        - Scan and detect card readers
        - Connect to Thai ID cards
        - Read personal information
        - Extract card photo
        - Export data in multiple formats (JSON, CSV)
        - Real-time debug logging

        **Requirements:**
        - PC/SC smart card reader
        - Thai National ID card
        - pcscd service running (Linux)

        **Usage:**
        1. Click "Scan Readers" to detect available readers
        2. Connect to a reader with a card inserted
        3. Click "Read Card" to extract data
        4. View and export the data

        **Technical Details:**
        - Uses pyscard library for smart card communication
        - Implements Thai ID card APDU commands
        - Validates CID checksum
        - Converts Buddhist calendar dates to Gregorian

        **Developed with:** Python, Streamlit, pyscard, Pydantic
        """)

        # Show system info
        st.markdown("### System Information")
        st.text(f"Python: {st.session_state.get('python_version', 'Unknown')}")
        st.text(f"Readers Found: {len(st.session_state.readers_info)}")
        st.text(f"Connected: {'Yes' if st.session_state.connected else 'No'}")


if __name__ == "__main__":
    main()
