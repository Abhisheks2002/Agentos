"""
Day 94: Biological Computing Integration
==========================================

Implementing biologically-inspired computing paradigms including DNA computing,
cellular automata, and organic computing for novel agent architectures.

Key Concepts:
- DNA Computing
- Cellular Automata
- Membrane Computing
- Evolutionary Algorithms
- Organic Computing
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import random
import math


class BioComputingParadigm(Enum):
    """Biological Computing Paradigms"""
    DNA_COMPUTING = "dna_computing"
    CELLULAR_AUTOMATA = "cellular_automata"
    MEMBRANE_COMPUTING = "membrane_computing"
    EVOLUTIONARY = "evolutionary"
    ORGANIC = "organic"


class DNABase(Enum):
    """DNA Bases"""
    ADENINE = "A"
    THYMINE = "T"
    GUANINE = "G"
    CYTOSINE = "C"
    URACIL = "U"


class CellState(Enum):
    """Cell State for Cellular Automata"""
    DEAD = 0
    ALIVE = 1
    DYING = 2
    REPLICATING = 3


class MembraneType(Enum):
    """Membrane Types"""
    SKIN = "skin"
    ORGANELLE = "organelle"
    NUCLEAR = "nuclear"


@dataclass
class DNAStrand:
    """DNA Strand"""
    strand_id: str
    sequence: List[DNABase]
    direction: str = "5_to_3"
    length: int = 0

    def __post_init__(self):
        self.length = len(self.sequence)


@dataclass
class DNAOperation:
    """DNA Computing Operation"""
    operation_type: str  # ligate, cut, amplify, complement
    input_strands: List[DNAStrand]
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Cell:
    """Cell for Cellular Automata"""
    cell_id: str
    position: Tuple[int, int]
    state: CellState
    age: int = 0
    energy: float = 100.0
    neighbors: List[str] = field(default_factory=list)


@dataclass
class Membrane:
    """Membrane for Membrane Computing"""
    membrane_id: str
    membrane_type: MembraneType
    objects: List[Any] = field(default_factory=list)
    child_membranes: List[str] = field(default_factory=list)
    parent_membrane: Optional[str] = None
    charge: float = 0.0


@dataclass
class Organism:
    """Organism with genome"""
    organism_id: str
    genome: List[DNAStrand]
    phenotype: Dict[str, Any] = field(default_factory=dict)
    fitness: float = 0.0
    generation: int = 0


class DNABioProcessor:
    """
    DNA Computing Processor
    =======================

    Processes problems using DNA computation.
    """

    def __init__(self):
        self.strands: Dict[str, DNAStrand] = {}
        self.operations_log: List[DNAOperation] = []

    def create_strand(self, sequence: str) -> DNAStrand:
        """Create DNA strand from sequence string"""
        strand_id = str(uuid.uuid4())
        bases = []

        for char in sequence.upper():
            try:
                base = DNABase(char)
                bases.append(base)
            except ValueError:
                continue

        strand = DNAStrand(strand_id=strand_id, sequence=bases)
        self.strands[strand_id] = strand

        print(f"[DNA] Created strand {strand_id[:8]} with {len(bases)} bases")
        return strand

    def complement(self, strand: DNAStrand) -> DNAStrand:
        """Generate complement strand"""
        complement_map = {
            DNABase.ADENINE: DNABase.THYMINE,
            DNABase.THYMINE: DNABase.ADENINE,
            DNABase.GUANINE: DNABase.CYTOSINE,
            DNABase.CYTOSINE: DNABase.GUANINE,
        }

        complement_bases = [complement_map.get(b, b) for b in strand.sequence]
        new_strand = DNAStrand(
            strand_id=str(uuid.uuid4()),
            sequence=complement_bases,
            direction="3_to_5"
        )

        self.strands[new_strand.strand_id] = new_strand
        self.operations_log.append(DNAOperation(
            operation_type="complement",
            input_strands=[strand]
        ))

        return new_strand

    def ligate(self, strand1: DNAStrand, strand2: DNAStrand) -> DNAStrand:
        """Ligate two DNA strands"""
        combined = DNAStrand(
            strand_id=str(uuid.uuid4()),
            sequence=strand1.sequence + strand2.sequence,
            direction=strand1.direction
        )

        self.strands[combined.strand_id] = combined
        self.operations_log.append(DNAOperation(
            operation_type="ligate",
            input_strands=[strand1, strand2]
        ))

        return combined

    def amplify(self, strand: DNAStrand, cycles: int) -> List[DNAStrand]:
        """Amplify (PCR) DNA strand"""
        copies = []
        for i in range(cycles):
            copy = DNAStrand(
                strand_id=str(uuid.uuid4()),
                sequence=strand.sequence.copy(),
                direction=strand.direction
            )
            self.strands[copy.strand_id] = copy
            copies.append(copy)

        self.operations_log.append(DNAOperation(
            operation_type="amplify",
            input_strands=[strand],
            parameters={"cycles": cycles}
        ))

        return copies

    def find_pattern(self, search_strand: DNAStrand, pattern: List[DNABase]) -> List[int]:
        """Find pattern in DNA strand"""
        positions = []
        pattern_len = len(pattern)

        for i in range(len(search_strand.sequence) - pattern_len + 1):
            if search_strand.sequence[i:i + pattern_len] == pattern:
                positions.append(i)

        return positions

    def hamming_distance(self, strand1: DNAStrand, strand2: DNAStrand) -> int:
        """Calculate Hamming distance between two strands"""
        if len(strand1.sequence) != len(strand2.sequence):
            min_len = min(len(strand1.sequence), len(strand2.sequence))
        else:
            min_len = len(strand1.sequence)

        distance = 0
        for i in range(min_len):
            if strand1.sequence[i] != strand2.sequence[i]:
                distance += 1

        return distance


class CellularAutomata:
    """
    Cellular Automata System
    ========================

    Grid-based computation using cell states.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid: Dict[Tuple[int, int], Cell] = {}
        self.generation = 0

    def initialize_random(self, density: float = 0.3):
        """Initialize grid with random cells"""
        for x in range(self.width):
            for y in range(self.height):
                cell_id = f"cell_{x}_{y}"
                state = CellState.ALIVE if random.random() < density else CellState.DEAD

                cell = Cell(
                    cell_id=cell_id,
                    position=(x, y),
                    state=state,
                    energy=random.uniform(50, 100)
                )
                self.grid[(x, y)] = cell

    def get_neighbors(self, x: int, y: int) -> List[Cell]:
        """Get neighboring cells (Moore neighborhood)"""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue

                nx, ny = (x + dx) % self.width, (y + dy) % self.height
                if (nx, ny) in self.grid:
                    neighbors.append(self.grid[(nx, ny)])

        return neighbors

    def count_alive_neighbors(self, x: int, y: int) -> int:
        """Count alive neighbors"""
        neighbors = self.get_neighbors(x, y)
        return sum(1 for n in neighbors if n.state == CellState.ALIVE)

    def apply_rules(self):
        """Apply cellular automata rules (Game of Life variant)"""
        new_grid = {}

        for (x, y), cell in self.grid.items():
            alive_neighbors = self.count_alive_neighbors(x, y)

            # Apply rules
            if cell.state == CellState.ALIVE:
                if alive_neighbors < 2 or alive_neighbors > 3:
                    new_state = CellState.DEAD
                else:
                    new_state = CellState.ALIVE

                # Random death from old age
                if cell.age > 100 and random.random() < 0.01:
                    new_state = CellState.DYING
            else:
                if alive_neighbors == 3:
                    new_state = CellState.REPLICATING
                else:
                    new_state = CellState.DEAD

            # Create new cell
            new_cell = Cell(
                cell_id=cell.cell_id,
                position=cell.position,
                state=new_state,
                age=cell.age + 1 if new_state == CellState.ALIVE else 0,
                energy=cell.energy * 0.99
            )
            new_grid[(x, y)] = new_cell

        self.grid = new_grid
        self.generation += 1

    def get_statistics(self) -> Dict[str, Any]:
        """Get population statistics"""
        states = {}
        for cell in self.grid.values():
            state_name = cell.state.name
            states[state_name] = states.get(state_name, 0) + 1

        return {
            "generation": self.generation,
            "total_cells": len(self.grid),
            "alive": states.get("ALIVE", 0),
            "dead": states.get("DEAD", 0),
            "dying": states.get("DYING", 0),
            "replicating": states.get("REPLICATING", 0)
        }


class MembraneSystem:
    """
    P-System / Membrane Computing
    ============================

    Distributed computation using membranes and objects.
    """

    def __init__(self):
        self.membranes: Dict[str, Membrane] = {}
        self.objects: List[Any] = []
        self.evolution_steps = 0

    def create_membrane(
        self,
        membrane_type: MembraneType,
        parent: Optional[str] = None
    ) -> str:
        """Create membrane"""
        membrane_id = str(uuid.uuid4())

        membrane = Membrane(
            membrane_id=membrane_id,
            membrane_type=membrane_type,
            parent_membrane=parent
        )

        if parent and parent in self.membranes:
            self.membranes[parent].child_membranes.append(membrane_id)

        self.membranes[membrane_id] = membrane

        print(f"[Membrane] Created {membrane_type.value} membrane: {membrane_id[:8]}")
        return membrane_id

    def add_object(self, membrane_id: str, obj: Any):
        """Add object to membrane"""
        if membrane_id in self.membranes:
            self.membranes[membrane_id].objects.append(obj)

    def evolve(self):
        """Evolve membrane system"""
        self.evolution_steps += 1

        for membrane_id, membrane in self.membranes.items():
            # Process objects in membrane
            for obj in membrane.objects[:]:
                # Apply rules based on membrane type
                if isinstance(obj, str) and len(obj) > 0:
                    # Transform object (simplified)
                    new_obj = obj.upper() if random.random() > 0.5 else obj.lower()
                    idx = membrane.objects.index(obj)
                    membrane.objects[idx] = new_obj

            # Redistribute objects to child membranes
            if membrane.child_membranes and len(membrane.objects) > 1:
                for child_id in membrane.child_membranes:
                    if child_id in self.membranes and self.membranes[child_id].membrane_type != MembraneType.NUCLEAR:
                        obj = membrane.objects.pop(0) if membrane.objects else None
                        if obj:
                            self.membranes[child_id].objects.append(obj)

    def get_membrane_hierarchy(self) -> Dict[str, List[str]]:
        """Get membrane hierarchy"""
        hierarchy = {}
        for membrane_id, membrane in self.membranes.items():
            hierarchy[membrane_id] = membrane.child_membranes
        return hierarchy


class EvolutionaryAlgorithm:
    """
    Evolutionary Algorithm
    =====================

    Genetic algorithm for optimization.
    """

    def __init__(self, population_size: int = 100):
        self.population_size = population_size
        self.population: List[Organism] = []
        self.generation = 0
        self.mutation_rate = 0.05
        self.crossover_rate = 0.7

    def initialize(self, genome_length: int = 10):
        """Initialize population with random genomes"""
        for i in range(self.population_size):
            organism_id = f"organism_{i}"

            # Create random genome
            bases = [random.choice(list(DNABase)) for _ in range(genome_length)]
            genome = [DNAStrand(strand_id=str(uuid.uuid4()), sequence=bases)]

            organism = Organism(
                organism_id=organism_id,
                genome=genome,
                fitness=0.0,
                generation=0
            )

            self.population.append(organism)

    def evaluate(self, fitness_function: callable):
        """Evaluate population fitness"""
        for organism in self.population:
            # Convert genome to numeric for evaluation
            genome_value = sum(
                hash(b.value) % 100 for strand in organism.genome for b in strand.sequence
            ) % 1000

            organism.fitness = fitness_function(genome_value)

    def select_parents(self) -> List[Organism]:
        """Tournament selection"""
        parents = []
        for _ in range(2):
            tournament = random.sample(self.population, min(5, len(self.population)))
            winner = max(tournament, key=lambda x: x.fitness)
            parents.append(winner)
        return parents

    def crossover(self, parent1: Organism, parent2: Organism) -> Organism:
        """Single-point crossover"""
        if not parent1.genome or not parent2.genome:
            return parent1

        strand1 = parent1.genome[0]
        strand2 = parent2.genome[0]

        if len(strand1.sequence) < 2:
            return parent1

        point = random.randint(1, len(strand1.sequence) - 1)

        child_sequence = strand1.sequence[:point] + strand2.sequence[point:]
        child_genome = [DNAStrand(strand_id=str(uuid.uuid4()), sequence=child_sequence)]

        child = Organism(
            organism_id=str(uuid.uuid4()),
            genome=child_genome,
            generation=self.generation + 1
        )

        return child

    def mutate(self, organism: Organism) -> Organism:
        """Point mutation"""
        if not organism.genome:
            return organism

        strand = organism.genome[0]
        new_sequence = strand.sequence.copy()

        for i in range(len(new_sequence)):
            if random.random() < self.mutation_rate:
                new_sequence[i] = random.choice(list(DNABase))

        organism.genome[0].sequence = new_sequence

        return organism

    def evolve(self, fitness_function: callable, generations: int = 10):
        """Run evolutionary algorithm"""
        self.evaluate(fitness_function)

        for gen in range(generations):
            new_population = []

            # Elitism: keep best
            sorted_pop = sorted(self.population, key=lambda x: x.fitness, reverse=True)
            new_population.extend(sorted_pop[:2])

            while len(new_population) < self.population_size:
                parents = self.select_parents()

                if random.random() < self.crossover_rate:
                    child = self.crossover(parents[0], parents[1])
                else:
                    child = parents[0]

                child = self.mutate(child)
                new_population.append(child)

            self.population = new_population[:self.population_size]
            self.generation += 1
            self.evaluate(fitness_function)

            if gen % 5 == 0:
                best = max(self.population, key=lambda x: x.fitness)
                print(f"[Evolution] Gen {gen}: Best fitness = {best.fitness:.2f}")

        return max(self.population, key=lambda x: x.fitness)


class BioComputingAgent:
    """
    Biological Computing Agent
    ==========================

    Agent that uses biological computing paradigms.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.dna_processor = DNABioProcessor()
        self.cellular_automata = CellularAutomata(20, 20)
        self.membrane_system = MembraneSystem()
        self.evolution = EvolutionaryAlgorithm(50)

    async def dna_compute(self, problem_data: str) -> Dict[str, Any]:
        """Solve problem using DNA computing"""
        # Create DNA representation
        strand = self.dna_processor.create_strand(problem_data)
        complement = self.dna_processor.complement(strand)

        return {
            "original_strand": strand.strand_id[:8],
            "complement_strand": complement.strand_id[:8],
            "original_length": strand.length,
            "complement_length": complement.length
        }

    async def run_cellular_automata(self, steps: int) -> Dict[str, Any]:
        """Run cellular automata simulation"""
        self.cellular_automata.initialize_random(0.3)

        for _ in range(steps):
            self.cellular_automata.apply_rules()

        return self.cellular_automata.get_statistics()

    async def evolve_solution(self, fitness_function: callable) -> float:
        """Evolve solution using genetic algorithm"""
        self.evolution.initialize(genome_length=20)
        best = self.evolution.evolve(fitness_function, generations=20)
        return best.fitness

    async def process_with_membranes(self, objects: List[Any]) -> Dict[str, Any]:
        """Process objects using membrane system"""
        # Create membrane hierarchy
        skin = self.membrane_system.create_membrane(MembraneType.SKIN)
        organelle1 = self.membrane_system.create_membrane(MembraneType.ORGANELLE, skin)
        organelle2 = self.membrane_system.create_membrane(MembraneType.ORGANELLE, skin)
        nucleus = self.membrane_system.create_membrane(MembraneType.NUCLEAR, organelle1)

        # Add objects to skin
        for obj in objects:
            self.membrane_system.add_object(skin, obj)

        # Evolve system
        for _ in range(5):
            self.membrane_system.evolve()

        # Get statistics
        hierarchy = self.membrane_system.get_membrane_hierarchy()

        return {
            "membranes": len(self.membrane_system.membranes),
            "evolution_steps": self.membrane_system.evolution_steps,
            "hierarchy": {k[:8]: len(v) for k, v in hierarchy.items()}
        }


async def main():
    """Demonstrate Biological Computing Integration"""
    print("=" * 60)
    print("Biological Computing Integration - Day 94")
    print("=" * 60)

    # Create bio-computing agent
    agent = BioComputingAgent("bio-agent-001")

    # DNA Computing
    print("\n[1] DNA Computing")
    print("-" * 40)

    result = await agent.dna_compute("AGCTTTAGCGTAGCT")
    print(f"  Original strand: {result['original_strand']}")
    print(f"  Complement: {result['complement_strand']}")
    print(f"  Length: {result['original_length']}")

    # Create more strands
    strand1 = agent.dna_processor.create_strand("ATGCCCGGGAAATTT")
    strand2 = agent.dna_processor.create_strand("CCCGGTACCTTGGA")
    ligated = agent.dna_processor.ligate(strand1, strand2)
    print(f"  Ligated strand length: {ligated.length}")

    # Cellular Automata
    print("\n[2] Cellular Automata")
    print("-" * 40)

    stats = await agent.run_cellular_automata(50)
    print(f"  Generation: {stats['generation']}")
    print(f"  Alive cells: {stats['alive']}")
    print(f"  Dead cells: {stats['dead']}")
    print(f"  Replicating: {stats['replicating']}")

    # Evolutionary Algorithm
    print("\n[3] Evolutionary Algorithm")
    print("-" * 40)

    # Define fitness function
    def target_fitness(genome_value):
        target = 999
        return 1.0 - abs(genome_value - target) / 1000.0

    best_fitness = await agent.evolve_solution(target_fitness)
    print(f"  Best fitness achieved: {best_fitness:.4f}")
    print(f"  Generations: {agent.evolution.generation}")

    # Membrane Computing
    print("\n[4] Membrane Computing")
    print("-" * 40)

    objects = ["ATP", "protein", "enzyme", "hormone", "gene"]
    membrane_result = await agent.process_with_membranes(objects)
    print(f"  Total membranes: {membrane_result['membranes']}")
    print(f"  Evolution steps: {membrane_result['evolution_steps']}")
    print(f"  Membrane hierarchy: {membrane_result['hierarchy']}")

    # Combined processing
    print("\n[5] Combined Bio-Computing")
    print("-" * 40)

    print(f"  DNA operations: {len(agent.dna_processor.operations_log)}")
    print(f"  EA population: {len(agent.evolution.population)}")
    print(f"  Membrane evolution: {agent.membrane_system.evolution_steps}")

    # Statistics
    print("\n[6] System Statistics")
    print("-" * 40)

    print(f"  DNA strands: {len(agent.dna_processor.strands)}")
    print(f"  Cellular grid: {agent.cellular_automata.width}x{agent.cellular_automata.height}")
    print(f"  Total organisms: {len(agent.evolution.population)}")
    print(f"  Membrane objects: {sum(len(m.objects) for m in agent.membrane_system.membranes.values())}")

    print("\n" + "=" * 60)
    print("Biological Computing Integration complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())