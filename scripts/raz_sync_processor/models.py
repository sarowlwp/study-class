"""数据模型定义."""


class PageText:
    """单页文本."""
    def __init__(self, page_num: int, text: str):
        self.page_num = page_num
        self.text = text


class WordTiming:
    """单词时间戳."""
    def __init__(self, word: str, start: float, end: float):
        self.word = word
        self.start = start
        self.end = end
