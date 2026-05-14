import numpy as np
import scipy.sparse as sp

class EASE:
    def __init__(self, reg_weight=250.0):
        """
        Args:
            reg_weight: The L2 regularization factor (lambda)
        """
        self.reg_weight = reg_weight
        self.B = None
        self.X_train = None

    def fit(self, X_train_csr):
        """
        Trains the model
        Args:
            X_train_csr: scipy.sparse.csr_matrix of shape (num_users, num_items)
        """
        self.X_train = X_train_csr.astype(np.float32)
        self.num_items = X_train_csr.shape[1]

        # Gram matrix G = X^T X
        G = self.X_train.T @ self.X_train
        
        # Added regularization to the diagonal
        G += self.reg_weight * sp.identity(G.shape[0], dtype=np.float32)
        
        # Converting to dense and inverting
        G_dense = G.todense()
        P = np.linalg.inv(G_dense)
        
        # weight matrix B
        self.B = P / (-np.diag(P))
        np.fill_diagonal(self.B, 0.0)
    
    def save_model(self):
        """
        Saves the B matrix to a compressed .npz file in ../models/B_ease.npz
        
        """
        np.savez_compressed('../models/B_ease.npz', B=self.B)

    def load_model(self, path):
        """
        Loads the model from a compressed .npz file
        
        Args:
            path: str, source path
        """
        self.B = np.load(path)['B']
        self.num_items = self.B.shape[1]

    def predict_new_user(self, interacted_item_ids, k=20, mask_interacted=True):
        """
        Predicts scores for a single new user and returns the Top-K recommendations
        
        Args:
            interacted_item_ids: list or 1D array of integer item indices
            k: int, the number of top recommendations to return
            mask_interacted: bool, if True, skips already interacted items
            
        Returns:
            top_k_item_ids: array of top-K recommendations
        """

        # callback if not fitted
        if self.B is None:
            raise ValueError("Model is not fitted yet. Call 'fit' first.")
            
        # user vector
        user_vector = np.zeros(self.num_items, dtype=np.float32)
        user_vector[interacted_item_ids] = 1.0
        
        # scores calculation
        scores = user_vector @ self.B
        scores = np.asarray(scores).flatten()
        
        # ignoring interacted items
        if mask_interacted:
            scores[interacted_item_ids] = -np.inf
        
        # top-k unsorted indices
        unsorted_top_k_idx = np.argpartition(-scores, k - 1)[:k] # partial sort
        
        # sorting top-k elements
        top_k_idx = unsorted_top_k_idx[np.argsort(-scores[unsorted_top_k_idx])]
        
        return top_k_idx