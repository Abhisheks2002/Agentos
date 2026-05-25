"""
Day 22: LangChain Components - LCEL & Chains
============================================
Skill: LangChain Expression Language
Mini Project: Composable Chain Builder

LangChain Expression Language (LCEL) provides declarative
composition of chains.
"""

from typing import List, Dict, Any, Callable, Union
from dataclasses import dataclass
from datetime import datetime
import asyncio


class Runnable:
    """Base Runnable class - interface for LCEL"""

    def invoke(self, input_data: Any) -> Any:
        """Synchronous invoke"""
        raise NotImplementedError

    async def ainvoke(self, input_data: Any) -> Any:
        """Async invoke"""
        return self.invoke(input_data)

    def __or__(self, other: 'Runnable') -> 'RunnableSequence':
        """Compose with | operator"""
        return RunnableSequence(self, other)


class Lambda(Runnable):
    """Simple lambda function as Runnable"""

    def __init__(self, func: Callable):
        self.func = func

    def invoke(self, input_data: Any) -> Any:
        return self.func(input_data)


class RunnableSequence(Runnable):
    """Sequence of Runnables"""

    def __init__(self, *runnables):
        self.runnables = runnables

    def invoke(self, input_data: Any) -> Any:
        result = input_data
        for runnable in self.runnables:
            result = runnable.invoke(result)
        return result

    async def ainvoke(self, input_data: Any) -> Any:
        result = input_data
        for runnable in self.runnables:
            if asyncio.iscoroutinefunction(runnable.invoke):
                result = await runnable.ainvoke(result)
            else:
                result = runnable.invoke(result)
        return result


class Chain(Runnable):
    """
    Chain - Base chain implementation
    ===================================
    """

    def __init__(self, steps: List[Runnable]):
        self.steps = steps

    def invoke(self, input_data: Any) -> Any:
        current = input_data

        for step in self.steps:
            if isinstance(current, dict):
                current = step.invoke(current)
            else:
                current = step.invoke({"input": current})["output"]

        return current


class Transform(Runnable):
    """
    Transform Chain - Transform input to output
    =============================================
    """

    def __init__(self, func: Callable[[Any], Any]):
        self.func = func

    def invoke(self, input_data: Any) -> Any:
        return self.func(input_data)


class RouteChain(Runnable):
    """
    Route Chain - Route to different chains based on input
    =========================================================
    """

    def __init__(self, routes: Dict[str, Runnable], default: Runnable = None):
        self.routes = routes
        self.default = default

    def invoke(self, input_data: Any) -> Any:
        # Determine route
        key = self._get_route_key(input_data)

        if key in self.routes:
            return self.routes[key].invoke(input_data)
        elif self.default:
            return self.default.invoke(input_data)

        return {"error": "No route found"}

    def _get_route_key(self, input_data: Any) -> str:
        """Determine which route to use"""
        if isinstance(input_data, dict):
            return input_data.get("route", "default")
        return "default"


class BranchChain(Runnable):
    """
    Branch Chain - Run different chains based on condition
    ========================================================
    """

    def __init__(self, condition: Callable[[Any], bool], if_true: Runnable, if_false: Runnable):
        self.condition = condition
        self.if_true = if_true
        self.if_false = if_false

    def invoke(self, input_data: Any) -> Any:
        if self.condition(input_data):
            return self.if_true.invoke(input_data)
        return self.if_false.invoke(input_data)


class MapChain(Runnable):
    """
    Map Chain - Apply chain to each item in list
    =============================================
    """

    def __init__(self, chain: Runnable):
        self.chain = chain

    def invoke(self, input_data: List[Any]) -> List[Any]:
        return [self.chain.invoke(item) for item in input_data]


class ReduceChain(Runnable):
    """
    Reduce Chain - Combine items using a chain
    ============================================
    """

    def __init__(self, chain: Runnable):
        self.chain = chain

    def invoke(self, input_data: List[Any]) -> Any:
        if not input_data:
            return None

        result = input_data[0]
        for item in input_data[1:]:
            result = self.chain.invoke({"prev": result, "current": item})

        return result


class FallbackChain(Runnable):
    """
    Fallback Chain - Try primary, fallback on error
    =================================================
    """

    def __init__(self, primary: Runnable, fallback: Runnable):
        self.primary = primary
        self.fallback = fallback

    def invoke(self, input_data: Any) -> Any:
        try:
            return self.primary.invoke(input_data)
        except Exception as e:
            return self.fallback.invoke(input_data)


# Demo
def run_demo():
    print("=" * 70)
    print("LangChain LCEL & Chains Demo")
    print("=" * 70)

    # Simple lambda chain
    print("\n[1] Lambda Chain")
    print("-" * 40)

    chain = (
        Lambda(lambda x: x.upper())
        | Lambda(lambda x: x + "!")
        | Lambda(lambda x: {"result": x})
    )

    result = chain.invoke("hello")
    print(f"Input: 'hello'")
    print(f"Output: {result}")

    # Transform chain
    print("\n[2] Transform Chain")
    print("-" * 40)

    transform = Transform(lambda x: [i for i in x if i % 2 == 0])
    result = transform.invoke([1, 2, 3, 4, 5, 6])
    print(f"Input: [1,2,3,4,5,6]")
    print(f"Output (evens): {result}")

    # Route chain
    print("\n[3] Route Chain")
    print("-" * 40)

    upper_route = Lambda(lambda x: x.upper())
    lower_route = Lambda(lambda x: x.lower())

    router = RouteChain(
        routes={"upper": upper_route, "lower": lower_route},
        default=lower_route
    )

    result = router.invoke({"route": "upper", "input": "Hello"})
    print(f"Route 'upper': {result}")

    result = router.invoke({"route": "lower", "input": "Hello"})
    print(f"Route 'lower': {result}")

    # Branch chain
    print("\n[4] Branch Chain")
    print("-" * 40)

    is_even = lambda x: x % 2 == 0
    double = Lambda(lambda x: x * 2)
    triple = Lambda(lambda x: x * 3)

    branch = BranchChain(is_even, double, triple)

    result = branch.invoke(4)
    print(f"4 is even: {result}")

    result = branch.invoke(5)
    print(f"5 is odd: {result}")

    # Map chain
    print("\n[5] Map Chain")
    print("-" * 40)

    mapper = MapChain(Lambda(lambda x: x * 2))
    result = mapper.invoke([1, 2, 3, 4])
    print(f"Input: [1,2,3,4]")
    print(f"Output (doubled): {result}")

    # Reduce chain
    print("\n[6] Reduce Chain")
    print("-" * 40)

    combiner = Lambda(lambda x: str(x['prev']) + "+" + str(x['current']))
    reducer = ReduceChain(combiner)

    result = reducer.invoke([1, 2, 3, 4])
    print(f"Input: [1,2,3,4]")
    print(f"Output (combined): {result}")

    # Fallback chain
    print("\n[7] Fallback Chain")
    print("-" * 40)

    primary = Lambda(lambda x: x / 0)  # Will fail
    fallback = Lambda(lambda x: "Fallback: " + str(x))

    safe = FallbackChain(primary, fallback)
    result = safe.invoke("test")
    print(f"Result: {result}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    run_demo()