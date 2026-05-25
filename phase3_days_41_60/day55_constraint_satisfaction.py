"""
Day 55: Constraint Satisfaction
===============================
Handling constraints in text generation.

Key Concepts:
- Hard constraints (must satisfy)
- Soft constraints (should satisfy)
- Constraint validation
- Constraint-based generation
"""

from typing import List, Dict, Any, Optional, Callable, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re
import uuid


class ConstraintType(Enum):
    """Types of constraints"""
    LENGTH = "length"
    FORMAT = "format"
    KEYWORD = "keyword"
    FORBIDDEN = "forbidden"
    STRUCTURE = "structure"
    STYLE = "style"
    REGEX = "regex"
    CUSTOM = "custom"


class ConstraintPriority(Enum):
    """Constraint priority levels"""
    CRITICAL = 3  # Must satisfy
    HIGH = 2  # Should satisfy
    MEDIUM = 1  # Nice to have
    LOW = 0  # Best effort


@dataclass
class Constraint:
    """A constraint to satisfy"""
    id: str
    type: ConstraintType
    priority: ConstraintPriority
    description: str
    config: Dict[str, Any] = field(default_factory=dict)
    validator: Callable[[str], Tuple[bool, str]] = None

    def validate(self, text: str) -> Tuple[bool, str]:
        """Validate text against constraint"""
        if self.validator:
            return self.validator(text)

        # Default validators based on type
        if self.type == ConstraintType.LENGTH:
            return self._validate_length(text)
        elif self.type == ConstraintType.KEYWORD:
            return self._validate_keyword(text)
        elif self.type == ConstraintType.FORBIDDEN:
            return self._validate_forbidden(text)
        elif self.type == ConstraintType.FORMAT:
            return self._validate_format(text)
        elif self.type == ConstraintType.REGEX:
            return self._validate_regex(text)

        return True, "No validation defined"

    def _validate_length(self, text: str) -> Tuple[bool, str]:
        """Validate length constraints"""
        min_len = self.config.get("min", 0)
        max_len = self.config.get("max", float("inf"))
        length = len(text)

        if length < min_len:
            return False, f"Too short: {length} < {min_len}"
        if length > max_len:
            return False, f"Too long: {length} > {max_len}"
        return True, f"Length {length} is valid"

    def _validate_keyword(self, text: str) -> Tuple[bool, str]:
        """Validate keyword presence"""
        required = self.config.get("keywords", [])
        text_lower = text.lower()

        missing = [kw for kw in required if kw.lower() not in text_lower]
        if missing:
            return False, f"Missing keywords: {missing}"
        return True, "All required keywords present"

    def _validate_forbidden(self, text: str) -> Tuple[bool, str]:
        """Validate no forbidden words"""
        forbidden = self.config.get("words", [])
        text_lower = text.lower()

        found = [w for w in forbidden if w.lower() in text_lower]
        if found:
            return False, f"Found forbidden words: {found}"
        return True, "No forbidden words"

    def _validate_format(self, text: str) -> Tuple[bool, str]:
        """Validate format constraints"""
        format_type = self.config.get("type")

        if format_type == "json":
            import json
            try:
                json.loads(text)
                return True, "Valid JSON"
            except:
                return False, "Invalid JSON"
        elif format_type == "markdown":
            has_headers = bool(re.search(r'^#+\s', text, re.MULTILINE))
            return has_headers, "Markdown format check"
        elif format_type == "code":
            has_code = bool(re.search(r'(def |class |function |import )', text))
            return has_code, "Code format check"

        return True, "Format validated"

    def _validate_regex(self, text: str) -> Tuple[bool, str]:
        """Validate against regex pattern"""
        pattern = self.config.get("pattern")
        if not pattern:
            return True, "No pattern to validate"

        if re.search(pattern, text):
            return True, "Pattern matched"
        return False, "Pattern not found"


class ConstraintSatisfaction:
    """
    Constraint Satisfaction System
    ==============================

    Manages constraints and ensures they're satisfied.
    """

    def __init__(self):
        self.constraints: List[Constraint] = []
        self.satisfied_count = 0
        self.failed_count = 0

    def add_constraint(
        self,
        constraint_type: ConstraintType,
        description: str,
        priority: ConstraintPriority = ConstraintPriority.MEDIUM,
        **config
    ) -> Constraint:
        """Add a constraint"""
        constraint = Constraint(
            id=f"constraint_{uuid.uuid4().hex[:8]}",
            type=constraint_type,
            priority=priority,
            description=description,
            config=config
        )
        self.constraints.append(constraint)
        return constraint

    def validate(self, text: str) -> Dict[str, Any]:
        """Validate text against all constraints"""
        results = {
            "valid": True,
            "satisfied": [],
            "failed": [],
            "warnings": [],
            "score": 0.0
        }

        critical_failed = False

        for constraint in self.constraints:
            is_valid, message = constraint.validate(text)

            result = {
                "id": constraint.id,
                "type": constraint.type.value,
                "priority": constraint.priority.value,
                "valid": is_valid,
                "message": message,
                "description": constraint.description
            }

            if is_valid:
                results["satisfied"].append(result)
            else:
                if constraint.priority == ConstraintPriority.CRITICAL:
                    critical_failed = True
                    results["valid"] = False
                results["failed"].append(result)

        # Calculate score
        total = len(self.constraints)
        if total > 0:
            satisfied = len(results["satisfied"])
            results["score"] = satisfied / total

        if critical_failed:
            results["valid"] = False

        return results

    def get_constraint_summary(self) -> str:
        """Get summary of constraints"""
        by_type = {}
        by_priority = {p: 0 for p in ConstraintPriority}

        for c in self.constraints:
            by_type[c.type.value] = by_type.get(c.type.value, 0) + 1
            by_priority[c.priority] += 1

        lines = ["Constraints Summary:"]
        lines.append(f"  Total: {len(self.constraints)}")

        lines.append("  By Type:")
        for t, count in by_type.items():
            lines.append(f"    {t}: {count}")

        lines.append("  By Priority:")
        for p, count in by_priority.items():
            lines.append(f"    {p.name}: {count}")

        return "\n".join(lines)


class ConstrainedGenerator:
    """
    Constrained Generator
    =====================

    Generates text while satisfying constraints.
    """

    def __init__(
        self,
        generator: Callable[[str], str] = None,
        max_attempts: int = 5
    ):
        self.generator = generator or (lambda p: "Generated response")
        self.max_attempts = max_attempts
        self.cs = ConstraintSatisfaction()

    def add_constraint(
        self,
        constraint_type: ConstraintType,
        description: str,
        priority: ConstraintPriority = ConstraintPriority.MEDIUM,
        **config
    ) -> Constraint:
        """Add a constraint to the generator"""
        return self.cs.add_constraint(
            constraint_type, description, priority, **config
        )

    def generate(
        self,
        prompt: str,
        base_prompt: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate text satisfying constraints"""
        # Build constrained prompt
        constrained_prompt = self._build_constrained_prompt(prompt)

        for attempt in range(self.max_attempts):
            # Generate
            if attempt == 0 and base_prompt:
                full_prompt = f"{base_prompt}\n\n{constrained_prompt}"
            else:
                full_prompt = constrained_prompt

            result = self.generator(full_prompt)

            # Validate
            validation = self.cs.validate(result)

            if validation["valid"]:
                return result, validation

            # Adjust prompt based on failures
            if attempt < self.max_attempts - 1:
                constrained_prompt = self._adjust_prompt(
                    constrained_prompt, validation
                )

        # Return best effort
        return result, validation

    def _build_constrained_prompt(self, prompt: str) -> str:
        """Build prompt with constraint instructions"""
        parts = [prompt]

        # Add constraint instructions
        for constraint in self.cs.constraints:
            if constraint.type == ConstraintType.LENGTH:
                min_l = constraint.config.get("min", "")
                max_l = constraint.config.get("max", "")
                parts.append(f"\nLength: {min_l}-{max_l} characters.")
            elif constraint.type == ConstraintType.KEYWORD:
                kw = constraint.config.get("keywords", [])
                parts.append(f"\nMust include: {', '.join(kw)}.")
            elif constraint.type == ConstraintType.FORBIDDEN:
                fw = constraint.config.get("words", [])
                parts.append(f"\nMust NOT include: {', '.join(fw)}.")

        return "\n".join(parts)

    def _adjust_prompt(
        self,
        prompt: str,
        validation: Dict[str, Any]
    ) -> str:
        """Adjust prompt based on validation failures"""
        adjustments = []

        for failed in validation.get("failed", []):
            if failed["type"] == "keyword":
                adjustments.append(
                    f"IMPORTANT: Include the keyword mentioned in the constraint."
                )
            elif failed["type"] == "forbidden":
                adjustments.append(
                    f"IMPORTANT: Avoid forbidden words."
                )
            elif failed["type"] == "length":
                adjustments.append(
                    f"IMPORTANT: Adjust length to meet requirements."
                )

        if adjustments:
            prompt += "\n\n" + " ".join(adjustments)

        return prompt


class ConstraintRepair:
    """
    Constraint Repair
    =================

    Post-process text to fix constraint violations.
    """

    def __init__(self):
        self.repair_strategies = {
            ConstraintType.LENGTH: self._repair_length,
            ConstraintType.KEYWORD: self._repair_keyword,
            ConstraintType.FORBIDDEN: self._repair_forbidden,
        }

    def repair(self, text: str, constraints: List[Constraint]) -> str:
        """Repair text to satisfy constraints"""
        result = text

        for constraint in constraints:
            validator = self.repair_strategies.get(constraint.type)
            if validator:
                result = validator(result, constraint)

        return result

    def _repair_length(self, text: str, constraint: Constraint) -> str:
        """Repair length constraint"""
        min_len = constraint.config.get("min", 0)
        max_len = constraint.config.get("max", float("inf"))

        if len(text) < min_len:
            # Pad with appropriate content
            padding = " " * (min_len - len(text))
            return text + padding

        if len(text) > max_len:
            return text[:max_len]

        return text

    def _repair_keyword(self, text: str, constraint: Constraint) -> str:
        """Repair missing keywords"""
        required = constraint.config.get("keywords", [])
        text_lower = text.lower()

        missing = [kw for kw in required if kw.lower() not in text_lower]

        if missing:
            # Append missing keywords naturally
            text += "\n\nNote: " + ", ".join(missing) + "."

        return text

    def _repair_forbidden(self, text: str, constraint: Constraint) -> str:
        """Remove forbidden words"""
        forbidden = constraint.config.get("words", [])

        for word in forbidden:
            # Replace with placeholder
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            text = pattern.sub("[REDACTED]", text)

        return text


# Demo function
def demo():
    """Demonstrate Constraint Satisfaction"""
    print("=" * 60)
    print("  Constraint Satisfaction Demo")
    print("=" * 60)

    # Create constraint satisfaction system
    cs = ConstraintSatisfaction()

    # Add various constraints
    cs.add_constraint(
        ConstraintType.LENGTH,
        "Response must be 50-200 characters",
        priority=ConstraintPriority.HIGH,
        min=50, max=200
    )

    cs.add_constraint(
        ConstraintType.KEYWORD,
        "Must include key terms",
        priority=ConstraintPriority.MEDIUM,
        keywords=["agent", "memory", "tool"]
    )

    cs.add_constraint(
        ConstraintType.FORBIDDEN,
        "Must not contain certain words",
        priority=ConstraintPriority.CRITICAL,
        words=["bad", "terrible", "hate"]
    )

    print("\n1. Constraint System:")
    print(cs.get_constraint_summary())

    # Test validation
    test_texts = [
        "This is a good agent with memory and tools.",
        "Agent systems have memory and tools for functionality.",
        "This is terrible and I hate bad things.",
        "Short",
    ]

    print("\n2. Validation Results:")
    for text in test_texts:
        result = cs.validate(text)
        status = "✓" if result["valid"] else "✗"
        print(f"\n{status} '{text[:40]}...'")
        print(f"  Score: {result['score']:.2f}")
        if result["failed"]:
            print(f"  Failed: {[f['type'] for f in result['failed']]}")

    # Constrained generator
    print("\n" + "-" * 50)
    print("3. Constrained Generator:")

    def mock_gen(prompt: str) -> str:
        responses = [
            "Agent with memory and tools is powerful.",
            "A good agent uses memory and tools effectively.",
            "This is a short response.",
            "This is a terrible response with bad words."
        ]
        import random
        return random.choice(responses)

    cg = ConstrainedGenerator(generator=mock_gen)
    cg.add_constraint(
        ConstraintType.LENGTH,
        "Response length",
        ConstraintPriority.HIGH,
        min=30, max=150
    )
    cg.add_constraint(
        ConstraintType.FORBIDDEN,
        "No bad words",
        ConstraintPriority.CRITICAL,
        words=["bad", "terrible"]
    )

    result, validation = cg.generate("Generate a response")
    print(f"Generated: {result[:50]}...")
    print(f"Valid: {validation['valid']}")

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    demo()