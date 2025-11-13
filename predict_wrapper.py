# predict_wrapper.py
"""
Tries to import your actual prediction function from common places,
otherwise uses a small fallback heuristic so the UI works immediately.

Expected return: (label_str, is_positive_bool, display_text_str)
"""

import traceback

# Default fallback predictor
def fallback_predict(text: str):
    txt = (text or "").lower()
    negative_words = ["bad", "sad", "angry", "hate", "terrible", "awful", "worst", "pain"]
    positive_words = ["good", "great", "love", "happy", "awesome", "best", "nice", "fantastic"]
    neg_score = sum(1 for w in negative_words if w in txt)
    pos_score = sum(1 for w in positive_words if w in txt)
    if pos_score >= neg_score:
        label = "Positive"
        is_pos = True
        display = f"Positive sentiment (score {pos_score} vs {neg_score})"
    else:
        label = "Negative"
        is_pos = False
        display = f"Negative sentiment (score {neg_score} vs {pos_score})"
    return label, is_pos, display

# Try several import locations where your real predictor might live
_candidates = [
    ("app", "predict_text"),           # if you exported predict_text from your app.py
    ("model", "predict_text"),         # if you have model.py
    ("predict", "predict_text"),       # another common name
]

wrapper_predict = None

for module_name, func_name in _candidates:
    try:
        module = __import__(module_name, fromlist=[func_name])
        func = getattr(module, func_name)
        if callable(func):
            wrapper_predict = func
            print(f"predict_wrapper: using {func_name} from module '{module_name}'")
            break
    except Exception:
        # skip silently but print debug for developer
        # print(f"predict_wrapper: couldn't import {func_name} from {module_name} -> {traceback.format_exc()}")
        pass

if wrapper_predict is None:
    wrapper_predict = fallback_predict
    print("predict_wrapper: using fallback predictor (heuristic)")

def predict_text(text: str):
    try:
        return wrapper_predict(text)
    except Exception:
        # if the real predictor throws, fallback safely
        return fallback_predict(text)
