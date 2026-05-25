/**
 * Multi-Agent Coordination System
 * Enables multiple agents to collaborate on tasks
 */

class MultiAgentCoordinator {
  constructor() {
    this.teams = new Map();
    this.collaborations = new Map();
    this.messageQueue = new Map();
    this.agentRoles = new Map();
    this.initDefaultTeams();
  }

  initDefaultTeams() {
    // Create a default collaboration team
    this.createTeam('general', {
      name: 'General Purpose',
      description: 'General purpose agent team',
      maxAgents: 10,
      allowDynamicMembership: true
    });
  }

  // Create a team of agents
  createTeam(teamId, config = {}) {
    const team = {
      id: teamId,
      name: config.name || teamId,
      description: config.description || '',
      agents: [],
      maxAgents: config.maxAgents || 5,
      roles: config.roles || ['coordinator', 'worker', 'observer'],
      allowDynamicMembership: config.allowDynamicMembership || false,
      leaderElection: config.leaderElection || 'first',
      createdAt: new Date().toISOString(),
      status: 'idle',
      tasks: [],
      sharedContext: {}
    };
    this.teams.set(teamId, team);
    return team;
  }

  // Add agent to a team
  addAgentToTeam(teamId, agentId, role = 'worker') {
    const team = this.teams.get(teamId);
    if (!team) return { success: false, error: 'Team not found' };

    if (team.agents.length >= team.maxAgents && !team.agents.includes(agentId)) {
      return { success: false, error: 'Team is full' };
    }

    if (!team.agents.includes(agentId)) {
      team.agents.push(agentId);
    }

    this.agentRoles.set(`${teamId}:${agentId}`, role);

    if (team.agents.length === 1 && team.leaderElection === 'first') {
      this.setTeamLeader(teamId, agentId);
    }

    return { success: true, role };
  }

  // Remove agent from team
  removeAgentFromTeam(teamId, agentId) {
    const team = this.teams.get(teamId);
    if (!team) return { success: false, error: 'Team not found' };

    team.agents = team.agents.filter(a => a !== agentId);
    this.agentRoles.delete(`${teamId}:${agentId}`);

    if (team.leader === agentId && team.agents.length > 0) {
      this.setTeamLeader(teamId, team.agents[0]);
    }

    return { success: true };
  }

  // Set team leader
  setTeamLeader(teamId, agentId) {
    const team = this.teams.get(teamId);
    if (!team) return { success: false, error: 'Team not found' };

    if (!team.agents.includes(agentId)) {
      return { success: false, error: 'Agent not in team' };
    }

    team.leader = agentId;
    this.agentRoles.set(`${teamId}:${agentId}`, 'coordinator');

    return { success: true };
  }

  // Get team info
  getTeam(teamId) {
    return this.teams.get(teamId);
  }

  // Get all teams
  getAllTeams() {
    return [...this.teams.values()];
  }

  // Get agent's teams
  getAgentTeams(agentId) {
    const result = [];
    for (const [teamId, team] of this.teams) {
      if (team.agents.includes(agentId)) {
        result.push({
          teamId,
          name: team.name,
          role: this.agentRoles.get(`${teamId}:${agentId}`)
        });
      }
    }
    return result;
  }

  // Create a collaboration session
  createCollaboration(teamId, task, context = {}) {
    const team = this.teams.get(teamId);
    if (!team) return { error: 'Team not found' };

    const collabId = `collab_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const collaboration = {
      id: collabId,
      teamId,
      task,
      context: { ...team.sharedContext, ...context },
      participants: [...team.agents],
      status: 'initiating',
      phases: [],
      currentPhase: 0,
      results: {},
      messages: [],
      startedAt: new Date().toISOString()
    };

    // Define phases
    collaboration.phases = [
      { name: 'planning', description: 'Analyze task and plan approach', participants: ['coordinator'] },
      { name: 'decomposition', description: 'Break task into subtasks', participants: ['coordinator'] },
      { name: 'execution', description: 'Execute subtasks in parallel', participants: ['worker'] },
      { name: 'integration', description: 'Combine results', participants: ['coordinator', 'worker'] },
      { name: 'verification', description: 'Verify and refine results', participants: ['coordinator'] }
    ];

    this.collaborations.set(collabId, collaboration);
    team.status = 'collaborating';
    team.currentTask = task;

    return collaboration;
  }

  // Get collaboration
  getCollaboration(collabId) {
    return this.collaborations.get(collabId);
  }

  // Advance collaboration to next phase
  advancePhase(collabId, results = {}) {
    const collab = this.collaborations.get(collabId);
    if (!collab) return { error: 'Collaboration not found' };

    if (collab.currentPhase < collab.phases.length - 1) {
      collab.results[collab.phases[collab.currentPhase].name] = results;
      collab.currentPhase++;
      collab.status = collab.phases[collab.currentPhase].name;

      return {
        success: true,
        phase: collab.phases[collab.currentPhase],
        progress: `${collab.currentPhase + 1}/${collab.phases.length}`
      };
    } else {
      collab.status = 'completed';
      collab.results.integration = results;
      collab.completedAt = new Date().toISOString();

      const team = this.teams.get(collab.teamId);
      if (team) team.status = 'idle';

      return { success: true, completed: true };
    }
  }

  // Send message to collaboration participants
  sendMessage(collabId, fromAgentId, message) {
    const collab = this.collaborations.get(collabId);
    if (!collab) return { error: 'Collaboration not found' };

    const msg = {
      id: `msg_${Date.now()}`,
      from: fromAgentId,
      content: message,
      timestamp: new Date().toISOString(),
      readBy: []
    };

    collab.messages.push(msg);

    // Queue message for other agents
    for (const agentId of collab.participants) {
      if (agentId !== fromAgentId) {
        if (!this.messageQueue.has(agentId)) {
          this.messageQueue.set(agentId, []);
        }
        this.messageQueue.get(agentId).push({
          collabId,
          message: msg
        });
      }
    }

    return { success: true, messageId: msg.id };
  }

  // Get messages for an agent
  getMessages(agentId) {
    return this.messageQueue.get(agentId) || [];
  }

  // Clear agent's message queue
  clearMessages(agentId) {
    this.messageQueue.delete(agentId);
    return { success: true };
  }

  // Assign subtask to agent
  assignSubtask(collabId, agentId, subtask) {
    const collab = this.collaborations.get(collabId);
    if (!collab) return { error: 'Collaboration not found' };

    if (!collab.participants.includes(agentId)) {
      return { error: 'Agent not in collaboration' };
    }

    if (!collab.subtasks) collab.subtasks = [];
    const subtaskId = `subtask_${collab.subtasks.length + 1}`;

    collab.subtasks.push({
      id: subtaskId,
      description: subtask,
      assignedTo: agentId,
      status: 'pending',
      result: null
    });

    return { success: true, subtaskId };
  }

  // Complete subtask
  completeSubtask(collabId, subtaskId, result) {
    const collab = this.collaborations.get(collabId);
    if (!collab || !collab.subtasks) return { error: 'Collaboration not found' };

    const subtask = collab.subtasks.find(s => s.id === subtaskId);
    if (!subtask) return { error: 'Subtask not found' };

    subtask.status = 'completed';
    subtask.result = result;
    subtask.completedAt = new Date().toISOString();

    return { success: true };
  }

  // Get team statistics
  getTeamStats(teamId) {
    const team = this.teams.get(teamId);
    if (!team) return null;

    const collabs = [...this.collaborations.values()].filter(c => c.teamId === teamId);

    return {
      teamId,
      name: team.name,
      agentCount: team.agents.length,
      maxAgents: team.maxAgents,
      status: team.status,
      totalCollaborations: collabs.length,
      completedCollaborations: collabs.filter(c => c.status === 'completed').length,
      activeCollaborations: collabs.filter(c => c.status !== 'completed').length
    };
  }

  // Delete team
  deleteTeam(teamId) {
    const team = this.teams.get(teamId);
    if (!team) return { error: 'Team not found' };

    // Remove all agents from team
    for (const agentId of team.agents) {
      this.agentRoles.delete(`${teamId}:${agentId}`);
    }

    this.teams.delete(teamId);
    return { success: true };
  }
}

module.exports = { MultiAgentCoordinator };