from __future__ import annotations

import pytest

from app.engine.pe_fit.weight_schema import validate_weights


@pytest.mark.engine
class TestValidateWeights:
    """Tests for validate_weights — pure function, no DB, no mocks."""

    # ------------------------------------------------------------------ #
    # Cas nominaux                                                         #
    # ------------------------------------------------------------------ #

    def test_valid_two_weights_no_exception(self):
        validate_weights({"gca": 0.6, "conscientiousness": 0.4})

    def test_valid_single_weight_1_0(self):
        """Borne supérieure incluse."""
        validate_weights({"gca": 1.0})

    def test_valid_very_small_weight(self):
        """Très petit mais > 0."""
        validate_weights({"gca": 0.0001})

    def test_valid_multiple_traits(self):
        validate_weights({"gca": 0.3, "openness": 0.3, "agreeableness": 0.4})

    # ------------------------------------------------------------------ #
    # Dict vide                                                            #
    # ------------------------------------------------------------------ #

    def test_empty_dict_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_weights({})

    def test_empty_dict_with_context_raises(self):
        with pytest.raises(ValueError, match="pj_fit weights"):
            validate_weights({}, context="pj_fit weights")

    # ------------------------------------------------------------------ #
    # Poids négatif                                                        #
    # ------------------------------------------------------------------ #

    def test_negative_weight_raises(self):
        with pytest.raises(ValueError) as exc_info:
            validate_weights({"gca": -0.1})
        assert "gca" in str(exc_info.value)

    def test_negative_weight_message_contains_trait(self):
        with pytest.raises(ValueError) as exc_info:
            validate_weights({"conscientiousness": -0.5})
        assert "conscientiousness" in str(exc_info.value)

    # ------------------------------------------------------------------ #
    # Poids nul                                                            #
    # ------------------------------------------------------------------ #

    def test_zero_weight_raises(self):
        with pytest.raises(ValueError) as exc_info:
            validate_weights({"gca": 0.0})
        assert "gca" in str(exc_info.value)

    def test_zero_weight_message_contains_trait(self):
        with pytest.raises(ValueError) as exc_info:
            validate_weights({"openness": 0.0})
        assert "openness" in str(exc_info.value)

    # ------------------------------------------------------------------ #
    # Poids > 1.0                                                         #
    # ------------------------------------------------------------------ #

    def test_weight_above_1_raises(self):
        with pytest.raises(ValueError) as exc_info:
            validate_weights({"gca": 1.1})
        assert "gca" in str(exc_info.value)

    def test_weight_above_1_message_contains_value(self):
        with pytest.raises(ValueError) as exc_info:
            validate_weights({"agreeableness": 2.0})
        assert "agreeableness" in str(exc_info.value)

    # ------------------------------------------------------------------ #
    # Paramètre context                                                    #
    # ------------------------------------------------------------------ #

    def test_context_included_in_error_message_negative_weight(self):
        with pytest.raises(ValueError) as exc_info:
            validate_weights({"gca": -0.1}, context="pj_fit weights")
        message = str(exc_info.value)
        assert "pj_fit weights" in message
        assert "gca" in message

    def test_context_included_in_error_message_above_1(self):
        with pytest.raises(ValueError) as exc_info:
            validate_weights({"gca": 1.5}, context="po_fit weights")
        message = str(exc_info.value)
        assert "po_fit weights" in message
        assert "gca" in message

    def test_context_included_in_error_message_zero(self):
        with pytest.raises(ValueError) as exc_info:
            validate_weights({"openness": 0.0}, context="ps_fit weights")
        message = str(exc_info.value)
        assert "ps_fit weights" in message
        assert "openness" in message

    def test_no_context_no_prefix_in_message(self):
        """Sans context, le message ne doit pas contenir de crochets vides."""
        with pytest.raises(ValueError) as exc_info:
            validate_weights({"gca": -0.1})
        assert "[]" not in str(exc_info.value)

    # ------------------------------------------------------------------ #
    # Cas mixtes dans le dict                                              #
    # ------------------------------------------------------------------ #

    def test_first_valid_second_invalid_raises_on_invalid(self):
        """Un seul trait invalide dans un dict mixte doit lever."""
        with pytest.raises(ValueError) as exc_info:
            validate_weights({"gca": 0.5, "bad_trait": -0.2})
        assert "bad_trait" in str(exc_info.value)

    def test_first_invalid_raises_immediately(self):
        with pytest.raises(ValueError) as exc_info:
            validate_weights({"bad_trait": 0.0, "good_trait": 0.5})
        assert "bad_trait" in str(exc_info.value)
