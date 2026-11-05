import dataclasses
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
    def __init__(self, root: str, path: str, db: DB, has_key=True, default_key=None):
        if not default_key:
            default_key = 'name'
        self.default_key = default_key
        self.root = root
        self.path = pathlib.Path('api', 'v2', path)
        self.db = db
        self.index = None
        if has_key:
            self.index = self.load_index()

    def load_index(self) -> Dict[str, int]:
        with open(self.root / self.path / 'index.json', 'r') as f:
            index = json.load(f)
        out = {}
        for entry in index['results']:
            url = pathlib.Path(entry['url']).parts
            out[entry[self.default_key]] = int(url[-1])
        return out

    def find_by_key(self, value: Any) -> Dict[Any, Any]:
        if not self.index:
            raise Exception("No key for this table")
        if value not in self.index:
            raise Exception(f"Failed to find {self.default_key}={value}")
        return self.find_by_idx(self.index[value])

    def find_by_idx(self, idx: int):
        with open(self.root / self.path / str(idx) / 'index.json', 'r') as f:
            return DBRow(json.load(f), self)

class DB:
    TABLES = [
        'pokemon-species',
        'pokemon',
        'move', 
        'language',
        'type',
        'move-learn-method',
        ('evolution-chain', {'has_key': False}),
        'evolution-trigger',
        'item',
        'location',
    ]

    def __init__(self, db_path):
        self.tables = {}
        for t_info in self.TABLES:
            if isinstance(t_info, tuple):
                table_name, init_args = t_info
            else:
                table_name = t_info
                init_args = {}
            self.tables[table_name] = DBTable(db_path, table_name, self, **init_args)

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


PokeDB = DB(DB_PATH)
