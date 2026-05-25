/**
 * Chain of Thought Reasoning Engine
 * Provides advanced reasoning capabilities for agents
 */

class ChainOfThoughtReasoning {
  constructor() {
    this.reasoningChains = new Map();
    this.thoughtCache = new Map();
  }

  // Create a new reasoning chain for an agent task
  createChain(agentId, problem, maxDepth = 5) {
    const chainId = `cot_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const chain = {
      id: chainId,
      agentId,
      problem,
      depth: 0,
      maxDepth,
      thoughts: [],
      currentStep: 'decompose',
      status: 'thinking',
      startedAt: new Date().toISOString(),
      branches: [],
      selectedBranch: null
    };
    this.reasoningChains.set(chainId, chain);
    return chain;
  }

  // Add a thought to the chain
  addThought(chainId, thought, reasoning = '', confidence = 0.8) {
    const chain = this.reasoningChains.get(chainId);
    if (!chain) return null;

    const thoughtEntry = {
      id: `thought_${chain.thoughts.length + 1}`,
      thought,
      reasoning,
      confidence,
      timestamp: new Date().toISOString(),
      children: [],
      parentId: chain.thoughts.length > 0 ? chain.thoughts[chain.thoughts.length - 1].id : null
    };

    chain.thoughts.push(thoughtEntry);
    chain.depth = chain.thoughts.length;

    // Add to parent's children
    if (thoughtEntry.parentId) {
      const parent = chain.thoughts.find(t => t.id === thoughtEntry.parentId);
      if (parent) parent.children.push(thoughtEntry.id);
    }

    return thoughtEntry;
  }

  // Create a branch in reasoning (for exploring alternatives)
  createBranch(chainId, fromThoughtId, alternativeReasoning) {
    const chain = this.reasoningChains.get(chainId);
    if (!chain) return null;

    const branch = {
      id: `branch_${chain.branches.length + 1}`,
      fromThoughtId,
      reasoning: alternativeReasoning,
      thoughts: [],
      createdAt: new Date().toISOString()
    };

    chain.branches.push(branch);
    return branch;
  }

  // Select a branch to continue
  selectBranch(chainId, branchId) {
    const chain = this.reasoningChains.get(chainId);
    if (!chain) return false;

    const branch = chain.branches.find(b => b.id === branchId);
    if (!branch) return false;

    chain.selectedBranch = branchId;
    return true;
  }

  // Evaluate the chain and reach a conclusion
  conclude(chainId, conclusion, justification = '') {
    const chain = this.reasoningChains.get(chainId);
    if (!chain) return null;

    chain.conclusion = conclusion;
    chain.justification = justification;
    chain.status = 'concluded';
    chain.completedAt = new Date().toISOString();

    // Cache the thought pattern for future use
    this.thoughtCache.set(chain.problem.substring(0, 50), {
      conclusion,
      confidence: this.calculateConfidence(chain)
    });

    return chain;
  }

  // Calculate overall confidence based on thought confidences
  calculateConfidence(chain) {
    if (chain.thoughts.length === 0) return 0;
    const sum = chain.thoughts.reduce((acc, t) => acc + t.confidence, 0);
    return sum / chain.thoughts.length;
  }

  // Get chain status
  getChain(chainId) {
    return this.reasoningChains.get(chainId) || null;
  }

  // Get all chains for an agent
  getAgentChains(agentId) {
    return [...this.reasoningChains.values()].filter(c => c.agentId === agentId);
  }

  // Delete a chain
  deleteChain(chainId) {
    return this.reasoningChains.delete(chainId);
  }

  // Get cached thought pattern
  getCachedPattern(problem) {
    return this.thoughtCache.get(problem.substring(0, 50));
  }

  // Step-by-step reasoning
  step(chainId) {
    const chain = this.reasoningChains.get(chainId);
    if (!chain || chain.status === 'concluded') return null;

    const steps = ['decompose', 'analyze', 'synthesize', 'evaluate', 'conclude'];
    const currentIndex = steps.indexOf(chain.currentStep);

    if (currentIndex < steps.length - 1) {
      chain.currentStep = steps[currentIndex + 1];
    }

    return { step: chain.currentStep, depth: chain.depth };
  }

  // Get reasoning statistics
  getStats() {
    const chains = [...this.reasoningChains.values()];
    return {
      totalChains: chains.length,
      thinking: chains.filter(c => c.status === 'thinking').length,
      concluded: chains.filter(c => c.status === 'concluded').length,
      cachedPatterns: this.thoughtCache.size,
      avgDepth: chains.length > 0
        ? chains.reduce((sum, c) => sum + c.thoughts.length, 0) / chains.length
        : 0
    };
  }
}

module.exports = { ChainOfThoughtReasoning };