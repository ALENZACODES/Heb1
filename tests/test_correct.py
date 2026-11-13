from heb1.correct import Corrector, budget, distance

WORDS = ["שלום", "כשרה", "בשרה", "סגור", "פתוח", "מסעדה", "קפה", "רחוב", "יציאה", "כניסה"]


def c():
    return Corrector(WORDS)


def test_distance_weights():
    assert distance("שלום", "שלום") == 0
    assert abs(distance("רחוב", "דחוב") - 0.4) < 1e-9     # ד/ר look alike
    assert abs(distance("יציאה", "יצאה") - 0.6) < 1e-9    # narrow letter dropped
    assert distance("שלום", "פתוח") > 1.5
    assert budget(1) == 0 and budget(2) == 0.4


def test_confident_words_are_never_changed():
    assert c().suggest("דחוב", 95) == "דחוב"
    assert c().suggest("דחוב", -1) == "דחוב"      # no confidence given: leave as read


def test_unsure_lookalike_is_fixed():
    assert c().suggest("דחוב", 75) == "רחוב"
    assert c().suggest("דחוב,", 75) == "רחוב,"     # punctuation kept


def test_ambiguous_is_left_alone():
    # כשרה and בשרה are both listed: a real ambiguity, needs context
    assert c().suggest("כשרה", 50) == "כשרה"
    assert Corrector(["כשרה", "בשרה"]).suggest("גשרה", 50) == "גשרה"


def test_prefixed_known_word_kept_and_skips():
    assert c().suggest("והקפה", 40) == "והקפה"
    assert c().suggest("123", 10) == "123"
    assert c().suggest("abc", 10) == "abc"
    assert c().suggest("שָׁלוֹם", 10) == "שָׁלוֹם"        # pointed text untouched
    assert c().suggest("\u05D9\u05D4\u05D5\u05D4", 10) == "\u05D9\u05D4\u05D5\u05D4"
