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

        # gram matrix G = X^T X
        G = self.X_train.T @ self.X_train
        
        # added regularization to the diagonal
        G += self.reg_weight * sp.identity(G.shape[0], dtype=np.float32)
        
        # converting to dense and inverting
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

    def predict_new_user(self, interacted_item_ids, interacted_item_ids_without_ignored, 
                         negative_feedback_item_ids, negative_weight=0.5, k=20, mask_interacted=True):
        """
        Predicts scores for a single new user and returns the Top-K recommendations
        
        Args:
            interacted_item_ids: list or 1D array of integer item indices (to mask from 
            recommendations)
            interacted_item_ids_without_ignored: list or 1D array of integer item indices 
            (to use for prediction)
            negative_feedback_item_ids: list or 1D array of integer item indices (to include 
            negative feedback)
            negative_weight: float, a negative weight applied to the user vector
            for unwanted items
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
        user_vector[interacted_item_ids_without_ignored] = 1.0
        if len(negative_feedback_item_ids) > 0: # negative feedback
            user_vector[negative_feedback_item_ids] = negative_weight
        
        # scores calculation
        scores = user_vector @ self.B
        scores = np.asarray(scores).flatten()
        
        # ignoring interacted items (and unwanted)
        if mask_interacted:
            mask_indices = np.concatenate([interacted_item_ids, negative_feedback_item_ids]).astype(int)
            scores[mask_indices] = -np.inf
        
        # top-k unsorted indices
        unsorted_top_k_idx = np.argpartition(-scores, k - 1)[:k] # partial sort
        
        # sorting top-k elements
        top_k_idx = unsorted_top_k_idx[np.argsort(-scores[unsorted_top_k_idx])]
        
        return top_k_idx

    def explain_recommendation(self, interacted_item_ids, target_item, top_n=3):
        """
        Explains a recommendation by finding which seen items contributed most
        
        Args:
            interacted_item_ids: list or 1D array of integer item indices
            target_item: int, the recommended item id to be explained
            top_n: int, how many predictors to return
            
        Returns:
            top_predictor_items: the seen items that caused target_item recommendation
            top_predictor_weights: their mathematical contributions
        """
        
        # gets the exact weights from the seen items to the target item
        contributions = np.asarray(self.B[interacted_item_ids, target_item]).flatten()
        
        # sorts the contributions to find the highest ones
        top_indices = np.argsort(contributions)[-top_n:][::-1]
        
        # maps the indices back to the actual item IDs and their weights
        top_predictor_items = [int(interacted_item_ids[idx]) for idx in top_indices]
        top_predictor_weights = [float(contributions[idx]) for idx in top_indices]
        
        return top_predictor_items, top_predictor_weights
