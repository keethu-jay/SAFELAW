# This file is a variant of the original GP-TSM algorithm that runs faster, and is designed for 
# applications that require a high level of responsiveness or interactivity. It 
# achieves higher speed by using smaller values for N and MAX_DEPTH and removing
# grammaticality from evaluation, which is a time-consuming metric to compute. However,
# this may mean that the key grammar-preserving feature can be violated at times. To
# achieve the best output quality, please use the original version in llm.py. 

try:
    from openai import OpenAI
    OPENAI_NEW_API = True
except ImportError:
    import openai
    OPENAI_NEW_API = False

from typing import List, Dict, Any
import time

MAX_DEPTH = 3 # The 'max depth', or number of successive times we'll try to shorten
# semantic score compare with the ORIGINAL paragraph (minimum 1 round; with additional rounds conditioned on score >= threshold)

TEMPERATURE = 0.8 # The temperature for ChatGPT calls

N = 3 # The number of responses to request from ChatGPT, for *each* query 

# framing of paper: focus on forgrounding how AI can hallucinate, especially summarization leading to misinformation. Because of that,
# we design a purely extractive system  "AI-resilient interface design" help humans notice, recover
# strike editing, redo GRE and open-ended reading; in future work, we mention editing and reading questions
EXTRACTIVE_SHORTENER_PROMPT_TEMPLATE = \
"""For each sentence in the following paragraph, delete phrases that are not the main subject, verb, or object of the sentence, or key modifiers/ terms. The length of the result should be at least 80 percent of the original length. Important: Please make sure the result remains grammatical!!

"{paragraph}"

Please do not add any new words or change words, only delete words."""

# Helper functions
def strip_wrapping_quotes(s: str) -> str:
    if not s:
        return s
    if s[0] == '"': 
        s = s[1:]
    if s and s[-1] == '"': 
        s = s[0:-1]
    return s

def evaluate_on_meaning(original: str, shortened: str) -> float:
    """Simplified semantic similarity evaluation"""
    # This is a placeholder - in the full version, this would use embeddings
    # For now, we'll use a simple word overlap metric
    original_words = set(original.lower().split())
    shortened_words = set(shortened.lower().split())
    if not original_words:
        return 0.0
    overlap = len(original_words & shortened_words) / len(original_words)
    return overlap

def evaluate_on_paraphrasing(original: str, shortened: str) -> float:
    """Simplified paraphrasing evaluation"""
    # Placeholder - would use more sophisticated metrics in full version
    if len(shortened) == 0:
        return 0.0
    length_ratio = len(shortened) / len(original) if len(original) > 0 else 0.0
    # Prefer summaries that are 80-90% of original length
    if 0.8 <= length_ratio <= 0.9:
        return 1.0
    elif length_ratio < 0.8:
        return length_ratio / 0.8
    else:
        return max(0, 1.0 - (length_ratio - 0.9) * 10)

def evaluate_on_length(original: str, shortened: str) -> float:
    """Evaluate based on length reduction"""
    if len(original) == 0:
        return 0.0
    reduction = 1 - (len(shortened) / len(original))
    # Prefer 10-20% reduction
    if 0.1 <= reduction <= 0.2:
        return 1.0
    elif reduction < 0.1:
        return reduction / 0.1
    else:
        return max(0, 1.0 - (reduction - 0.2) * 5)

def revert_paraphrasing(original: str, shortened: str) -> str:
    """Revert paraphrasing by aligning shortened text with original"""
    # Simplified version - in full implementation, this would do more sophisticated alignment
    # For now, return the shortened version as-is
    return shortened

def get_shortened_paragraph(orig_paragraph: str, api_key: str) -> List[str]:
    """
    Main function to shorten a paragraph using GP-TSM lite algorithm.
    Returns a list of shortened versions at each depth level.
    """
    print(f"[GPTSM] Starting summarization with text length: {len(orig_paragraph)}")
    
    if OPENAI_NEW_API:
        client = OpenAI(api_key=api_key)
    else:
        openai.api_key = api_key
    
    cur_depth = 0
    best_responses = [orig_paragraph]
    paragraph = orig_paragraph
    
    while cur_depth < MAX_DEPTH:
        responses = []
        
        try:
            # Generate N responses from ChatGPT
            print(f"[GPTSM] Depth {cur_depth}: Generating {N} responses from OpenAI...")
            for i in range(N):
                try:
                    if OPENAI_NEW_API:
                        response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are a helpful assistant that extracts key information from text while preserving grammar."
                                },
                                {
                                    "role": "user",
                                    "content": EXTRACTIVE_SHORTENER_PROMPT_TEMPLATE.format(paragraph=paragraph)
                                }
                            ],
                            temperature=TEMPERATURE,
                            max_tokens=2000
                        )
                        text_response = response.choices[0].message.content.strip()
                    else:
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are a helpful assistant that extracts key information from text while preserving grammar."
                                },
                                {
                                    "role": "user",
                                    "content": EXTRACTIVE_SHORTENER_PROMPT_TEMPLATE.format(paragraph=paragraph)
                                }
                            ],
                            temperature=TEMPERATURE,
                            max_tokens=2000
                        )
                        text_response = response.choices[0].message.content.strip()
                    
                    print(f"[GPTSM] Response {i+1}: Generated {len(text_response)} chars (original: {len(paragraph)} chars)")
                    responses.append(strip_wrapping_quotes(text_response))
                except Exception as inner_error:
                    print(f"[GPTSM] Error on response {i+1}: {inner_error}")
                    raise
        except Exception as e:
            print(f"[GPTSM] Error calling OpenAI API: {e}")
            # If API call fails, return what we have so far
            break
        
        if not responses:
            break
            
        response_infos = []
        for response in responses:
            reverted = revert_paraphrasing(paragraph, response)
            semantic_score = evaluate_on_meaning(orig_paragraph, reverted)
            paraphrase_score = evaluate_on_paraphrasing(paragraph, response)
            length_score = evaluate_on_length(paragraph, reverted)
            
            response_infos.append({
                "response": response,
                "reverted": reverted,
                "semantic_score": semantic_score,
                "paraphrase_score": paraphrase_score,
                "length_score": length_score,
                "composite_score": semantic_score + paraphrase_score + length_score
            })
        
        response_infos.sort(key=lambda x: x["composite_score"], reverse=True)
        
        if not response_infos:
            break
            
        best_response = response_infos[0]
        cur_depth += 1
        best_responses.append(best_response['reverted'])
        paragraph = best_response["reverted"]
        
        # Early stopping if no significant improvement
        if best_response['composite_score'] < 1.5:
            break
    
    return best_responses

def summarize_text(text: str, api_key: str) -> Dict[str, Any]:
    """
    Summarize text using GP-TSM lite and return the best result.
    Returns a dictionary with the summarization and metadata.
    """
    start_time = time.time()
    shortened_versions = get_shortened_paragraph(text, api_key)
    
    if not shortened_versions:
        return {
            "summarization": text,
            "original_length": len(text),
            "summarized_length": len(text),
            "processing_time": time.time() - start_time,
            "error": "Failed to generate summarization"
        }
    
    # Return the best (last) shortened version
    best_summary = shortened_versions[-1]
    
    return {
        "summarization": best_summary,
        "original_length": len(text),
        "summarized_length": len(best_summary),
        "processing_time": time.time() - start_time,
        "all_versions": shortened_versions
    }

