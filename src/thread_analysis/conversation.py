#!/usr/bin/env python3
"""
Conversation Flow Analysis module for Project Authentica.
Analyzes conversation patterns and dynamics in Reddit threads.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict
import re
import networkx as nx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConversationFlow:
    """
    Analyzes conversation flow and dynamics in Reddit threads.
    
    This class provides methods for:
    1. Identifying conversation patterns and structures
    2. Detecting discussion branches and forks
    3. Analyzing reply chains and their characteristics
    4. Identifying key conversation points and transitions
    """
    
    def __init__(self):
        """Initialize the ConversationFlow analyzer."""
        pass
    
    def analyze(self, comment_forest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze conversation flow in a comment forest.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest to analyze.
            
        Returns:
            Dict[str, Any]: Conversation flow analysis results.
        """
        logger.info("Analyzing conversation flow")
        
        # Initialize analysis results
        analysis = {
            "branching_factor": 0.0,
            "max_chain_length": 0,
            "avg_chain_length": 0.0,
            "conversation_density": 0.0,
            "reply_patterns": {},
            "discussion_hotspots": [],
            "conversation_graph": {},
        }
        
        # Build conversation graph
        graph = self._build_conversation_graph(comment_forest)
        analysis["conversation_graph"] = self._serialize_graph(graph)
        
        # Calculate branching factor
        analysis["branching_factor"] = self._calculate_branching_factor(comment_forest)
        
        # Calculate chain statistics
        chains = self._identify_chains(comment_forest)
        if chains:
            analysis["max_chain_length"] = max(len(chain) for chain in chains)
            analysis["avg_chain_length"] = sum(len(chain) for chain in chains) / len(chains)
        
        # Calculate conversation density
        analysis["conversation_density"] = self._calculate_conversation_density(comment_forest)
        
        # Identify reply patterns
        analysis["reply_patterns"] = self._identify_reply_patterns(comment_forest)
        
        # Identify discussion hotspots
        analysis["discussion_hotspots"] = self._identify_hotspots(comment_forest)
        
        logger.info("Conversation flow analysis complete")
        return analysis
    
    def _build_conversation_graph(self, comment_forest: Dict[str, Any]) -> nx.DiGraph:
        """
        Build a directed graph representing the conversation structure.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest.
            
        Returns:
            nx.DiGraph: A directed graph of the conversation.
        """
        graph = nx.DiGraph()
        
        # Add nodes and edges
        self._add_nodes_and_edges(None, comment_forest, graph)
        
        return graph
    
    def _add_nodes_and_edges(self, parent_id: Optional[str], comment_forest: Dict[str, Any], graph: nx.DiGraph) -> None:
        """
        Add nodes and edges to the conversation graph recursively.
        
        Args:
            parent_id (Optional[str]): ID of the parent comment.
            comment_forest (Dict[str, Any]): The comment forest.
            graph (nx.DiGraph): The graph to update.
        """
        for comment_id, comment_data in comment_forest.items():
            # Add node with attributes
            node_attrs = {
                "author": comment_data.get("author", "[deleted]"),
                "score": comment_data.get("score", 0),
                "depth": comment_data.get("depth", 0),
            }
            graph.add_node(comment_id, **node_attrs)
            
            # Add edge from parent to this comment
            if parent_id is not None:
                graph.add_edge(parent_id, comment_id)
            
            # Process replies
            if "replies" in comment_data:
                self._add_nodes_and_edges(comment_id, comment_data["replies"], graph)
    
    def _serialize_graph(self, graph: nx.DiGraph) -> Dict[str, Any]:
        """
        Serialize a NetworkX graph for JSON output.
        
        Args:
            graph (nx.DiGraph): The graph to serialize.
            
        Returns:
            Dict[str, Any]: Serialized graph.
        """
        return {
            "nodes": [{"id": node, **graph.nodes[node]} for node in graph.nodes()],
            "edges": [{"source": u, "target": v} for u, v in graph.edges()],
        }
    
    def _calculate_branching_factor(self, comment_forest: Dict[str, Any]) -> float:
        """
        Calculate the average branching factor of the conversation.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest.
            
        Returns:
            float: Average branching factor.
        """
        # Count nodes and their children
        total_nodes = 0
        total_children = 0
        
        def count_nodes_and_children(forest: Dict[str, Any]) -> Tuple[int, int]:
            nodes = len(forest)
            children = 0
            
            for comment_id, comment_data in forest.items():
                if "replies" in comment_data:
                    reply_nodes, reply_children = count_nodes_and_children(comment_data["replies"])
                    children += len(comment_data["replies"])
                    nodes += reply_nodes
                    children += reply_children
            
            return nodes, children
        
        total_nodes, total_children = count_nodes_and_children(comment_forest)
        
        # Calculate branching factor
        if total_nodes > 0:
            return total_children / total_nodes
        else:
            return 0.0
    
    def _identify_chains(self, comment_forest: Dict[str, Any]) -> List[List[str]]:
        """
        Identify conversation chains in the comment forest.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest.
            
        Returns:
            List[List[str]]: List of conversation chains.
        """
        chains = []
        
        def traverse_chain(forest: Dict[str, Any], current_chain: List[str]) -> None:
            for comment_id, comment_data in forest.items():
                # Add this comment to the current chain
                chain = current_chain + [comment_id]
                
                # If this comment has exactly one reply, continue the chain
                if "replies" in comment_data and len(comment_data["replies"]) == 1:
                    traverse_chain(comment_data["replies"], chain)
                else:
                    # End of chain
                    if len(chain) > 1:  # Only consider chains with at least 2 comments
                        chains.append(chain)
                    
                    # If this comment has multiple replies, start new chains
                    if "replies" in comment_data and len(comment_data["replies"]) > 1:
                        for reply_id in comment_data["replies"]:
                            traverse_chain({reply_id: comment_data["replies"][reply_id]}, [comment_id])
        
        # Start traversal from top-level comments
        for comment_id in comment_forest:
            traverse_chain({comment_id: comment_forest[comment_id]}, [])
        
        return chains
    
    def _calculate_conversation_density(self, comment_forest: Dict[str, Any]) -> float:
        """
        Calculate the conversation density (replies per comment).
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest.
            
        Returns:
            float: Conversation density.
        """
        total_comments = 0
        total_replies = 0
        
        def count_comments_and_replies(forest: Dict[str, Any]) -> Tuple[int, int]:
            comments = len(forest)
            replies = 0
            
            for comment_id, comment_data in forest.items():
                if "replies" in comment_data:
                    reply_count = len(comment_data["replies"])
                    replies += reply_count
                    
                    # Recursively count in replies
                    sub_comments, sub_replies = count_comments_and_replies(comment_data["replies"])
                    comments += sub_comments
                    replies += sub_replies
            
            return comments, replies
        
        total_comments, total_replies = count_comments_and_replies(comment_forest)
        
        # Calculate density
        if total_comments > 0:
            return total_replies / total_comments
        else:
            return 0.0
    
    def _identify_reply_patterns(self, comment_forest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify common reply patterns in the conversation.
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest.
            
        Returns:
            Dict[str, Any]: Reply pattern analysis.
        """
        patterns = {
            "back_and_forth": 0,  # A-B-A-B pattern
            "multi_participant": 0,  # A-B-C-D pattern
            "star": 0,  # A responds to multiple comments
            "triangle": 0,  # A-B-C-A pattern (circular)
        }
        
        # Build author reply graph
        author_graph = nx.DiGraph()
        
        def build_author_graph(forest: Dict[str, Any], parent_author: Optional[str] = None) -> None:
            for comment_id, comment_data in forest.items():
                author = comment_data.get("author", "[deleted]")
                
                # Add node if not exists
                if author not in author_graph:
                    author_graph.add_node(author)
                
                # Add edge from parent author to this author
                if parent_author is not None and parent_author != author:
                    if author_graph.has_edge(parent_author, author):
                        # Increment weight
                        author_graph[parent_author][author]["weight"] += 1
                    else:
                        # Create edge with weight 1
                        author_graph.add_edge(parent_author, author, weight=1)
                
                # Process replies
                if "replies" in comment_data:
                    build_author_graph(comment_data["replies"], author)
        
        # Build the author graph
        build_author_graph(comment_forest)
        
        # Analyze patterns
        
        # Back and forth (edges with weight > 1 in both directions)
        for u, v in author_graph.edges():
            if author_graph.has_edge(v, u):
                if author_graph[u][v]["weight"] > 1 and author_graph[v][u]["weight"] > 1:
                    patterns["back_and_forth"] += 1
        
        # Multi-participant (paths of length 3+ with different authors)
        for path in nx.all_simple_paths(author_graph, source=None, target=None, cutoff=3):
            if len(path) >= 3 and len(set(path)) == len(path):
                patterns["multi_participant"] += 1
        
        # Star pattern (authors with high out-degree)
        for node in author_graph.nodes():
            if author_graph.out_degree(node) > 2:
                patterns["star"] += 1
        
        # Triangle pattern (cycles of length 3)
        patterns["triangle"] = len(list(nx.simple_cycles(author_graph, length_bound=3)))
        
        return patterns
    
    def _identify_hotspots(self, comment_forest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify discussion hotspots (comments with high engagement).
        
        Args:
            comment_forest (Dict[str, Any]): The comment forest.
            
        Returns:
            List[Dict[str, Any]]: List of hotspot comments.
        """
        hotspots = []
        
        def find_hotspots(forest: Dict[str, Any]) -> None:
            for comment_id, comment_data in forest.items():
                # Calculate hotspot score based on replies and score
                reply_count = len(comment_data.get("replies", {}))
                score = comment_data.get("score", 0)
                
                # Simple hotspot heuristic: high reply count OR high score
                if reply_count > 5 or score > 10:
                    hotspots.append({
                        "comment_id": comment_id,
                        "author": comment_data.get("author", "[deleted]"),
                        "reply_count": reply_count,
                        "score": score,
                        "depth": comment_data.get("depth", 0),
                        "hotspot_score": reply_count * 2 + score,  # Simple scoring formula
                    })
                
                # Process replies
                if "replies" in comment_data:
                    find_hotspots(comment_data["replies"])
        
        # Find all hotspots
        find_hotspots(comment_forest)
        
        # Sort by hotspot score
        hotspots.sort(key=lambda x: x["hotspot_score"], reverse=True)
        
        # Return top 10 hotspots
        return hotspots[:10] 