import pytest
import numpy as np
from unittest.mock import patch
from ml.models_code.EASE import EASE

def test_ease_fit(dummy_matrix):
    """
    Tests if model trains and computes B matrix correctly
    """
    model = EASE(reg_weight=1.0)
    model.fit(dummy_matrix)

    assert model.B is not None
    assert model.B.shape == (4, 4) 
    assert model.num_items == 4
    
    np.testing.assert_array_equal(np.diag(model.B), np.zeros(4))

def test_predict_new_user_success(dummy_matrix):
    """
    Tests top-k recommendations and masking
    """
    model = EASE(reg_weight=1.0)
    model.fit(dummy_matrix)

    # user interacted with 0 and 2, but ignored 2.
    interacted = [0, 2]
    not_ignored = [0]
    
    recs = model.predict_new_user(interacted, not_ignored, k=2, mask_interacted=True)

    assert len(recs) == 2
    # items 0 and 2 should be masked from recommendations
    assert 0 not in recs
    assert 2 not in recs
    
    # item 1 should be the top recommendation due to co-occurrence with 0
    assert recs[0] == 1

def test_predict_not_fitted():
    """
    Tests exception when predicting without training
    """
    model = EASE()
    
    with pytest.raises(ValueError) as exc_info:
        model.predict_new_user([0], [0], k=2)
        
    assert "not fitted" in str(exc_info.value).lower()

@patch("numpy.savez_compressed")
def test_save_model(mock_savez, dummy_matrix):
    """
    Tests if model triggers numpy save without writing to disk
    """
    model = EASE()
    model.fit(dummy_matrix)
    model.save_model()

    # verifies numpy save was called
    mock_savez.assert_called_once()
    
    # verifies it used the hardcoded path and passed the B matrix
    args, kwargs = mock_savez.call_args
    assert args[0] == '../models/B_ease.npz'
    assert 'B' in kwargs

@patch("numpy.load")
def test_load_model(mock_load):
    """
    Tests loading the B matrix from a mocked disk file
    """
    # mock the dictionary-like object returned by np.load
    mock_npz = {'B': np.array([[0.0, 0.5], [0.5, 0.0]])}
    mock_load.return_value = mock_npz

    model = EASE()
    model.load_model("fake_path.npz")

    mock_load.assert_called_once_with("fake_path.npz")
    assert model.num_items == 2
    assert model.B.shape == (2, 2)

def test_explain_recommendation_success(dummy_matrix):
    """
    Tests correct extraction and sorting of predictor items
    """
    model = EASE(reg_weight=1.0)
    model.fit(dummy_matrix)
    
    items, weights = model.explain_recommendation(
        interacted_item_ids=[0, 2],
        target_item=[1],
        top_n=2
    )
    
    assert len(items) == 2
    # item 0 should be the strongest predictor for item 1
    assert items[0] == 0
    assert weights[0] > weights[1]

def test_explain_recommendation_bounds(dummy_matrix):
    """
    Tests explain bounds when top_n > len(interacted items)
    """
    model = EASE(reg_weight=1.0)
    model.fit(dummy_matrix)
    
    # user watched only 1 item, asking for top 5 predictors
    items, weights = model.explain_recommendation(
        interacted_item_ids=[0],
        target_item=[1],
        top_n=5
    )
    
    # should safely return the 1 available item without index errors
    assert len(items) == 1
    assert items == [0]