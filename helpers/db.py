import pathlib
import json


DB_PATH = pathlib.Path(__name__).parent.parent / 'api-data' / 'data'

class DBRow:
    def __init__(self, data, table):
        self.data = data
        self.table = table

    def _fundamental_type(self, value):
        return isinstance(value, int) or isinstance(value, str) or value is None

    def reflow_text(self, text):
        return text.replace('\n', ' ').replace('\u000c', ' ')

    def __getattr__(self, key):
        if key not in self.data:
            raise Exception(f"Unknown key {key}")
        if self._fundamental_type(self.data[key]):
            if isinstance(self.data[key], str):
                return self.reflow_text(self.data[key])
            return self.data[key]
        if isinstance(self.data[key], dict) and 'url' in self.data[key]:
            # this is a lookup in another table
            table, idx = self.table.db.get_table_and_idx_from_url(self.data[key]['url'])
            assert idx is not None
            return table.find_by_idx(idx)
        return DBRow(self.data[key], self.table)

    def __getitem__(self, idx):
        if not isinstance(self.data, list):
            raise Exception(f"Not a list")
        if self._fundamental_type(self.data[idx]):
            return self.data[idx]
        return DBRow(self.data[idx], self.table)

class DBTable:
    def __init__(self, root: str, path: str, db: DB, default_key=None):
        if not default_key:
            default_key = 'name'
        self.default_key = default_key
        self.root = root
        self.path = pathlib.Path('api', 'v2', path)
        self.db = db

    def find_by_key(self, value: Any, key: str|None = None) -> Dict[Any, Any]:
        if not key:
            key = self.default_key

        with open(self.root / self.path / 'index.json', 'r') as f:
            index = json.load(f)
        for entry in index["results"]:
            if entry[key] == value:
                table, idx = self.db.get_table_and_idx_from_url(entry['url'])
                return table.find_by_idx(idx)
        raise Exception(f"Failed to find {key}={value}")

    def find_by_idx(self, idx: int):
        with open(self.root / self.path / str(idx) / 'index.json', 'r') as f:
            return DBRow(json.load(f), self)


class DB:
    def __init__(self, db_path, table_names):
        self.tables = {table_name: DBTable(db_path, table_name, self) for table_name in table_names}

    def get_table_and_idx_from_url(self, url):
        url = pathlib.Path(url).parts
        try:
            idx = int(url[-1])
            return (self.tables[url[-2]], idx)
        except ValueError:
            return (self.tables[url[-1]], None)

    def __getattr__(self, name):
        return self.tables[name]


def filter_by_language(text_list: List[Any], language='en') -> List[Any]:
    return [entry for entry in text_list if entry.language.name == language]



PokeDB = DB(DB_PATH, ['pokemon-species', 'pokemon', 'move', 'language', 'type', 'move-learn-method'])
