# Tutorial: Image Recall System

Build an image storage and retrieval system using AB's buffer storage
and metadata searching capabilities.

## Overview

Images present unique challenges for memory systems:

- **Binary data** - Can't be searched as text
- **Rich metadata** - Tags, descriptions, creation dates
- **Visual relationships** - Similar images should be grouped

AB handles these by storing images in buffers with searchable metadata.

## Use Case

We'll build a system that:

1. Stores images with metadata (tags, descriptions, dimensions)
2. Searches by metadata and descriptions
3. Groups visually related images
4. Recalls frequently accessed images faster

## Implementation

### Step 1: Store Images

```python
from ab import ABMemory, Buffer
import os
import hashlib
from datetime import datetime

memory = ABMemory("image_memory.sqlite")

def store_image(
    memory: ABMemory,
    image_path: str,
    tags: list[str] = None,
    description: str = "",
    category: str = "uncategorized"
) -> int:
    """Store an image with metadata."""
    
    # Read image file
    with open(image_path, "rb") as f:
        image_data = f.read()
    
    # Extract metadata
    filename = os.path.basename(image_path)
    file_ext = os.path.splitext(filename)[1].lower()
    file_hash = hashlib.md5(image_data).hexdigest()
    
    # Create buffers
    buffers = [
        # The actual image data
        Buffer(
            name="image",
            payload=image_data,
            headers={
                "filename": filename,
                "content_type": f"image/{file_ext[1:]}",
                "size_bytes": len(image_data),
                "hash": file_hash,
            }
        ),
        # Searchable description
        Buffer(
            name="description",
            payload=description.encode(),
            headers={"type": "text"}
        ),
        # Tags for filtering
        Buffer(
            name="tags",
            payload=",".join(tags or []).encode(),
            headers={}
        ),
        # Category
        Buffer(
            name="category",
            payload=category.encode(),
            headers={}
        ),
    ]
    
    card = memory.store_card(label="image", buffers=buffers)
    return card.id

# Example: Store an image
image_id = store_image(
    memory,
    "/path/to/sunset.jpg",
    tags=["nature", "sunset", "landscape"],
    description="Beautiful sunset over the ocean with orange and purple sky",
    category="photography"
)
```

### Step 2: Retrieve Images by ID

```python
def get_image(memory: ABMemory, card_id: int) -> tuple[bytes, dict]:
    """Retrieve an image and its metadata."""
    
    card = memory.get_card(card_id)
    
    # Strengthen memory on access
    memory.recall_card(card_id)
    
    image_data = None
    metadata = {}
    
    for buf in card.buffers:
        if buf.name == "image":
            image_data = buf.payload
            metadata.update(buf.headers)
        elif buf.name == "description":
            metadata["description"] = buf.payload.decode()
        elif buf.name == "tags":
            metadata["tags"] = buf.payload.decode().split(",")
        elif buf.name == "category":
            metadata["category"] = buf.payload.decode()
    
    return image_data, metadata

# Example: Get an image
image_data, metadata = get_image(memory, image_id)
print(f"Size: {metadata['size_bytes']} bytes")
print(f"Tags: {metadata['tags']}")
```

### Step 3: Search by Description

```python
from ab import semantic_search

def search_images_by_description(
    memory: ABMemory,
    query: str,
    max_results: int = 10
) -> list[dict]:
    """Search images by semantic similarity to description."""
    
    results = semantic_search(
        memory,
        query,
        top_k=max_results,
        label_filter="image"
    )
    
    images = []
    for card, score in results:
        # Get metadata without loading full image
        metadata = {"card_id": card.id, "score": score}
        for buf in card.buffers:
            if buf.name == "description":
                metadata["description"] = buf.payload.decode()
            elif buf.name == "tags":
                metadata["tags"] = buf.payload.decode().split(",")
            elif buf.name == "image":
                metadata["filename"] = buf.headers.get("filename")
                metadata["size_bytes"] = buf.headers.get("size_bytes")
        images.append(metadata)
    
    return images

# Example: Search for sunset images
results = search_images_by_description(memory, "sunset sky evening")
for img in results:
    print(f"{img['filename']}: {img['description'][:50]}... (score: {img['score']:.3f})")
```

### Step 4: Search by Tags

```python
from ab import search_cards

def search_images_by_tags(
    memory: ABMemory,
    tags: list[str]
) -> list[int]:
    """Find images containing all specified tags."""
    
    # Search by first tag, then filter
    all_images = search_cards(memory, label="image")
    
    matching = []
    for card in all_images:
        for buf in card.buffers:
            if buf.name == "tags":
                card_tags = buf.payload.decode().split(",")
                if all(tag in card_tags for tag in tags):
                    matching.append(card.id)
                    break
    
    return matching

# Example: Find images with nature and sunset tags
matching_ids = search_images_by_tags(memory, ["nature", "sunset"])
```

### Step 5: Group Related Images

```python
def link_similar_images(
    memory: ABMemory,
    card_id_1: int,
    card_id_2: int,
    similarity_type: str = "visually_similar"
) -> None:
    """Create a connection between similar images."""
    memory.create_connection(
        source_card_id=card_id_1,
        target_card_id=card_id_2,
        relation=similarity_type,
        strength=2.0
    )

def get_similar_images(
    memory: ABMemory,
    card_id: int,
    max_hops: int = 2
) -> list[int]:
    """Find images connected as similar."""
    from ab import rfs_recall
    
    results = rfs_recall(memory, card_id, max_hops=max_hops)
    
    similar = []
    for card, score, path in results:
        if card.label == "image" and card.id != card_id:
            similar.append(card.id)
    
    return similar

# Example: Link and find similar images
link_similar_images(memory, sunset_id, other_sunset_id, "same_album")
similar = get_similar_images(memory, sunset_id)
```

### Step 6: Build Image Collections

```python
def create_album(
    memory: ABMemory,
    name: str,
    image_ids: list[int]
) -> int:
    """Create an album linking multiple images."""
    
    # Create album card
    album = memory.store_card(
        label="album",
        buffers=[
            Buffer(name="name", payload=name.encode(), headers={}),
            Buffer(name="image_count", payload=str(len(image_ids)).encode(), headers={})
        ]
    )
    
    # Link images to album
    for img_id in image_ids:
        memory.create_connection(
            source_card_id=album.id,
            target_card_id=img_id,
            relation="contains",
            strength=1.0
        )
    
    return album.id

def get_album_images(memory: ABMemory, album_id: int) -> list[int]:
    """Get all images in an album."""
    connections = memory.list_connections(card_id=album_id)
    return [
        c["target_card_id"]
        for c in connections
        if c["relation"] == "contains"
    ]
```

## Example: Image Gallery

```python
# Store some images
nature_images = [
    store_image(memory, "sunset.jpg", ["nature", "sunset"], "Ocean sunset"),
    store_image(memory, "forest.jpg", ["nature", "trees"], "Dense forest"),
    store_image(memory, "mountain.jpg", ["nature", "mountain"], "Snow capped peaks"),
]

# Create an album
album_id = create_album(memory, "Nature Collection", nature_images)

# Link similar images
link_similar_images(memory, nature_images[0], nature_images[1])

# Search by description
results = search_images_by_description(memory, "natural landscape outdoor")

# Get album contents
album_images = get_album_images(memory, album_id)
```

## Debugging

```python
from ab.debug import DebugPrinter, MemoryInspector

printer = DebugPrinter()
inspector = MemoryInspector(memory)

# See memory summary
inspector.summary()

# Inspect an image card (shows buffers without loading full image)
inspector.inspect_card(image_id)
```

## Performance Tips

1. **Don't load full images for search** - Only load metadata
2. **Use connections for similarity** - Faster than computing similarity each time
3. **Recall frequently used images** - They'll rank higher in search
4. **Apply decay to clean up** - Unused images fade away

## Integration with ML

For more advanced image similarity:

```python
# Pseudocode for ML integration
from your_ml_library import get_image_embedding

def store_image_with_embedding(memory, image_path, **kwargs):
    card_id = store_image(memory, image_path, **kwargs)
    
    # Get ML embedding
    with open(image_path, "rb") as f:
        embedding = get_image_embedding(f.read())
    
    # Store embedding as additional buffer
    card = memory.get_card(card_id)
    buffers = list(card.buffers) + [
        Buffer(name="embedding", payload=pickle.dumps(embedding), headers={"type": "vector"})
    ]
    memory.update_card_buffers(card_id, buffers)
    
    return card_id
```

## Next Steps

- [AI Agent Memory](ai_agent_memory.md) - Build conversation memory
- [Knowledge Graph](knowledge_graph.md) - Connect concepts
