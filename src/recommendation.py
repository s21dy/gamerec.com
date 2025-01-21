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
    def __init__(self, db_engine, similarity_matrix_path, top_k=30, n_components=200):
        self.db_engine = db_engine
        self.similarity_matrix_path = similarity_matrix_path
        self.top_k = top_k
        self.n_components = n_components
        self.dataset = None
        self.similarity_matrix = None

    def load_dataset(self, chunk_size=1000):
        if self.dataset is not None:
            print("Dataset already loaded. Skipping reload.")
            return self.dataset

        # Count rows for batching
        count_query = "SELECT COUNT(*) FROM processed_game WHERE all_reviews IS NOT NULL AND genre IS NOT NULL AND popular_tags IS NOT NULL AND recent_reviews IS NOT NULL"
        total_rows = pd.read_sql_query(count_query, con=self.db_engine).iloc[0, 0]

        # Fetch in chunks
        dataset_chunks = []
        for offset in range(0, total_rows, chunk_size):
            query = f"""
            SELECT id, name, all_reviews, genre, popular_tags, recent_reviews
            FROM processed_game
            WHERE all_reviews IS NOT NULL
            AND genre IS NOT NULL
            AND popular_tags IS NOT NULL
            AND recent_reviews IS NOT NULL
            ORDER BY id
            OFFSET {offset} LIMIT {chunk_size};
            """
            chunk = pd.read_sql_query(query, con=self.db_engine)
            dataset_chunks.append(chunk)

        # Combine chunks
        self.dataset = pd.concat(dataset_chunks, ignore_index=True)

        # Optimize types
        self.dataset['genre'] = self.dataset['genre'].astype('category')
        self.dataset['popular_tags'] = self.dataset['popular_tags'].astype('category')
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
        for column, weight in weights.items():
            tfidf_matrix = vectorizer.fit_transform(self.dataset[column].apply(self.preprocess_text))
            weighted_matrix = tfidf_matrix * weight
            vectors.append(weighted_matrix)
        combined_matrix = hstack(vectors).toarray()

        # Dimensionality Reduction
        reduced_matrix = TruncatedSVD(n_components=self.n_components, random_state=42).fit_transform(combined_matrix)
        reduced_matrix = reduced_matrix.astype('float32')
        
        # FAISS Index for Similarity Search
        index = faiss.IndexFlatIP(self.n_components)
        print(f"reduced_matrix dtype: {reduced_matrix.dtype}, shape: {reduced_matrix.shape}")

        faiss.normalize_L2(reduced_matrix)
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

    def load_similarity_matrix(self):
        """Load or compute the similarity matrix."""
        if self.similarity_matrix is not None:
            print("Similarity matrix already loaded. Skipping reload.")
            return self.similarity_matrix

        # Ensure the dataset is loaded
        if self.dataset is None:
            print("Dataset is not loaded. Loading dataset...")
            self.load_dataset()
            print(f"Dataset loaded. Size: {len(self.dataset)} rows.")

        # Check if the file exists
        if os.path.exists(self.similarity_matrix_path):
            print(f"Loading similarity matrix from file: {self.similarity_matrix_path}")
            self.similarity_matrix = load_npz(self.similarity_matrix_path)
             # Initialize the FAISS index from the similarity matrix
            feature_matrix = self.similarity_matrix.toarray().astype('float32')  # Convert sparse matrix to dense
            faiss.normalize_L2(feature_matrix)
            self.faiss_index = faiss.IndexFlatIP(feature_matrix.shape[1])
            self.faiss_index.add(feature_matrix)
        else:
            print("Similarity matrix file not found. Computing new similarity matrix...")
            self.similarity_matrix = self.compute_similarity_matrix()
            self.save_similarity_matrix()

        # Verify consistency
        if self.similarity_matrix.shape[0] != len(self.dataset):
            print("Matrix row count does not match dataset row count. Recomputing matrix...")
            self.similarity_matrix = self.compute_similarity_matrix()
            self.save_similarity_matrix()
        else:
            print("Matrix loaded successfully and is consistent with dataset.")

        return self.similarity_matrix

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
    