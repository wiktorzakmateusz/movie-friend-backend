import pytest
import numpy as np
from ml.models_code.svd import SVD

def test_svd_init():
    """
    Tests default initialization parameters
    """
    model = SVD(n_factors=50, n_epochs=10)
    
    assert model.n_factors == 50
    assert model.n_epochs == 10
    assert model.lr_all == 0.005

def test_svd_fit(dummy_data):
    """
    tests training loop and matrix initialization shapes
    """
    model = SVD(n_factors=10, n_epochs=5)
    model.fit(dummy_data)

    # 3 unique users (0, 1, 2), 3 unique items (0, 1, 2)
    assert model.n_users == 3
    assert model.n_items == 3
    
    # global mean of [5, 4, 3, 2, 5] is 3.8
    assert np.isclose(model.global_mean, 3.8)

def test_svd_estimate_known(dummy_data):
    """
    Tests prediction for a user and item in the training set
    """
    model = SVD(n_factors=10, n_epochs=5)
    model.fit(dummy_data)
    
    est = model.estimate(0, 1)
    
    assert isinstance(est, float)
    # prediction should be somewhat near the 1-5 scale
    assert 0 <= est <= 6 

def test_svd_estimate_unknown_boundaries(dummy_data):
    """
    Tests fallback to global mean for completely unknown users/items
    """
    model = SVD()
    model.fit(dummy_data)
    
    # user 99 and item 99 do not exist in dummy_data
    est = model.estimate(99, 99)
    
    assert est == model.global_mean

def test_svd_cross_validation(dummy_data):
    """
    Tests if cross validation runs and returns valid metrics
    """
    model = SVD(n_factors=5, n_epochs=2)
    
    # n_splits=2 because dummy_data is very small
    rmse, mae = model.cross_validation(dummy_data, n_splits=2)
    
    assert isinstance(rmse, float)
    assert isinstance(mae, float)
    assert rmse >= 0
    assert mae >= 0

def test_svd_save_not_fitted(tmp_path):
    """
    tests save rejection when model is untrained
    """
    model = SVD()
    filepath = str(tmp_path / "untrained_model.npz")
    
    with pytest.raises(AttributeError) as exc_info:
        model.save(filepath)
        
    assert "not initialized" in str(exc_info.value).lower()

def test_svd_save_and_load(dummy_data, tmp_path):
    """
    Tests writing cython model to disk and restoring it accurately
    """
    original_model = SVD(n_factors=10, n_epochs=5)
    original_model.fit(dummy_data)
    
    filepath = str(tmp_path / "test_svd.npz")
    
    # saves to temporary directory
    original_model.save(filepath)
    
    # loads a fresh model instance from disk
    loaded_model = SVD.load(filepath)
    
    # verifies scalar properties
    assert loaded_model.n_factors == original_model.n_factors
    assert loaded_model.n_users == original_model.n_users
    assert loaded_model.global_mean == original_model.global_mean
    
    # verifies arrays restored correctly by ensuring predictions match perfectly
    assert loaded_model.estimate(0, 1) == original_model.estimate(0, 1)
    assert loaded_model.estimate(2, 1) == original_model.estimate(2, 1)