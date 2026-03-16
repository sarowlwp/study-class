import pytest
from datetime import datetime
from app.services.english_quiz_service import EnglishQuizService
from app.models.english_word import EnglishWord, EnglishQuizMode, ResultType


class TestEnglishQuizService:
    def test_generate_options(self):
        service = EnglishQuizService(None, None)
        correct = EnglishWord(word="cat", meaning="猫", lesson="Unit 1", semester="Grade 3")
        all_words = [
            correct,
            EnglishWord(word="dog", meaning="狗", lesson="Unit 1", semester="Grade 3"),
            EnglishWord(word="pig", meaning="猪", lesson="Unit 1", semester="Grade 3"),
            EnglishWord(word="cow", meaning="牛", lesson="Unit 1", semester="Grade 3"),
        ]

        options = service._generate_options(correct, all_words, 4)

        assert len(options) == 4
        assert any(opt["is_correct"] for opt in options)
        assert sum(1 for opt in options if opt["is_correct"]) == 1

    def test_generate_options_not_enough_words(self):
        service = EnglishQuizService(None, None)
        correct = EnglishWord(word="cat", meaning="猫", lesson="Unit 1", semester="Grade 3")
        all_words = [correct, EnglishWord(word="dog", meaning="狗", lesson="Unit 1", semester="Grade 3")]

        options = service._generate_options(correct, all_words, 4)

        assert len(options) == 2  # Only 2 available
