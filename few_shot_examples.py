few_shot_examples = {
    1: {
        "Instruction": "Extract name, dob (DD/MM/YYYY), address, gender, and aadhaar_number from this Aadhaar ID card image as a JSON object.",
        "Input": r"examples\3_Adhar card-short.png",
        "Sample output(JSON)": """
{
  "name": "Akash Vinay Pittalwar",
  "dob": "04/08/1999",
  "address": "Plot no 55 Talmale Layout Khutamba Road Katol, Nagpur, Maharashtra 441302",
  "gender": "Male",
  "aadhaar_number": "3522 3342 1369"
}
        """.strip(),
    },

}
