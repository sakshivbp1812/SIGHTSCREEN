"""Localised deterministic phrases (English, Hinglish, Hindi). Player names and digits are kept as-is so numbers stay verifiable."""
LANGS = ("en", "hinglish", "hi")
LANG_NAME = {"en": "English", "hinglish": "Hinglish (Hindi written in Roman letters)", "hi": "Hindi in Devanagari script"}
HOW = {"hinglish": {"bowled": "bowled", "lbw": "LBW", "caught at long-on": "long-on par catch", "caught behind": "keeper ke haathon catch", "run out": "run out"},
       "hi": {
"bowled": "बोल्ड", "lbw": "एलबीडब्ल्यू", "caught at long-on": "लॉन्ग-ऑन पर कैच", "caught behind": "विकेटकीपर द्वारा कैच", "run out": "रन आउट"}}
KIND = {"hinglish": {"FOUR": "chauka", "SIX": "chhakka"}, "hi": {"FOUR": "चौका", "SIX": "छक्का"}}
T = {
    "hinglish": {
        "sit": "Abhi: {runs}/{w}, {ov} over ke baad. {need} run chahiye {balls} gend mein, required rate {rrr}, pressure {p}/100.",
        "miss_h": "Aapne yeh miss kiya:", "none": "Pichhli baar dekhne ke baad kuch khaas nahi hua.",
        "m_w": "{label} {batter} out ({how}), ab {need} run chahiye {balls} gend mein.", "m_b": "{label} {batter} ne {bowler} par {kind} maara, {need} run chahiye {balls} gend mein.",
        "trend_dn": "Pichhli baar se pressure {p0} se ghat kar {p1} hua.", "trend_up": "Pichhli baar se pressure {p0} se badh kar {p1} hua.",
        "watch": "Aage: {batter} strike par, {bowler} gendbaazi karenge. Chhakke se required rate {r0} se {r1} ho jayega; wicket se pressure {p0} se {p1}.",
        "over": "Match khatam: {result}. Final score {runs}/{w}.",
        "p_w": "Wicket! {w} out, {need} run chahiye {balls} gend mein", "p_4": "Chauka! {need} run chahiye {balls} gend mein", "p_6": "Chhakka! {need} run chahiye {balls} gend mein",
        "wicket": "{batter} out ho gaye ({how}), {bowler} ki gend par. {w} wicket gire, {need} run chahiye {balls} gend mein, required rate {rrr}.",
        "boundary": "{batter} ne {bowler} par {kind} maara. Ab {need} run chahiye {balls} gend mein; required rate {rb} se {ra} ho gaya.",
        "sq": " Yahan square boundary chhoti hai ({m} m).", "st": " Straight boundary lambi hai ({m} m), isliye shot door tak gaya.",
        "why_w": " Naya batter aaya hai, agli kuch gendein risky hain.", "why_6": " Is chhakke se target ka bada hissa kat gaya.", "why_4": " Har boundary se pressure kam hota hai.",
        "tac": " Pressure {p0} se {p1}. {bowler}: {r}/{w} {b} gend mein (is replay mein).",
        "fan_w": " Role watch: {nb} agla batter hai; {batter} {runs} par out.", "fan_b": " Role watch: {batter} ab {runs} run par ({balls} gend).",
        "fan_n": " (Koi points ya picks nahi: yeh simulated data hai.)",
        "state": "Score {runs}/{w} ({ov} over), target {target}; {need} run chahiye {balls} gend mein; required rate {rrr}, abhi ka rate {crr}; pressure index {p} (heuristic).",
        "l_casual": "Seedhi baat: chase mein chhote swing bhi jaldi jud jaate hain.", "l_tactical": "Tactical nazar: required {rrr} aur abhi ka {crr} ke beech ka gap batters ko bharna hai.",
        "l_fantasy": "Fantasy nazar: roles aur strike par kaun hai, yeh dekhiye. Is demo mein koi official points ya picks nahi.",
        "ask_note": "(Poore Hinglish jawab ke liye AI key chalu karein; tathya neeche English mein hain.)",
        "no_bets": "Sightscreen betting advice, odds ya guarantee nahi deta. Yeh match ko samjhata hai: pressure, required rate aur what-if poochiye.",
        "good": " {team} ke liye badi khabar.", "bad": " {team} ke liye mushkil pal."},
    "hi": {
        "sit": "अभी: {runs}/{w}, {ov} ओवर के बाद। {need} रन चाहिए {balls} गेंद में, रिक्वायर्ड रेट {rrr}, प्रेशर {p}/100।",
        "miss_h": "आपने यह मिस किया:", "none": "पिछली बार देखने के बाद कुछ खास नहीं हुआ।",
        "m_w": "{label} {batter} आउट ({how}), अब {need} रन चाहिए {balls} गेंद में।", "m_b": "{label} {batter} ने {bowler} पर {kind} मारा, {need} रन चाहिए {balls} गेंद में।",
        "trend_dn": "पिछली बार से प्रेशर {p0} से घटकर {p1} हुआ।", "trend_up": "पिछली बार से प्रेशर {p0} से बढ़कर {p1} हुआ।",
        "watch": "आगे: {batter} स्ट्राइक पर, गेंदबाज़ी {bowler}। छक्के से रिक्वायर्ड रेट {r0} से {r1}; विकेट से प्रेशर {p0} से {p1}।",
        "over": "मैच खत्म: {result}। फाइनल स्कोर {runs}/{w}।",
        "p_w": "विकेट! {w} आउट, {need} रन चाहिए {balls} गेंद में", "p_4": "चौका! {need} रन चाहिए {balls} गेंद में", "p_6": "छक्का! {need} रन चाहिए {balls} गेंद में",
        "wicket": "{batter} आउट ({how}), गेंदबाज़ {bowler}। {w} विकेट गिरे, {need} रन चाहिए {balls} गेंद में, रिक्वायर्ड रेट {rrr}।",
        "boundary": "{batter} ने {bowler} पर {kind} मारा। अब {need} रन चाहिए {balls} गेंद में; रिक्वायर्ड रेट {rb} से {ra} हुआ।",
        "sq": " यहाँ स्क्वायर बाउंड्री छोटी है ({m} मीटर)।", "st": " सीधी बाउंड्री लंबी है ({m} मीटर), इसलिए शॉट दूर तक गया।",
        "why_w": " नया बल्लेबाज़ आया है, अगली कुछ गेंदें जोखिम भरी हैं।", "why_6": " इस छक्के से लक्ष्य का बड़ा हिस्सा कम हुआ।", "why_4": " हर बाउंड्री से दबाव घटता है।",
        "tac": " दबाव {p0} से {p1}। {bowler} (इस रिप्ले में): {r} रन, {w} विकेट, {b} गेंद।",
        "fan_w": " रोल वॉच: {nb} अगला बल्लेबाज़ है; {batter} {runs} पर आउट।", "fan_b": " रोल वॉच: {batter} अब {runs} रन पर ({balls} गेंद)।",
        "fan_n": " (कोई पॉइंट्स या पिक्स नहीं: यह सिम्युलेटेड डेटा है।)",
        "state": "स्कोर {runs}/{w} ({ov} ओवर), लक्ष्य {target}; {need} रन चाहिए {balls} गेंद में; रिक्वायर्ड रेट {rrr}, मौजूदा रेट {crr}; प्रेशर इंडेक्स {p} (अनुमानित)।",
        "l_casual": "आसान भाषा में: चेज़ में छोटे बदलाव भी जल्दी जुड़ जाते हैं।", "l_tactical": "टैक्टिकल नज़र: रिक्वायर्ड {rrr} और मौजूदा {crr} का अंतर बल्लेबाज़ों को भरना है।",
        "l_fantasy": "फैंटेसी नज़र: रोल और स्ट्राइक पर कौन है, यह देखें। इस डेमो में कोई आधिकारिक पॉइंट्स या पिक्स नहीं।",
        "ask_note": "(पूरे हिंदी जवाब के लिए AI कुंजी चालू करें; तथ्य नीचे अंग्रेज़ी में हैं।)",
        "no_bets": "Sightscreen सट्टेबाज़ी की सलाह, ऑड्स या गारंटी नहीं देता। यह मैच को समझाता है: प्रेशर, रिक्वायर्ड रेट और व्हाट-इफ पूछें।",
        "good": " {team} के लिए बड़ी खबर।", "bad": " {team} के लिए मुश्किल पल।"},
    "en": {
        "sit": "Where we are: {runs}/{w} after {ov} overs. {need} needed from {balls} balls, required rate {rrr}, pressure {p} out of 100.",
        "miss_h": "What you missed:", "none": "Nothing major has happened since you last looked.",
        "m_w": "{label} {batter} out ({how}), {need} needed from {balls}.", "m_b": "{label} {batter} hit a {kind} off {bowler}, {need} needed from {balls}.",
        "trend_dn": "Pressure has eased from {p0} to {p1} since you last looked.", "trend_up": "Pressure has risen from {p0} to {p1} since you last looked.",
        "watch": "Next: {batter} on strike, {bowler} bowling. A six would take the required rate from {r0} to {r1}; a wicket would move pressure from {p0} to {p1}.",
        "over": "Match over: {result}. Final score {runs}/{w}.",
        "p_w": "Wicket! {w} down, need {need} off {balls}", "p_4": "Four! Need {need} off {balls}", "p_6": "Six! Need {need} off {balls}","good": " Big moment for {team}.", "bad": " Tough moment for {team}.",
           "no_bets": "Sightscreen does not give betting advice, odds or guarantees. It explains what is happening in the match "
                      "and how pressure changes. Ask about a moment, the required rate or a what-if."},
}


def how(lang: str, h) -> str:
    return HOW.get(lang, {}).get(h, h) if h else ""


def kind(lang: str, k: str) -> str:
    return KIND.get(lang, {}).get(k, k.lower())
