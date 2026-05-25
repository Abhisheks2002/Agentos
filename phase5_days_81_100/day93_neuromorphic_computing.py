"""
Day 93: Neuromorphic Computing Integration
=============================================

Implementing brain-inspired computing paradigms for efficient AI agents
using neuromorphic hardware integration and spiking neural networks.

Key Concepts:
- Spiking Neural Networks
- Leaky Integrate-and-Fire Neurons
- Neuromorphic Hardware
- Event-Based Processing
- Brain-Inspired Architecture
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import random
import math


class NeuronType(Enum):
    """Neuron Types"""
    LIF = "lif"           # Leaky Integrate-and-Fire
    IZHIKEVICH = "izhikevich"
    HODGKIN_HUXLEY = "hodgkin_huxley"
    ADEX = "adex"         # Adaptive Exponential
    RESERVOIR = "reservoir"


class SynapseType(Enum):
    """Synapse Types"""
    EXCITATORY = "excitatory"
    INHIBITORY = "inhibitory"
    ELECTRICAL = "electrical"
    CHEMICAL = "chemical"


@dataclass
class Spike:
    """Neural Spike Event"""
    timestamp: float
    neuron_id: str
    layer: str
    amplitude: float = 1.0
    width_ms: float = 1.0


@dataclass
class NeuronState:
    """Neuron State"""
    neuron_id: str
    membrane_potential: float = -70.0
    threshold: float = -50.0
    reset_potential: float = -75.0
    refractory_period: float = 0.0
    last_spike_time: float = -1.0
    adaptation: float = 0.0


@dataclass
class Synapse:
    """Synaptic Connection"""
    synapse_id: str
    source_neuron: str
    target_neuron: str
    weight: float
    delay_ms: float
    synapse_type: SynapseType
    plastic: bool = True
    last_update: float = 0.0


@dataclass
class NeuralLayer:
    """Neural Network Layer"""
    layer_id: str
    layer_type: str  # input, hidden, output
    neurons: Dict[str, NeuronState] = field(default_factory=dict)
    synapses: List[Synapse] = field(default_factory=list)
    size: int = 0


@dataclass
class SpikingNetwork:
    """Spiking Neural Network"""
    network_id: str
    layers: Dict[str, NeuralLayer] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)


class LeakyIntegrateFireNeuron:
    """
    Leaky Integrate-and-Fire Neuron
    =================================

    Simplified LIF neuron model.
    """

    def __init__(
        self,
        neuron_id: str,
        tau_mem: float = 20.0,      # Membrane time constant (ms)
        v_reset: float = -75.0,     # Reset potential (mV)
        v_thresh: float = -50.0,     # Threshold potential (mV)
        v_rest: float = -70.0,       # Resting potential (mV)
        r_mem: float = 10.0         # Membrane resistance (MOhm)
    ):
        self.neuron_id = neuron_id
        self.tau_mem = tau_mem
        self.v_reset = v_reset
        self.v_thresh = v_thresh
        self.v_rest = v_rest
        self.r_mem = r_mem
        self.v_membrane = v_rest
        self.last_spike = -1.0
        self.refractory_time = 2.0  # ms

    def update(self, current_input: float, dt: float) -> Optional[Spike]:
        """Update neuron state"""
        # Leaky integration
        dv = (-(self.v_membrane - self.v_rest) + self.r_mem * current_input) * (dt / self.tau_mem)
        self.v_membrane += dv

        # Check for spike
        if self.v_membrane >= self.v_thresh and (datetime.now().timestamp() * 1000 - self.last_spike) > self.refractory_time:
            spike = Spike(
                timestamp=datetime.now().timestamp() * 1000,
                neuron_id=self.neuron_id,
                layer="layer1",
                amplitude=self.v_membrane
            )
            self.v_membrane = self.v_reset
            self.last_spike = datetime.now().timestamp() * 1000
            return spike

        return None


class IzhikevichNeuron:
    """
    Izhikevich Neuron Model
    =======================

    More biologically realistic neuron model.
    """

    def __init__(self, neuron_id: str, neuron_type: str = "regular_spiking"):
        self.neuron_id = neuron_id
        self.neuron_type = neuron_type

        # Parameters for different neuron types
        self.params = {
            "regular_spiking": {"a": 0.02, "b": 0.2, "c": -65, "d": 8},
            "fast_spiking": {"a": 0.1, "c": -65, "d": 2},
            "chattering": {"a": 0.02, "b": 0.2, "c": -50, "d": 2},
            "low_threshold": {"a": 0.02, "b": 0.25, "c": -65, "d": 2},
        }.get(neuron_type, {"a": 0.02, "b": 0.2, "c": -65, "d": 8})

        self.v = -65  # Membrane potential
        self.u = self.params["b"] * self.v  # Recovery variable
        self.last_spike = -100.0

    def update(self, current_input: float, dt: float) -> Optional[Spike]:
        """Update Izhikevich neuron"""
        a = self.params.get("a", 0.02)
        b = self.params.get("b", 0.2)
        c = self.params.get("c", -65)
        d = self.params.get("d", 8)

        # Update membrane potential
        self.v += 0.04 * self.v * dt + 5 * self.v - self.u * dt + 30 + current_input * dt

        # Update recovery variable
        self.u += a * (b * self.v - self.u) * dt

        # Check for spike
        if self.v >= 30:
            spike = Spike(
                timestamp=datetime.now().timestamp() * 1000,
                neuron_id=self.neuron_id,
                layer="izhikevich",
                amplitude=30
            )
            self.v = c
            self.u += d
            self.last_spike = datetime.now().timestamp() * 1000
            return spike

        return None


class AdaptiveExponentialNeuron:
    """
    Adaptive Exponential Integrate-and-Fire
    ========================================

    AdEx neuron model with spike-frequency adaptation.
    """

    def __init__(self, neuron_id: str):
        self.neuron_id = neuron_id
        self.v = -70.0
        self.w = 0.0  # Adaptation variable
        self.delta_t = 2.0  # Slope factor
        self.a = 0.001  # Adaptation parameter
        self.tau_w = 100.0
        self.b = 7.0  # Spike-triggered adaptation
        self.v_thresh = -50.0
        self.v_reset = -60.0

    def update(self, current_input: float, dt: float) -> Optional[Spike]:
        """Update AdEx neuron"""
        # Update adaptation
        self.w += self.a * (self.a * (self.v + 60) - self.w) * dt / self.tau_w

        # Update membrane potential
        if self.v < self.v_thresh:
            self.v += (-(self.v + 60) + self.delta_t * math.exp((self.v - self.v_thresh) / self.delta_t) + self.w + current_input) * dt / 10.0
        else:
            self.v = self.v_reset
            self.w += self.b

        if self.v >= self.v_thresh:
            return Spike(
                timestamp=datetime.now().timestamp() * 1000,
                neuron_id=self.neuron_id,
                layer="adex",
                amplitude=self.v
            )

        return None


class SpikeTimingDependentPlasticity:
    """
    STDP Learning Rule
    ==================

    Spike Timing Dependent Plasticity for learning.
    """

    def __init__(self):
        self.tau_plus = 20.0   # Time constant for LTP
        self.tau_minus = 20.0  # Time constant for LTD
        self.a_plus = 0.01    # Learning rate for LTP
        self.a_minus = 0.012   # Learning rate for LTD

    def update_weight(
        self,
        synapse: Synapse,
        pre_spike_time: float,
        post_spike_time: float
    ) -> float:
        """Update synaptic weight based on spike timing"""
        delta_t = post_spike_time - pre_spike_time

        if delta_t > 0:
            # Pre before post: LTP (strengthen)
            delta_w = self.a_plus * math.exp(-delta_t / self.tau_plus)
        else:
            # Post before pre: LTD (weaken)
            delta_w = -self.a_minus * math.exp(delta_t / self.tau_minus)

        # Update weight
        synapse.weight += delta_w

        # Clamp weight
        synapse.weight = max(0.0, min(1.0, synapse.weight))
        synapse.last_update = datetime.now().timestamp() * 1000

        return synapse.weight


class ReservoirComputing:
    """
    Liquid State Machine / Reservoir Computing
    ============================================

    Echo state network for temporal pattern processing.
    """

    def __init__(self, reservoir_size: int = 100):
        self.reservoir_size = reservoir_size
        self.neurons = {}
        self.synapses = []
        self.input_weights = {}
        self.output_weights = {}
        self.firing_history = []
        self.spectral_radius = 0.9

        self._initialize_reservoir()

    def _initialize_reservoir(self):
        """Initialize reservoir network"""
        # Create neurons
        for i in range(self.reservoir_size):
            neuron_id = f"reservoir_{i}"
            self.neurons[neuron_id] = {
                "state": random.uniform(-0.1, 0.1),
                "threshold": 0.5,
                "firing_rate": 0.0
            }

        # Create random connections (sparse)
        connectivity = 0.1
        for i in range(self.reservoir_size):
            for j in range(self.reservoir_size):
                if random.random() < connectivity and i != j:
                    synapse = Synapse(
                        synapse_id=str(uuid.uuid4()),
                        source_neuron=f"reservoir_{i}",
                        target_neuron=f"reservoir_{j}",
                        weight=random.uniform(-1, 1),
                        delay_ms=random.uniform(0.5, 3.0),
                        synapse_type=SynapseType.CHEMICAL
                    )
                    self.synapses.append(synapse)

        # Input weights
        for i in range(min(10, self.reservoir_size)):
            self.input_weights[f"input_{i}"] = random.uniform(-1, 1)

    def process_input(self, input_data: List[float], steps: int = 10) -> List[float]:
        """Process input through reservoir"""
        reservoir_state = []

        for step in range(steps):
            # Inject input
            for i, weight in self.input_weights.items():
                idx = int(i.split("_")[1])
                if idx < len(input_data):
                    self.neurons[f"reservoir_{idx}"]["state"] += weight * input_data[idx]

            # Update reservoir dynamics
            new_states = {}
            for neuron_id, neuron in self.neurons.items():
                # Sum inputs from connected neurons
                total_input = 0
                for synapse in self.synapses:
                    if synapse.target_neuron == neuron_id:
                        pre_neuron = self.neurons.get(synapse.source_neuron)
                        if pre_neuron:
                            total_input += synapse.weight * pre_neuron["state"]

                # Apply activation
                new_state = neuron["state"] * self.spectral_radius + total_input
                new_state = math.tanh(new_state)  # Bounded activation
                new_states[neuron_id] = new_state

            self.neurons.update(new_states)

            # Record state
            if step % 2 == 0:
                state_vector = [n["state"] for n in self.neurons.values()]
                reservoir_state.append(state_vector)

        return reservoir_state


class NeuromorphicProcessor:
    """
    Neuromorphic Processor Emulator
    ================================

    Simulates neuromorphic hardware behavior.
    """

    def __init__(self):
        self.neurons: Dict[str, Any] = {}
        self.spikes: List[Spike] = []
        self.event_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.lif_neurons: Dict[str, LeakyIntegrateFireNeuron] = {}
        self.izhikevich_neurons: Dict[str, IzhikevichNeuron] = {}
        self.adex_neurons: Dict[str, AdaptiveExponentialNeuron] = {}
        self.stdp = SpikeTimingDependentPlasticity()

    def create_neuron(
        self,
        neuron_id: str,
        neuron_type: NeuronType = NeuronType.LIF
    ) -> str:
        """Create neuron of specified type"""
        if neuron_type == NeuronType.LIF:
            self.lif_neurons[neuron_id] = LeakyIntegrateFireNeuron(neuron_id)
        elif neuron_type == NeuronType.IZHIKEVICH:
            self.izhikevich_neurons[neuron_id] = IzhikevichNeuron(neuron_id)
        elif neuron_type == NeuronType.ADEX:
            self.adex_neurons[neuron_id] = AdaptiveExponentialNeuron(neuron_id)

        self.neurons[neuron_id] = {
            "type": neuron_type,
            "spike_count": 0,
            "last_activity": 0
        }

        print(f"[Neuromorphic] Created {neuron_type.value} neuron: {neuron_id}")
        return neuron_id

    async def simulate(
        self,
        duration_ms: float,
        input_current: Dict[str, float]
    ) -> List[Spike]:
        """Simulate neuromorphic processing"""
        dt = 1.0  # Time step in ms
        all_spikes = []

        for t in range(int(duration_ms / dt)):
            # Update LIF neurons
            for neuron_id, neuron in self.lif_neurons.items():
                current = input_current.get(neuron_id, 0.0)
                spike = neuron.update(current, dt)
                if spike:
                    all_spikes.append(spike)
                    self.neurons[neuron_id]["spike_count"] += 1

            # Update Izhikevich neurons
            for neuron_id, neuron in self.izhikevich_neurons.items():
                current = input_current.get(neuron_id, 0.0)
                spike = neuron.update(current, dt)
                if spike:
                    all_spikes.append(spike)
                    self.neurons[neuron_id]["spike_count"] += 1

            # Update AdEx neurons
            for neuron_id, neuron in self.adex_neurons.items():
                current = input_current.get(neuron_id, 0.0)
                spike = neuron.update(current, dt)
                if spike:
                    all_spikes.append(spike)
                    self.neurons[neuron_id]["spike_count"] += 1

            # Small delay for simulation
            if t % 10 == 0:
                await asyncio.sleep(0.001)

        self.spikes.extend(all_spikes)
        return all_spikes

    def get_firing_rates(self) -> Dict[str, float]:
        """Calculate firing rates for neurons"""
        rates = {}
        total_time = 100.0  # ms
        for neuron_id, info in self.neurons.items():
            rates[neuron_id] = info["spike_count"] / (total_time / 1000.0)
        return rates

    def get_raster_plot(self) -> List[Tuple[float, str]]:
        """Get spike raster data"""
        return [(s.timestamp, s.neuron_id) for s in self.spikes]


class NeuromorphicAgent:
    """
    Neuromorphic Agent
    ==================

    Agent that uses neuromorphic computing for processing.
    """

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.processor = NeuromorphicProcessor()
        self.reservoir = ReservoirComputing()
        self.behavior_state = "idle"

    async def process_sensory_input(self, input_data: List[float]) -> Dict[str, Any]:
        """Process sensory input through neuromorphic system"""
        # Use reservoir for temporal processing
        reservoir_output = self.reservoir.process_input(input_data, steps=20)

        # Convert to input currents
        input_current = {}
        for i in range(min(10, len(reservoir_output[-1]))):
            input_current[f"neuron_{i}"] = reservoir_output[-1][i] * 10

        # Simulate spike generation
        spikes = await self.processor.simulate(100.0, input_current)

        # Get firing rates
        firing_rates = self.processor.get_firing_rates()

        return {
            "reservoir_output": reservoir_output,
            "spikes_generated": len(spikes),
            "firing_rates": firing_rates,
            "output": reservoir_output[-1][:5] if reservoir_output else []
        }

    async def learn_pattern(self, pattern: List[float]):
        """Learn temporal pattern using STDP"""
        # Process pattern
        reservoir_output = self.reservoir.process_input(pattern, steps=30)

        # Apply STDP to synapses
        for synapse in self.reservoir.synapses:
            if synapse.plastic:
                pre_time = datetime.now().timestamp() * 1000 - random.uniform(0, 20)
                post_time = datetime.now().timestamp() * 1000
                self.processor.stdp.update_weight(synapse, pre_time, post_time)

        print(f"[NeuromorphicAgent] Learned pattern, {len(self.reservoir.synapses)} synapses updated")

    def get_neuromorphic_stats(self) -> Dict[str, Any]:
        """Get neuromorphic processing statistics"""
        return {
            "neurons": len(self.processor.neurons),
            "spikes": len(self.processor.spikes),
            "reservoir_size": self.reservoir.reservoir_size,
            "reservoir_synapses": len(self.reservoir.synapses),
            "state": self.behavior_state
        }


async def main():
    """Demonstrate Neuromorphic Computing Integration"""
    print("=" * 60)
    print("Neuromorphic Computing Integration - Day 93")
    print("=" * 60)

    # Create neuromorphic agent
    agent = NeuromorphicAgent("neuromorphic-agent-001")

    # Create neurons
    print("\n[1] Neuron Creation")
    print("-" * 40)

    for i in range(5):
        agent.processor.create_neuron(f"lif_neuron_{i}", NeuronType.LIF)

    for i in range(3):
        agent.processor.create_neuron(f"izh_neuron_{i}", NeuronType.IZHIKEVICH)

    for i in range(2):
        agent.processor.create_neuron(f"adex_neuron_{i}", NeuronType.ADEX)

    # Process sensory input
    print("\n[2] Sensory Processing")
    print("-" * 40)

    sensory_input = [random.uniform(-1, 1) for _ in range(10)]
    result = await agent.process_sensory_input(sensory_input)

    print(f"  Input data: {sensory_input[:5]}...")
    print(f"  Spikes generated: {result['spikes_generated']}")
    print(f"  Output: {result['output']}")

    # Learning
    print("\n[3] STDP Learning")
    print("-" * 40)

    for i in range(3):
        pattern = [random.uniform(-1, 1) for _ in range(10)]
        await agent.learn_pattern(pattern)

    # Firing rates
    print("\n[4] Firing Rates")
    print("-" * 40)

    firing_rates = agent.processor.get_firing_rates()
    for neuron_id, rate in list(firing_rates.items())[:5]:
        print(f"  {neuron_id}: {rate:.2f} Hz")

    # Reservoir computing
    print("\n[5] Reservoir Computing")
    print("-" * 40)

    reservoir = ReservoirComputing(reservoir_size=50)
    input_data = [1.0, 0.5, -0.5, -1.0, 0.0]
    output = reservoir.process_input(input_data, steps=15)

    print(f"  Input: {input_data}")
    print(f"  Reservoir states: {len(output)}")
    print(f"  Final state: {output[-1][:5]}...")

    # Statistics
    print("\n[6] Neuromorphic Statistics")
    print("-" * 40)

    stats = agent.get_neuromorphic_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Spike raster
    print("\n[7] Spike Events")
    print("-" * 40)

    raster = agent.processor.get_raster_plot()
    print(f"  Total spike events: {len(raster)}")
    if raster:
        print(f"  First spike: {raster[0][1]} at {raster[0][0]:.2f}ms")

    print("\n" + "=" * 60)
    print("Neuromorphic Computing Integration complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())