"""
Certificate Generator — Techno Kids, Techno Future
Streamlit app shell: page config + tab router.
All logic lives in core/ and pages/.
"""

import streamlit as st

from pages import generate, validate, registry

st.set_page_config(
    page_title="Certificate System — Techno Future",
    page_icon="\U0001f393",
    layout="wide",
)

deep_verify_id = st.query_params.get("verify") or st.query_params.get("cert_id")

st.title("\U0001f393 Certificate System — Techno Future")
st.caption(
    "Official certificate generator, database registry, and instant ID verification portal"
)

tab1, tab2, tab3 = st.tabs(
    [
        "\U0001f393 Generate Certificate",
        "\U0001f50d Validate Certificate",
        "\U0001f4dc Certificate Registry",
    ]
)

with tab1:
    generate.render()

with tab2:
    validate.render(verify_id=deep_verify_id)

with tab3:
    registry.render()
