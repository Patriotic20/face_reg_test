import re
import unicodedata

# Tezlik uchun oldindan kompilyatsiyalangan regex
_punct_re = re.compile(r"[^\w\s']", re.UNICODE)  # apostrofni saqlaydi
_space_re = re.compile(r"\s+")

# O'zbek tilida ishlatiladigan turli apostrof belgilar
UZ_APOSTROPHES = "ʼʻ’‘`´"

# Barcha apostrof variantlarini standart apostrofga "'" o'zgartirish
apostrophe_table = str.maketrans({c: "'" for c in UZ_APOSTROPHES})


def normalize_str(text: str) -> str:
    """
    Matnni qidiruv uchun normallashtiradi.

    Ushbu funksiyaning vazifasi:
    1. Matnni kichik harflarga o'tkazish va boshlanish/oxiridagi bo'sh joylarni olib tashlash.
    2. Unicode aksentlarini olib tashlash (masalan, 'á' → 'a').
    3. O'zbek tilida turli apostrof belgilarini bitta standart apostrof "'" ga o'zgartirish.
       Misol: o‘, o’, o` → o'
    4. Barcha boshqa punktuatsiya belgilarini bo'sh joy bilan almashtirish (apostrof saqlanadi).
    5. Ko'p bo'sh joylarni bitta bo'sh joyga kamaytirish.
    
    Natija sifatida qaytarilgan matn qidiruv (SQLAlchemy ILIKE yoki full-text search) 
    uchun moslashgan, tozalangan va normallashtirilgan bo'ladi.

    Args:
        text (str): Normallashtiriladigan kirish matni.

    Returns:
        str: Tozalangan va qidiruv uchun tayyor matn.

    Misollar:
        >>> normalize_str("O`tkir")
        "o'tkir"
        >>> normalize_str("O‘TKIR!!!")
        "o'tkir"
        >>> normalize_str("  Shoxrux   ")
        "shoxrux"
    """
    
    if not isinstance(text, str):
        return ""

    # Kichik harflarga o'tkazish va bo'sh joylarni olib tashlash
    text = text.lower().strip()

    # Aksent belgilarini olib tashlash
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))

    # Barcha apostrof variantlarini standart apostrof "'" ga o'zgartirish
    text = text.translate(apostrophe_table)

    # Boshqa punktuatsiya belgilarini bo'sh joy bilan almashtirish (apostrof saqlanadi)
    text = _punct_re.sub(" ", text)

    # Ko'p bo'sh joylarni bitta bo'sh joyga kamaytirish
    text = _space_re.sub(" ", text)

    return text.strip()