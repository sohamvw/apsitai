from langdetect import detect


def detect_lang(text):

    try:
        return detect(text)
    except:
        return "en"