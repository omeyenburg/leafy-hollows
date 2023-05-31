class File:
    @staticmethod
    def read(path):
        with open(path, "r") as f:
            lines = f.readlines()
        return lines
    
    @staticmethod
    def path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
