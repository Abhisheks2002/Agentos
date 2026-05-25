"""
Day 7: Semantic Router & Intent Classification
=================================================
Skill: Routing LLM requests
Mini Project: Traffic Controller

Routes user input to the correct AgentOS module without using a full LLM call.
Uses embeddings only for efficient routing.
"""

from typing import Dict, List, Callable, Any
import re

class Route:
    """Represents a route in the semantic router"""

    def __init__(self, name: str, description: str, handler: Callable):
        self.name = name
        self.description = description
        self.handler = handler
        self.keywords = self._extract_keywords(description)

    def _extract_keywords(self, text: str) -> set:
        """Extract keywords from description"""
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common words
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'to', 'for', 'in', 'on', 'at', 'is', 'are', 'was', 'were'}
        return {w for w in words if w not in stopwords and len(w) > 2}

    def match_score(self, query: str) -> float:
        """Calculate match score for a query"""
        query_words = set(re.findall(r'\b\w+\b', query.lower()))
        if not query_words:
            return 0.0

        matches = len(query_words & self.keywords)
        return matches / max(len(self.keywords), 1)

class SemanticRouter:
    """Routes requests to appropriate handlers using keyword matching"""

    def __init__(self):
        self.routes: List[Route] = []

    def add_route(self, name: str, description: str, handler: Callable):
        """Add a route to the router"""
        route = Route(name, description, handler)
        self.routes.append(route)

    def route(self, query: str) -> tuple[str, Any]:
        """Route a query to the best matching handler"""
        if not self.routes:
            return "unknown", None

        # Score all routes
        scores = [(route, route.match_score(query)) for route in self.routes]
        scores.sort(key=lambda x: x[1], reverse=True)

        best_route, best_score = scores[0]

        # Threshold for acceptance
        if best_score > 0.1:
            return best_route.name, best_route.handler
        else:
            return "unknown", None

# Define handlers for each route
def handle_identity(args):
    """Handle identity-related requests"""
    return {"module": "identity", "action": "lookup", "response": "Looking up agent identity..."}

def handle_memory(args):
    """Handle memory-related requests"""
    return {"module": "memory", "action": "search", "response": "Searching agent memory..."}

def handle_communication(args):
    """Handle communication requests"""
    return {"module": "communication", "action": "send", "response": "Processing message..."}

def handle_unknown(args):
    """Handle unknown requests"""
    return {"module": "unknown", "action": "none", "response": "I couldn't determine what you need. Try rephrasing."}

# Create the Traffic Controller
def create_traffic_controller() -> SemanticRouter:
    """Create the AgentOS Traffic Controller"""
    router = SemanticRouter()

    # Add routes with descriptions
    router.add_route(
        "identity",
        "Look up agent identity, permissions, roles, or user information",
        handle_identity
    )

    router.add_route(
        "memory",
        "Search memories, retrieve past conversations, or find stored information",
        handle_memory
    )

    router.add_route(
        "communication",
        "Send messages, emails, or notifications to users or other agents",
        handle_communication
    )

    return router

def demo():
    """Demo the Traffic Controller"""
    print("=" * 70)
    print("AgentOS Traffic Controller - Semantic Routing Demo")
    print("=" * 70)

    router = create_traffic_controller()

    test_queries = [
        "Who is this agent and what permissions do they have?",
        "Find my previous conversation about the project",
        "Send a message to the development team",
        "What's the weather like?",
        "Can you check my memory for details about the meeting?",
        "I need to email the user about the update",
    ]

    for query in test_queries:
        route_name, handler = router.route(query)
        print(f"\nQuery: {query}")
        print(f"Route: {route_name}")

        if handler:
            result = handler(None)
            print(f"Response: {result['response']}")
        else:
            print("Response: Could not route to any module")

if __name__ == "__main__":
    demo()