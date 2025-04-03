from kiwipiepy import Kiwi
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from konlpy.tag import Mecab
from collections import defaultdict, Counter

# 1. 문장 분리 (kiwi 사용)
text = (
    "배송은 느렸지만 제품 품질은 정말 좋았습니다. 가격도 괜찮은 편이고, "
    "포장도 만족스러웠어요. 다만 고객 응대는 조금 아쉬웠어요."
)
kiwi = Kiwi()  # Kiwi 객체 생성 (기본 설정으로 충분)
# kiwi.split_into_sents()는 Sentence 객체들의 리스트를 반환하므로, text 속성을 추출
sentences = [sent.text for sent in kiwi.split_into_sents(text)]

# 2. KoBERT 기반 임베딩 (SentenceTransformer 사용)
model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS")
embeddings = model.encode(sentences)

# 3. 클러스터링 (KMeans, 여기서는 3개 주제로 설정)
n_clusters = 3
kmeans = KMeans(n_clusters=n_clusters, random_state=42)
labels = kmeans.fit_predict(embeddings)

# 4. 클러스터별 주요 키워드 추출 (Mecab 사용)
mecab = Mecab()
clusters = defaultdict(list)
for sentence, label in zip(sentences, labels):
    clusters[label].append(sentence)

# 각 클러스터에서 Mecab을 사용해 명사를 추출하고 빈도수로 대표 키워드를 선정
for label, group in clusters.items():
    nouns = []
    for sentence in group:
        nouns.extend(mecab.nouns(sentence))
    keyword_counts = Counter(nouns).most_common(3)
    keywords = ", ".join([kw for kw, _ in keyword_counts])
    
    print(f"\n[클러스터 {label} - 대표 키워드: {keywords}]")
    for sent in group:
        print(" -", sent)
