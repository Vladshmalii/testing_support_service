class ModelPrefixMixin:
    PREFIX = ""

    @property
    def display_id(self) -> str:
        return f"{self.PREFIX}{self.id:06d}"

    @classmethod
    def parse_display_id(cls, display_id: str) -> int:
        if display_id.startswith(cls.PREFIX):
            return int(display_id[len(cls.PREFIX):])
        raise ValueError(f"Invalid display_id format for {cls.__name__}")