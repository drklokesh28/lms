import ast

class ListParser:
    @staticmethod
    def parse_integer_list(value):
        if isinstance(value,list):
            return [int(x) for x in value]
        value=str(value).strip()
        if not value:
            return []
        try:
            result=ast.literal_eval(value)
            if isinstance(result,list):
                return [int(x) for x in result]
        except:
            pass
        return [int(x.strip()) for x in value.strip("[]").split(",") if x.strip()]

    @staticmethod
    def parse_string_list(value):
        if isinstance(value,list):
            return [str(x).strip() for x in value if str(x).strip()]
        value=str(value).strip()
        if not value:
            return []
        try:
            result=ast.literal_eval(value)
            if isinstance(result,list):
                return [str(x).strip() for x in result if str(x).strip()]
        except:
            pass
        return [x.strip().strip("'\"") for x in value.strip("[]").split(",") if x.strip()]

    @staticmethod
    def parse_paths(value):
        if isinstance(value,list):
            return [str(x).strip() for x in value if str(x).strip()]
        return [x.strip() for x in str(value).split(",") if x.strip()]

    @classmethod
    def validate_pair_lengths(cls,faculty_ids,sections):
        faculty_ids=cls.parse_integer_list(faculty_ids)
        sections=cls.parse_string_list(sections)
        return len(faculty_ids)==len(sections)