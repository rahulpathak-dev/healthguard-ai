from app.emergency.schemas import EmergencyTopic

TOPICS = (
    EmergencyTopic(
        slug="chest-pain",
        title="Chest pain",
        immediate_action="Call 112 now for chest pain, pressure, or pain with sweating, nausea, or shortness of breath.",
        instructions=[
            "Sit or lie still.",
            "Unlock the door if alone.",
            "Have medicines and allergies ready.",
        ],
        do_not=["Do not drive yourself.", "Do not wait to see if it passes."],
        call_now_if=[
            "Pain, pressure, faintness, sweating, breathlessness, or pain spreading to arm, jaw, back, or shoulder."
        ],
    ),
    EmergencyTopic(
        slug="stroke-signs",
        title="Stroke signs",
        immediate_action="Call 112 now for face drooping, arm weakness, or speech trouble.",
        instructions=["Note the time symptoms started.", "Keep the person safe and still."],
        do_not=["Do not give food, drink, or medicine.", "Do not let the person sleep it off."],
        call_now_if=[
            "Sudden weakness, confusion, vision loss, severe headache, face droop, or speech trouble."
        ],
    ),
    EmergencyTopic(
        slug="severe-bleeding",
        title="Severe bleeding",
        immediate_action="Call 112 now and press firmly on the bleeding area.",
        instructions=[
            "Use clean cloth or gauze.",
            "Keep steady pressure.",
            "Add layers if blood soaks through.",
        ],
        do_not=["Do not remove embedded objects.", "Do not repeatedly lift the cloth to check."],
        call_now_if=[
            "Bleeding is heavy, spurting, from a deep wound, or will not slow with pressure."
        ],
    ),
    EmergencyTopic(
        slug="choking",
        title="Choking",
        immediate_action="Call 112 if the person cannot breathe, cough, cry, or speak.",
        instructions=[
            "Encourage coughing if they can cough.",
            "Use local first-aid guidance for choking maneuvers.",
        ],
        do_not=[
            "Do not put fingers in the mouth unless you can clearly see and remove an object.",
            "Do not give water.",
        ],
        call_now_if=["Unable to breathe, speak, cough, or the person becomes blue or unconscious."],
    ),
    EmergencyTopic(
        slug="burns",
        title="Burns",
        immediate_action="Cool the burn under cool running water and call 112 for serious burns.",
        instructions=[
            "Cool for 20 minutes if possible.",
            "Remove tight items near the burn.",
            "Cover loosely with clean dressing.",
        ],
        do_not=["Do not use ice.", "Do not pop blisters.", "Do not apply butter or oils."],
        call_now_if=[
            "Large, deep, chemical, electrical, face, hand, genital, airway, or child burns."
        ],
    ),
    EmergencyTopic(
        slug="poisoning",
        title="Poisoning",
        immediate_action="Call 112 or a local poison helpline now.",
        instructions=[
            "Keep the container or label.",
            "Tell responders what, when, and how much.",
            "Move away from fumes if safe.",
        ],
        do_not=[
            "Do not induce vomiting unless poison control tells you.",
            "Do not give food or drink unless advised.",
        ],
        call_now_if=[
            "Trouble breathing, confusion, seizure, unconsciousness, or possible overdose."
        ],
    ),
    EmergencyTopic(
        slug="seizure",
        title="Seizure",
        immediate_action="Keep the person safe and time the seizure.",
        instructions=[
            "Move hazards away.",
            "Turn them on their side if possible.",
            "Stay until fully awake.",
        ],
        do_not=["Do not hold them down.", "Do not put anything in their mouth."],
        call_now_if=[
            "First seizure, lasts over 5 minutes, repeated seizures, injury, pregnancy, diabetes, or breathing trouble."
        ],
    ),
    EmergencyTopic(
        slug="fainting",
        title="Fainting",
        immediate_action="Lay the person flat and check breathing.",
        instructions=[
            "Raise legs if no injury.",
            "Loosen tight clothing.",
            "Keep them lying down until recovered.",
        ],
        do_not=[
            "Do not give food or drink until fully alert.",
            "Do not ignore fainting with chest pain or breathlessness.",
        ],
        call_now_if=[
            "No breathing, chest pain, injury, pregnancy, seizure, repeated fainting, or not waking quickly."
        ],
    ),
    EmergencyTopic(
        slug="breathing-difficulty",
        title="Breathing difficulty",
        immediate_action="Call 112 now for severe or worsening breathing difficulty.",
        instructions=[
            "Sit upright.",
            "Loosen tight clothing.",
            "Use prescribed rescue medicine if already prescribed.",
        ],
        do_not=["Do not lie flat if it worsens breathing.", "Do not use someone else's medicine."],
        call_now_if=[
            "Blue lips, severe shortness of breath, confusion, chest pain, or cannot speak full sentences."
        ],
    ),
    EmergencyTopic(
        slug="severe-allergic-reaction",
        title="Severe allergic reaction",
        immediate_action="Call 112 now. Use prescribed epinephrine auto-injector if available.",
        instructions=[
            "Lay down unless breathing is easier sitting.",
            "Be ready to give a second prescribed auto-injector if directed.",
        ],
        do_not=[
            "Do not wait for rash to appear.",
            "Do not rely on antihistamines for severe symptoms.",
        ],
        call_now_if=[
            "Trouble breathing, throat/tongue swelling, faintness, widespread hives, vomiting, or known severe allergy exposure."
        ],
    ),
    EmergencyTopic(
        slug="fractures",
        title="Fractures",
        immediate_action="Keep the injured area still and seek urgent care.",
        instructions=[
            "Support the area.",
            "Apply cold pack wrapped in cloth.",
            "Cover open wounds lightly.",
        ],
        do_not=[
            "Do not push bone back in.",
            "Do not move the person if spine, hip, or major injury is possible.",
        ],
        call_now_if=[
            "Open fracture, severe pain, deformity, numbness, blue/cold limb, head/spine injury, or major trauma."
        ],
    ),
    EmergencyTopic(
        slug="unconsciousness",
        title="Unconsciousness",
        immediate_action="Call 112 now and check breathing.",
        instructions=[
            "Place on side if breathing.",
            "Start CPR if not breathing and trained or dispatcher instructs.",
            "Stay with them.",
        ],
        do_not=["Do not give food, drink, or medicine.", "Do not shake violently."],
        call_now_if=["Always call for unconsciousness."],
    ),
)
