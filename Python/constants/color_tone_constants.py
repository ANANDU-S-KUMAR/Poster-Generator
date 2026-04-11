from typing import Final

SENTIMENT_TONE: Final = {
    "pos": {"tone": "fresh, calm, uplifting", "font_color": "amber" },
    "neu": {"tone": "muted, balanced, minimal", "font_color": "beige" },
    "compound": {"tone": "cool, subdued, melancholic", "font_color": "light grey" },
    "neg": {"tone":"dark, stark, intense", "font_color": "maroon" },
}

GENRE_TONE: Final = {
    "drama":   {"tone": "muted, balanced, minimal",        "font_color": "white"},
    "comedy":  {"tone": "warm, playful, lighthearted",   "font_color": "amber"},
    "action":  {"tone": "bold, gritty, high contrast",   "font_color": "dark navy"},
    "romance": {"tone": "soft, dreamy, pastel",           "font_color": "pink"},
    "horror":  {"tone": "light dark, eerie, desaturated",      "font_color": "grey"},
    "sci-fi":  {"tone": "futuristic, cold, calm, uplifting",     "font_color": "white"},
    "thriller":{"tone": "tense, shadowy, high contrast", "font_color": "dark slate"},
    "fantasy": {"tone": "ethereal, magical, vivid",      "font_color": "deep purple"},
}

def get_color_tone(sentiment):
    if sentiment in SENTIMENT_TONE:
        return SENTIMENT_TONE[sentiment]['tone']
    else:
        return GENRE_TONE[sentiment.lower()]['tone']

def get_font_color(sentiment):
    if sentiment in SENTIMENT_TONE:
        return SENTIMENT_TONE[sentiment]['font_color']
    else:
        return GENRE_TONE[sentiment.lower()]['font_color']
    



