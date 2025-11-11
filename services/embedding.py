import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from config import ST_MODEL

def encode_text(text: str):
    return ST_MODEL.encode(text).tolist()

def compute_similarity(target_emb, pool_embs, pool_ids):
    if not pool_embs:
        return []
    sims = cosine_similarity(np.array(target_emb).reshape(1, -1), np.array(pool_embs)).flatten()
    results = [(pid, s) for pid, s in zip(pool_ids, sims) if s > 0]
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def score_label(score_100: float) -> str:
    if 85 <= score_100 <= 100: return "Excellent Match"
    elif 75 <= score_100 < 85: return "Very Good Match"
    elif 65 <= score_100 < 75: return "Good Match"
    elif 45 <= score_100 < 65: return "Fair Match"
    elif 30 <= score_100 < 45: return "Moderate Match"
    elif 20 <= score_100 < 30: return "Limited Match"
    else: return "Minimal Match"
