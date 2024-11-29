class Forms:
    @staticmethod
    def t(lang: str, form: str, message: str):
        return {"{}_{}".format(form, lang): message}
