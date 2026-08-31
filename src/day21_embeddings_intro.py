"""
Day 21 -- ContextGuard project
--------------------------------
Goal: get a real, hands-on feel for what an embedding actually captures,
by embedding a handful of sentences and comparing their similarity --
BEFORE we use this on real code next.

Install first (only needs to be done once):
    pip install sentence-transformers

The first time you run this script specifically, it will also download
a small pretrained model (a few hundred MB) -- this needs an internet
connection and may take a minute or two, but only happens once; it's
cached locally after that.
"""

from sentence_transformers import SentenceTransformer, util

# "all-MiniLM-L6-v2" is a small, fast, well-known sentence-embedding
# model -- a good default choice for exactly this kind of beginner
# project: accurate enough, and light enough to run on a normal laptop
# with no special hardware.
model = SentenceTransformer("all-MiniLM-L6-v2")

# Five sentences, deliberately chosen so you can SEE what embeddings
# capture: sentences 0 and 1 mean something similar despite sharing
# almost no words; same for sentences 2 and 3. Sentence 4 is unrelated
# to everything else.
sentences = [
    "The cat sat on the mat.",                # 0
    "A feline rested on the rug.",             # 1 -- similar MEANING to 0, different words
    "I love programming in Python.",           # 2
    "Coding in Python is my passion.",         # 3 -- similar MEANING to 2, different words
    "The stock market crashed today.",         # 4 -- unrelated to everything else
]

# model.encode() turns each sentence into a list of numbers (a vector).
# Passing a LIST of sentences encodes all of them at once, more
# efficiently than one at a time.
embeddings = model.encode(sentences)

# util.cos_sim compares every embedding against every other one, and
# gives back a grid (matrix) of similarity scores.
similarity_matrix = util.cos_sim(embeddings, embeddings)

print("Similarity scores (1.0 = identical meaning, 0.0 = unrelated):\n")

for i in range(len(sentences)):
    for j in range(len(sentences)):
        if i < j:  # only print each pair once, not twice, and skip comparing a sentence to itself
            score = similarity_matrix[i][j].item()  # .item() turns a 1-element tensor into a plain Python number
            print(f"  [{i}] vs [{j}]: {score:.3f}")
            print(f"      \"{sentences[i]}\"")
            print(f"      \"{sentences[j]}\"\n")
