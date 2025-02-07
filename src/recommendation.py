# Data Preporcess
import os
import pandas as pd
import numpy as np
import faiss

#Recommendation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix, load_npz, save_npz, hstack

class GameRecommender:
    def __init__(self, db_engine, similarity_matrix_path, top_k=15, n_components=200):
        self.db_engine = db_engine
        self.similarity_matrix_path = similarity_matrix_path
        self.top_k = top_k
        self.n_components = n_components
        self.dataset = None
        self.similarity_matrix = None
        self.faiss_index = None

    def load_dataset(self, chunk_size=1000):
        if self.dataset is not None:
            print("Dataset already loaded. Skipping reload.")
            return self.dataset

        query_template = """
        SELECT id, name, 
            all_reviews, 
            genre, 
            popular_tags, 
            recent_reviews
        FROM processed_game
        WHERE all_reviews IS NOT NULL
        AND genre IS NOT NULL
        AND popular_tags IS NOT NULL
        AND recent_reviews IS NOT NULL
        ORDER BY id
        OFFSET {offset} LIMIT {chunk_size};
        """

        def chunk_generator():
            offset = 0
            while True:
                query = query_template.format(offset=offset, chunk_size=chunk_size)
                try:
                    chunk = pd.read_sql_query(query, con=self.db_engine)
                    if chunk.empty:
                        break
                    yield chunk
                    offset += chunk_size
                except Exception as e:
                    print(f"Error loading chunk: {e}")
                    break

        self.dataset = pd.concat(
            (chunk.assign(
                genre=lambda df: df['genre'].astype('category'),
                popular_tags=lambda df: df['popular_tags'].astype('category')
            ) for chunk in chunk_generator()),
            ignore_index=True
        )

        print(f"Dataset loaded. Size: {len(self.dataset)} rows.")
        return self.dataset

    def compute_similarity_matrix(self):
        
        """Compute the similarity matrix using FAISS."""
        if self.dataset is None:
            raise ValueError("Dataset is not loaded. Call `load_dataset()` first.")
        
        # Compute weighted TF-IDF vectors
        weights = {'all_reviews': 0.3, 'genre': 0.1, 'recent_reviews': 0.4, 'popular_tags': 0.2}
        
        vectorizer = TfidfVectorizer(stop_words='english', max_features=20000)
        vectors = []
        # Fit vectorizer once and transform for each column
        for column, weight in weights.items():
            if column == 'genre' or column == 'popular_tags':
                tfidf_matrix = vectorizer.fit_transform(self.dataset[column].astype(str))
            else:
                tfidf_matrix = vectorizer.fit_transform(self.dataset[column].apply(self.preprocess_text))
            vectors.append(tfidf_matrix * weight)
        combined_matrix = hstack(vectors, format='csr')
        
        reduced_matrix = TruncatedSVD(n_components=self.n_components, random_state=42).fit_transform(combined_matrix)
        reduced_matrix = reduced_matrix.astype('float32')
        
        # Normalize vectors for FAISS
        faiss.normalize_L2(reduced_matrix)

        # Build FAISS Index
        index = faiss.IndexFlatIP(self.n_components)
        index.add(reduced_matrix)

        # Query Top-K Neighbors
        distances, indices = index.search(reduced_matrix, self.top_k)
        
        rows, cols, values = [], [], []
        for row_idx, (dist, idx) in enumerate(zip(distances, indices)):
            rows.extend([row_idx] * len(idx))
            cols.extend(idx)
            values.extend(dist)

        self.similarity_matrix = csr_matrix((values, (rows, cols)), shape=(self.dataset.shape[0], self.dataset.shape[0]))
        return self.similarity_matrix

    def is_matrix_consistent(self):
        return self.similarity_matrix is not None and \
            self.similarity_matrix.shape[0] == len(self.dataset)
    
    def load_similarity_matrix(self):
        """Load or compute the similarity matrix."""   
        # Ensure the dataset is loaded
        if self.dataset is None:
            print("Dataset is not loaded. Loading dataset...")
            self.load_dataset(columns=["id", "feature_1", "feature_2"])
            print(f"Dataset loaded. Size: {len(self.dataset)} rows.")

        # Load or compute the similarity matrix
        if os.path.exists(self.similarity_matrix_path):
            print(f"Loading similarity matrix from file: {self.similarity_matrix_path}")
            self.similarity_matrix = load_npz(self.similarity_matrix_path)
        else:
            print("Similarity matrix file not found. Computing new similarity matrix...")
            self.similarity_matrix = self.compute_similarity_matrix()
            self.save_similarity_matrix()

        # Validate consistency
        if not self.is_matrix_consistent():
            print("Matrix is inconsistent. Recomputing...")
            self.similarity_matrix = self.compute_similarity_matrix()
            self.save_similarity_matrix()

        # Initialize FAISS index
        self.initialize_faiss_index()

        return self.similarity_matrix

    def initialize_faiss_index(self):
        print("Initializing FAISS index...")
        self.faiss_index = faiss.IndexFlatIP(self.similarity_matrix.shape[1])
        for row_idx in range(self.similarity_matrix.shape[0]):
    
            sparse_row = self.similarity_matrix.getrow(row_idx)
            dense_row = sparse_row.toarray().astype('float32')
            faiss.normalize_L2(dense_row)
            self.faiss_index.add(dense_row)

    def save_similarity_matrix(self):
        """Save the similarity matrix to a memory-mapped file."""
        save_npz(self.similarity_matrix_path, self.similarity_matrix)
        print(f"Similarity matrix saved to {self.similarity_matrix_path}.")

    def get_recommendations(self, selected_game, top_n=15):
        """Compute similarity dynamically for the selected game."""
        if self.dataset is None:
            self.dataset = self.load_dataset()
        if self.similarity_matrix is None:
            self.load_similarity_matrix()
        # Find the game index
        try:
            game_index = self.dataset[self.dataset['name'] == selected_game].index[0]
        except IndexError:
            return pd.DataFrame({'Error': [f"'{selected_game}' not found in the dataset."]})
        # Query the similarity matrix
        query_vector = self.similarity_matrix[game_index:game_index + 1].toarray().astype('float32')
        query_vector = np.ascontiguousarray(query_vector)
        distances, indices = self.faiss_index.search(query_vector, top_n)

        # Retrieve recommended games
        recommended_indices = indices.flatten()

        # Exclude the selected game itself
        recommended_indices = recommended_indices[recommended_indices != game_index]
        return self.dataset.iloc[recommended_indices]
    

    @staticmethod
    def preprocess_text(text):
        """Preprocess text data."""
        if not isinstance(text, str):
            return ""  # Convert invalid types to empty string
        return ' '.join(text.split()).lower()
    