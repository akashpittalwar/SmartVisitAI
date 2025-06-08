import textwrap
import re

# ---------------------------------------------------------------------------
# Helper: Mask Aadhaar Number
# ---------------------------------------------------------------------------
def mask_aadhaar(aadhaar_number: str) -> str:
    """
    Masks all but the last four digits of an Aadhaar number,
    grouping into blocks of four for readability.
    """
    digits = re.sub(r"\D", "", aadhaar_number)
    if len(digits) <= 4:
        return digits
    masked = "*" * (len(digits) - 4) + digits[-4:]
    return " ".join(masked[i:i+4] for i in range(0, len(masked), 4))

# ---------------------------------------------------------------------------
# Visiting Card Utilities
# ---------------------------------------------------------------------------
def print_visiting_card(data: dict):
    """
    Prints a simple ASCII-based visiting card to the server logs,
    including all the collected information, with Aadhaar masked.
    """
    wrap = lambda s, w=50: textwrap.fill(s, w)

    print("\n" + "=" * 60)
    print(" " * 15 + "🏥  VISITING CARD  🏥")
    print("=" * 60)

    # Aadhaar fields (masked)
    aad = data.get("aadhaar_fields", {})
    name       = aad.get("name", "—")
    dob        = aad.get("dob", "—")
    gender     = aad.get("gender", "—")
    raw_aad    = aad.get("aadhaar_number", "—")
    aad_masked = mask_aadhaar(raw_aad)

    print(f"Patient Name       : {name}")
    print(f"DOB                : {dob}")
    print(f"Gender             : {gender}")
    print(f"Aadhaar Number     : {aad_masked}")
    print(f"Address            : {wrap(aad.get('address','—'))}")
    print(f"Email              : {data.get('email','—')}")
    print(f"WhatsApp           : {data.get('whatsapp','—')}")
    ec = data.get("emergency", {})
    print(f"Emergency Contact  : {ec.get('name','—')} / {ec.get('phone','—')}")
    print("-" * 60)

    print("History Summary:")
    print(wrap(data.get("history_summary", "No history provided.")))
    print("-" * 60)

    print("Symptoms / Allergies:")
    print(wrap(data.get("symptoms_paragraph", "—")))
    print("-" * 60)

    slot = data.get("appointment_slot")
    print(f"Appointment Slot   : {slot if isinstance(slot, str) else '—'}")
    print(f"Doctor Assigned    : {data.get('doctor_assigned','—')}")
    print("=" * 60 + "\n")


def generate_visiting_card_html(data: dict) -> str:
    """
    Returns an HTML snippet for the visiting card with Aadhaar masked,
    and formats medical history and symptoms with inline styling.
    """
    # Extract Aadhaar and contact info
    aadhaar     = data.get("aadhaar_fields", {})
    name        = aadhaar.get("name", "")
    dob         = aadhaar.get("dob", "")
    gender      = aadhaar.get("gender", "")
    raw_no      = aadhaar.get("aadhaar_number", "")
    masked_no   = mask_aadhaar(raw_no)
    address     = aadhaar.get("address", "")

    email       = data.get("email", "")
    whatsapp    = data.get("whatsapp", "No WhatsApp provided.")
    emergency   = data.get("emergency", {})
    em_name     = emergency.get("name", "")
    em_phone    = emergency.get("phone", "")

    # Format medical history as HTML list with inline style
    history     = data.get("history_summary", "No history provided.")
    lines       = [ln.strip() for ln in history.split("\n") if ln.strip()]
    history_items = []
    for ln in lines:
        content = re.sub(r'^[\*\-\•]\s*', '', ln)
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        history_items.append(f"<li style='margin:0.25em 0'>{content}</li>")
    history_html = (
        "<ul style='margin:0.5em 0 0.5em 1.25em;"
        "padding:0;list-style:disc inside;'>" +
        "".join(history_items) +
        "</ul>"
    )

    # Format symptoms as paragraphs
    symptoms    = data.get("symptoms_paragraph", "—")
    paras       = [p.strip() for p in symptoms.split("\n") if p.strip()]
    symptoms_html = ''.join(f"<p style='margin:0.5em 0'>{p}</p>" for p in paras)

    doctor      = data.get("doctor_assigned", "")
    slot        = data.get("appointment_slot", "")

    # Build HTML card with improved formatting
    html = f"""
    <div class=\"visiting-card\" style=\"
            border: 1px solid #333;
            padding: 12px;
            border-radius: 8px;
            max-width: 400px;
            background: #fff;
            margin: 10px auto;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        \" >
      <h3 style=\"margin:0 0 12px; font-size:1.2rem; text-align:center;\" >
        Appointment Visiting Card
      </h3>
      <div style=\"font-size:0.95rem; line-height:1.5;\" >
        <strong>Patient Name:</strong> {name}<br/>
        <strong>DOB:</strong> {dob}<br/>
        <strong>Gender:</strong> {gender}<br/>
        <strong>Aadhaar No.:</strong> {masked_no}<br/>
        <strong>Address:</strong> {address}<br/>
        <strong>Email:</strong> {email}<br/>
        <strong>WhatsApp:</strong> {whatsapp}<br/>
        <strong>Emergency Contact:</strong> {em_name} ({em_phone})<br/>
        <hr style=\"margin:12px 0; border:none; border-top:1px solid #ccc;\"/>
        <strong>Medical History:</strong>
        {history_html}
        <hr style=\"margin:12px 0; border:none; border-top:1px solid #ccc;\"/>
        <strong>Symptoms / Allergies:</strong>
        {symptoms_html}
        <hr style=\"margin:12px 0; border:none; border-top:1px solid #ccc;\"/>
        <strong>Doctor:</strong> {doctor}<br/>
        <strong>Slot:</strong> {slot}<br/>
      </div>
    </div>
    """
    return html.strip()