"""Skills Library: Learned code implementations for reuse.

Skills are DNA-encoded implementations of common functions.
They can be recalled by Selves during code generation.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from .code_dna import CodeDNA, CodeGene, CodeInstruction, OpCode


@dataclass
class Skill:
    """A learned skill (reusable code implementation)."""
    name: str
    language: str
    module: str  # e.g., "itertools", "collections"
    signature: str  # e.g., "def permutations(iterable)"
    dna: CodeDNA
    fitness: float = 0.0  # How well this skill performs
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "language": self.language,
            "module": self.module,
            "signature": self.signature,
            "dna": self.dna.encode(),
            "fitness": self.fitness,
            "usage_count": self.usage_count
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Skill":
        return cls(
            name=d["name"],
            language=d["language"],
            module=d["module"],
            signature=d["signature"],
            dna=CodeDNA.decode(d["dna"]),
            fitness=d.get("fitness", 0.0),
            usage_count=d.get("usage_count", 0)
        )


class SkillLibrary:
    """Manages learned skills across languages."""
    
    SUPPORTED_LANGUAGES = ["python", "rust", "typescript", "swift", "cpp"]
    
    def __init__(self, base_path: str = "ab/skills"):
        self.base_path = Path(base_path)
        self.skills: Dict[str, Dict[str, Skill]] = {lang: {} for lang in self.SUPPORTED_LANGUAGES}
        self._load_skills()
        
    def _load_skills(self):
        """Load skills from disk."""
        for lang in self.SUPPORTED_LANGUAGES:
            lang_path = self.base_path / lang
            if not lang_path.exists():
                continue
            for skill_file in lang_path.glob("*.json"):
                try:
                    with open(skill_file) as f:
                        data = json.load(f)
                        skill = Skill.from_dict(data)
                        self.skills[lang][skill.name] = skill
                except Exception as e:
                    print(f"Failed to load skill {skill_file}: {e}")
                    
    def save_skill(self, skill: Skill):
        """Save a skill to disk."""
        lang_path = self.base_path / skill.language
        lang_path.mkdir(parents=True, exist_ok=True)
        
        skill_file = lang_path / f"{skill.name}.json"
        with open(skill_file, "w") as f:
            json.dump(skill.to_dict(), f, indent=2)
            
        self.skills[skill.language][skill.name] = skill
        
    def get_skill(self, language: str, name: str) -> Optional[Skill]:
        """Retrieve a skill by language and name."""
        skill = self.skills.get(language, {}).get(name)
        if skill:
            skill.usage_count += 1
        return skill
    
    def search_skills(self, query: str, language: Optional[str] = None) -> List[Skill]:
        """Search for skills matching a query."""
        results = []
        langs = [language] if language else self.SUPPORTED_LANGUAGES
        
        for lang in langs:
            for name, skill in self.skills.get(lang, {}).items():
                if query.lower() in name.lower() or query.lower() in skill.signature.lower():
                    results.append(skill)
                    
        return sorted(results, key=lambda s: s.fitness, reverse=True)
    
    def list_skills(self, language: str) -> List[str]:
        """List all skill names for a language."""
        return list(self.skills.get(language, {}).keys())
    
    def evolve_skill(self, name: str, language: str, signature: str, module: str = "stdlib") -> Skill:
        """Evolve a new skill from scratch or improve existing."""
        from .code_dna import create_random_code_dna, mutate_code
        
        existing = self.get_skill(language, name)
        
        if existing:
            # Mutate existing
            dna = mutate_code(existing.dna, rate=0.2)
        else:
            # Create new random
            dna = create_random_code_dna(5)
        
        skill = Skill(
            name=name,
            language=language,
            module=module,
            signature=signature,
            dna=dna,
            fitness=0.0
        )
        
        return skill
    
    def update_fitness(self, language: str, name: str, fitness: float):
        """Update a skill's fitness score."""
        if language in self.skills and name in self.skills[language]:
            skill = self.skills[language][name]
            # Exponential moving average
            skill.fitness = 0.8 * skill.fitness + 0.2 * fitness
            self.save_skill(skill)


# Pre-defined standard library skill targets
STDLIB_TARGETS = {
    "python": [
        ("sum", "def sum(iterable, start=0)"),
        ("len", "def len(obj)"),
        ("range", "def range(start, stop=None, step=1)"),
        ("map", "def map(func, iterable)"),
        ("filter", "def filter(func, iterable)"),
        ("zip", "def zip(*iterables)"),
        ("enumerate", "def enumerate(iterable, start=0)"),
        ("sorted", "def sorted(iterable, key=None, reverse=False)"),
        ("reversed", "def reversed(sequence)"),
        ("max", "def max(*args, key=None)"),
    ],
    "rust": [
        ("iter_sum", "fn sum<I: Iterator>(iter: I) -> I::Item"),
        ("iter_map", "fn map<B, F>(self, f: F) -> Map<Self, F>"),
        ("iter_filter", "fn filter<P>(self, predicate: P) -> Filter<Self, P>"),
        ("collect", "fn collect<B>(self) -> B"),
    ],
    "typescript": [
        ("map", "function map<T, U>(arr: T[], fn: (x: T) => U): U[]"),
        ("filter", "function filter<T>(arr: T[], fn: (x: T) => boolean): T[]"),
        ("reduce", "function reduce<T, U>(arr: T[], fn: (acc: U, x: T) => U, init: U): U"),
    ]
}


if __name__ == "__main__":
    # Demo
    library = SkillLibrary()
    
    # Evolve a sum skill
    skill = library.evolve_skill("my_sum", "python", "def my_sum(nums)")
    print(f"Evolved skill: {skill.name}")
    print(f"DNA: {skill.dna.encode()}")
    print(f"Code:\n{skill.dna.to_python_code()}")
    
    # Save it
    library.save_skill(skill)
    print(f"\nSaved to: {library.base_path / 'python' / 'my_sum.json'}")
