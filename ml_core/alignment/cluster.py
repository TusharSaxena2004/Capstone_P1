"""
Aligns claims across different witnesses that refer to the same underlying entity or event.
Uses sentence-transformers embedding similarity + agglomerative clustering.
"""
import logging
from typing import List
from ml_core.schema.models import Claim

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import AgglomerativeClustering
    # Load lightweight local model automatically
    model = SentenceTransformer('all-MiniLM-L6-v2')
except ImportError:
    logger.warning("Dependencies missing for claim clustering. Install sentence-transformers and scikit-learn.")
    model = None

def align_claims(claims: List[Claim]) -> List[List[Claim]]:
    """
    Clusters extracted claims into aligned groups for contradiction detection.
    Returns a list of claim clusters.
    """
    if not claims:
        return []
        
    if not model or len(claims) == 1:
        # Fallback: each claim is its own cluster
        return [[c] for c in claims]
        
    # 1. Embed the textual action/subject of the claims
    # (Falling back to empty string if missing text)
    texts = [c.event.text if c.event.text else f"{c.event.subject} {c.event.action} {c.event.object}" for c in claims]
    embeddings = model.encode(texts)
    
    # 2. Cluster using Agglomerative Clustering
    # distance <= 0.65 groups related incident movements/actions across witnesses
    clusterer = AgglomerativeClustering(
        n_clusters=None, 
        distance_threshold=0.65, 
        metric='cosine', 
        linkage='average'
    )
    
    labels = clusterer.fit_predict(embeddings)
    
    # 3. Group claims by their cluster label
    clusters_dict = {}
    for label, claim in zip(labels, claims):
        if label not in clusters_dict:
            clusters_dict[label] = []
        clusters_dict[label].append(claim)
        
    return list(clusters_dict.values())
