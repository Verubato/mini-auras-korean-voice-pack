"""Renders the Korean voice packs into src/Sounds/<pack>/.

The spell lists, the file naming and the rendering pipeline all belong to MiniAuras, so this
imports its generator from the sibling checkout rather than restating any of it. What lives here
is the Korean side: which voices, what they say, and the check that the clip names still match
the packs MiniAuras ships.

Run from the repo root with the ELEVENLABS_API_KEY environment variable set:
    python scripts/GenerateVoicePack.py [--force] [--allow-english]

Existing clips are skipped unless --force is given. A spell with no Korean name stops the run,
because a pack that announces one spell in English is worse than one that was never built;
--allow-english renders it in English anyway.
"""

import json
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
# MiniAuras is expected beside this repo. Nothing is copied out of it: the spell lists and the
# clip names have one owner, and a stale duplicate here would ship a pack that plays nothing.
MINIAURAS = REPO.parent / "MiniAuras"

if not MINIAURAS.is_dir():
    sys.exit(f"MiniAuras checkout not found at {MINIAURAS}")

sys.path.insert(0, str(MINIAURAS / "scripts"))

import GenerateTtsAudio as base  # noqa: E402

VOICES = {
    "Hyuk": "ZJCNdZEjYwkOElxugmW2",
    "Rosa Oh": "sf8Bpb1IU97NI9BHSMRf",
}
# Korean is not tonal, so the model the Mandarin packs needed for tone accuracy buys nothing
# here and multilingual v2 has the steadier delivery.
MODEL_ID = "eleven_multilingual_v2"

NAMES = pathlib.Path(__file__).resolve().parent / "SpellNamesKoKR.json"
OUT_DIR = REPO / "src" / "Sounds"
# The pack every generated clip name is checked against.
REFERENCE_PACK = MINIAURAS / "src" / "Sounds" / "TTS" / "David"

PREVIEWS = {
    "PreviewImportant": "중요",
    "PreviewDefensive": "방어",
    "PreviewEnemyDebuff": "적 약화",
}
# Spoken when the pack is picked in the dropdown. A real announcement, long enough to judge the
# voice by.
PREVIEW_VOICE_TEXT = "영혼나그네의 은총"

# English spell name -> what the Korean voices say instead of the client's name for it. Most
# entries cut a long name down to the part a player reacts to. The rest correct a name the
# client gets wrong for us, because our spell id is the aura and the aura carries another
# ability's name.
SHORT_NAMES = {
    "Ancient of Lore": "고대정령",
    "Arcane Surge": "쇄도",
    "Aspect of the Turtle": "거북",
    "Avenging Crusader": "응징",
    "Avenging Wrath": "응징",
    "Barkskin": "껍질",
    "Blessing of Freedom": "자유",
    "Blessing of Protection": "보축",
    "Blessing of Sacrifice": "희생",
    "Blessing of Sanctuary": "성역",
    "Blessing of Spellwarding": "주문 수호",
    "Celestial Alignment": "화신",
    "Cloak of Shadows": "망토",
    "Colossus Smash": "강타",
    "Dark Simulacrum": "복제",
    "Divine Protection": "가호",
    "Divine Shield": "무적",
    "Emerald Communion": "교감",
    "Enraged Regeneration": "재생력",
    "Greater Invisibility": "투명화",
    "Grounding Totem": "마법흡수",
    "Guardian of the Forgotten Queen": "잊힌 여왕의 수호자",
    "Ice Block": "얼방",
    "Incarnation: Avatar of Ashamane": "화신",
    "Incarnation: Chosen of Elune": "화신",
    "Incarnation: Guardian of Ursoc": "화신",
    "Invoke Chi-Ji, the Red Crane": "츠지",
    "Invoke Niuzao, the Black Ox": "니우짜오",
    "Invoke Yu'lon, the Jade Serpent": "위론",
    "Life Cocoon": "고치",
    "Nullifying Shroud": "장막",
    "Obsidian Scales": "비늘",
    "Rallying Cry": "함성",
    "Sharpen Blade": "무기 연마",
    "Shield Wall": "방벽",
    "Spell Reflection": "반사",
    "Spirit Link": "정신의 고리",
    "Survival Instincts": "본능",
    "Touch of Karma": "업보",
    "Unending Resolve": "결의",
    "Void Metamorphosis": "탈태",
}


def build_texts(categories, names):
    """File stem -> the Korean text that stem's clip speaks, and the names with no Korean."""
    texts = {}
    untranslated = []

    for ids in categories.values():
        for name in ids.values():
            text = base.spoken_text(name)
            spoken = SHORT_NAMES.get(text) or names.get(text)

            if not spoken:
                untranslated.append(text)

            texts[base.slug(text)] = spoken or text

    texts.update(PREVIEWS)
    texts["PreviewVoice"] = PREVIEW_VOICE_TEXT

    return texts, sorted(set(untranslated))


def check_against_shipped(stems):
    """A pack whose file names drift from MiniAuras' own plays nothing for the clips that
    differ, and says so nowhere, so the mismatch is caught here instead."""
    if not REFERENCE_PACK.is_dir():
        sys.exit(f"reference pack not found at {REFERENCE_PACK}")

    shipped = {path.stem for path in REFERENCE_PACK.glob("*.ogg")}
    missing = sorted(shipped - stems)
    extra = sorted(stems - shipped)

    if missing or extra:
        sys.exit(f"clip names do not match {REFERENCE_PACK.name}: missing {missing}, extra {extra}")


def main():
    api_key = os.environ.get("ELEVENLABS_API_KEY")

    if not api_key:
        sys.exit("set ELEVENLABS_API_KEY")

    force = "--force" in sys.argv

    names = json.loads(NAMES.read_text(encoding="utf-8"))
    texts, untranslated = build_texts(base.parse_categories(), names)

    if untranslated and "--allow-english" not in sys.argv:
        listed = "\n  ".join(untranslated)
        sys.exit(
            f"no Korean name for:\n  {listed}\n"
            "re-run scripts/FetchSpellNamesKoKR.py, or pass --allow-english to speak these in English"
        )

    for name in untranslated:
        print(f"WARNING: no Korean name for '{name}', speaking English")

    check_against_shipped(set(texts))

    rendered, reused = 0, 0

    for pack, voice_id in VOICES.items():
        pack_dir = OUT_DIR / pack
        pack_dir.mkdir(parents=True, exist_ok=True)

        for file_stem in sorted(texts):
            path = pack_dir / f"{file_stem}.ogg"

            if path.exists() and not force:
                reused += 1
                continue

            base.render(api_key, voice_id, texts[file_stem], path, 0.0, MODEL_ID)
            rendered += 1
            print(f"rendered {pack}/{path.name}")

    print(f"{rendered} clip(s) rendered, {reused} reused")


if __name__ == "__main__":
    main()
