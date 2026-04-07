import json
from pathlib import Path
from datetime import datetime, date

DB_DIR = Path("./app/database")
DB_DIR.mkdir(exist_ok=True)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        # Enum objects converted to .value automatically
        if hasattr(obj, "value"):
            return obj.value
        return super().default(obj)


def read_json(file_name: str) -> dict[int, dict]:
    file_path = DB_DIR / f"{file_name}.json"
    if not file_path.exists():
        return {}
    with open(file_path, "r") as file:
        data = json.load(file)
        return {int(k): v for k, v in data.items()}


def write_json(file_name: str, data: dict[int, dict]) -> None:
    file_path = DB_DIR / f"{file_name}.json"
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4, cls=JSONEncoder)


def next_id(data: dict[int, dict]) -> int:
    return max(data.keys()) + 1 if data else 1


# CRUD OPERATIONS
def create_record(file_name: str, record: dict) -> dict:
    data = read_json(file_name)
    record["id"] = next_id(data)
    data[record["id"]] = record
    write_json(file_name, data)
    return record


def read_record(file_name: str, record_id: int) -> dict | None:
    return read_json(file_name).get(record_id)


def read_all_records(file_name: str) -> list[dict]:
    return list(read_json(file_name).values())


def update_record(file_name: str, record_id: int, updates: dict) -> bool:
    data = read_json(file_name)
    if record_id not in data:
        return False
    data[record_id].update(updates)
    write_json(file_name, data)
    return True


def delete_record(file_name: str, record_id: int) -> bool:
    data = read_json(file_name)
    if record_id not in data:
        return False
    del data[record_id]
    write_json(file_name, data)
    return True


# QUERY FUNCTIONS
def find(file_name: str, **filters) -> list[dict]:
    results = []
    for record in read_all_records(file_name):
        match = True
        for k, v in filters.items():
            # Normalize comparison for enums and dates
            rec_val = record.get(k)
            if hasattr(v, "value"):  # Enum
                v = v.value
            if isinstance(rec_val, str) and isinstance(v, date):
                rec_val = date.fromisoformat(rec_val)
            if rec_val != v:
                match = False
                break
        if match:
            results.append(record)
    return results


def find_one(file_name: str, **filters) -> dict | None:
    results = find(file_name, **filters)
    return results[0] if results else None
