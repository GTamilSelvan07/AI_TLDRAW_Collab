# backend/services/tldraw.py
import json
import re
import random
import math
from typing import List, Dict, Any, Optional, Tuple, Union
import logging

# Configure logging
logger = logging.getLogger(__name__)

def generate_flowchart(llm_response: Union[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate TLDraw shapes for a flowchart based on the LLM response.
    
    Args:
        llm_response: The response from the LLM (either text or JSON)
        
    Returns:
        A list of TLDraw shapes
    """
    try:
        # Check if response is already JSON
        if isinstance(llm_response, dict):
            flowchart_data = llm_response
        else:
            # Try to parse JSON from the text response
            try:
                # Look for JSON content in the response
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = llm_response[json_start:json_end]
                    flowchart_data = json.loads(json_str)
                else:
                    # Fall back to text parsing
                    return parse_flowchart_from_text(llm_response)
            except (json.JSONDecodeError, AttributeError):
                # Fall back to text parsing
                return parse_flowchart_from_text(llm_response)
        
        # Create a title shape
        shapes = []
        title = flowchart_data.get("title", "Flowchart")
        shapes.append({
            "type": "text",
            "x": 100,
            "y": 50,
            "props": {
                "text": title,
                "font": "draw",
                "size": "xl",
                "color": "black",
                "align": "middle"
            }
        })
        
        # Track node positions for connecting arrows
        node_positions = {}
        
        # Generate shapes from nodes
        nodes = flowchart_data.get("nodes", [])
        start_x, start_y = 100, 150
        col_width, row_height = 250, 150
        
        # Calculate grid layout
        cols = min(3, max(1, math.ceil(math.sqrt(len(nodes)))))
        
        for i, node in enumerate(nodes):
            # Basic grid positioning
            col = i % cols
            row = i // cols
            
            x = start_x + col * col_width
            y = start_y + row * row_height
            
            node_id = node.get("id", str(i+1))
            node_text = node.get("text", f"Node {i+1}")
            node_type = node.get("type", "process")
            
            # Determine shape geometry based on node type
            geo_type = "rectangle"  # Default
            if node_type == "start" or node_type == "end":
                geo_type = "ellipse"
            elif node_type == "decision":
                geo_type = "diamond"
            elif node_type == "input":
                geo_type = "parallelogram"
                
            # Determine color based on node type
            color = "light-blue"  # Default
            if node_type == "start":
                color = "blue"
            elif node_type == "end":
                color = "green"
            elif node_type == "decision":
                color = "orange"
            
            # Create shape
            shape = {
                "type": "geo",
                "x": x,
                "y": y,
                "props": {
                    "w": 160 if geo_type != "diamond" else 180,
                    "h": 80 if geo_type != "diamond" else 100,
                    "geo": geo_type,
                    "color": color,
                    "text": node_text,
                    "align": "middle",
                    "font": "draw"
                }
            }
            
            shapes.append(shape)
            
            # Store position for connections
            node_positions[node_id] = (x, y)
        
        # Create connection arrows
        connections = flowchart_data.get("connections", [])
        for conn in connections:
            from_id = conn.get("from")
            to_id = conn.get("to")
            label = conn.get("label", "")
            
            if from_id not in node_positions or to_id not in node_positions:
                continue
                
            from_x, from_y = node_positions[from_id]
            to_x, to_y = node_positions[to_id]
            
            # Add label text if present
            if label:
                # Calculate mid-point for label
                mid_x = (from_x + to_x) / 2
                mid_y = (from_y + to_y) / 2
                
                # Offset label slightly
                offset = 15
                label_shape = {
                    "type": "text",
                    "x": mid_x + offset,
                    "y": mid_y - offset,
                    "props": {
                        "text": label,
                        "font": "draw",
                        "size": "s",
                        "color": "black"
                    }
                }
                shapes.append(label_shape)
            
            # Create arrow
            arrow = {
                "type": "arrow",
                "x": from_x + 80,
                "y": from_y + 40,
                "props": {
                    "start": {
                        "x": 0,
                        "y": 0,
                    },
                    "end": {
                        "x": to_x - from_x,
                        "y": to_y - from_y,
                    },
                    "color": "black",
                    "dash": "draw",
                    "size": "m"
                }
            }
            
            shapes.append(arrow)
        
        return shapes
    
    except Exception as e:
        logger.error(f"Error generating flowchart: {e}")
        # Return a simple error shape
        return [{
            "type": "text",
            "x": 100,
            "y": 100,
            "props": {
                "text": f"Error generating diagram: {str(e)}",
                "color": "red",
                "font": "draw",
                "size": "m"
            }
        }]

def parse_flowchart_from_text(text: str) -> List[Dict[str, Any]]:
    """Legacy method to parse flowchart from text when JSON parsing fails"""
    nodes, connections = parse_flowchart_response(text)
    
    shapes = []
    node_positions = {}
    start_x, start_y = 100, 100
    
    # Create shapes for each node
    for i, node in enumerate(nodes):
        # Basic grid positioning
        x = start_x + (i % 3) * 250
        y = start_y + (i // 3) * 150
        
        node_id = f"node-{i}"
        node_positions[node_id] = (x, y)
        
        # Determine shape type based on node text
        shape_type = "rectangle"
        if "decision" in node.lower() or "if" in node.lower() or "?" in node:
            shape_type = "diamond"
        elif "start" in node.lower() or "begin" in node.lower():
            shape_type = "ellipse"
        elif "end" in node.lower() or "finish" in node.lower():
            shape_type = "ellipse"
        
        # Create the shape
        shape = {
            "type": "geo",
            "x": x,
            "y": y,
            "props": {
                "w": 160 if shape_type != "diamond" else 180,
                "h": 80 if shape_type != "diamond" else 100,
                "geo": shape_type,
                "color": "blue" if "start" in node.lower() else 
                        "green" if "end" in node.lower() else
                        "orange" if shape_type == "diamond" else "light-blue",
                "text": node,
                "align": "middle",
                "font": "draw"
            }
        }
        
        shapes.append(shape)
    
    # Create arrows for connections
    for connection in connections:
        from_node_id = connection[0]
        to_node_id = connection[1]
        
        # Skip if nodes don't exist
        if from_node_id not in node_positions or to_node_id not in node_positions:
            continue
            
        from_x, from_y = node_positions[from_node_id]
        to_x, to_y = node_positions[to_node_id]
        
        # Create an arrow
        arrow = {
            "type": "arrow",
            "x": from_x + 80,
            "y": from_y + 40,
            "props": {
                "start": {
                    "x": 0,
                    "y": 0,
                },
                "end": {
                    "x": to_x - from_x,
                    "y": to_y - from_y,
                },
                "color": "black",
                "dash": "draw",
                "size": "m"
            }
        }
        
        shapes.append(arrow)
    
    return shapes

def parse_flowchart_response(text: str) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Legacy parser for the LLM response to extract nodes and connections.
    """
    nodes = []
    connections = []
    
    # Look for nodes
    node_pattern = r"(?:Node|Step|Process|Action|Decision)[:]\s*(.*?)(?:\n|$)"
    for match in re.finditer(node_pattern, text, re.IGNORECASE):
        nodes.append(match.group(1).strip())
    
    # If no nodes found, try to extract them differently
    if not nodes:
        # Look for numbered or bulleted lists
        list_pattern = r"(?:\d+\.|\*|\-)\s*(.*?)(?:\n|$)"
        for match in re.finditer(list_pattern, text):
            nodes.append(match.group(1).strip())
    
    # If still no nodes, just split by lines and take non-empty ones
    if not nodes:
        nodes = [line.strip() for line in text.split('\n') if line.strip()]
        nodes = nodes[:min(len(nodes), 10)]  # Limit to 10 nodes
    
    # Create connections
    for i in range(len(nodes) - 1):
        connections.append((f"node-{i}", f"node-{i+1}"))
    
    return nodes, connections

def generate_process_diagram(llm_response: Union[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate a process diagram from LLM response"""
    # For process diagrams, we can reuse the flowchart logic with some styling differences
    try:
        shapes = generate_flowchart(llm_response)
        
        # Customize for process diagram appearance
        for shape in shapes:
            if shape["type"] == "geo":
                shape["props"]["dash"] = "solid"
                if shape["props"]["geo"] == "rectangle":
                    shape["props"]["color"] = "light-green"
        
        return shapes
    except Exception as e:
        logger.error(f"Error generating process diagram: {e}")
        return [{
            "type": "text",
            "x": 100,
            "y": 100,
            "props": {
                "text": f"Error generating process diagram: {str(e)}",
                "color": "red",
                "font": "draw",
                "size": "m"
            }
        }]

def generate_mind_map(llm_response: Union[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate a mind map from LLM response"""
    try:
        # Check if response is already JSON
        if isinstance(llm_response, dict):
            mind_map_data = llm_response
        else:
            # Try to parse JSON from the text response
            try:
                # Look for JSON content in the response
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = llm_response[json_start:json_end]
                    mind_map_data = json.loads(json_str)
                else:
                    # Fall back to text parsing
                    return parse_mindmap_from_text(llm_response)
            except (json.JSONDecodeError, AttributeError):
                # Fall back to text parsing
                return parse_mindmap_from_text(llm_response)
        
        shapes = []
        center_x, center_y = 400, 300
        
        # Add title
        title = mind_map_data.get("title", "Mind Map")
        shapes.append({
            "type": "text",
            "x": center_x - 100,
            "y": 50,
            "props": {
                "text": title,
                "font": "draw",
                "size": "xl",
                "color": "black",
                "align": "middle"
            }
        })
        
        # Create central node
        central_node = mind_map_data.get("centralNode", {"text": "Central Topic", "color": "blue", "id": "center"})
        central_shape = {
            "type": "geo",
            "x": center_x - 100,
            "y": center_y - 50,
            "props": {
                "w": 200,
                "h": 100,
                "geo": "ellipse",
                "color": central_node.get("color", "blue"),
                "text": central_node.get("text", "Central Topic"),
                "align": "middle",
                "font": "draw",
                "fill": "solid"
            }
        }
        shapes.append(central_shape)
        
        # Track node positions for connections
        node_positions = {
            central_node.get("id", "center"): (center_x, center_y)
        }
        
        # Create branch nodes in a radial layout
        branches = mind_map_data.get("branches", [])
        num_branches = len(branches)
        radius = 250
        
        for i, branch in enumerate(branches):
            # Calculate position based on angle around central node
            angle = 2 * math.pi * i / max(1, num_branches)
            branch_x = center_x + radius * math.cos(angle)
            branch_y = center_y + radius * math.sin(angle)
            
            branch_id = branch.get("id", f"branch{i+1}")
            branch_text = branch.get("text", f"Branch {i+1}")
            branch_color = branch.get("color", get_color_for_branch(i))
            
            # Create branch shape
            branch_shape = {
                "type": "geo",
                "x": branch_x - 80,
                "y": branch_y - 40,
                "props": {
                    "w": 160,
                    "h": 80,
                    "geo": "rectangle",
                    "color": branch_color,
                    "text": branch_text,
                    "align": "middle",
                    "font": "draw",
                    "fill": "solid"
                }
            }
            shapes.append(branch_shape)
            
            # Store position for connections
            node_positions[branch_id] = (branch_x, branch_y)
            
            # Connect to central node
            arrow = {
                "type": "arrow",
                "x": center_x,
                "y": center_y,
                "props": {
                    "start": {
                        "x": 0,
                        "y": 0,
                    },
                    "end": {
                        "x": branch_x - center_x,
                        "y": branch_y - center_y,
                    },
                    "color": branch_color,
                    "dash": "draw",
                    "size": "m"
                }
            }
            shapes.append(arrow)
            
            # Create sub-topic nodes
            sub_nodes = branch.get("nodes", [])
            num_sub_nodes = len(sub_nodes)
            
            for j, sub_node in enumerate(sub_nodes):
                # Calculate position in arc around branch
                sub_angle = angle - math.pi/6 + (math.pi/3) * (j / max(1, num_sub_nodes - 1))
                sub_radius = 150
                sub_x = branch_x + sub_radius * math.cos(sub_angle)
                sub_y = branch_y + sub_radius * math.sin(sub_angle)
                
                sub_id = sub_node.get("id", f"{branch_id}-{j+1}")
                sub_text = sub_node.get("text", f"Sub-topic {j+1}")
                sub_color = sub_node.get("color", branch_color)
                
                # Create sub-node shape
                sub_shape = {
                    "type": "geo",
                    "x": sub_x - 70,
                    "y": sub_y - 35,
                    "props": {
                        "w": 140,
                        "h": 70,
                        "geo": "rectangle",
                        "color": sub_color,
                        "text": sub_text,
                        "align": "middle",
                        "font": "draw",
                        "dash": "draw"
                    }
                }
                shapes.append(sub_shape)
                
                # Store position for connections
                node_positions[sub_id] = (sub_x, sub_y)
                
                # Connect to branch
                arrow = {
                    "type": "arrow",
                    "x": branch_x,
                    "y": branch_y,
                    "props": {
                        "start": {
                            "x": 0,
                            "y": 0,
                        },
                        "end": {
                            "x": sub_x - branch_x,
                            "y": sub_y - branch_y,
                        },
                        "color": sub_color,
                        "dash": "draw",
                        "size": "s"
                    }
                }
                shapes.append(arrow)
        
        # Add cross-connections
        connections = mind_map_data.get("connections", [])
        for conn in connections:
            from_id = conn.get("from")
            to_id = conn.get("to")
            label = conn.get("label", "")
            
            if from_id not in node_positions or to_id not in node_positions:
                continue
                
            from_x, from_y = node_positions[from_id]
            to_x, to_y = node_positions[to_id]
            
            # Add label if present
            if label:
                # Calculate mid-point for label
                mid_x = (from_x + to_x) / 2
                mid_y = (from_y + to_y) / 2
                
                # Add label text
                label_shape = {
                    "type": "text",
                    "x": mid_x - 40,
                    "y": mid_y - 10,
                    "props": {
                        "text": label,
                        "font": "draw",
                        "size": "s",
                        "color": "black"
                    }
                }
                shapes.append(label_shape)
            
            # Create connection arrow
            conn_arrow = {
                "type": "arrow",
                "x": from_x,
                "y": from_y,
                "props": {
                    "start": {
                        "x": 0,
                        "y": 0,
                    },
                    "end": {
                        "x": to_x - from_x,
                        "y": to_y - from_y,
                    },
                    "color": "gray",
                    "dash": "dashed",
                    "size": "s"
                }
            }
            shapes.append(conn_arrow)
        
        return shapes
    
    except Exception as e:
        logger.error(f"Error generating mind map: {e}")
        return [{
            "type": "text",
            "x": 100,
            "y": 100,
            "props": {
                "text": f"Error generating mind map: {str(e)}",
                "color": "red",
                "font": "draw",
                "size": "m"
            }
        }]

def parse_mindmap_from_text(text: str) -> List[Dict[str, Any]]:
    """Legacy method to parse mind map from text when JSON parsing fails"""
    topics = extract_mind_map_topics(text)
    
    shapes = []
    center_x, center_y = 400, 300
    
    # Create central node
    central_topic = topics[0] if topics else "Central Topic"
    central_shape = {
        "type": "geo",
        "x": center_x - 100,
        "y": center_y - 50,
        "props": {
            "w": 200,
            "h": 100,
            "geo": "ellipse",
            "color": "violet",
            "text": central_topic,
            "align": "middle",
            "font": "draw",
            "fill": "solid"
        }
    }
    shapes.append(central_shape)
    
    # Create branch nodes in a radial layout
    num_branches = min(len(topics) - 1, 8)
    radius = 250
    
    for i in range(num_branches):
        angle = 2 * math.pi * i / max(1, num_branches)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        branch_shape = {
            "type": "geo",
            "x": x - 80,
            "y": y - 40,
            "props": {
                "w": 160,
                "h": 80,
                "geo": "rectangle",
                "color": get_color_for_branch(i),
                "text": topics[i + 1] if i + 1 < len(topics) else f"Topic {i+1}",
                "align": "middle",
                "font": "draw",
                "fill": "solid",
                "dash": "draw"
            }
        }
        shapes.append(branch_shape)
        
        # Connect to central node
        arrow = {
            "type": "arrow",
            "x": center_x,
            "y": center_y,
            "props": {
                "start": {
                    "x": 0,
                    "y": 0,
                },
                "end": {
                    "x": x - center_x,
                    "y": y - center_y,
                },
                "color": get_color_for_branch(i),
                "dash": "draw",
                "size": "m"
            }
        }
        shapes.append(arrow)
    
    return shapes

def extract_mind_map_topics(text: str) -> List[str]:
    """Extract topics for mind map from LLM response"""
    topics = []
    
    # Look for main topic/central concept
    main_topic_pattern = r"(?:Main topic|Central concept|Central idea|Main idea|Central|Root)[:]\s*(.*?)(?:\n|$)"
    main_topic_match = re.search(main_topic_pattern, text, re.IGNORECASE)
    if main_topic_match:
        topics.append(main_topic_match.group(1).strip())
    else:
        # Just use the first line as main topic
        first_line = text.strip().split('\n')[0]
        topics.append(first_line)
    
    # Look for main branches
    branch_pattern = r"(?:\d+\.|\*|\-|Branch|Main branch|Primary)[:]\s*(.*?)(?:\n|$)"
    for match in re.finditer(branch_pattern, text, re.IGNORECASE):
        branch_text = match.group(1).strip()
        if branch_text and len(branch_text) < 100:  # Skip too long branches
            topics.append(branch_text)
    
    # Look for sub-topics
    subtopic_pattern = r"(?:Sub-topic|Sub branch|Secondary)[:]\s*(.*?)(?:\n|$)"
    for match in re.finditer(subtopic_pattern, text, re.IGNORECASE):
        topics.append(match.group(1).strip())
    
    # If not enough topics found, extract more text chunks
    if len(topics) < 5:
        # Split by newlines and look for short paragraphs or list items
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and line not in topics and len(line) < 100:
                # Check if it looks like a list item or heading
                if re.match(r'^(?:\d+\.|\*|\-|[A-Z]\.|\([a-z]\)|[IVXLCDM]+\.)?\s*.+$', line):
                    topics.append(line)
                    if len(topics) >= 9:  # Limit to 8 branches + 1 central
                        break
    
    return topics

def get_color_for_branch(index: int) -> str:
    """Get a color for a mind map branch based on its index"""
    colors = [
        "blue", "green", "orange", "red", 
        "violet", "light-blue", "yellow", "light-green"
    ]
    return colors[index % len(colors)]