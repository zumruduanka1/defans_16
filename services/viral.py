def viral_score(score):
    if score>500: return 1
    if score>100: return 0.7
    if score>20: return 0.4
    return 0.1