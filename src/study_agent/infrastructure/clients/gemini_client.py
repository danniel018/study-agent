"""Gemini API client for LLM operations."""

import google.generativeai as genai
from typing import List, Dict, Any
import json

from study_agent.config.settings import settings
from study_agent.core.exceptions import LLMServiceError


class GeminiClient:
    """Client for Google Gemini API."""
    
    def __init__(self):
        """Initialize Gemini client."""
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
    
    async def generate_quiz_questions(
        self,
        topic_content: str,
        topic_title: str,
        num_questions: int = 5,
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions from topic content.
        
        Args:
            topic_content: The study material content
            topic_title: Title of the topic
            num_questions: Number of questions to generate
            
        Returns:
            List of question dictionaries with 'question' and 'answer' keys
            
        Raises:
            LLMServiceError: If generation fails
        """
        prompt = f"""You are an expert educator creating quiz questions. 
        
Topic: {topic_title}

Content:
{topic_content}

Generate {num_questions} thoughtful quiz questions that test understanding of this material. 
For each question, provide a clear, correct answer.

Format your response as a JSON array with objects containing "question" and "answer" fields.
Mix question types: some multiple choice, some open-ended.

Example format:
[
  {{"question": "What is X?", "answer": "X is..."}},
  {{"question": "Choose the correct: A) ..., B) ..., C) ...", "answer": "B) ..."}}
]

Return ONLY the JSON array, no other text."""

        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            questions = json.loads(text)
            return questions
        except Exception as e:
            raise LLMServiceError(f"Failed to generate questions: {str(e)}")
    
    async def evaluate_answer(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
        context: str,
    ) -> Dict[str, Any]:
        """Evaluate user's answer using LLM.
        
        Args:
            question: The quiz question
            user_answer: User's answer
            correct_answer: Expected correct answer
            context: Topic context for evaluation
            
        Returns:
            Dictionary with 'score' (0.0-1.0), 'is_correct', and 'feedback'
            
        Raises:
            LLMServiceError: If evaluation fails
        """
        prompt = f"""You are evaluating a student's answer to a quiz question.

Context: {context[:500]}...

Question: {question}
Correct Answer: {correct_answer}
Student's Answer: {user_answer}

Evaluate the student's answer:
1. Give a score from 0.0 to 1.0 (0.0 = completely wrong, 1.0 = perfect)
2. Determine if it's correct (score >= 0.6 is correct)
3. Provide brief, constructive feedback

Be lenient with wording differences if the meaning is correct.

Format your response as JSON:
{{
  "score": 0.0-1.0,
  "is_correct": true/false,
  "feedback": "Brief feedback here"
}}

Return ONLY the JSON object, no other text."""

        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            evaluation = json.loads(text)
            return evaluation
        except Exception as e:
            raise LLMServiceError(f"Failed to evaluate answer: {str(e)}")
