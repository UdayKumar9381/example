import re
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any, TypeVar, Generic
from pathlib import Path
import mimetypes
from enum import Enum

from pydantic import BaseModel


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int
    has_next: bool
    has_prev: bool


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class ProjectType(str, Enum):
    TEAM_MANAGED = "TEAM_MANAGED"
    COMPANY_MANAGED = "COMPANY_MANAGED"


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"
    VIEWER = "VIEWER"


class ActivityAction(str, Enum):
    TASK_CREATED = "TASK_CREATED"
    TASK_UPDATED = "TASK_UPDATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    ASSIGNEE_CHANGED = "ASSIGNEE_CHANGED"
    COMMENT_ADDED = "COMMENT_ADDED"
    ATTACHMENT_ADDED = "ATTACHMENT_ADDED"
    SUBTASK_ADDED = "SUBTASK_ADDED"


def generate_project_key(project_name: str, max_length: int = 5) -> str:
    cleaned_name = re.sub(r"[^a-zA-Z0-9]", "", project_name.upper())
    
    if len(cleaned_name) <= max_length:
        return cleaned_name
    
    vowels = "AEIOU"
    consonants = [c for c in cleaned_name if c not in vowels]
    
    if len(consonants) >= max_length:
        return "".join(consonants[:max_length])
    
    return cleaned_name[:max_length]


def generate_task_key(project_key: str, task_number: int) -> str:
    return f"{project_key}-{task_number}"


def parse_task_key(task_key: str) -> tuple[str, int]:
    parts = task_key.rsplit("-", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid task key format: {task_key}")
    
    project_key = parts[0]
    try:
        task_number = int(parts[1])
    except ValueError:
        raise ValueError(f"Invalid task number in key: {task_key}")
    
    return project_key, task_number


def generate_magic_link_token() -> str:
    return secrets.token_urlsafe(32)


def generate_uuid() -> str:
    return str(uuid.uuid4())


def generate_short_uuid() -> str:
    return uuid.uuid4().hex[:12]


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def get_utc_now() -> datetime:
    return datetime.utcnow()


def get_timestamp() -> int:
    return int(datetime.utcnow().timestamp())


def add_minutes(dt: datetime, minutes: int) -> datetime:
    return dt + timedelta(minutes=minutes)


def add_days(dt: datetime, days: int) -> datetime:
    return dt + timedelta(days=days)


def is_expired(expiry_time: datetime) -> bool:
    return datetime.utcnow() > expiry_time


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return dt.strftime(fmt)


def parse_datetime(dt_string: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    return datetime.strptime(dt_string, fmt)


def get_date_range(start_date: date, end_date: date) -> List[date]:
    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]


def get_week_boundaries(dt: datetime) -> tuple[datetime, datetime]:
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)
    return (
        start.replace(hour=0, minute=0, second=0, microsecond=0),
        end.replace(hour=23, minute=59, second=59, microsecond=999999)
    )


def get_month_boundaries(dt: datetime) -> tuple[datetime, datetime]:
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if dt.month == 12:
        end = dt.replace(year=dt.year + 1, month=1, day=1) - timedelta(seconds=1)
    else:
        end = dt.replace(month=dt.month + 1, day=1) - timedelta(seconds=1)
    return start, end


def validate_project_key(key: str) -> bool:
    pattern = r"^[A-Z][A-Z0-9]{1,9}$"
    return bool(re.match(pattern, key))


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    name = re.sub(r"[^\w\s.-]", "", filename)
    name = re.sub(r"\s+", "_", name)
    return name[:255]


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def get_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def generate_unique_filename(original_filename: str) -> str:
    extension = get_file_extension(original_filename)
    unique_id = generate_short_uuid()
    timestamp = get_timestamp()
    return f"{timestamp}_{unique_id}{extension}"


def bytes_to_human_readable(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def paginate(
    items: List[T],
    page: int,
    limit: int
) -> PaginatedResponse[T]:
    total = len(items)
    pages = (total + limit - 1) // limit
    start = (page - 1) * limit
    end = start + limit
    
    return PaginatedResponse(
        items=items[start:end],
        total=total,
        page=page,
        limit=limit,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )


def calculate_pagination_offset(page: int, limit: int) -> int:
    return (page - 1) * limit


def normalize_search_query(query: str) -> str:
    normalized = query.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


def build_search_pattern(query: str) -> str:
    return f"%{query}%"


def extract_mentions(text: str) -> List[str]:
    pattern = r"@(\w+)"
    return re.findall(pattern, text)


def extract_task_references(text: str) -> List[str]:
    pattern = r"([A-Z]+-\d+)"
    return re.findall(pattern, text)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def snake_to_camel(snake_str: str) -> str:
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def camel_to_snake(camel_str: str) -> str:
    pattern = re.compile(r"(?<!^)(?=[A-Z])")
    return pattern.sub("_", camel_str).lower()


def dict_to_camel_case(data: Dict[str, Any]) -> Dict[str, Any]:
    return {snake_to_camel(k): v for k, v in data.items()}


def filter_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def get_changes(
    old_data: Dict[str, Any],
    new_data: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    changes = {}
    all_keys = set(old_data.keys()) | set(new_data.keys())
    
    for key in all_keys:
        old_value = old_data.get(key)
        new_value = new_data.get(key)
        
        if old_value != new_value:
            changes[key] = {
                "old": old_value,
                "new": new_value
            }
    
    return changes


def flatten_dict(
    data: Dict[str, Any],
    parent_key: str = "",
    separator: str = "."
) -> Dict[str, Any]:
    items = []
    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        else:
            items.append((new_key, value))
    return dict(items)


def get_client_ip(request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def mask_email(email: str) -> str:
    local, domain = email.rsplit("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*" * (len(local) - 1)
    else:
        masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
    return f"{masked_local}@{domain}"


def generate_color_from_string(text: str) -> str:
    hash_value = hashlib.md5(text.encode()).hexdigest()
    return f"#{hash_value[:6]}"


def calculate_story_points_sum(tasks: List[Dict[str, Any]]) -> int:
    return sum(
        task.get("story_points", 0) or 0
        for task in tasks
    )


def group_tasks_by_status(
    tasks: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    grouped = {status.value: [] for status in TaskStatus}
    
    for task in tasks:
        status = task.get("status", TaskStatus.TODO.value)
        if status in grouped:
            grouped[status].append(task)
    
    return grouped


def calculate_completion_percentage(
    total_tasks: int,
    completed_tasks: int
) -> float:
    if total_tasks == 0:
        return 0.0
    return round((completed_tasks / total_tasks) * 100, 2)


def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    return [
        items[i:i + chunk_size]
        for i in range(0, len(items), chunk_size)
    ]


def deduplicate_list(items: List[T]) -> List[T]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    result = {}
    for d in dicts:
        result.update(d)
    return result


def get_nested_value(
    data: Dict[str, Any],
    keys: List[str],
    default: Any = None
) -> Any:
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data


def set_nested_value(
    data: Dict[str, Any],
    keys: List[str],
    value: Any
) -> None:
    for key in keys[:-1]:
        data = data.setdefault(key, {})
    data[keys[-1]] = value


KANBAN_COLUMNS = [
    {"id": "todo", "name": "To Do", "status": TaskStatus.TODO.value, "order": 1},
    {"id": "in_progress", "name": "In Progress", "status": TaskStatus.IN_PROGRESS.value, "order": 2},
    {"id": "done", "name": "Done", "status": TaskStatus.DONE.value, "order": 3},
]


def get_kanban_board_structure() -> List[Dict[str, Any]]:
    return KANBAN_COLUMNS.copy()


def get_status_transition_rules() -> Dict[str, List[str]]:
    return {
        TaskStatus.TODO.value: [TaskStatus.IN_PROGRESS.value],
        TaskStatus.IN_PROGRESS.value: [TaskStatus.TODO.value, TaskStatus.DONE.value],
        TaskStatus.DONE.value: [TaskStatus.IN_PROGRESS.value, TaskStatus.ARCHIVED.value],
        TaskStatus.ARCHIVED.value: [TaskStatus.TODO.value],
    }


def is_valid_status_transition(
    current_status: str,
    new_status: str
) -> bool:
    rules = get_status_transition_rules()
    allowed_transitions = rules.get(current_status, [])
    return new_status in allowed_transitions


def format_activity_message(
    action: str,
    user_name: str,
    task_key: str,
    details: Optional[Dict[str, Any]] = None
) -> str:
    messages = {
        ActivityAction.TASK_CREATED.value: f"{user_name} created task {task_key}",
        ActivityAction.TASK_UPDATED.value: f"{user_name} updated task {task_key}",
        ActivityAction.STATUS_CHANGED.value: f"{user_name} changed status of {task_key}",
        ActivityAction.ASSIGNEE_CHANGED.value: f"{user_name} changed assignee of {task_key}",
        ActivityAction.COMMENT_ADDED.value: f"{user_name} commented on {task_key}",
        ActivityAction.ATTACHMENT_ADDED.value: f"{user_name} added attachment to {task_key}",
        ActivityAction.SUBTASK_ADDED.value: f"{user_name} added subtask to {task_key}",
    }
    
    base_message = messages.get(action, f"{user_name} performed action on {task_key}")
    
    if details:
        if action == ActivityAction.STATUS_CHANGED.value:
            old_status = details.get("old_status", "")
            new_status = details.get("new_status", "")
            base_message += f" from {old_status} to {new_status}"
    
    return base_message