# backend/models/llm.py
import aiohttp
import asyncio
import logging
import json
from typing import Optional, Dict, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

# Ollama URL
OLLAMA_URL = "http://localhost:11434/api/generate"

async def get_llm_response(prompt: str, diagram_type: str = "flowchart") -> Union[str, Dict[str, Any]]:
    """
    Get a response from the LLM (Ollama) based on the prompt and diagram type.
    
    Args:
        prompt: The user's prompt
        diagram_type: The type of diagram to generate
    
    Returns:
        Either a JSON object (for structured responses) or a string (for text responses)
    """
    # Select the prompt template based on diagram type
    if diagram_type == "flowchart":
        enhanced_prompt = create_flowchart_prompt(prompt)
    elif diagram_type == "process":
        enhanced_prompt = create_process_diagram_prompt(prompt)
    elif diagram_type == "mindmap":
        enhanced_prompt = create_mindmap_prompt(prompt)
    else:
        enhanced_prompt = prompt
    
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "gemma3:1B",  # Using Gemma 3 1B model
                "prompt": enhanced_prompt,
                "stream": False,
                "temperature": 0.5,  # Lower temperature for more structured output
            }
            
            async with session.post(OLLAMA_URL, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error from Ollama: {error_text}")
                    return f"Error communicating with LLM: {response.status}"
                
                result = await response.json()
                llm_response = result.get("response", "No response from LLM")
                
                # Try to parse as JSON if it looks like JSON
                if diagram_type in ["mindmap", "flowchart", "process"] and (
                    llm_response.strip().startswith("{") or llm_response.strip().startswith("[")
                ):
                    try:
                        # Find JSON in the response (sometimes LLMs add explanatory text)
                        json_start = llm_response.find('{')
                        json_end = llm_response.rfind('}') + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = llm_response[json_start:json_end]
                            return json.loads(json_str)
                    except json.JSONDecodeError:
                        logger.warning("Could not parse LLM response as JSON, returning as text")
                
                return llm_response
    
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        return f"Error: {str(e)}"

def create_flowchart_prompt(prompt: str) -> str:
    """Create a prompt for flowchart generation"""
    return f"""
    You are a diagram generation assistant that creates structured flowcharts for TLDraw.
    
    TASK: Generate a flowchart based on this request: "{prompt}"
    
    IMPORTANT: Return your response as a JSON object with the following structure:
    
    {{
        "title": "The main title of the flowchart",
        "description": "A brief description of what this flowchart represents",
        "nodes": [
            {{
                "id": "1",
                "text": "Start",
                "type": "start"
            }},
            {{
                "id": "2",
                "text": "Process Step 1",
                "type": "process"
            }},
            {{
                "id": "3",
                "text": "Decision?",
                "type": "decision"
            }},
            {{
                "id": "4",
                "text": "End",
                "type": "end"
            }}
        ],
        "connections": [
            {{
                "from": "1",
                "to": "2",
                "label": ""
            }},
            {{
                "from": "2",
                "to": "3",
                "label": ""
            }},
            {{
                "from": "3",
                "to": "4",
                "label": "Yes"
            }},
            {{
                "from": "3",
                "to": "2",
                "label": "No"
            }}
        ]
    }}
    
    NODE TYPES:
    - "start": Oval shape representing the start of the flowchart
    - "end": Oval shape representing the end of the flowchart
    - "process": Rectangle shape representing a process or action
    - "decision": Diamond shape representing a decision point (always phrase as a question)
    - "input": Parallelogram shape representing input/output
    
    GUIDELINES:
    1. Use clear, concise text for each node (under 10 words if possible)
    2. Ensure logical flow from start to end
    3. Decisions should always have at least two connections (typically "Yes" and "No")
    4. All nodes must be connected
    5. Make sure all node IDs are unique
    
    ONLY RESPOND WITH THE JSON OBJECT. Do not include any other text or explanation.
    """

def create_process_diagram_prompt(prompt: str) -> str:
    """Create a prompt for process diagram generation"""
    return f"""
    You are a diagram generation assistant that creates structured process diagrams for TLDraw.
    
    TASK: Generate a process diagram based on this request: "{prompt}"
    
    IMPORTANT: Return your response as a JSON object with the following structure:
    
    {{
        "title": "The main title of the process diagram",
        "description": "A brief description of what this process represents",
        "phases": [
            {{
                "name": "Phase 1: Planning",
                "steps": [
                    {{
                        "id": "1.1",
                        "text": "Define Requirements",
                        "type": "process"
                    }},
                    {{
                        "id": "1.2",
                        "text": "Establish Timeline",
                        "type": "process"
                    }}
                ]
            }},
            {{
                "name": "Phase 2: Execution",
                "steps": [
                    {{
                        "id": "2.1",
                        "text": "Implementation",
                        "type": "process"
                    }},
                    {{
                        "id": "2.2",
                        "text": "Quality approved?",
                        "type": "decision"
                    }}
                ]
            }}
        ],
        "connections": [
            {{
                "from": "1.1",
                "to": "1.2",
                "label": ""
            }},
            {{
                "from": "1.2",
                "to": "2.1",
                "label": ""
            }},
            {{
                "from": "2.1",
                "to": "2.2",
                "label": ""
            }},
            {{
                "from": "2.2",
                "to": "2.1",
                "label": "No"
            }}
        ]
    }}
    
    NODE TYPES:
    - "start": Oval shape representing the start of the process
    - "end": Oval shape representing the end of the process
    - "process": Rectangle shape representing a process step or action
    - "decision": Diamond shape representing a decision point (always phrase as a question)
    - "input": Parallelogram shape representing input/output
    - "document": Document shape representing documentation
    
    GUIDELINES:
    1. Organize steps into logical phases
    2. Use clear, concise text for each step (under 10 words if possible)
    3. Ensure the process flows logically from start to end
    4. Decisions should always have at least two connections (typically "Yes" and "No")
    5. All steps must be connected
    6. Make sure all step IDs are unique
    
    ONLY RESPOND WITH THE JSON OBJECT. Do not include any other text or explanation.
    """

def create_mindmap_prompt(prompt: str) -> str:
    """Create a prompt for mind map generation specifically optimized for TLDraw"""
    return f"""
    You are a diagram generation assistant that creates structured mind maps for TLDraw visualization.
    
    TASK: Generate a detailed mind map based on this request: "{prompt}"
    
    IMPORTANT: Return your response as a JSON object with the following structure:
    
    {{
        "title": "Main Topic",
        "description": "Brief description of what this mind map represents",
        "centralNode": {{
            "id": "center",
            "text": "Central Concept",
            "color": "blue"
        }},
        "branches": [
            {{
                "id": "branch1",
                "text": "Main Branch 1",
                "color": "green",
                "nodes": [
                    {{
                        "id": "node1.1",
                        "text": "Sub-topic 1.1",
                        "color": "green"
                    }},
                    {{
                        "id": "node1.2",
                        "text": "Sub-topic 1.2",
                        "color": "green"
                    }}
                ]
            }},
            {{
                "id": "branch2",
                "text": "Main Branch 2",
                "color": "red",
                "nodes": [
                    {{
                        "id": "node2.1",
                        "text": "Sub-topic 2.1",
                        "color": "red"
                    }},
                    {{
                        "id": "node2.2",
                        "text": "Sub-topic 2.2",
                        "color": "red"
                    }}
                ]
            }}
        ],
        "connections": [
            {{
                "from": "node1.1",
                "to": "node2.1",
                "label": "relates to"
            }}
        ]
    }}
    
    GUIDELINES:
    1. The central node should capture the main concept of the mind map
    2. Create 4-6 main branches that represent primary categories or themes
    3. Each branch should have 2-4 sub-topics that elaborate on the branch theme
    4. Use short, clear text for each node (typically 1-5 words for maximum visual clarity)
    5. Add 1-3 cross-connections between nodes that have meaningful relationships
    6. Use different colors for different branches to make the mind map visually distinct
    7. Ensure all IDs are unique
    8. Make sure the content is accurate and relevant to the topic
    
    COLOR OPTIONS:
    - "blue", "green", "red", "yellow", "purple", "orange", "teal", "pink"
    
    ONLY RESPOND WITH THE JSON OBJECT. Do not include any other text or explanation.
    """