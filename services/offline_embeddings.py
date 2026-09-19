"""Deterministic test-only vectors; never passed off as a live semantic model."""
import hashlib
import re

class OfflineFixtureEmbedding:
    def embed_documents(self,texts,*,batch_size=32):
        vectors=[]
        for text in texts:
            vector=[0.0]*256
            for token in re.findall(r'\w+',text.casefold()):
                vector[int.from_bytes(hashlib.sha256(token.encode()).digest()[:2],'big')%256]+=1
            vectors.append(vector)
        return vectors
