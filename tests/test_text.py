from heb1 import text as T

NAME = "\u05D9\u05D4\u05D5\u05D4"          # never written out in this repo
POINTED_NAME = "\u05D9\u05B0\u05D4\u05B9\u05D5\u05B8\u05D4"


def test_show_name_bare_pointed_and_prefixed():
    assert T.show_name(f"ברוך אתה {NAME} אלהינו") == "ברוך אתה ה׳ אלהינו"
    assert T.show_name(POINTED_NAME) == "ה׳"
    assert T.show_name("ל" + NAME) == "לה׳"
    assert T.show_name("וב" + NAME) == "ובה׳"
    assert T.has_name(NAME) and not T.has_name("יהודה")
    assert T.show_name("יהודה") == "יהודה"


def test_strip_nikud_and_teamim():
    pointed = "בְּרֵאשִׁ֖ית בָּרָ֣א"
    assert T.strip_nikud(pointed) == "בראשית ברא"
    only_vowels = T.strip_cantillation(pointed)
    assert "\u0596" not in only_vowels and "\u05B0" in only_vowels
    assert T.strip_nikud("בֵּית־סֵפֶר") == "בית־ספר"
    assert T.strip_nikud("בֵּית־סֵפֶר", keep_maqaf=False) == "בית-ספר"


def test_final_letters():
    assert T.fix_final_letters("שלומ עולמ") == "שלום עולם"
    assert T.fix_final_letters("ךלב") == "כלב"
    assert T.fix_final_letters("מלך") == "מלך"
    assert T.fix_final_letters("צ׳ק") == "צ׳ק"        # abbreviation-style tokens untouched
    assert T.fix_final_letters("ן") == "ן"


def test_geresh_gershayim():
    assert T.fix_geresh('צה"ל') == "צה״ל"
    assert T.fix_geresh("ג'ירפה") == "ג׳ירפה"
    assert T.fix_geresh('הוא אמר "שלום"') == 'הוא אמר "שלום"'


def test_bidi_and_presentation_forms():
    assert T.strip_bidi("\u200Fשלום\u200E") == "שלום"
    assert T.normalize("\uFB2A") == "\u05E9\u05C1"     # precomposed shin+shin dot unfolded
    assert T.for_display("שלום\nabc") == "\u200Fשלום\nabc"


def test_reversed_line_detection_and_fix():
    logical = "שלום לכם מן העולם"
    visual = logical[::-1]
    assert not T.looks_reversed(logical)
    assert T.looks_reversed(visual)
    assert T.to_logical(visual) == logical
    assert T.to_logical("2026 םולש"[::-1][::-1]) == "שלום 2026"


def test_clean_chain():
    raw = "\u200Fשלומ  עולמ\n\n\n\nצה\"ל " + NAME
    assert T.clean(raw) == "שלום עולם\n\nצה״ל ה׳"
    assert T.clean("שָׁלוֹם", nikud="strip") == "שלום"
