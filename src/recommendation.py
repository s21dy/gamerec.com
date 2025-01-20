# Data Preporcess
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from scipy.sparse import csr_matrix, hstack, save_npz, load_npz

#Recommendation
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix, hstack
from sklearn.decomposition import TruncatedSVD

GAMES_DB_PATH = os.getenv(
    "GAMES_DB_PATH", 
    "postgresql://game_ztiv_user:0dclW2K3zpb80TNxSuF85nBEi0YpdRxV@dpg-cu6qj3ogph6c73c97n6g-a.oregon-postgres.render.com/game_ztiv"
    )
engine = create_engine(GAMES_DB_PATH)

SIMILARITY_MATRIX_PATH = "../data/processed/similarity_matrix.npz"
os.makedirs(os.path.dirname(SIMILARITY_MATRIX_PATH), exist_ok=True)

# Load Dataset
def load_data():
    query = "SELECT * FROM processed_game ORDER BY id"
    data = pd.read_sql_query(query, con=engine)
    
    # Optimize memory usage
    data = data.dropna(subset=['all_reviews', 'genre', 'recent_reviews', 'popular_tags'])
    data = data.reset_index(drop=True)
    
    data['id'] = data['id'].astype(int)
    data['all_reviews'] = data['all_reviews'].astype(str)
    data['genre'] = data['genre'].astype(str)
    data['recent_reviews'] = data['recent_reviews'].astype(str)
    data['popular_tags'] = data['popular_tags'].astype(str)
    return data

# Text Preprocessing
def preprocess_text(text):
    """Preprocess text data by cleaning and removing unnecessary characters."""
    return ' '.join(text.split()).lower()

def reduce_dimensions(matrix, n_components=200):
    svd = TruncatedSVD(n_components=n_components, n_iter=3, random_state=42)
    reduced_matrix = svd.fit_transform(matrix)
    return csr_matrix(reduced_matrix)

# Compute Similarity Matrix
def compute_similarity_matrix(data, weights=None, top_k=30, n_components=200):
    if weights is None:
        weights = {'all_reviews': 0.3, 'genre': 0.1, 
                   'recent_reviews': 0.4, 'popular_tags': 0.2}

    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),  # Unigrams and bigrams
        max_features=20000,
        max_df=0.9,
        min_df=0.01)
    
    vectors = []
    for column, weight in weights.items():
        tfidf_matrix = vectorizer.fit_transform(data[column].apply(preprocess_text))
        weighted_matrix = tfidf_matrix * weight
        vectors.append(weighted_matrix)

    combined_matrix = hstack(vectors) # Combine all vectors into one matrix

    # Dimensionality Reduction with UMAP
    reduced_matrix = reduce_dimensions(combined_matrix, n_components)
    similarity = cosine_similarity(reduced_matrix, dense_output=False)
    
    # Retain only the top-k similarities for each row
    rows, cols, values = [], [], []
    for row_idx in range(similarity.shape[0]):
        row = similarity.getrow(row_idx).toarray().flatten()
        top_indices = np.argsort(row)[-top_k - 1:-1][::-1]  # Get top-k indices (excluding self)
        rows.extend([row_idx] * len(top_indices))  # Row indices
        cols.extend(top_indices)                  # Column indices
        values.extend(row[top_indices])           
    sparse_matrix = csr_matrix((values, (rows, cols)), shape=(data.shape[0], data.shape[0]))
    return sparse_matrix
    
    
def save_similarity_matrix(matrix):
    """Save the similarity matrix in sparse .npz format."""
    save_npz(SIMILARITY_MATRIX_PATH, matrix)
    print("Similarity matrix saved as similarity_matrix.npz.")

# Load Similarity Matrix
def load_similarity_matrix(data):
    """
    Load the similarity matrix from a .npz file.
    If the file does not exist, compute and save the matrix.
    """
    if not os.path.exists(SIMILARITY_MATRIX_PATH):
        print("Similarity matrix file not found. Computing similarity matrix...")
        # Compute and save the similarity matrix
        matrix = compute_similarity_matrix(data)
        save_similarity_matrix(matrix)
        print("Similarity matrix computed and saved.")
        return matrix

    # Load the matrix from the .npz file
    print("Loading similarity matrix from file...")
    matrix = load_npz(SIMILARITY_MATRIX_PATH)

    # Check if the matrix fits the data row count
    if matrix.shape[0] != len(data):
        print("Mismatch detected between similarity matrix and dataset rows. Recomputing matrix...")
        matrix = compute_similarity_matrix(data)
        save_similarity_matrix(matrix)
        print("Updated similarity matrix saved.")
        return matrix
    
    print("Similarity matrix loaded and validated.")
    return matrix

# Recommendation function
def get_game_rec(selected_game, data, similarity_matrix, top_n=15):
    """
    Recommend games based on the selected game.
    Args:
        selected_game (str): Name of the selected game.
        data (pd.DataFrame): Game data with names and other attributes.
        similarity_matrix (scipy.sparse.csr_matrix): Precomputed similarity matrix.
        top_n (int): Number of recommendations to return. 
    Returns:
        pd.Series: Recommended game names.
    """
    try:
        # Find the index of the selected game
        game_index = data[data['name'] == selected_game].index[0]
        game_similarities = similarity_matrix[game_index].toarray().flatten()        
        similar_games = sorted(enumerate(game_similarities), key=lambda x: x[1], reverse=True)
        recommended_indices = [i[0] for i in similar_games[1:top_n + 1]]
        
        return data.iloc[recommended_indices]   
    
    except IndexError:
        return pd.DataFrame({'Error': [f"'{selected_game}' not found in the dataset."]})
    except Exception as e:
        return pd.DataFrame({'Error': [str(e)]})

p_data = load_data()
similarity_matrix = load_similarity_matrix(p_data)