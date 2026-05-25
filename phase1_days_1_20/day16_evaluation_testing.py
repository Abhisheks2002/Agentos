"""
Day 16: Evaluation & Testing - Measuring Agent Performance
============================================================
Skill: AI System Evaluation
Mini Project: Agent Quality Assurance Dashboard

Learn to evaluate AI agents using RAGAS metrics and LLM-as-a-Judge
paradigms for robust, measurable agent performance.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import math
import re

# Note: This is a self-contained evaluation framework
# In production, install: pip install ragas


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics"""
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    context_precision: float = 0.0
    context_recall: float = 0.0
    answer_relevancy: float = 0.0
    faithfulness: float = 0.0
    hallucination_score: float = 0.0
    latency_ms: float = 0.0
    tokens_used: int = 0


@dataclass
class TestCase:
    """A test case for agent evaluation"""
    question: str
    expected_answer: str
    context: List[str] = field(default_factory=list)
    ground_truth: Optional[str] = None


class RAGASEvaluator:
    """
    RAGAS (RAG Assessment) Evaluation Framework
    ===========================================

    Measures:
    - Context Precision: How relevant is the retrieved context?
    - Context Recall: How much of the relevant info was retrieved?
    - Answer Relevancy: How relevant is the answer to the question?
    - Faithfulness: Does the answer match the context?
    """

    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []

    def evaluate_context_precision(
        self,
        question: str,
        contexts: List[str],
        answer: str
    ) -> float:
        """
        Context Precision: Measures if relevant chunks are ranked higher

        Higher precision = important info appears first
        """
        if not contexts:
            return 0.0

        # Simple keyword-based relevance scoring
        # In production: use embeddings or LLM for this
        question_keywords = set(question.lower().split())
        relevance_scores = []

        for ctx in contexts:
            ctx_keywords = set(ctx.lower().split())
            # Jaccard similarity
            intersection = question_keywords & ctx_keywords
            score = len(intersection) / len(question_keywords) if question_keywords else 0
            relevance_scores.append(score)

        # Weighted by position (earlier = higher weight)
        weighted_score = sum(
            score * (1.0 / (i + 1))
            for i, score in enumerate(relevance_scores)
        )

        return min(weighted_score * 2, 1.0)  # Normalize

    def evaluate_context_recall(
        self,
        ground_truth: str,
        contexts: List[str]
    ) -> float:
        """
        Context Recall: Measures if relevant info was retrieved

        Compares ground truth against retrieved context
        """
        if not ground_truth or not contexts:
            return 0.0

        gt_keywords = set(ground_truth.lower().split())
        found_keywords = set()

        for ctx in contexts:
            ctx_keywords = set(ctx.lower().split())
            found_keywords |= (gt_keywords & ctx_keywords)

        recall = len(found_keywords) / len(gt_keywords) if gt_keywords else 0.0
        return min(recall, 1.0)

    def evaluate_answer_relevancy(
        self,
        question: str,
        answer: str
    ) -> float:
        """
        Answer Relevancy: How directly does answer address the question?

        Measures semantic similarity between question and answer
        """
        # Simple approach: check question keyword overlap
        q_keywords = set(question.lower().split())
        a_keywords = set(answer.lower().split())

        # Remove common stopwords
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'to',
            'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as'
        }

        q_significant = q_keywords - stopwords
        a_significant = a_keywords - stopwords

        if not q_significant:
            return 0.0

        overlap = len(q_significant & a_significant)
        return min(overlap / len(q_significant), 1.0)

    def evaluate_faithfulness(
        self,
        answer: str,
        contexts: List[str]
    ) -> float:
        """
        Faithfulness: Does the answer stay true to the context?

        Checks if answer claims match provided context
        """
        if not contexts or not answer:
            return 0.0

        # Simple check: extract claims from answer
        # In production: use NER or LLM for claim extraction
        answer_sentences = answer.split('.')
        supported_sentences = 0

        combined_context = ' '.join(contexts).lower()

        for sentence in answer_sentences:
            if not sentence.strip():
                continue
            # Check if key terms exist in context
            sentence_keywords = set(sentence.lower().split())
            context_keywords = set(combined_context.split())
            overlap = len(sentence_keywords & context_keywords)
            if overlap > len(sentence_keywords) * 0.5:
                supported_sentences += 1

        return supported_sentences / len(answer_sentences) if answer_sentences else 0.0

    def run_evaluation(
        self,
        question: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> EvaluationMetrics:
        """Run full RAGAS evaluation suite"""

        metrics = EvaluationMetrics()

        # Compute metrics
        metrics.context_precision = self.evaluate_context_precision(
            question, contexts, answer
        )
        metrics.answer_relevancy = self.evaluate_answer_relevancy(
            question, answer
        )
        metrics.faithfulness = self.evaluate_faithfulness(
            answer, contexts
        )

        if ground_truth:
            metrics.context_recall = self.evaluate_context_recall(
                ground_truth, contexts
            )
            # Calculate F1 from precision and recall
            if metrics.context_precision + metrics.context_recall > 0:
                metrics.f1_score = (
                    2 * metrics.context_precision * metrics.context_recall /
                    (metrics.context_precision + metrics.context_recall)
                )

        # Store result
        self.test_results.append({
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        })

        return metrics


class LLMasJudge:
    """
    LLM-as-a-Judge Evaluation
    ==========================

    Use an LLM to evaluate agent responses on:
    - Helpfulness
    - Harmlessness
    - Honesty
    - Accuracy
    """

    # Evaluation criteria definitions
    CRITERIA = {
        "helpfulness": "Does the response provide useful information?",
        "harmlessness": "Does the response avoid causing harm?",
        "honesty": "Does the response acknowledge uncertainties?",
        "accuracy": "Is the response factually correct?",
        "completeness": "Does the response fully address the question?",
        "clarity": "Is the response clear and well-structured?"
    }

    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        self.judgments: List[Dict[str, Any]] = []

    def evaluate_response(
        self,
        question: str,
        response: str,
        criteria: List[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a response using LLM-as-a-Judge

        In production, this calls the LLM API
        Here we simulate with rule-based scoring
        """
        if criteria is None:
            criteria = ["helpfulness", "harmlessness", "accuracy"]

        scores = {}

        for criterion in criteria:
            score = self._score_criterion(criterion, question, response)
            scores[criterion] = score

        # Overall score is weighted average
        overall = sum(scores.values()) / len(scores) if scores else 0.0

        result = {
            "question": question,
            "response": response,
            "scores": scores,
            "overall_score": overall,
            "verdict": self._get_verdict(overall),
            "model": self.model_name,
            "timestamp": datetime.now().isoformat()
        }

        self.judgments.append(result)
        return result

    def _score_criterion(self, criterion: str, question: str, response: str) -> float:
        """Score a specific criterion (simulated)"""
        response_lower = response.lower()
        question_lower = question.lower()

        if criterion == "helpfulness":
            # Check response length and relevance
            if len(response) < 20:
                return 0.3
            # Check for question keyword overlap
            q_words = set(question_lower.split())
            r_words = set(response_lower.split())
            overlap = len(q_words & r_words) / max(len(q_words), 1)
            return min(0.5 + overlap * 0.5, 1.0)

        elif criterion == "harmlessness":
            # Check for harmful keywords (simplified)
            harmful = ["hack", "attack", "steal", "fraud", "malware"]
            if any(word in response_lower for word in harmful):
                return 0.2
            return 1.0

        elif criterion == "honesty":
            # Check for hedge words indicating uncertainty
            hedges = ["maybe", "perhaps", "might", "possibly", "uncertain"]
            has_hedge = any(word in response_lower for word in hedges)
            # Also check for overconfidence
            overconfident = ["definitely", "certainly", "absolutely", "prove"]
            has_overconfidence = any(word in response_lower for word in overconfident)

            if has_overconfidence and not has_hedge:
                return 0.6
            return 0.8

        elif criterion == "accuracy":
            # Simplified accuracy check
            # In production: verify claims against knowledge base
            if "?" in response:
                return 0.7  # Questions might indicate uncertainty
            return 0.8

        elif criterion == "completeness":
            # Check if response ends abruptly
            if response.rstrip()[-1] not in '.!?':
                return 0.5
            return 0.8

        elif criterion == "clarity":
            # Check for formatting
            has_list = any(c in response for c in ['-', '*', '1.', '•'])
            has_paragraph = '\n\n' in response
            if has_list or has_paragraph:
                return 0.9
            return 0.7

        return 0.5

    def _get_verdict(self, score: float) -> str:
        """Convert score to verdict"""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.7:
            return "Good"
        elif score >= 0.5:
            return "Acceptable"
        elif score >= 0.3:
            return "Needs Improvement"
        else:
            return "Poor"

    def compare_responses(
        self,
        question: str,
        response_a: str,
        response_b: str
    ) -> Dict[str, Any]:
        """Compare two responses and pick a winner"""
        result_a = self.evaluate_response(question, response_a)
        result_b = self.evaluate_response(question, response_b)

        winner = "A" if result_a["overall_score"] > result_b["overall_score"] else "B"

        return {
            "question": question,
            "response_a": response_a,
            "response_b": response_b,
            "score_a": result_a["overall_score"],
            "score_b": result_b["overall_score"],
            "winner": winner,
            "reasoning": f"Response {winner} has higher overall score"
        }


# Demo runner
def run_evaluation_demo():
    """Demonstrate evaluation capabilities"""

    print("=" * 70)
    print("AgentOS Evaluation Framework Demo")
    print("=" * 70)

    # Test RAGAS Evaluator
    print("\n[1] RAGAS Evaluation")
    print("-" * 40)

    evaluator = RAGASEvaluator()

    # Sample test case
    question = "What is AgentOS?"
    contexts = [
        "AgentOS is an AI agent governance platform.",
        "It provides enterprise features for managing AI agents.",
        "AgentOS includes security and monitoring."
    ]
    answer = "AgentOS is a platform for governing and managing AI agents in enterprise settings."
    ground_truth = "AgentOS is an AI agent governance platform with enterprise features."

    metrics = evaluator.run_evaluation(question, answer, contexts, ground_truth)

    print(f"Question: {question}")
    print(f"Answer: {answer}")
    print(f"\nMetrics:")
    print(f"  Context Precision: {metrics.context_precision:.2f}")
    print(f"  Context Recall:    {metrics.context_recall:.2f}")
    print(f"  Answer Relevancy:  {metrics.answer_relevancy:.2f}")
    print(f"  Faithfulness:      {metrics.faithfulness:.2f}")
    print(f"  F1 Score:          {metrics.f1_score:.2f}")

    # Test LLM-as-a-Judge
    print("\n[2] LLM-as-a-Judge Evaluation")
    print("-" * 40)

    judge = LLMasJudge()

    question = "How do I secure my AI agent?"
    response = "To secure your AI agent, implement authentication, use encryption, monitor access logs, and follow security best practices. This is definitely the best approach."

    result = judge.evaluate_response(question, response)

    print(f"Question: {question}")
    print(f"Response: {response}")
    print(f"\nScores:")
    for criterion, score in result["scores"].items():
        print(f"  {criterion}: {score:.2f}")
    print(f"\nOverall: {result['overall_score']:.2f} - {result['verdict']}")

    # Compare responses
    print("\n[3] Response Comparison")
    print("-" * 40)

    comparison = judge.compare_responses(
        "What is RAG?",
        "RAG stands for Retrieval-Augmented Generation, a technique to improve LLM responses.",
        "RAG is a technique."
    )

    print(f"Response A: {comparison['response_a'][:50]}...")
    print(f"Response B: {comparison['response_b']}")
    print(f"Winner: {comparison['winner']} (Score: {comparison[f'score_{comparison['winner'].lower()}']:.2f})")

    print("\n" + "=" * 70)
    print("Evaluation complete!")
    print("=" * 70)


if __name__ == "__main__":
    run_evaluation_demo()