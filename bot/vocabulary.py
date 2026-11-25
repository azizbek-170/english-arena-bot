"""
Darajalarga mos lug'atlar (AI tomonidan tayyorlangan).

Har bir so'z:
  uz      - o'zbekcha so'z (ishtirokchiga ko'rsatiladi)
  en      - inglizcha to'g'ri javob (typing bosqichi uchun)
  options - 4 ta variant, 0-indeks (a) doimo to'g'ri javob.

Admin panelidagi "AI orqali lug'at qo'shish" tugmasi shu lug'atlarni
tanlangan arenaga savol sifatida yuklaydi.
"""

from .idioms_data import ALL_IDIOMS, IDIOMS

VOCABULARY = {
    "A1": [
        {"uz": "salom", "en": "hello", "options": ["hello", "goodbye", "thanks", "please"]},
        {"uz": "rahmat", "en": "thank you", "options": ["thank you", "hello", "sorry", "yes"]},
        {"uz": "ha", "en": "yes", "options": ["yes", "no", "maybe", "please"]},
        {"uz": "yo'q", "en": "no", "options": ["no", "yes", "okay", "thanks"]},
        {"uz": "kitob", "en": "book", "options": ["book", "pen", "bag", "desk"]},
        {"uz": "suv", "en": "water", "options": ["water", "bread", "milk", "juice"]},
        {"uz": "non", "en": "bread", "options": ["bread", "water", "cheese", "rice"]},
        {"uz": "uy", "en": "house", "options": ["house", "school", "car", "tree"]},
        {"uz": "do'st", "en": "friend", "options": ["friend", "teacher", "brother", "doctor"]},
        {"uz": "yaxshi", "en": "good", "options": ["good", "bad", "slow", "old"]},
    ],
    "A2": [
        {"uz": "kutubxona", "en": "library", "options": ["library", "market", "hospital", "station"]},
        {"uz": "sayohat", "en": "journey", "options": ["journey", "lesson", "meal", "meeting"]},
        {"uz": "ertalab", "en": "morning", "options": ["morning", "evening", "night", "afternoon"]},
        {"uz": "kechqurun", "en": "evening", "options": ["evening", "morning", "noon", "midnight"]},
        {"uz": "ishlamoq", "en": "to work", "options": ["to work", "to sleep", "to play", "to eat"]},
        {"uz": "o'qimoq", "en": "to study", "options": ["to study", "to forget", "to break", "to buy"]},
        {"uz": "savol", "en": "question", "options": ["question", "answer", "problem", "secret"]},
        {"uz": "javob", "en": "answer", "options": ["answer", "question", "choice", "reason"]},
        {"uz": "qiziqarli", "en": "interesting", "options": ["interesting", "boring", "tired", "quiet"]},
        {"uz": "bugungi", "en": "today's", "options": ["today's", "yesterday's", "tomorrow's", "former"]},
    ],
    "B1": [
        {"uz": "tajriba", "en": "experience", "options": ["experience", "experiment", "exercise", "expert"]},
        {"uz": "maqsad", "en": "goal", "options": ["goal", "tool", "rule", "road"]},
        {"uz": "muvaffaqiyat", "en": "success", "options": ["success", "failure", "effort", "chance"]},
        {"uz": "qiyinchilik", "en": "challenge", "options": ["challenge", "change", "chance", "charge"]},
        {"uz": "taklif", "en": "suggestion", "options": ["suggestion", "decision", "question", "reaction"]},
        {"uz": "munosabat", "en": "relationship", "options": ["relationship", "relative", "relevance", "reason"]},
        {"uz": "ta'sir", "en": "impact", "options": ["impact", "imprint", "impulse", "impose"]},
        {"uz": "izlanish", "en": "research", "options": ["research", "searching", "resource", "respect"]},
        {"uz": "o'zgarish", "en": "change", "options": ["change", "chance", "charge", "choice"]},
        {"uz": "kelajak", "en": "future", "options": ["future", "past", "present", "moment"]},
    ],
    "B2": [
        {"uz": "natija", "en": "outcome", "options": ["outcome", "output", "outset", "outfit"]},
        {"uz": "hal qiluvchi", "en": "crucial", "options": ["crucial", "cruel", "critical", "cultural"]},
        {"uz": "tahlil", "en": "analysis", "options": ["analysis", "analyst", "analyze", "analogy"]},
        {"uz": "farq", "en": "difference", "options": ["difference", "difficulty", "differently", "diffuse"]},
        {"uz": "mas'uliyat", "en": "responsibility", "options": ["responsibility", "response", "responsible", "responsive"]},
        {"uz": "ishonch", "en": "confidence", "options": ["confidence", "confidential", "conference", "confirmation"]},
        {"uz": "munozara", "en": "discussion", "options": ["discussion", "decision", "discipline", "distinction"]},
        {"uz": "xolis", "en": "impartial", "options": ["impartial", "important", "impatient", "impersonal"]},
        {"uz": "moslashuv", "en": "adaptation", "options": ["adaptation", "adoption", "addition", "adjustment"]},
        {"uz": "keng qamrovli", "en": "comprehensive", "options": ["comprehensive", "comprehension", "compressive", "compromise"]},
    ],
    "C1": [
        {"uz": "noaniqlik", "en": "ambiguity", "options": ["ambiguity", "ambition", "analogy", "anxiety"]},
        {"uz": "mohiyat", "en": "essence", "options": ["essence", "existence", "evidence", "estimate"]},
        {"uz": "ziddiyat", "en": "contradiction", "options": ["contradiction", "contrast", "contribution", "convention"]},
        {"uz": "ishonchlilik", "en": "reliability", "options": ["reliability", "relevance", "relation", "reluctance"]},
        {"uz": "taraqqiyot", "en": "advancement", "options": ["advancement", "advertisement", "advantage", "adventure"]},
        {"uz": "murakkablik", "en": "complexity", "options": ["complexity", "complicity", "commodity", "community"]},
        {"uz": "taxmin", "en": "assumption", "options": ["assumption", "assurance", "assignment", "association"]},
        {"uz": "qarama-qarshilik", "en": "opposition", "options": ["opposition", "opportunity", "option", "oppression"]},
        {"uz": "chuqur", "en": "profound", "options": ["profound", "profane", "profitable", "professional"]},
        {"uz": "o'ziga xos", "en": "distinctive", "options": ["distinctive", "distant", "distinguished", "distractive"]},
    ],
    "C2": [
        {"uz": "o'tkinchi", "en": "ephemeral", "options": ["ephemeral", "eternal", "emphasized", "empirical"]},
        {"uz": "nuqtai nazar", "en": "standpoint", "options": ["standpoint", "standstill", "setting", "stance"]},
        {"uz": "hal qiluvchi", "en": "pivotal", "options": ["pivotal", "pilot", "personal", "potential"]},
        {"uz": "nomuvofiqlik", "en": "discrepancy", "options": ["discrepancy", "discretion", "discrimination", "discussion"]},
        {"uz": "keng tarqalgan", "en": "prevalent", "options": ["prevalent", "previous", "preventive", "primitive"]},
        {"uz": "qat'iy", "en": "unequivocal", "options": ["unequivocal", "unessential", "unusual", "unanimous"]},
        {"uz": "noyob", "en": "unprecedented", "options": ["unprecedented", "unpredictable", "unreasonable", "unnoticed"]},
        {"uz": "o'zaro bog'liqlik", "en": "interdependence", "options": ["interdependence", "independence", "interaction", "intervention"]},
        {"uz": "murakkab", "en": "intricate", "options": ["intricate", "intrigue", "intimate", "integral"]},
        {"uz": "ma'nodosh", "en": "synonymous", "options": ["synonymous", "synchronous", "synthetic", "sympathetic"]},
    ],
}


# Gap filling (nuqtalarni to'ldirish) savollari.
# uz  -> nuqtali gap (ishtirokchiga ko'rsatiladi)
# en  -> nuqta o'rniga keladigan so'z
# options[0] doimo to'g'ri javob
GAP_FILLING = {
    "A1": [
        {"uz": "I ___ from Uzbekistan.", "en": "am", "options": ["am", "is", "are", "be"]},
        {"uz": "She ___ a student.", "en": "is", "options": ["is", "am", "are", "be"]},
        {"uz": "They ___ friends.", "en": "are", "options": ["are", "is", "am", "be"]},
        {"uz": "This is ___ apple.", "en": "an", "options": ["an", "a", "the", "some"]},
        {"uz": "I have ___ book.", "en": "a", "options": ["a", "an", "the", "two"]},
        {"uz": "We ___ to school every day.", "en": "go", "options": ["go", "goes", "going", "went"]},
        {"uz": "He ___ football on Sunday.", "en": "plays", "options": ["plays", "play", "playing", "played"]},
        {"uz": "I drink ___ every morning.", "en": "water", "options": ["water", "bread", "chair", "pen"]},
        {"uz": "My name ___ Aziz.", "en": "is", "options": ["is", "are", "am", "be"]},
        {"uz": "It ___ a cat.", "en": "is", "options": ["is", "are", "am", "be"]},
    ],
    "A2": [
        {"uz": "I ___ to the library yesterday.", "en": "went", "options": ["went", "go", "goes", "going"]},
        {"uz": "She is ___ a book now.", "en": "reading", "options": ["reading", "read", "reads", "reader"]},
        {"uz": "There ___ some water in the glass.", "en": "is", "options": ["is", "are", "were", "be"]},
        {"uz": "I have never ___ to London.", "en": "been", "options": ["been", "went", "gone", "go"]},
        {"uz": "He is interested ___ music.", "en": "in", "options": ["in", "on", "at", "for"]},
        {"uz": "We will ___ the test tomorrow.", "en": "take", "options": ["take", "takes", "took", "taking"]},
        {"uz": "This question is ___ than that one.", "en": "easier", "options": ["easier", "easy", "easiest", "easily"]},
        {"uz": "I usually get up ___ 7 o'clock.", "en": "at", "options": ["at", "in", "on", "for"]},
        {"uz": "She can ___ English very well.", "en": "speak", "options": ["speak", "speaks", "speaking", "spoke"]},
        {"uz": "They are looking ___ the blackboard.", "en": "at", "options": ["at", "in", "on", "to"]},
    ],
    "B1": [
        {"uz": "If I ___ more time, I would travel.", "en": "had", "options": ["had", "have", "has", "having"]},
        {"uz": "He has worked here ___ 2019.", "en": "since", "options": ["since", "for", "from", "during"]},
        {"uz": "The meeting was ___ until Friday.", "en": "postponed", "options": ["postponed", "postpone", "postponing", "postponement"]},
        {"uz": "She suggested ___ a break.", "en": "taking", "options": ["taking", "take", "to take", "taken"]},
        {"uz": "I am not used ___ getting up early.", "en": "to", "options": ["to", "for", "with", "at"]},
        {"uz": "By the time we arrived, the film ___.", "en": "had started", "options": ["had started", "has started", "started", "was starting"]},
        {"uz": "He speaks English ___ he were a native.", "en": "as if", "options": ["as if", "as", "like", "though"]},
        {"uz": "The book ___ I told you about is interesting.", "en": "that", "options": ["that", "what", "who", "whom"]},
        {"uz": "It's high time you ___ your homework.", "en": "did", "options": ["did", "do", "does", "doing"]},
        {"uz": "She is likely ___ the exam.", "en": "to pass", "options": ["to pass", "pass", "passing", "passed"]},
    ],
    "B2": [
        {"uz": "Hardly ___ we left when it started raining.", "en": "had", "options": ["had", "have", "did", "were"]},
        {"uz": "The report, ___ was published last week, caused debate.", "en": "which", "options": ["which", "that", "what", "who"]},
        {"uz": "He would rather ___ at home tonight.", "en": "stay", "options": ["stay", "stays", "staying", "stayed"]},
        {"uz": "I wish I ___ the answer.", "en": "knew", "options": ["knew", "know", "knows", "knowing"]},
        {"uz": "Little ___ he realize the danger.", "en": "did", "options": ["did", "does", "had", "was"]},
        {"uz": "The deadline is ___ extended.", "en": "being", "options": ["being", "been", "be", "is"]},
        {"uz": "She demanded that he ___ on time.", "en": "be", "options": ["be", "is", "was", "were"]},
        {"uz": "___ the heavy rain, the match continued.", "en": "Despite", "options": ["Despite", "Although", "Because", "However"]},
        {"uz": "By no means ___ the solution simple.", "en": "is", "options": ["is", "was", "are", "were"]},
        {"uz": "The theory was ___ by new evidence.", "en": "disproved", "options": ["disproved", "disprove", "disproving", "disproval"]},
    ],
    "C1": [
        {"uz": "The proposal was met with considerable ___.", "en": "skepticism", "options": ["skepticism", "skeptic", "skeptical", "skeptically"]},
        {"uz": "His argument was fundamentally ___.", "en": "flawed", "options": ["flawed", "flaw", "flawing", "flawlessly"]},
        {"uz": "The new policy is ___ with existing regulations.", "en": "inconsistent", "options": ["inconsistent", "inconsistency", "consistently", "consist"]},
        {"uz": "She spoke in a remarkably ___ manner.", "en": "articulate", "options": ["articulate", "articulation", "articulately", "inarticulate"]},
        {"uz": "The two accounts are completely ___.", "en": "contradictory", "options": ["contradictory", "contradiction", "contradict", "contradictorily"]},
        {"uz": "We must ___ the possibility of error.", "en": "acknowledge", "options": ["acknowledge", "acknowledgment", "acknowledged", "acknowledging"]},
        {"uz": "His comments were ___ to the discussion.", "en": "irrelevant", "options": ["irrelevant", "relevance", "relevantly", "irrelevance"]},
        {"uz": "The evidence remains ___ inconclusive.", "en": "largely", "options": ["largely", "large", "larger", "largest"]},
        {"uz": "She has an ___ eye for detail.", "en": "acute", "options": ["acute", "acutely", "acuteness", "accurate"]},
        {"uz": "The plan was ___ abandoned.", "en": "ultimately", "options": ["ultimately", "ultimate", "ultimatum", "ulterior"]},
    ],
    "C2": [
        {"uz": "The notion is ___ absurd.", "en": "patently", "options": ["patently", "patent", "patents", "patentee"]},
        {"uz": "His remarks were ___ sarcastic.", "en": "overtly", "options": ["overtly", "overt", "over", "overture"]},
        {"uz": "The manuscript is ___ authentic.", "en": "arguably", "options": ["arguably", "argue", "argument", "argumentative"]},
        {"uz": "She displayed an ___ command of the subject.", "en": "unequivocal", "options": ["unequivocal", "unequivocally", "equivocal", "equivocate"]},
        {"uz": "The phenomenon remains ___ unexplained.", "en": "stubbornly", "options": ["stubbornly", "stubborn", "stubbornness", "stubbornest"]},
        {"uz": "His theory was eventually ___.", "en": "vindicated", "options": ["vindicated", "vindicate", "vindicating", "vindication"]},
        {"uz": "The two versions are ___ indistinguishable.", "en": "virtually", "options": ["virtually", "virtual", "virtue", "virtuous"]},
        {"uz": "He is ___ unwilling to compromise.", "en": "adamantly", "options": ["adamantly", "adamant", "adamance", "adam"]},
        {"uz": "The argument is ___ circular.", "en": "transparently", "options": ["transparently", "transparent", "transparency", "transparence"]},
        {"uz": "Such behavior is ___ unacceptable.", "en": "categorically", "options": ["categorically", "categorical", "category", "categorize"]},
    ],
}


IDIOM_LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")


def _clean_key(text: str) -> str:
    """Idiomalarni solishtirish uchun oddiy normalizatsiya."""
    return " ".join((text or "").strip().lower().replace("’", "'").split())


def get_idiom_info(idiom: str):
    """Idiom bo'yicha definition va o'zbekcha tarjimani qaytaradi."""
    target = _clean_key(idiom)
    for item in ALL_IDIOMS:
        if _clean_key(item["idiom"]) == target:
            return item
    return None


def _idiom_items(level: str):
    """IDIOMS lug'atini add_questions_bulk uchun savol shakliga o'tkazadi."""
    lvl = level.upper()
    if lvl not in IDIOM_LEVELS:
        return []

    entries = IDIOMS.get(lvl, [])
    definitions = [item["definition"] for item in ALL_IDIOMS]
    level_offset = sum(len(IDIOMS[x]) for x in IDIOM_LEVELS[: IDIOM_LEVELS.index(lvl)])

    items = []
    for index, entry in enumerate(entries):
        correct = entry["definition"]
        distractors = []
        base = level_offset + index
        step = 1
        while len(distractors) < 3 and step <= len(definitions):
            candidate = definitions[(base + step * 17) % len(definitions)]
            if (
                _clean_key(candidate) != _clean_key(correct)
                and candidate not in distractors
            ):
                distractors.append(candidate)
            step += 1

        items.append(
            {
                "uz": entry["idiom"],
                "en": entry["idiom"],
                "options": [correct, *distractors],
                "definition": entry["definition"],
                "uzbek": entry["uzbek"],
            }
        )
    return items


def get_vocabulary(level: str, qtype: str = "vocab"):
    lvl = (level or "").upper()
    if qtype == "idiom":
        return _idiom_items(lvl)
    if qtype == "gap":
        return GAP_FILLING.get(lvl, [])
    return VOCABULARY.get(lvl, [])
