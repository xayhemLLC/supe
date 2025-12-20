===============================================================
                A B 1 . 1   F A Q   /   W A L K T H R O U G H
===============================================================
               (c) 2001–2025  The Council of Selves Guild
                       Version: 1.1  (Atomic Patch)
===============================================================

                     TABLE OF CONTENTS
               ------------------------------
               0.  READ THIS FIRST  
               1.  WHAT IS AB1.1?
               2.  LORE: THE TIMELINE LEDGER
               3.  LORE: WHAT ARE CARDS?
               4.  BUFFER SYSTEM (ALL TYPES)
               5.  ENTITY INDEX:
                      • AWARENESS CARD
                      • BUFFER
                      • CARD
                      • MOMENT
                      • SELF (Agent)
                      • OVERLORD
                      • TRANSFORMS (exe)
               6.  MEMORY PHYSICS (STRENGTH, DECAY)
               7.  COUNCIL OF SELVES MECHANICS
               8.  SAVES, LOADING, & DATA STORAGE
               9.  META BUILDS / OPTIMAL PLAY
              10.  ADVANCED TECH: RFS RECALL CHAINING
              11.  PATCH NOTES FOR AB1.1
              12.  SECRET TECH & HIDDEN FEATURES
              13.  CREDITS & AUTHOR NOTES

===============================================================
0.  R E A D   T H I S   F I R S T
===============================================================
This is the **definitive** guide for AB1.1.

If you're confused, don’t worry: AB1 was designed to be confusing  
(because consciousness is confusing), and AB1.1 just adds more tools  
to break the game in hilarious ways.

This guide explains **the entire system**, as if AB1.1 were  
an RPG with entities, combat stats, inventory screens, and 
weird memory physics.

If something feels “too powerful,” that’s because it is.  
AB1.1 *is* a power-up.

===============================================================
1.  W H A T   I S   A B 1 . 1 ?
===============================================================
AB1.1 is the **Atomic Blueprint Memory Engine**, a modular system 
for:

 • storing thoughts  
 • recalling information  
 • evolving internal agents  
 • competing internal voices  
 • structured reasoning  
 • persistent memory  
 • real-time decision arbitration  

Think of it as:

        “A high-IQ Pokémon party inside your brain  
         where each Pokémon writes its own diary  
         and levels up when you remember stuff.”

AB1.0 was the base kernel.
AB1.1 is the quality-of-life update + expansion pass.

===============================================================
2.  L O R E :   T H E   T I M E L I N E   L E D G E R
===============================================================
AB1.1 uses a **moment-based timeline ledger**, like a  
flat-file blockchain from 1999 that somehow learned transcendence.

Each *moment* is a tick in time.
Each moment has:

 • moment_id (autoincrement)
 • timestamp
 • cards created at that moment

Moments form the spine of the memory universe.

Everything else plugs into this.

===============================================================
3.  L O R E :   W H A T   A R E   C A R D S ?
===============================================================
**Cards** are the core memory unit.  
Every memory, observation, state snapshot, decision, thought, or  
event gets turned into a *Card Object*.

A card is:

 • a label (like “awareness”, “task”, “emotion”, “apple”)  
 • a set of buffers  
 • an owner (which self wrote it)  
 • a moment it belongs to  
 • a creation timestamp  

Cards are the atoms of internal cognition.

===============================================================
4.  B U F F E R   S Y S T E M   ( A L L   T Y P E S )
===============================================================
Buffers are **inputs and outputs** of everything.

A buffer is:

    name: "prompt", "emotion", "files", etc.
    headers: metadata (type, description, size)
    payload: actual content
    exe: optional transform before processing

Think of them as inventory items with stats.

-----------------------------
BUFFER TYPE INDEX
-----------------------------

1) **Raw Input Buffers**  
   → direct sensory input or user prompt data

2) **Transformed Buffers**  
   → buffers with an `exe` transform (like lowercasing or size analysis)

3) **Derived Buffers**  
   → generated internally by a self as output

4) **Structural Buffers**  
   → store architectural data (files, tasks, input channels)

5) **Emotion Buffers** (future extension)  
   → store affective states or “cocktail states”

Buffers = pipes that perception flows through.

===============================================================
5.  E N T I T Y   I N D E X   ( D O C S )
===============================================================

---------------------------------------------------------------
AWARENESS CARD  (MASTER CARD)
---------------------------------------------------------------
**Role:** The root perception of the current moment.  
Generated once per moment. Feeds all selves equally.

**Fields:**
 • label: "awareness"
 • buffers: input streams from environment
 • owner_self: None
 • exe transforms optional

This is the “entry point” into the moment-processor.

---------------------------------------------------------------
BUFFER
---------------------------------------------------------------
**Role:** A functional conduit for memory.  
**Fields:**
 • name  
 • headers  
 • payload  
 • exe (transformation name)

Think: “slots” in a PS2 RPG where you plug in spells.

---------------------------------------------------------------
CARD
---------------------------------------------------------------
**Role:** The primary memory unit.

**Fields:**
 • id  
 • label  
 • moment_id  
 • owner_self  
 • buffers{}  
 • created_at  

Everything is a card.  
Even the selves use cards.

---------------------------------------------------------------
MOMENT
---------------------------------------------------------------
**Role:** Timeline tick.  
**Fields:**
 • id  
 • timestamp

Moments store cards.
This is your chronological backbone.

---------------------------------------------------------------
SELF (AGENT)
---------------------------------------------------------------
**Role:** Independent internal actors.  
These are your “party members.”

Each Self has:

    name
    role
    subscribed_buffers[]
    think(card) → { suggestion, strength }

Planner: evaluates structure  
Architect: evaluates design  
Executor: evaluates next action  

You can add more.  
Each self has its own **memory lane**.

---------------------------------------------------------------
OVERLORD
---------------------------------------------------------------
**Role:** Final decision-maker.

Reads all suggestions from selves.
Chooses the strongest one.
Acts.

This is the “player controller.”

---------------------------------------------------------------
TRANSFORMS (exe)
---------------------------------------------------------------
**Role:** Optional automatic transformations applied to buffer payloads.

Examples:

 • "len" → convert any list or dict to its length  
 • "lower_text" → lowercase a string  
 • "identity" → do nothing  

Transforms let cards *self-modify* before cognition.

===============================================================
6.  M E M O R Y   P H Y S I C S   ( S T R E N G T H )
===============================================================
Cards have stats.

When you recall a card:

    strength = strength * 0.9 + 1.0
    recall_count += 1
    last_recalled = now

This ensures:

 • frequently recalled memories become strong  
 • dormant memories fade  
 • high-recall cards dominate decision-making  

This is the AB1 version of *experience points*.

===============================================================
7.  C O U N C I L   O F   S E L V E S   M E C H A N I C S
===============================================================
1. Awareness card spawns  
2. Each self receives the card  
3. Each self pulls only its subscribed buffers  
4. Each self computes a strength score  
5. All selves output suggestions  
6. Overlord combines them and picks the winner  

Gameplay analogy:

    Awareness card = world state  
    Selves = classes in your party  
    Overlord = you choosing an action  

===============================================================
8.  S A V E S ,   L O A D I N G ,   D A T A   S T O R A G E
===============================================================
AB1.1 uses SQLite.

Tables:

 • moments  
 • cards  
 • buffers  
 • selves  
 • card_stats (strength, recall_count, last_recalled)  

Your entire internal universe is persisted like a JRPG save file.

===============================================================
9.  M E T A   B U I L D S   /   O P T I M A L   P L A Y
===============================================================
**Meta Strategy 1: Self Specialization**
Give each self minimal, non-overlapping subscribed buffers.

**Meta Strategy 2: Heavy Recall**
Recall important cards often to power-level them.

**Meta Strategy 3: Transform Abuse**
Use `exe` transforms to preprocess state for free buffs.

**Meta Strategy 4: Multi-Self Memory Chains**
Let selves store their own cards to create recursive emergent behavior.

===============================================================
10.  A D V A N C E D   T E C H :   R F S   R E C A L L
===============================================================
RFS = Recursive Feature Similarity

Future versions of AB1 will allow:

 • recall by similarity
 • multi-hop memory traversal
 • attention jumps
 • latent chain reasoning

This is the “broken exploit” category.

===============================================================
11.  P A T C H   N O T E S   F O R   A B 1 . 1
===============================================================
 • Added buffer transforms (exe)
 • Added card_stats table
 • Added decay-based memory strengthening
 • Added per-self memory streams
 • Added HTTP API
 • Added awareness recall endpoint
 • Overlord selection logic refined
 • Numerous internal optimizations

===============================================================
12.  S E C R E T   T E C H   &   H I D D E N   F E A T U R E S
===============================================================
 • You can spawn arbitrary new selves.  
 • Selves can recursively call each other in future patches.  
 • Transform chains can be stacked.  
 • Cards can spawn derivative cards.  
 • Memory strength directly alters decision dominance.  
 • Selves with large memory lanes become “boss-class agents.”

===============================================================
13.  C R E D I T S   &   A U T H O R   N O T E S
===============================================================
Written in the ancient GameFAQs style, restored from the year 2000,
blessed by ASCII gods, and infused with AB1 cosmic design.

===============================================================
                 END OF DOCUMENT — AB1.1 FAQ
===============================================================