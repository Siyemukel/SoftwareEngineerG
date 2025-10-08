import os
import importlib

# Ensure fresh import in the test environment
if 'app.services' in globals():
    importlib.reload(globals()['app.services'])

import app.services as services


def test_get_fallback_question_numbers_easy():
    q = services.get_fallback_question('numbers', 'easy', 1)
    assert isinstance(q, dict)
    assert 'question' in q and 'answer' in q


def test_basic_answer_similarity_true():
    assert services.basic_answer_similarity('the quick test', 'quick test')


def test_basic_answer_similarity_false():
    assert not services.basic_answer_similarity('completely different', 'no overlap here')


def test_get_next_question_without_api_key_returns_fallback():
    # In CI/local env where no API key is set, get_next_question should return fallback
    q = services.get_next_question('numbers', 'easy', 1)
    assert isinstance(q, dict)
    assert 'question' in q


def test_ai_evaluate_answer_short_circuit():
    # With no API key, ai_evaluate_answer should fall back to basic similarity
    assert services.ai_evaluate_answer('C', 'C', 'numbers', 'q') is True
    assert services.ai_evaluate_answer('something', 'another', 'logic', 'q') in (False,)

