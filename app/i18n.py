"""Localisation for the eight Indic languages SAHAYAK supports.

Everything the worker hears is produced from this table: the AI disclosure,
the follow-up questions, the verbal readback, the danger-sign referral, and
the validation re-ask prompts. No string is hardcoded in the dialogue layer.
"""

from __future__ import annotations

SUPPORTED = ("hi", "ta", "te", "kn", "ml", "bn", "mr", "en")
DEFAULT = "en"

LANGUAGE_NAMES = {
    "hi": "हिन्दी",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "kn": "ಕನ್ನಡ",
    "ml": "മലയാളം",
    "bn": "বাংলা",
    "mr": "मराठी",
    "en": "English",
}

# Locale codes handed to the Gnani STT / TTS clients.
LOCALE_CODES = {
    "hi": "hi-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "kn": "kn-IN",
    "ml": "ml-IN",
    "bn": "bn-IN",
    "mr": "mr-IN",
    "en": "en-IN",
}

STRINGS = {
    "en": {
        "greeting": (
            "Hello. I am an AI assistant, not a doctor. Tell me about your visit "
            "and I will fill the record. Start whenever you are ready."
        ),
        "q_beneficiary_id": "What is the beneficiary's ID?",
        "q_visit_type": "What kind of visit is this: ANC, PNC, newborn or immunisation?",
        "q_weight": "What is the weight in kilos?",
        "q_vaccinations": "Are any vaccinations due? You can say none.",
        "q_next_visit": "When is the next visit?",
        "readback_prefix": "Let me read it back. ",
        "rb_id": "ID {value}",
        "rb_visit": "visit type {value}",
        "rb_weight": "weight {value} kilos",
        "rb_vacc": "vaccinations due: {value}",
        "rb_date": "next visit {value}",
        "rb_none": "none",
        "ask_correct": "Is this correct?",
        "ask_change": "What should I change?", 
        "saved": "Saved. Follow-ups:",
        "fu_next": "Next visit: {value}",
        "fu_vacc": "Vaccinations due: {value}",
        "fu_referral": "Referral to PHC flagged",
        "already_saved": "This visit is saved. Start a new visit to continue.",
        "did_not_catch": "Sorry, I did not catch that. Please say it again.",
        "take_your_time": "Sure, take your time! I am right here whenever you are ready.",
        "language_set": "Language set to {language}. Please continue.",
        "refer": (
            "Danger sign noted: {label}. Please refer to the PHC now. "
            "I have flagged this record."
        ),
        "fix_id": "That beneficiary ID does not look right. Please say the ID again.",
        "fix_visit": "Please say the visit type: ANC, PNC, newborn or immunisation.",
        "fix_weight": (
            "A weight of {value} kilos is not possible for a {visit} visit. "
            "Please say the weight again."
        ),
        "fix_date": "The next visit date must be in the future. Please say the date again.",
        "lbl_bleeding_pregnancy": "Bleeding in pregnancy",
        "lbl_fever_newborn": "High fever in newborn",
        "lbl_convulsions": "Convulsions or fits",
        "lbl_not_breathing_well": "Difficulty breathing",
        "visit_ANC": "ANC",
        "visit_PNC": "PNC",
        "visit_newborn": "newborn",
        "visit_immunisation": "immunisation",
        "yes_words": "yes,yeah,ya,haan,han,haa,sahi,theek,thik,correct,right,save,ok,okay",
        "no_words": "no,nope,nahi,nahin,nhi,galat,wrong,incorrect",
    },
    "hi": {
        "greeting": (
            "नमस्ते। मैं एक एआई सहायक हूँ, डॉक्टर नहीं। अपनी विज़िट के बारे में बताइए, "
            "मैं रिकॉर्ड भर दूँगी। जब तैयार हों, शुरू कीजिए।"
        ),
        "q_beneficiary_id": "लाभार्थी की आईडी क्या है?",
        "q_visit_type": "यह कौन सी विज़िट है: एएनसी, पीएनसी, नवजात या टीकाकरण?",
        "q_weight": "वज़न कितने किलो है?",
        "q_vaccinations": "कोई टीका देना बाकी है? नहीं भी कह सकती हैं।",
        "q_next_visit": "अगली विज़िट कब है?",
        "readback_prefix": "मैं दोबारा पढ़ती हूँ। ",
        "rb_id": "आईडी {value}",
        "rb_visit": "विज़िट {value}",
        "rb_weight": "वज़न {value} किलो",
        "rb_vacc": "बाकी टीके: {value}",
        "rb_date": "अगली विज़िट {value}",
        "rb_none": "कोई नहीं",
        "ask_correct": "क्या यह सही है?",
        "ask_change": "क्या बदलना है?", 
        "saved": "सेव हो गया। फॉलो-अप:",
        "fu_next": "अगली विज़िट: {value}",
        "fu_vacc": "बाकी टीके: {value}",
        "fu_referral": "पीएचसी रेफरल चिह्नित",
        "already_saved": "यह विज़िट सेव हो चुकी है। नई विज़िट शुरू कीजिए।",
        "did_not_catch": "माफ़ कीजिए, समझ नहीं आया। फिर से बोलिए।",
        "take_your_time": "हाँ ज़रूर, आप समय लीजिए! जब आप तैयार हों, बताइएगा।",
        "language_set": "भाषा {language} पर सेट हो गई। आगे बताइए।",
        "refer": (
            "खतरे का संकेत मिला: {label}। कृपया अभी पीएचसी रेफर कीजिए। "
            "मैंने यह रिकॉर्ड चिह्नित कर दिया है।"
        ),
        "fix_id": "यह लाभार्थी आईडी सही नहीं लग रही। आईडी फिर से बोलिए।",
        "fix_visit": "विज़िट का प्रकार बोलिए: एएनसी, पीएनसी, नवजात या टीकाकरण।",
        "fix_weight": (
            "{visit} विज़िट के लिए {value} किलो वज़न संभव नहीं है। "
            "वज़न फिर से बोलिए।"
        ),
        "fix_date": "अगली विज़िट की तारीख आगे की होनी चाहिए। तारीख फिर से बोलिए।",
        "lbl_bleeding_pregnancy": "गर्भावस्था में खून आना",
        "lbl_fever_newborn": "नवजात को तेज़ बुखार",
        "lbl_convulsions": "दौरा या झटके",
        "lbl_not_breathing_well": "सांस लेने में कठिनाई",
        "visit_ANC": "एएनसी",
        "visit_PNC": "पीएनसी",
        "visit_newborn": "नवजात",
        "visit_immunisation": "टीकाकरण",
        "yes_words": "हाँ,हां,हा,सही,ठीक,हाँ जी,haan,han,haa,sahi,theek,thik,ok,okay,save",
        "no_words": "नहीं,नही,गलत,nahi,nahin,nhi,galat,wrong",
    },
    "ta": {
        "greeting": (
            "வணக்கம். நான் ஒரு செயற்கை நுண்ணறிவு உதவியாளர், மருத்துவர் அல்ல. "
            "உங்கள் வீட்டு வருகையைப் பற்றிச் சொல்லுங்கள், நான் பதிவை நிரப்புகிறேன். "
            "தயாராக இருந்தால் தொடங்குங்கள்."
        ),
        "q_beneficiary_id": "பயனாளியின் ஐடி என்ன?",
        "q_visit_type": "இது எந்த வகை வருகை: ஏஎன்சி, பிஎன்சி, புதிதாகப் பிறந்தவர் அல்லது தடுப்பூசி?",
        "q_weight": "எடை எத்தனை கிலோ?",
        "q_vaccinations": "ஏதேனும் தடுப்பூசி வழங்க வேண்டுமா? இல்லை என்றும் சொல்லலாம்.",
        "q_next_visit": "அடுத்த வருகை எப்போது?",
        "readback_prefix": "மீண்டும் படிக்கிறேன். ",
        "rb_id": "ஐடி {value}",
        "rb_visit": "வருகை வகை {value}",
        "rb_weight": "எடை {value} கிலோ",
        "rb_vacc": "வழங்க வேண்டிய தடுப்பூசிகள்: {value}",
        "rb_date": "அடுத்த வருகை {value}",
        "rb_none": "எதுவும் இல்லை",
        "ask_correct": "இது சரியா?",
        "ask_change": "என்ன மாற்ற வேண்டும்?", 
        "saved": "சேமிக்கப்பட்டது. பின்தொடர்வுகள்:",
        "fu_next": "அடுத்த வருகை: {value}",
        "fu_vacc": "வழங்க வேண்டிய தடுப்பூசிகள்: {value}",
        "fu_referral": "பிஎச்சி பரிந்துரை குறிக்கப்பட்டது",
        "already_saved": "இந்த வருகை சேமிக்கப்பட்டது. புதிய வருகையைத் தொடங்குங்கள்.",
        "did_not_catch": "மன்னிக்கவும், புரியவில்லை. மீண்டும் சொல்லுங்கள்.",
        "take_your_time": "நிச்சயமாக, நேரம் எடுத்துக் கொள்ளுங்கள்! தயாரானதும் சொல்லுங்கள்.",
        "language_set": "மொழி {language} ஆக அமைக்கப்பட்டது. தொடரலாம்.",
        "refer": (
            "ஆபத்து அறிகுறி கண்டறியப்பட்டது: {label}. உடனே பிஎச்சிக்கு அனுப்புங்கள். "
            "இந்தப் பதிவைக் குறித்துள்ளேன்."
        ),
        "fix_id": "இந்த ஐடி சரியாகத் தெரியவில்லை. ஐடியை மீண்டும் சொல்லுங்கள்.",
        "fix_visit": "வருகை வகையைச் சொல்லுங்கள்: ஏஎன்சி, பிஎன்சி, புதிதாகப் பிறந்தவர் அல்லது தடுப்பூசி.",
        "fix_weight": (
            "{visit} வருகைக்கு {value} கிலோ எடை சாத்தியமில்லை. "
            "எடையை மீண்டும் சொல்லுங்கள்."
        ),
        "fix_date": "அடுத்த வருகை தேதி எதிர்காலத்தில் இருக்க வேண்டும். தேதியை மீண்டும் சொல்லுங்கள்.",
        "lbl_bleeding_pregnancy": "கர்ப்பத்தில் இரத்தப்போக்கு",
        "lbl_fever_newborn": "புதிதாகப் பிறந்த குழந்தைக்கு அதிக காய்ச்சல்",
        "lbl_convulsions": "வலிப்பு",
        "lbl_not_breathing_well": "மூச்சுத் திணறல்",
        "visit_ANC": "ஏஎன்சி",
        "visit_PNC": "பிஎன்சி",
        "visit_newborn": "புதிதாகப் பிறந்தவர்",
        "visit_immunisation": "தடுப்பூசி",
        "yes_words": "ஆம்,ஆமா,அமாம்,சரி,ஓகே,aam,amam,sari,seri,ok,okay,save",
        "no_words": "இல்லை,இல்ல,தவறு,illai,illa,thavaru,wrong",
    },
    "te": {
        "greeting": (
            "నమస్తే. నేను ఒక ఏఐ సహాయకుడిని, డాక్టర్ కాదు. మీ ఇంటి సందర్శన గురించి "
            "చెప్పండి, నేను రికార్డు నింపుతాను. సిద్ధమైతే ప్రారంభించండి."
        ),
        "q_beneficiary_id": "లబ్ధిదారు ఐడీ ఏమిటి?",
        "q_visit_type": "ఇది ఏ రకమైన సందర్శన: ఏఎన్సీ, పీఎన్సీ, నవజాత శిశువు లేదా టీకా?",
        "q_weight": "బరువు ఎన్ని కిలోలు?",
        "q_vaccinations": "ఏమైనా టీకాలు ఇవ్వాలా? లేదు అని కూడా చెప్పవచ్చు.",
        "q_next_visit": "తదుపరి సందర్శన ఎప్పుడు?",
        "readback_prefix": "మళ్ళీ చదువుతాను. ",
        "rb_id": "ఐడీ {value}",
        "rb_visit": "సందర్శన రకం {value}",
        "rb_weight": "బరువు {value} కిలోలు",
        "rb_vacc": "ఇవ్వాల్సిన టీకాలు: {value}",
        "rb_date": "తదుపరి సందర్శన {value}",
        "rb_none": "ఏమీ లేదు",
        "ask_correct": "ఇది సరైనదా?",
        "ask_change": "ఏమి మార్చాలి?", 
        "saved": "సేవ్ అయింది. ఫాలో-అప్‌లు:",
        "fu_next": "తదుపరి సందర్శన: {value}",
        "fu_vacc": "ఇవ్వాల్సిన టీకాలు: {value}",
        "fu_referral": "పీహెచ్‌సీ రెఫరల్ గుర్తించబడింది",
        "already_saved": "ఈ సందర్శన సేవ్ అయింది. కొత్త సందర్శన ప్రారంభించండి.",
        "did_not_catch": "క్షమించండి, అర్థం కాలేదు. మళ్ళీ చెప్పండి.",
        "take_your_time": "తప్పకుండా, మీ సమయం తీసుకోండి! మీరు సిద్ధంగా ఉన్నప్పుడు చెప్పండి.",
        "language_set": "భాష {language} కు మార్చబడింది. కొనసాగించండి.",
        "refer": (
            "ప్రమాద సంకేతం గుర్తించబడింది: {label}. దయచేసి వెంటనే పీహెచ్‌సీకి పంపండి. "
            "ఈ రికార్డును గుర్తించాను."
        ),
        "fix_id": "ఈ ఐడీ సరిగా లేదు. ఐడీని మళ్ళీ చెప్పండి.",
        "fix_visit": "సందర్శన రకం చెప్పండి: ఏఎన్సీ, పీఎన్సీ, నవజాత శిశువు లేదా టీకా.",
        "fix_weight": (
            "{visit} సందర్శనకు {value} కిలోల బరువు సాధ్యం కాదు. "
            "బరువును మళ్ళీ చెప్పండి."
        ),
        "fix_date": "తదుపరి సందర్శన తేదీ భవిష్యత్తులో ఉండాలి. తేదీని మళ్ళీ చెప్పండి.",
        "lbl_bleeding_pregnancy": "గర్భధారణలో రక్తస్రావం",
        "lbl_fever_newborn": "నవజాత శిశువుకు తీవ్ర జ్వరం",
        "lbl_convulsions": "మూర్ఛ లేదా ఫిట్స్",
        "lbl_not_breathing_well": "శ్వాస తీసుకోవడంలో ఇబ్బంది",
        "visit_ANC": "ఏఎన్సీ",
        "visit_PNC": "పీఎన్సీ",
        "visit_newborn": "నవజాత శిశువు",
        "visit_immunisation": "టీకా",
        "yes_words": "అవును,అవునా,సరే,ఓకే,avunu,sare,ok,okay,save",
        "no_words": "కాదు,లేదు,తప్పు,kadu,ledu,thappu,wrong",
    },
    "kn": {
        "greeting": (
            "ನಮಸ್ಕಾರ. ನಾನು ಒಬ್ಬ ಎಐ ಸಹಾಯಕ, ವೈದ್ಯರಲ್ಲ. ನಿಮ್ಮ ಮನೆ ಭೇಟಿಯ ಬಗ್ಗೆ ಹೇಳಿ, "
            "ನಾನು ದಾಖಲೆ ತುಂಬುತ್ತೇನೆ. ಸಿದ್ಧರಾದಾಗ ಪ್ರಾರಂಭಿಸಿ."
        ),
        "q_beneficiary_id": "ಫಲಾನುಭವಿಯ ಐಡಿ ಏನು?",
        "q_visit_type": "ಇದು ಯಾವ ರೀತಿಯ ಭೇಟಿ: ಎಎನ್‌ಸಿ, ಪಿಎನ್‌ಸಿ, ನವಜಾತ ಅಥವಾ ಲಸಿಕೆ?",
        "q_weight": "ತೂಕ ಎಷ್ಟು ಕಿಲೋ?",
        "q_vaccinations": "ಯಾವುದಾದರೂ ಲಸಿಕೆ ಬಾಕಿ ಇದೆಯೇ? ಇಲ್ಲ ಎಂದೂ ಹೇಳಬಹುದು.",
        "q_next_visit": "ಮುಂದಿನ ಭೇಟಿ ಯಾವಾಗ?",
        "readback_prefix": "ಮತ್ತೊಮ್ಮೆ ಓದುತ್ತೇನೆ. ",
        "rb_id": "ಐಡಿ {value}",
        "rb_visit": "ಭೇಟಿ ಪ್ರಕಾರ {value}",
        "rb_weight": "ತೂಕ {value} ಕಿಲೋ",
        "rb_vacc": "ಬಾಕಿ ಲಸಿಕೆಗಳು: {value}",
        "rb_date": "ಮುಂದಿನ ಭೇಟಿ {value}",
        "rb_none": "ಯಾವುದೂ ಇಲ್ಲ",
        "ask_correct": "ಇದು ಸರಿಯೇ?",
        "ask_change": "ಏನು ಬದಲಾಯಿಸಬೇಕು?", 
        "saved": "ಉಳಿಸಲಾಗಿದೆ. ಫಾಲೋ-ಅಪ್‌ಗಳು:",
        "fu_next": "ಮುಂದಿನ ಭೇಟಿ: {value}",
        "fu_vacc": "ಬಾಕಿ ಲಸಿಕೆಗಳು: {value}",
        "fu_referral": "ಪಿಎಚ್‌ಸಿ ರೆಫರಲ್ ಗುರುತಿಸಲಾಗಿದೆ",
        "already_saved": "ಈ ಭೇಟಿ ಉಳಿಸಲಾಗಿದೆ. ಹೊಸ ಭೇಟಿ ಪ್ರಾರಂಭಿಸಿ.",
        "did_not_catch": "ಕ್ಷಮಿಸಿ, ಅರ್ಥವಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಹೇಳಿ.",
        "take_your_time": "ಖಂಡಿತ, ನಿಮ್ಮ ಸಮಯ ತೆಗೆದುಕೊಳ್ಳಿ! ಸಿದ್ಧರಾದಾಗ ತಿಳಿಸಿ.",
        "language_set": "ಭಾಷೆ {language} ಗೆ ಹೊಂದಿಸಲಾಗಿದೆ. ಮುಂದುವರಿಸಿ.",
        "refer": (
            "ಅಪಾಯದ ಚಿಹ್ನೆ ಕಂಡುಬಂದಿದೆ: {label}. ದಯವಿಟ್ಟು ಈಗಲೇ ಪಿಎಚ್‌ಸಿಗೆ ಕಳುಹಿಸಿ. "
            "ಈ ದಾಖಲೆಯನ್ನು ಗುರುತಿಸಿದ್ದೇನೆ."
        ),
        "fix_id": "ಈ ಐಡಿ ಸರಿಯಾಗಿ ಕಾಣುತ್ತಿಲ್ಲ. ಐಡಿ ಮತ್ತೆ ಹೇಳಿ.",
        "fix_visit": "ಭೇಟಿ ಪ್ರಕಾರ ಹೇಳಿ: ಎಎನ್‌ಸಿ, ಪಿಎನ್‌ಸಿ, ನವಜಾತ ಅಥವಾ ಲಸಿಕೆ.",
        "fix_weight": (
            "{visit} ಭೇಟಿಗೆ {value} ಕಿಲೋ ತೂಕ ಸಾಧ್ಯವಿಲ್ಲ. ತೂಕ ಮತ್ತೆ ಹೇಳಿ."
        ),
        "fix_date": "ಮುಂದಿನ ಭೇಟಿ ದಿನಾಂಕ ಭವಿಷ್ಯದಲ್ಲಿರಬೇಕು. ದಿನಾಂಕ ಮತ್ತೆ ಹೇಳಿ.",
        "lbl_bleeding_pregnancy": "ಗರ್ಭಾವಸ್ಥೆಯಲ್ಲಿ ರಕ್ತಸ್ರಾವ",
        "lbl_fever_newborn": "ನವಜಾತ ಶಿಶುವಿಗೆ ತೀವ್ರ ಜ್ವರ",
        "lbl_convulsions": "ಸೆಳೆತ ಅಥವಾ ಫಿಟ್ಸ್",
        "lbl_not_breathing_well": "ಉಸಿರಾಟದ ತೊಂದರೆ",
        "visit_ANC": "ಎಎನ್‌ಸಿ",
        "visit_PNC": "ಪಿಎನ್‌ಸಿ",
        "visit_newborn": "ನವಜಾತ",
        "visit_immunisation": "ಲಸಿಕೆ",
        "yes_words": "ಹೌದು,ಸರಿ,ಓಕೆ,haudu,howdu,sari,ok,okay,save",
        "no_words": "ಇಲ್ಲ,ತಪ್ಪು,illa,alla,tappu,wrong",
    },
    "ml": {
        "greeting": (
            "നമസ്കാരം. ഞാൻ ഒരു എഐ സഹായിയാണ്, ഡോക്ടർ അല്ല. നിങ്ങളുടെ വീട്ടുസന്ദർശനത്തെക്കുറിച്ച് "
            "പറയൂ, ഞാൻ രേഖ പൂരിപ്പിക്കാം. തയ്യാറാകുമ്പോൾ തുടങ്ങൂ."
        ),
        "q_beneficiary_id": "ഗുണഭോക്താവിന്റെ ഐഡി എന്താണ്?",
        "q_visit_type": "ഇത് ഏത് തരം സന്ദർശനമാണ്: എഎൻസി, പിഎൻസി, നവജാതൻ അല്ലെങ്കിൽ പ്രതിരോധ കുത്തിവയ്പ്പ്?",
        "q_weight": "ഭാരം എത്ര കിലോ?",
        "q_vaccinations": "ഏതെങ്കിലും കുത്തിവയ്പ്പ് ബാക്കിയുണ്ടോ? ഇല്ല എന്നും പറയാം.",
        "q_next_visit": "അടുത്ത സന്ദർശനം എപ്പോൾ?",
        "readback_prefix": "ഒന്നുകൂടി വായിക്കാം. ",
        "rb_id": "ഐഡി {value}",
        "rb_visit": "സന്ദർശനം {value}",
        "rb_weight": "ഭാരം {value} കിലോ",
        "rb_vacc": "ബാക്കിയുള്ള കുത്തിവയ്പ്പുകൾ: {value}",
        "rb_date": "അടുത്ത സന്ദർശനം {value}",
        "rb_none": "ഒന്നുമില്ല",
        "ask_correct": "ഇത് ശരിയാണോ?",
        "ask_change": "എന്താണ് മാറ്റേണ്ടത്?", 
        "saved": "സേവ് ചെയ്തു. ഫോളോ-അപ്പുകൾ:",
        "fu_next": "അടുത്ത സന്ദർശനം: {value}",
        "fu_vacc": "ബാക്കിയുള്ള കുത്തിവയ്പ്പുകൾ: {value}",
        "fu_referral": "പിഎച്ച്സി റെഫറൽ അടയാളപ്പെടുത്തി",
        "already_saved": "ഈ സന്ദർശനം സേവ് ചെയ്തു. പുതിയ സന്ദർശനം തുടങ്ങൂ.",
        "did_not_catch": "ക്ഷമിക്കണം, മനസ്സിലായില്ല. വീണ്ടും പറയൂ.",
        "take_your_time": "തീർച്ചയായും, സമയമെടുക്കൂ! തയ്യാറാകുമ്പോൾ പറയൂ.",
        "language_set": "ഭാഷ {language} ആയി സെറ്റ് ചെയ്തു. തുടരാം.",
        "refer": (
            "അപായ സൂചന കണ്ടെത്തി: {label}. ദയവായി ഉടൻ പിഎച്ച്സിയിലേക്ക് അയക്കൂ. "
            "ഈ രേഖ അടയാളപ്പെടുത്തിയിട്ടുണ്ട്."
        ),
        "fix_id": "ഈ ഐഡി ശരിയല്ല. ഐഡി വീണ്ടും പറയൂ.",
        "fix_visit": "സന്ദർശന തരം പറയൂ: എഎൻസി, പിഎൻസി, നവജാതൻ അല്ലെങ്കിൽ കുത്തിവയ്പ്പ്.",
        "fix_weight": (
            "{visit} സന്ദർശനത്തിന് {value} കിലോ ഭാരം സാധ്യമല്ല. ഭാരം വീണ്ടും പറയൂ."
        ),
        "fix_date": "അടുത്ത സന്ദർശന തീയതി ഭാവിയിൽ ആയിരിക്കണം. തീയതി വീണ്ടും പറയൂ.",
        "lbl_bleeding_pregnancy": "ഗർഭകാലത്ത് രക്തസ്രാവം",
        "lbl_fever_newborn": "നവജാതശിശുവിന് കടുത്ത പനി",
        "lbl_convulsions": "അപസ്മാരം അല്ലെങ്കിൽ ഫിറ്റ്സ്",
        "lbl_not_breathing_well": "ശ്വാസം എടുക്കാൻ ബുദ്ധിമുട്ട്",
        "visit_ANC": "എഎൻസി",
        "visit_PNC": "പിഎൻസി",
        "visit_newborn": "നവജാതൻ",
        "visit_immunisation": "കുത്തിവയ്പ്പ്",
        "yes_words": "അതെ,ശരി,ഓക്കേ,athe,sheri,ok,okay,save",
        "no_words": "ഇല്ല,അല്ല,തെറ്റ്,illa,alla,thett,wrong",
    },
    "bn": {
        "greeting": (
            "নমস্কার। আমি একটি এআই সহায়ক, ডাক্তার নই। আপনার বাড়ি পরিদর্শনের কথা বলুন, "
            "আমি রেকর্ডটি পূরণ করব। প্রস্তুত হলে শুরু করুন।"
        ),
        "q_beneficiary_id": "সুবিধাভোগীর আইডি কী?",
        "q_visit_type": "এটি কোন ধরনের ভিজিট: এএনসি, পিএনসি, নবজাতক বা টিকাকরণ?",
        "q_weight": "ওজন কত কেজি?",
        "q_vaccinations": "কোনো টিকা বাকি আছে? নেই-ও বলতে পারেন।",
        "q_next_visit": "পরবর্তী ভিজিট কখন?",
        "readback_prefix": "আবার পড়ি। ",
        "rb_id": "আইডি {value}",
        "rb_visit": "ভিজিট {value}",
        "rb_weight": "ওজন {value} কেজি",
        "rb_vacc": "বাকি টিকা: {value}",
        "rb_date": "পরবর্তী ভিজিট {value}",
        "rb_none": "কিছু নেই",
        "ask_correct": "এটি কি ঠিক আছে?",
        "ask_change": "কী পরিবর্তন করতে হবে?", 
        "saved": "সেভ হয়েছে। ফলো-আপ:",
        "fu_next": "পরবর্তী ভিজিট: {value}",
        "fu_vacc": "বাকি টিকা: {value}",
        "fu_referral": "পিএইচসি রেফারেল চিহ্নিত",
        "already_saved": "এই ভিজিট সেভ হয়েছে। নতুন ভিজিট শুরু করুন।",
        "did_not_catch": "দুঃখিত, বুঝতে পারিনি। আবার বলুন।",
        "take_your_time": "অবশ্যই, সময় নিন! আপনি প্রস্তুত হলে বলুন।",
        "language_set": "ভাষা {language} সেট হয়েছে। চালিয়ে যান।",
        "refer": (
            "বিপদের লক্ষণ পাওয়া গেছে: {label}। অনুগ্রহ করে এখনই পিএইচসিতে পাঠান। "
            "রেকর্ডটি চিহ্নিত করেছি।"
        ),
        "fix_id": "এই আইডি ঠিক মনে হচ্ছে না। আইডি আবার বলুন।",
        "fix_visit": "ভিজিটের ধরন বলুন: এএনসি, পিএনসি, নবজাতক বা টিকাকরণ।",
        "fix_weight": (
            "{visit} ভিজিটের জন্য {value} কেজি ওজন সম্ভব নয়। ওজন আবার বলুন।"
        ),
        "fix_date": "পরবর্তী ভিজিটের তারিখ ভবিষ্যতে হতে হবে। তারিখ আবার বলুন।",
        "lbl_bleeding_pregnancy": "গর্ভাবস্থায় রক্তক্ষরণ",
        "lbl_fever_newborn": "নবজাতকের তীব্র জ্বর",
        "lbl_convulsions": "খিঁচুনি বা ফিট",
        "lbl_not_breathing_well": "শ্বাসকষ্ট",
        "visit_ANC": "এএনসি",
        "visit_PNC": "পিএনসি",
        "visit_newborn": "নবজাতক",
        "visit_immunisation": "টিকাকরণ",
        "yes_words": "হ্যাঁ,হাঁ,ঠিক,ওকে,haan,hyan,thik,ok,okay,save",
        "no_words": "না,ভুল,na,naa,vul,wrong",
    },
    "mr": {
        "greeting": (
            "नमस्कार. मी एक एआय सहाय्यक आहे, डॉक्टर नाही. तुमच्या भेटीबद्दल सांगा, "
            "मी नोंद भरते. तयार असाल तर सुरू करा."
        ),
        "q_beneficiary_id": "लाभार्थ्याची आयडी काय आहे?",
        "q_visit_type": "ही कोणती भेट आहे: एएनसी, पीएनसी, नवजात किंवा लसीकरण?",
        "q_weight": "वजन किती किलो आहे?",
        "q_vaccinations": "कोणतीही लस बाकी आहे का? नाही असेही सांगू शकता.",
        "q_next_visit": "पुढील भेट कधी आहे?",
        "readback_prefix": "मी पुन्हा वाचते. ",
        "rb_id": "आयडी {value}",
        "rb_visit": "भेट {value}",
        "rb_weight": "वजन {value} किलो",
        "rb_vacc": "बाकी लसी: {value}",
        "rb_date": "पुढील भेट {value}",
        "rb_none": "काहीही नाही",
        "ask_correct": "हे बरोबर आहे का?",
        "ask_change": "काय बदलायचे आहे?", 
        "saved": "सेव्ह झाले. फॉलो-अप:",
        "fu_next": "पुढील भेट: {value}",
        "fu_vacc": "बाकी लसी: {value}",
        "fu_referral": "पीएचसी रेफरल चिन्हांकित",
        "already_saved": "ही भेट सेव्ह झाली आहे. नवीन भेट सुरू करा.",
        "did_not_catch": "माफ करा, समजले नाही. पुन्हा सांगा.",
        "take_your_time": "हो नक्कीच, वेळ घ्या! आपण तयार झाल्यावर सांगा.",
        "language_set": "भाषा {language} वर सेट झाली. पुढे सांगा.",
        "refer": (
            "धोक्याचे लक्षण आढळले: {label}. कृपया आत्ताच पीएचसीला पाठवा. "
            "ही नोंद चिन्हांकित केली आहे."
        ),
        "fix_id": "ही आयडी बरोबर वाटत नाही. आयडी पुन्हा सांगा.",
        "fix_visit": "भेटीचा प्रकार सांगा: एएनसी, पीएनसी, नवजात किंवा लसीकरण.",
        "fix_weight": (
            "{visit} भेटीसाठी {value} किलो वजन शक्य नाही. वजन पुन्हा सांगा."
        ),
        "fix_date": "पुढील भेटीची तारीख पुढील काळातील असावी. तारीख पुन्हा सांगा.",
        "lbl_bleeding_pregnancy": "गर्भारपणात रक्तस्राव",
        "lbl_fever_newborn": "नवजात बाळाला तीव्र ताप",
        "lbl_convulsions": "झटके किंवा फिट्स",
        "lbl_not_breathing_well": "श्वास घेण्यास त्रास",
        "visit_ANC": "एएनसी",
        "visit_PNC": "पीएनसी",
        "visit_newborn": "नवजात",
        "visit_immunisation": "लसीकरण",
        "yes_words": "हो,होय,बरोबर,ठीक,ओके,ho,hoi,barobar,thik,ok,okay,save",
        "no_words": "नाही,नको,चूक,nahi,nai,chook,wrong",
    },
}

# --------------------------------------------------------------------------- #
# Conversational voice
#
# The session greets like an assistant, acknowledges what it just heard and
# then asks for whatever is still missing, instead of reading a form aloud.
# These entries override or extend the table above.
# --------------------------------------------------------------------------- #
CONVERSATIONAL = {
    "en": {
        "greeting": (
            "Welcome! I am Sahayak, your field assistant. What are we doing today?"
        ),
        "q_beneficiary_id": "Which beneficiary is this? Please say the ID.",
        "q_visit_type": "What kind of visit is it: ANC, PNC, newborn, or immunisation?",
        "q_weight": "What is the weight, in kilos?",
        "q_vaccinations": "Any vaccinations due? Say none if there are none.",
        "q_next_visit": "When should the next visit be?",
        "ack": "Got it: {summary}.",
        "ask_save": "Is this correct? Should I save it?",
        "switched": "Okay, I will speak in {language} from now on.",
        "nothing_heard": "I did not catch a new detail.",
        "saved": "Saved. It is on the dashboard now. Follow-ups:",
    },
    "hi": {
        "greeting": (
            "नमस्ते! मैं सहायक हूँ, आपका फ़ील्ड असिस्टेंट। आज क्या करना है?"
        ),
        "q_beneficiary_id": "किस लाभार्थी के घर जा रही हैं? आईडी बताइए।",
        "q_visit_type": "यह कैसी विज़िट है: एएनसी, पीएनसी, नवजात या टीकाकरण?",
        "q_weight": "वज़न कितने किलो है?",
        "q_vaccinations": "कोई टीका बाकी है? नहीं है तो ‘कोई नहीं’ कहिए।",
        "q_next_visit": "अगली विज़िट कब रखनी है?",
        "ack": "ठीक है: {summary}।",
        "ask_save": "क्या यह सही है? सेव कर दूँ?",
        "switched": "ठीक है, अब मैं {language} में बात करूँगी।",
        "nothing_heard": "कोई नई जानकारी नहीं मिली।",
        "saved": "सेव हो गया। रिकॉर्ड अब डैशबोर्ड पर है। फॉलो-अप:",
    },
    "ta": {
        "greeting": (
            "வணக்கம்! நான் சகாயக், உங்கள் கள உதவியாளர். இன்று என்ன செய்யலாம்?"
        ),
        "q_beneficiary_id": "யாருடைய வீட்டுக்குப் போகிறீர்கள்? ஐடி சொல்லுங்கள்.",
        "q_visit_type": "இது எந்த வருகை: ஏஎன்சி, பிஎன்சி, புதிதாகப் பிறந்தவர் அல்லது தடுப்பூசியா?",
        "q_weight": "எடை எத்தனை கிலோ?",
        "q_vaccinations": "தடுப்பூசி ஏதாவது பாக்கியா? இல்லை என்றால் ‘இல்லை’ சொல்லுங்கள்.",
        "q_next_visit": "அடுத்த வருகையை எப்போது வைக்கலாம்?",
        "ack": "சரி: {summary}.",
        "ask_save": "இது சரிதானே? சேமிக்கவா?",
        "switched": "சரி, இனிமேல் {language} மொழியில் பேசுகிறேன்.",
        "nothing_heard": "புதிய தகவல் எதுவும் கிடைக்கவில்லை.",
        "saved": "சேமிக்கப்பட்டது. பதிவு இப்போது டாஷ்போர்டில் உள்ளது. பின்தொடர்வுகள்:",
    },
    "te": {
        "greeting": (
            "నమస్తే! నేను సహాయక్, మీ ఫీల్డ్ సహాయకుడు. ఈరోజు ఏం చేయాలి?"
        ),
        "q_beneficiary_id": "ఎవరి ఇంటికి వెళ్తున్నారు? ఐడీ చెప్పండి.",
        "q_visit_type": "ఇది ఏ రకమైన సందర్శన: ఏఎన్సీ, పీఎన్సీ, నవజాత శిశువు లేదా టీకా?",
        "q_weight": "బరువు ఎన్ని కిలోలు?",
        "q_vaccinations": "ఏమైనా టీకాలు బాకీ ఉన్నాయా? లేకపోతే ‘లేదు’ అనండి.",
        "q_next_visit": "తదుపరి సందర్శన ఎప్పుడు పెట్టాలి?",
        "ack": "సరే: {summary}.",
        "ask_save": "ఇది సరైనదేనా? సేవ్ చేయాలా?",
        "switched": "సరే, ఇప్పటి నుంచి {language} లో మాట్లాడతాను.",
        "nothing_heard": "కొత్త వివరం ఏమీ దొరకలేదు.",
        "saved": "సేవ్ అయింది. రికార్డు ఇప్పుడు డాష్‌బోర్డ్‌లో ఉంది. ఫాలో-అప్‌లు:",
    },
    "kn": {
        "greeting": (
            "ನಮಸ್ಕಾರ! ನಾನು ಸಹಾಯಕ್, ನಿಮ್ಮ ಕ್ಷೇತ್ರ ಸಹಾಯಕ. ಇವತ್ತು ಏನು ಮಾಡೋಣ?"
        ),
        "q_beneficiary_id": "ಯಾರ ಮನೆಗೆ ಹೋಗುತ್ತಿದ್ದೀರಿ? ಐಡಿ ಹೇಳಿ.",
        "q_visit_type": "ಇದು ಯಾವ ಭೇಟಿ: ಎಎನ್‌ಸಿ, ಪಿಎನ್‌ಸಿ, ನವಜಾತ ಅಥವಾ ಲಸಿಕೆ?",
        "q_weight": "ತೂಕ ಎಷ್ಟು ಕಿಲೋ?",
        "q_vaccinations": "ಯಾವುದಾದರೂ ಲಸಿಕೆ ಬಾಕಿ ಇದೆಯೇ? ಇಲ್ಲ ಅಂದರೆ ‘ಇಲ್ಲ’ ಹೇಳಿ.",
        "q_next_visit": "ಮುಂದಿನ ಭೇಟಿ ಯಾವಾಗ ಇಡೋಣ?",
        "ack": "ಸರಿ: {summary}.",
        "ask_save": "ಇದು ಸರಿನಾ? ಉಳಿಸಲೇ?",
        "switched": "ಸರಿ, ಇನ್ನು {language} ನಲ್ಲಿ ಮಾತನಾಡುತ್ತೇನೆ.",
        "nothing_heard": "ಹೊಸ ವಿವರ ಏನೂ ಸಿಗಲಿಲ್ಲ.",
        "saved": "ಉಳಿಸಲಾಗಿದೆ. ದಾಖಲೆ ಈಗ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್‌ನಲ್ಲಿದೆ. ಫಾಲೋ-ಅಪ್‌ಗಳು:",
    },
    "ml": {
        "greeting": (
            "നമസ്കാരം! ഞാൻ സഹായക്, നിങ്ങളുടെ ഫീൽഡ് സഹായി. ഇന്ന് എന്താണ് ചെയ്യേണ്ടത്?"
        ),
        "q_beneficiary_id": "ആരുടെ വീട്ടിലേക്കാണ് പോകുന്നത്? ഐഡി പറയൂ.",
        "q_visit_type": "ഇത് ഏത് സന്ദർശനമാണ്: എഎൻസി, പിഎൻസി, നവജാതൻ അല്ലെങ്കിൽ കുത്തിവയ്പ്പ്?",
        "q_weight": "ഭാരം എത്ര കിലോ?",
        "q_vaccinations": "കുത്തിവയ്പ്പ് ബാക്കിയുണ്ടോ? ഇല്ലെങ്കിൽ ‘ഇല്ല’ പറയൂ.",
        "q_next_visit": "അടുത്ത സന്ദർശനം എപ്പോൾ വെക്കണം?",
        "ack": "ശരി: {summary}.",
        "ask_save": "ഇത് ശരിയാണോ? സേവ് ചെയ്യണോ?",
        "switched": "ശരി, ഇനി ഞാൻ {language} സംസാരിക്കാം.",
        "nothing_heard": "പുതിയ വിവരം ഒന്നും കിട്ടിയില്ല.",
        "saved": "സേവ് ചെയ്തു. രേഖ ഇപ്പോൾ ഡാഷ്ബോർഡിൽ ഉണ്ട്. ഫോളോ-അപ്പുകൾ:",
    },
    "bn": {
        "greeting": (
            "নমস্কার! আমি সহায়ক, আপনার ফিল্ড সহকারী। আজ কী করব?"
        ),
        "q_beneficiary_id": "কার বাড়িতে যাচ্ছেন? আইডি বলুন।",
        "q_visit_type": "এটি কোন ভিজিট: এএনসি, পিএনসি, নবজাতক নাকি টিকাকরণ?",
        "q_weight": "ওজন কত কেজি?",
        "q_vaccinations": "কোনো টিকা বাকি আছে? না থাকলে ‘নেই’ বলুন।",
        "q_next_visit": "পরের ভিজিট কখন রাখব?",
        "ack": "ঠিক আছে: {summary}।",
        "ask_save": "এটা ঠিক আছে তো? সেভ করব?",
        "switched": "ঠিক আছে, এখন থেকে {language} ভাষায় বলব।",
        "nothing_heard": "নতুন কোনো তথ্য পাইনি।",
        "saved": "সেভ হয়েছে। রেকর্ডটি এখন ড্যাশবোর্ডে আছে। ফলো-আপ:",
    },
    "mr": {
        "greeting": (
            "नमस्कार! मी सहायक, तुमचा फील्ड सहाय्यक. आज काय करायचं आहे?"
        ),
        "q_beneficiary_id": "कोणाच्या घरी जात आहात? आयडी सांगा.",
        "q_visit_type": "ही कशी भेट आहे: एएनसी, पीएनसी, नवजात की लसीकरण?",
        "q_weight": "वजन किती किलो आहे?",
        "q_vaccinations": "काही लस बाकी आहे का? नसेल तर ‘नाही’ म्हणा.",
        "q_next_visit": "पुढची भेट कधी ठेवायची?",
        "ack": "बरं: {summary}.",
        "ask_save": "हे बरोबर आहे ना? सेव्ह करू का?",
        "switched": "ठीक आहे, आता मी {language} मध्ये बोलते.",
        "nothing_heard": "नवीन माहिती मिळाली नाही.",
        "saved": "सेव्ह झाले. नोंद आता डॅशबोर्डवर आहे. फॉलो-अप:",
    },
}

for _code, _block in CONVERSATIONAL.items():
    STRINGS.setdefault(_code, {}).update(_block)


# Fixed phrases pre-synthesised at startup (README: sub-50 ms first audio on
# fixed turns).
FIXED_KEYS = (
    "greeting",
    "q_beneficiary_id",
    "q_visit_type",
    "q_weight",
    "q_vaccinations",
    "q_next_visit",
    "ask_save",
    "saved",
)


def normalize_lang(code, default: str = DEFAULT) -> str:
    """'hi-IN' / 'hi-IN,en-IN' / 'hi_en' -> 'hi'. Unknown codes fall back."""
    if not code:
        return default
    if isinstance(code, (list, tuple)) and code:
        code = code[0]
    text = str(code).strip().lower().replace("_", "-")
    primary = text.split(",")[0].split("-")[0]
    return primary if primary in SUPPORTED else default


def locale_for(lang) -> str:
    return LOCALE_CODES.get(normalize_lang(lang), LOCALE_CODES[DEFAULT])


def stt_language_header(lang) -> str:
    """One locale only: the v3 stream rejects a comma-separated language_code."""
    return LOCALE_CODES[normalize_lang(lang)]


def stt_multilingual_header() -> str:
    """Prisma v3.0 identifies the spoken language and reports it back."""
    return "indic-auto"


def t(lang, key, **kwargs) -> str:
    """Look up a localised string, falling back to English then to the key."""
    lang = normalize_lang(lang)
    table = STRINGS.get(lang) or STRINGS[DEFAULT]
    text = table.get(key)
    if text is None:
        text = STRINGS[DEFAULT].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def words(lang, key) -> tuple:
    """Split a yes/no word list into tokens."""
    raw = t(lang, key)
    return tuple(w.strip().lower() for w in raw.split(",") if w.strip())


def danger_label(lang, sign_id, fallback) -> str:
    return t(lang, f"lbl_{sign_id}") or fallback


def visit_label(lang, visit_type) -> str:
    if not visit_type:
        return ""
    return t(lang, f"visit_{visit_type}") or visit_type


def fixed_phrases(lang):
    """[(key, text)] of the phrases worth pre-caching for a language."""
    return [(key, t(lang, key)) for key in FIXED_KEYS]


def language_name(code) -> str:
    return LANGUAGE_NAMES.get(normalize_lang(code), LANGUAGE_NAMES[DEFAULT])
