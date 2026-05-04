memory={}
def anomaly_score(text):
    k=text[:30]
    memory[k]=memory.get(k,0)+1
    return min(memory[k]/5,1)