# TASC API Reference

Task Atom system for AI-native task management.

## Tasc Class

### Creating Tasks

```python
from tasc.tasc import Tasc

task = Tasc(
    id="TASK-001",
    status="queued",
    title="Implement user authentication",
    additional_notes="Use OAuth2 with Google provider",
    testing_instructions="Test with test accounts",
    desired_outcome="Users can log in with Google",
    dependencies=["TASK-000"]  # Depends on another task
)
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `str` | Unique task identifier |
| `status` | `str` | Task status (queued, active, done, etc.) |
| `title` | `str` | Short task title |
| `additional_notes` | `str` | Detailed notes |
| `testing_instructions` | `str` | How to verify completion |
| `desired_outcome` | `str` | Expected result |
| `dependencies` | `List[str]` | Dependent task IDs |

---

## Binary Encoding

Tasks use efficient binary encoding for storage.

### to_atom / from_atom

```python
# Encode to Atom
atom = task.to_atom()
binary_data = atom.encode()

# Decode from Atom
from tasc.atom import decode_atom
decoded_atom, offset = decode_atom(binary_data, 0)
task = Tasc.from_atom(decoded_atom)
```

---

## AB Memory Integration

### store_tasc

Store a task in AB memory.

```python
from ab import ABMemory
from tasc.ab_integration import store_tasc

memory = ABMemory("tasks.sqlite")
task = Tasc(id="T-001", status="queued", title="My Task", ...)

card_id = store_tasc(memory, task)
print(f"Stored as card {card_id}")
```

### load_tasc

Load a task from AB memory.

```python
from tasc.ab_integration import load_tasc

task = load_tasc(memory, card_id)
print(task.title)
```

---

## TascQueue

Manage a queue of tasks.

```python
from ab import ABMemory
from tasc.tasc_queue import TascQueue
from tasc.tasc import Tasc

memory = ABMemory("queue.sqlite")
queue = TascQueue(memory)

# Enqueue
task = Tasc(id="T-001", status="queued", title="First task", ...)
queue.enqueue(task)

# Get next queued task
next_task = queue.dequeue()

# Mark complete
queue.complete(next_task.id)
```

---

## QManager

Higher-level queue management.

```python
from ab import ABMemory
from tasc.q_manager import QManager
from tasc.tasc import Tasc

memory = ABMemory("work.sqlite")
manager = QManager(memory)

# Add task
task = Tasc(id="T-001", status="queued", title="Work item", ...)
manager.add_task(task)

# Get next available
next_task = manager.get_next()

# Start working
manager.start_task(next_task.id)

# Complete
manager.complete_task(next_task.id)
```

---

## Atom Types

Low-level encoding primitives.

### Varint

Variable-length integer encoding.

```python
from tasc.varint import encode_varint, decode_varint

encoded = encode_varint(12345)
decoded, bytes_read = decode_varint(encoded, 0)
```

### AtomType Registry

```python
from tasc.atomtypes import registry

# Get type by ID
str_type = registry.get_by_id(1)

# Get type by name
int_type = registry.get_by_name("Int64")

# List all types
for type_id, type_obj in registry.types.items():
    print(f"{type_id}: {type_obj.name}")
```

---

## Example: Task Workflow

```python
from ab import ABMemory
from tasc.tasc import Tasc
from tasc.ab_integration import store_tasc, load_tasc

memory = ABMemory("project.sqlite")

# Create tasks
auth_task = Tasc(
    id="AUTH-001",
    status="queued",
    title="Implement OAuth",
    additional_notes="Use Google OAuth2",
    testing_instructions="Try login with test account",
    desired_outcome="Users can log in",
    dependencies=[]
)

profile_task = Tasc(
    id="PROFILE-001",
    status="queued",
    title="Add profile page",
    additional_notes="Show user info from OAuth",
    testing_instructions="Check profile displays correctly",
    desired_outcome="Users see their profile",
    dependencies=["AUTH-001"]  # Must complete auth first
)

# Store
auth_card = store_tasc(memory, auth_task)
profile_card = store_tasc(memory, profile_task)

# Connect tasks
memory.create_connection(auth_card, profile_card, "blocks")

# Load and update
auth = load_tasc(memory, auth_card)
auth.status = "active"
store_tasc(memory, auth)  # Re-store with new status
```
