import os
import json
import base64
import re
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, send_from_directory
from config import client, types
from few_shot_examples import few_shot_examples
from utils.image_utils import read_image_bytes
from utils.validators import is_valid_phone, is_valid_email
from utils.visiting_card import generate_visiting_card_html

# In-memory data stores
sessions = {}
doctors = [
    {"id": 1, "name": "Dr. S. Rao", "specialty": "Pulmonology"},
    {"id": 2, "name": "Dr. A. Patel", "specialty": "General Medicine"},
]
appointments = []

# Helpers

def mask_aadhaar(aadhaar_number: str) -> str:
    digits = re.sub(r"\D", "", aadhaar_number)
    if len(digits) <= 4:
        return digits
    masked = "*" * (len(digits) - 4) + digits[-4:]
    return " ".join(masked[i:i+4] for i in range(0, len(masked), 4))


def is_base64_image(data_str: str) -> bool:
    if data_str.startswith("data:image") and "," in data_str:
        _, data_str = data_str.split(",", 1)
    try:
        raw = base64.b64decode(data_str, validate=True)
    except Exception:
        return False
    return raw.startswith(b"\x89PNG\r\n\x1a\n") or raw.startswith(b"\xff\xd8")

# Gemini Layers

def is_valid_aadhaar_with_gemini(image_bytes: bytes) -> bool:
    prompt = (
        "Step: Determine if the following image is a valid Indian Aadhaar card. "
        "Reply with exactly 'Yes' or 'No'."
    )
    parts = [
        types.Part.from_text(text=prompt),
        types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
        types.Part.from_text(text="Answer:")
    ]
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=parts,
        config=types.GenerateContentConfig(temperature=0)
    )
    return resp.text.strip().lower().startswith("yes")


def extract_info_with_gemini(image_bytes: bytes) -> dict:
    schema = {
        "name": "Patient's full name",
        "dob": "Date of Birth (DD/MM/YYYY)",
        "address": "Full address, including pin code",
        "gender": "Male or Female",
        "aadhaar_number": "Aadhaar number"
    }
    prompt = "Step: Extract the following Aadhaar fields from the image:\n"
    for k, v in schema.items():
        prompt += f"- {k}: {v}\n"
    prompt += "Return EXACTLY a JSON object with those keys."
    parts = [types.Part.from_text(text=prompt)]
    for idx, ex in few_shot_examples.items():
        parts.append(types.Part.from_text(text=f"Example {idx}: {ex['Instruction']}"))
        sample = read_image_bytes(ex['Input'])
        parts.append(types.Part.from_bytes(data=sample, mime_type="image/png"))
        parts.append(types.Part.from_text(text=f"Expected JSON:\n{ex['Sample output(JSON)']}"))
    parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/png"))
    parts.append(types.Part.from_text(text="Return only the JSON object."))
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=parts,
        config=types.GenerateContentConfig(temperature=0)
    )
    raw = resp.text.strip()
    m = re.search(r"\{.*\}", raw, re.S)
    js = m.group(0) if m else raw
    try:
        return json.loads(js)
    except:
        return {"error": "parse_failure"}


def summarize_discharge_with_gemini(image_bytes: bytes) -> str:
    prompt = (
        "You are a medical assistant. Below is an image of a discharge summary.\n"
        "Produce a concise medical history of patient in bullet points. Consider Date, Illness, Hospital, Location etc.\n"
        "[Begin summary]"
    )
    parts = [
        types.Part.from_text(text=prompt),
        types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
        types.Part.from_text(text="[End]")
    ]
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=parts,
        config=types.GenerateContentConfig(temperature=0)
    )
    return resp.text.strip()


def normalize_symptoms_with_gemini(text: str) -> str:
    sys = types.Part.from_text(text="Summarize patient symptoms/allergies into a concise paragraph. Use 24h format for times.")
    usr = types.Part.from_text(text=text)
    resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[sys, usr],
        config=types.GenerateContentConfig(temperature=0)
    )
    return resp.text.strip()

# Appointment slots

def get_available_slots() -> list:
    slots = []
    now = datetime.now()
    cur = (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    while len(slots) < 5:
        if cur.hour > 17:
            cur = (cur + timedelta(days=1)).replace(hour=9, minute=0, second=0)
            continue
        for d in doctors:
            if not any(a['doctor_id']==d['id'] and a['datetime']==cur for a in appointments):
                slots.append({
                    'doctor_id': d['id'], 'doctor_name': d['name'],
                    'specialty': d['specialty'], 'slot': cur.strftime("%Y-%m-%d %H:%M")
                })
                if len(slots) == 5:
                    break
        cur += timedelta(hours=1)
    return slots


def book_appointment_slot(doctor_id: int, slot: str) -> dict:
    try:
        dt = datetime.strptime(slot, "%Y-%m-%d %H:%M")
    except ValueError:
        return {'success': False, 'error': 'Invalid format'}
    if any(a['doctor_id']==doctor_id and a['datetime']==dt for a in appointments):
        return {'success': False, 'error': 'Slot taken'}
    appointments.append({'doctor_id': doctor_id, 'datetime': dt})
    doc = next(d for d in doctors if d['id']==doctor_id)
    return {'success': True, 'doctor_assigned': f"{doc['name']} ({doc['specialty']})"}

# Flask app
app = Flask(__name__, static_folder='static', static_url_path='')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    payload = request.json or {}
    uid = payload.get('user_id')
    if not uid:
        return jsonify({'error': 'Missing user_id'}), 400
    if uid not in sessions:
        sessions[uid] = {'step': 'ask_aadhaar'}
    state = sessions[uid]
    step = state['step']
    inp = (payload.get('last_input') or '').strip()
    if not inp:
        return jsonify({'error': 'Missing last_input'}), 400

    # Step 1: Ask Aadhaar
    if step == 'ask_aadhaar':
        state['step'] = 'awaiting_aadhaar'
        return jsonify({'bot_message': 'Hello! Please upload a photo of your Aadhaar card .'}), 200

    # Step 2: Validate & extract Aadhaar
    if step == 'awaiting_aadhaar':
        if not (inp.startswith('data:image') or is_base64_image(inp)):
            return jsonify({'bot_message': 'Please send a valid base64-encoded Aadhaar image.'}), 200
        b64 = inp.split(',', 1)[-1]
        try:
            img = base64.b64decode(b64)
        except Exception:
            return jsonify({'bot_message': 'Invalid base64, please retry.'}), 200
        # Gemini validation
        if not is_valid_aadhaar_with_gemini(img):
            return jsonify({'bot_message': 'That doesn’t look like a valid Aadhaar card. Please upload a valid Aadhaar card image.'}), 200
        info = extract_info_with_gemini(img)
        if info.get('error'):
            return jsonify({'bot_message': 'Extraction failed. Please upload a clearer image.'}), 200
        state['aadhaar_fields'] = info
        state['step'] = 'confirm_aadhaar'
        num = mask_aadhaar(info.get('aadhaar_number', ''))
        return jsonify({'bot_message': (
            f"I have extracted your Aadhaar details as:\n"
            f"• Name: {info.get('name')}\n"
            f"• DOB: {info.get('dob')}\n"
            f"• Address: {info.get('address')}\n"
            f"• Gender: {info.get('gender')}\n"
            f"• Aadhaar Number: {num}\n\n"
            "If any field is incorrect, type correct <field> <new_value>. Otherwise reply OK."
        )}), 200

    # Step 3: Confirm or correct Aadhaar
    if step == 'confirm_aadhaar':
        low = inp.lower()
        if low.startswith('correct '):
            parts = inp.split(maxsplit=2)
            if len(parts) < 3:
                return jsonify({'bot_message': 'Usage: correct <field> <new_value>'}), 200
            _, fld, val = parts
            key = next((k for k in state['aadhaar_fields'] if k.lower() == fld.lower()), None)
            if not key:
                return jsonify({'bot_message': 'Unknown field. Allowed: name, dob, address, gender, aadhaar_number.'}), 200
            state['aadhaar_fields'][key] = val
            num = mask_aadhaar(state['aadhaar_fields'].get('aadhaar_number', ''))
            return jsonify({'bot_message': (
                f"Updated details:\n"
                f"• Name: {state['aadhaar_fields']['name']}\n"
                f"• DOB: {state['aadhaar_fields']['dob']}\n"
                f"• Address: {state['aadhaar_fields']['address']}\n"
                f"• Gender: {state['aadhaar_fields']['gender']}\n"
                f"• Aadhaar Number: {num}\n\n"
                "Reply OK to continue or correct again."
            )}), 200
        if low == 'ok':
            state['step'] = 'ask_email'
            return jsonify({'bot_message': 'Great! Please enter your email address.'}), 200
        return jsonify({'bot_message': 'Please type correct <field> <new_value> or OK.'}), 200

    # Step 4: Validate email
    if step == 'ask_email':
        if is_valid_email(inp):
            state['email'] = inp
            state['step'] = 'ask_whatsapp'
            return jsonify({'bot_message': 'Thank you! Enter your WhatsApp number or type skip.'}), 200
        return jsonify({'bot_message': 'That doesn’t look valid. Try again.'}), 200

    # Step 5: WhatsApp or skip
    if step == 'ask_whatsapp':
        if inp.lower() == 'skip':
            state['whatsapp'] = 'No WhatsApp provided.'
        elif is_valid_phone(inp):
            state['whatsapp'] = inp
        else:
            return jsonify({'bot_message': 'Invalid phone. Retry or skip.'}), 200
        state['step'] = 'ask_emergency'
        return jsonify({'bot_message': 'Provide emergency contact as Name, phone.'}), 200

    # Step 6: Emergency contact
    if step == 'ask_emergency':
        if ',' not in inp:
            return jsonify({'bot_message': 'Use format Name, phone.'}), 200
        name, phone = [x.strip() for x in inp.split(',', 1)]
        if not is_valid_phone(phone):
            return jsonify({'bot_message': 'Invalid phone. Retry.'}), 200
        state['emergency'] = {'name': name, 'phone': phone}
        state['step'] = 'ask_discharge'
        return jsonify({'bot_message': 'Upload discharge summary image or type skip.'}), 200

    # Step 7: Discharge summary or skip
    if step == 'ask_discharge':
        if inp.lower() == 'skip':
            state['history_summary'] = 'No history provided.'
            state['step'] = 'ask_symptoms'
            return jsonify({'bot_message': 'Please send an image of your discharge summary, or type skip.'}), 200
        if not (inp.startswith('data:image') or is_base64_image(inp)):
            return jsonify({'bot_message': 'Send valid image or skip.'}), 200
        b64 = inp.split(',', 1)[-1]
        try:
            img = base64.b64decode(b64)
        except Exception:
            return jsonify({'bot_message': 'Invalid base64. Retry or skip.'}), 200
        summary = summarize_discharge_with_gemini(img)
        state['history_summary'] = summary
        state['step'] = 'ask_symptoms'
        return jsonify({'bot_message': f"Here is your discharge summary:\n{summary}\n \nNow describe your symptoms, and any medical allergies."}), 200

    # Step 8: Symptoms normalization and slot listing
    if step == 'ask_symptoms':
        norm = normalize_symptoms_with_gemini(inp)
        state['symptoms_paragraph'] = norm
        slots = get_available_slots()
        state['latest_slots'] = slots
        state['step'] = 'choose_slot'
        lines = [f"Your symptoms: {norm}", "", "Next five slots:"]
        for i, s in enumerate(slots, 1):
            lines.append(f"{i}. {s['doctor_name']} ({s['specialty']}) - {s['slot']}")
        lines.append("Type option number 1-5 or refresh.")
        return jsonify({'bot_message': "\n".join(lines)}), 200

    # Step 9: Booking or refresh
    if step == 'choose_slot':
        if inp.lower() == 'refresh':
            slots = get_available_slots()
            state['latest_slots'] = slots
            text = "Refreshed slots:\n" + "\n".join(
                f"{i+1}. {s['doctor_name']} ({s['specialty']}) - {s['slot']}"
                for i, s in enumerate(slots)
            )
            return jsonify({'bot_message': text}), 200
        try:
            idx = int(inp) - 1
            choice = state['latest_slots'][idx]
        except Exception:
            return jsonify({'bot_message': 'Invalid choice.'}), 200
        book = book_appointment_slot(choice['doctor_id'], choice['slot'])
        if book.get('success'):
            state['appointment_slot'] = choice['slot']
            state['doctor_assigned'] = book['doctor_assigned']
            state['step'] = 'done'
            card = generate_visiting_card_html(state)
            return jsonify({
                'bot_message': f"🎉 Appointment confirmed with {book['doctor_assigned']} at {choice['slot']}",
                'visiting_card_html': card
            }), 200
        return jsonify({'bot_message': f"Could not book: {book['error']}"}), 200

    # Fallback
    return jsonify({'bot_message': 'I\'m here to help!'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))
