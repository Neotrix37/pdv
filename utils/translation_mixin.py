from utils.translations import get_text

class TranslationMixin:
    def t(self, key):
        """Traduz uma chave para o idioma atual"""
        return get_text(key, self.page.data.get("language", "pt")) 