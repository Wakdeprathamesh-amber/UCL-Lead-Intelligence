"""
Conversation Aggregator Module
Handles text-based aggregation across ALL conversation data
Used for queries like "top queries", "most common concerns", "frequently mentioned amenities"
"""

import re
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import json


class ConversationAggregator:
    """
    Aggregates and analyzes conversation data to extract patterns, counts, and rankings.
    Designed for text-based aggregation queries that need ALL data, not just samples.
    """
    
    def __init__(self, db_path: str = "data/leads.db"):
        """
        Initialize the conversation aggregator
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        
        # Define category patterns for automatic categorization
        self.query_patterns = {
            'budget': [
                r'\b(budget|price|cost|how much|expensive|cheap|afford|payment|rent|fee|deposit)\b',
                r'\b(£|€|$|\d+\s*(pound|dollar|euro))',
            ],
            'move_in': [
                r'\b(move.?in|moving|arrival|start date|when can|available|check.?in)\b',
                r'\b(september|october|january|date|asap)\b',
            ],
            'room_type': [
                r'\b(room type|studio|ensuite|shared|private|single|double|twin|bedroom)\b',
                r'\b(apartment|flat|accommodation type)\b',
            ],
            'location': [
                r'\b(location|near|close to|distance|far|how long|transport|commute)\b',
                r'\b(university|campus|city center|station)\b',
            ],
            'amenities': [
                r'\b(wifi|internet|gym|pool|laundry|parking|kitchen|bathroom)\b',
                r'\b(facilities|amenities|included|features)\b',
            ],
            'contract': [
                r'\b(contract|lease|duration|term|extend|cancel|flexible|break clause)\b',
                r'\b(12 week|29 week|semester|academic year)\b',
            ],
            'guest_policy': [
                r'\b(guest|visitor|friend|family|overnight|stay over)\b',
            ],
            'bills': [
                r'\b(bills?|utilities|electricity|water|gas|included|extra)\b',
            ],
            'booking': [
                r'\b(book|reserve|confirm|secure|hold|available|vacancy)\b',
            ],
            'security': [
                r'\b(safe|secure|security|cctv|lock|key|card)\b',
            ],
        }
        
        self.concern_patterns = {
            'financial': [
                r'\b(expensive|too much|can\'?t afford|budget concern|high price)\b',
            ],
            'availability': [
                r'\b(not available|sold out|wait.?list|no rooms|full)\b',
            ],
            'distance': [
                r'\b(too far|long commute|not close|distance concern)\b',
            ],
            'quality': [
                r'\b(quality|condition|old|maintenance|renovation)\b',
            ],
            'contract_terms': [
                r'\b(contract issue|too long|inflexible|can\'?t extend)\b',
            ],
            'communication': [
                r'\b(no response|slow|unresponsive|waiting for|not heard)\b',
            ],
        }
    
    def aggregate_queries(
        self,
        query_type: str = "all",
        limit: int = 5000,
        min_length: int = 10
    ) -> Dict[str, Any]:
        """
        Aggregate and categorize queries/questions from student messages.
        
        Args:
            query_type: Type of messages to analyze ('whatsapp', 'call', 'email', 'all')
            limit: Maximum number of messages to analyze
            min_length: Minimum message length to consider (filters out "ok", "yes", etc.)
        
        Returns:
            Dict with categories, counts, examples, and statistics
        """
        # Get messages
        messages = self._get_messages(query_type, limit, min_length)
        
        if not messages:
            return {
                "success": False,
                "error": "No messages found",
                "total_analyzed": 0
            }
        
        # Categorize messages
        categorized = self._categorize_messages(messages, self.query_patterns)
        
        # Calculate statistics
        total = len(messages)
        category_counts = Counter(cat for msg in categorized for cat in msg['categories'])
        
        # Get top categories with examples
        top_categories = []
        for category, count in category_counts.most_common(10):
            # Get examples for this category
            examples = [
                msg['content'][:150] + ('...' if len(msg['content']) > 150 else '')
                for msg in categorized
                if category in msg['categories']
            ][:3]  # Top 3 examples
            
            top_categories.append({
                "category": category.replace('_', ' ').title(),
                "count": count,
                "percentage": round((count / total) * 100, 1),
                "examples": examples
            })
        
        return {
            "success": True,
            "total_analyzed": total,
            "total_categorized": len([m for m in categorized if m['categories']]),
            "categories": top_categories,
            "query_type": query_type,
            "summary": f"Analyzed {total} messages, identified {len(category_counts)} distinct query types"
        }
    
    def aggregate_concerns(
        self,
        query_type: str = "all",
        limit: int = 5000,
        min_length: int = 20
    ) -> Dict[str, Any]:
        """
        Aggregate and categorize concerns/objections from messages.
        
        Args:
            query_type: Type of messages to analyze
            limit: Maximum number of messages to analyze
            min_length: Minimum message length (concerns are usually longer)
        
        Returns:
            Dict with concern categories, counts, examples, and statistics
        """
        # Get messages
        messages = self._get_messages(query_type, limit, min_length)
        
        if not messages:
            return {
                "success": False,
                "error": "No messages found",
                "total_analyzed": 0
            }
        
        # Categorize concerns
        categorized = self._categorize_messages(messages, self.concern_patterns)
        
        # Calculate statistics
        total = len(messages)
        concern_counts = Counter(cat for msg in categorized for cat in msg['categories'])
        
        # Get top concerns with examples
        top_concerns = []
        for concern, count in concern_counts.most_common(10):
            examples = [
                msg['content'][:150] + ('...' if len(msg['content']) > 150 else '')
                for msg in categorized
                if concern in msg['categories']
            ][:3]
            
            top_concerns.append({
                "concern": concern.replace('_', ' ').title(),
                "count": count,
                "percentage": round((count / total) * 100, 1),
                "examples": examples
            })
        
        return {
            "success": True,
            "total_analyzed": total,
            "total_with_concerns": len([m for m in categorized if m['categories']]),
            "concerns": top_concerns,
            "query_type": query_type,
            "summary": f"Analyzed {total} messages, identified {len(concern_counts)} distinct concern types"
        }
    
    def aggregate_mentions(
        self,
        keywords: List[str],
        query_type: str = "all",
        limit: int = 5000,
        case_sensitive: bool = False
    ) -> Dict[str, Any]:
        """
        Count mentions of specific keywords or topics across messages.
        
        Args:
            keywords: List of keywords to search for
            query_type: Type of messages to analyze
            limit: Maximum number of messages to analyze
            case_sensitive: Whether to use case-sensitive matching
        
        Returns:
            Dict with mention counts and examples for each keyword
        """
        # Get messages
        messages = self._get_messages(query_type, limit, min_length=5)
        
        if not messages:
            return {
                "success": False,
                "error": "No messages found",
                "total_analyzed": 0
            }
        
        # Count mentions
        results = {}
        for keyword in keywords:
            pattern = keyword if case_sensitive else re.compile(re.escape(keyword), re.IGNORECASE)
            
            matching_messages = []
            for msg in messages:
                if (case_sensitive and keyword in msg['content']) or \
                   (not case_sensitive and re.search(pattern, msg['content'])):
                    matching_messages.append(msg)
            
            # Get examples
            examples = [
                msg['content'][:150] + ('...' if len(msg['content']) > 150 else '')
                for msg in matching_messages[:5]
            ]
            
            results[keyword] = {
                "count": len(matching_messages),
                "percentage": round((len(matching_messages) / len(messages)) * 100, 1),
                "examples": examples
            }
        
        # Sort by count
        sorted_results = sorted(results.items(), key=lambda x: x[1]['count'], reverse=True)
        
        return {
            "success": True,
            "total_analyzed": len(messages),
            "keywords_analyzed": len(keywords),
            "mentions": dict(sorted_results),
            "query_type": query_type,
            "summary": f"Analyzed {len(messages)} messages for {len(keywords)} keywords"
        }
    
    def aggregate_amenities(
        self,
        limit: int = 5000
    ) -> Dict[str, Any]:
        """
        Extract and count amenity mentions from conversations.
        
        Args:
            limit: Maximum number of messages to analyze
        
        Returns:
            Dict with amenity counts and examples
        """
        # Common amenities to search for
        amenities = [
            'wifi', 'internet', 'gym', 'pool', 'swimming pool',
            'laundry', 'washing machine', 'parking', 'garage',
            'kitchen', 'ensuite', 'private bathroom', 'air conditioning',
            'heating', 'tv', 'desk', 'study area', 'common room',
            'security', 'cctv', 'reception', '24/7', 'concierge',
            'bike storage', 'cinema room', 'games room', 'garden',
            'balcony', 'terrace', 'dishwasher', 'microwave', 'oven'
        ]
        
        return self.aggregate_mentions(amenities, query_type="all", limit=limit, case_sensitive=False)
    
    def aggregate_by_status(
        self,
        category: str = "queries",
        limit: int = 5000
    ) -> Dict[str, Any]:
        """
        Aggregate conversations by lead status (Won, Lost, etc.).
        
        Args:
            category: What to analyze ('queries', 'concerns', 'mentions')
            limit: Maximum number of messages per status
        
        Returns:
            Dict with aggregated data grouped by lead status
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get leads by status
        cursor.execute("""
            SELECT DISTINCT status
            FROM leads
            WHERE status IS NOT NULL AND status != ''
        """)
        statuses = [row[0] for row in cursor.fetchall()]
        
        results = {}
        for status in statuses:
            # Get messages for this status
            cursor.execute("""
                SELECT te.content, te.lead_id
                FROM timeline_events te
                JOIN leads l ON te.lead_id = l.lead_id
                WHERE l.status = ?
                  AND te.event_type IN ('whatsapp', 'call', 'email')
                  AND te.content IS NOT NULL
                  AND LENGTH(te.content) > 10
                LIMIT ?
            """, (status, limit))
            
            messages = [
                {"content": row[0], "lead_id": row[1]}
                for row in cursor.fetchall()
            ]
            
            if messages:
                if category == "queries":
                    categorized = self._categorize_messages(messages, self.query_patterns)
                elif category == "concerns":
                    categorized = self._categorize_messages(messages, self.concern_patterns)
                else:
                    categorized = []
                
                category_counts = Counter(cat for msg in categorized for cat in msg['categories'])
                
                results[status] = {
                    "total_messages": len(messages),
                    "top_categories": [
                        {"category": cat, "count": count}
                        for cat, count in category_counts.most_common(5)
                    ]
                }
        
        conn.close()
        
        return {
            "success": True,
            "statuses_analyzed": len(statuses),
            "results": results,
            "summary": f"Analyzed {category} across {len(statuses)} lead statuses"
        }
    
    def _get_messages(
        self,
        query_type: str,
        limit: int,
        min_length: int
    ) -> List[Dict[str, Any]]:
        """
        Get messages from database based on criteria.
        
        Args:
            query_type: Type of messages ('whatsapp', 'call', 'email', 'all')
            limit: Maximum number to retrieve
            min_length: Minimum content length
        
        Returns:
            List of message dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if query_type == "all":
            event_types = ('whatsapp', 'call', 'email')
        else:
            event_types = (query_type,)
        
        placeholders = ','.join('?' * len(event_types))
        
        query = f"""
            SELECT content, lead_id, event_type, timestamp
            FROM timeline_events
            WHERE event_type IN ({placeholders})
              AND content IS NOT NULL
              AND LENGTH(content) > ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        cursor.execute(query, (*event_types, min_length, limit))
        
        messages = [
            {
                "content": row[0],
                "lead_id": row[1],
                "event_type": row[2],
                "timestamp": row[3]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return messages
    
    def _categorize_messages(
        self,
        messages: List[Dict[str, Any]],
        patterns: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Categorize messages based on regex patterns.
        
        Args:
            messages: List of message dictionaries
            patterns: Dictionary of category: [regex patterns]
        
        Returns:
            List of messages with added 'categories' field
        """
        categorized = []
        
        for msg in messages:
            content_lower = msg['content'].lower()
            matched_categories = []
            
            for category, pattern_list in patterns.items():
                for pattern in pattern_list:
                    if re.search(pattern, content_lower):
                        matched_categories.append(category)
                        break  # One match per category is enough
            
            categorized.append({
                **msg,
                "categories": matched_categories
            })
        
        return categorized


def aggregate_conversations(
    aggregation_type: str,
    query_type: str = "all",
    keywords: Optional[List[str]] = None,
    limit: int = 5000,
    db_path: Optional[str] = None
) -> str:
    """
    Main entry point for conversation aggregation.
    This function is exposed as a tool to the AI agent.
    
    Args:
        aggregation_type: Type of aggregation ('queries', 'concerns', 'mentions', 'amenities', 'by_status')
        query_type: Type of messages to analyze ('whatsapp', 'call', 'email', 'all')
        keywords: Optional list of keywords for 'mentions' type
        limit: Maximum messages to analyze
        db_path: Optional database path (auto-detects if not provided)
    
    Returns:
        JSON string with aggregation results
    """
    # Auto-detect database path if not provided
    if db_path is None:
        import os
        for path in ["data/leads.db", "Data/leads.db"]:
            if os.path.exists(path):
                db_path = path
                break
        if db_path is None:
            db_path = "data/leads.db"  # Default
    
    aggregator = ConversationAggregator(db_path=db_path)
    
    try:
        if aggregation_type == "queries":
            result = aggregator.aggregate_queries(query_type=query_type, limit=limit)
        
        elif aggregation_type == "concerns":
            result = aggregator.aggregate_concerns(query_type=query_type, limit=limit)
        
        elif aggregation_type == "mentions":
            if not keywords:
                return json.dumps({"error": "Keywords required for 'mentions' aggregation type"})
            result = aggregator.aggregate_mentions(keywords=keywords, query_type=query_type, limit=limit)
        
        elif aggregation_type == "amenities":
            result = aggregator.aggregate_amenities(limit=limit)
        
        elif aggregation_type == "by_status":
            result = aggregator.aggregate_by_status(category="queries", limit=limit)
        
        else:
            return json.dumps({"error": f"Unknown aggregation type: {aggregation_type}"})
        
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({"error": f"Aggregation failed: {str(e)}"})

