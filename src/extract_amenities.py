"""
Amenity Extraction Module
Extracts amenities from conversations, structured data, and RAG documents
"""

import sqlite3
import json
import re
from typing import List, Dict, Set
import sys
import os

# Add error handling
sys.path.insert(0, os.path.dirname(__file__))
try:
    from error_handling import ErrorHandler
except ImportError:
    class ErrorHandler:
        @staticmethod
        def handle_database_error(func):
            return func


class AmenityExtractor:
    """Extract amenities from various data sources"""
    
    # Common amenities to look for
    AMENITY_KEYWORDS = {
        'wifi': ['wifi', 'wi-fi', 'wireless', 'internet', 'broadband'],
        'gym': ['gym', 'fitness', 'workout', 'exercise', 'fitness center'],
        'kitchen': ['kitchen', 'cooking', 'cook', 'stove', 'oven', 'microwave'],
        'study_area': ['study', 'study area', 'study room', 'quiet study', 'library'],
        'laundry': ['laundry', 'washing machine', 'dryer', 'washing'],
        'parking': ['parking', 'car park', 'parking space'],
        'security': ['security', 'secure', 'safe', 'cctv', 'camera'],
        'elevator': ['elevator', 'lift'],
        'air_conditioning': ['air conditioning', 'ac', 'air con', 'cooling'],
        'heating': ['heating', 'central heating', 'radiator'],
        'balcony': ['balcony', 'terrace', 'outdoor space'],
        'common_area': ['common area', 'common room', 'lounge', 'social space'],
        'bike_storage': ['bike storage', 'bicycle storage', 'bike room'],
        'reception': ['reception', 'receptionist', 'front desk'],
        'cleaning': ['cleaning', 'housekeeping', 'maid service'],
        'pool': ['pool', 'swimming pool'],
        'garden': ['garden', 'outdoor garden', 'courtyard'],
        'rooftop': ['rooftop', 'roof terrace', 'roof garden'],
        'game_room': ['game room', 'games room', 'recreation'],
        'cinema': ['cinema', 'movie room', 'theater'],
        'soundproof': ['soundproof', 'sound proof', 'quiet', 'noise'],
        'ensuite': ['ensuite', 'en-suite', 'private bathroom'],
        'private_bathroom': ['private bathroom', 'own bathroom', 'private bath'],
        'private_kitchen': ['private kitchen', 'own kitchen', 'personal kitchen'],
        'shared_kitchen': ['shared kitchen', 'communal kitchen'],
        'double_bed': ['double bed', 'double bedroom'],
        'single_bed': ['single bed', 'single bedroom'],
        'twin_bed': ['twin bed', 'twin room'],
        'wardrobe': ['wardrobe', 'closet', 'storage'],
        'desk': ['desk', 'study desk', 'work desk'],
        'chair': ['chair', 'desk chair', 'office chair'],
        'window': ['window', 'windows', 'natural light'],
        'top_floor': ['top floor', 'high floor', 'upper floor'],
        'ground_floor': ['ground floor', 'first floor', 'lower floor'],
        'near_transport': ['near transport', 'close to transport', 'transport links'],
        'near_university': ['near university', 'close to university', 'university nearby'],
        'near_shops': ['near shops', 'close to shops', 'shopping nearby'],
        'near_gym': ['near gym', 'close to gym', 'gym nearby']
    }
    
    def __init__(self, db_path: str = "data/leads.db"):
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        try:
            if not os.path.exists(self.db_path):
                raise FileNotFoundError(f"Database file not found: {self.db_path}")
            return sqlite3.connect(self.db_path)
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to connect to database: {str(e)}")
    
    def _normalize_amenity(self, text: str) -> str:
        """Normalize amenity text to standard form"""
        text_lower = text.lower().strip()
        
        # Check against keywords
        for standard_name, keywords in self.AMENITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return standard_name.replace('_', ' ').title()
        
        # Return capitalized version if no match
        return text.strip().title()
    
    def _extract_from_text(self, text: str) -> Set[str]:
        """Extract amenities from free text"""
        if not text or not isinstance(text, str):
            return set()
        
        text_lower = text.lower()
        found_amenities = set()
        
        for standard_name, keywords in self.AMENITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_amenities.add(standard_name.replace('_', ' ').title())
                    break  # Found one keyword for this amenity, move to next
        
        return found_amenities
    
    def _extract_from_structured_data(self, structured_data: Dict) -> Set[str]:
        """Extract amenities from structured data"""
        amenities = set()
        
        # Check requirements -> accommodation_requirements -> amenities
        if 'requirements' in structured_data:
            req = structured_data['requirements']
            if 'accommodation_requirements' in req:
                acc_req = req['accommodation_requirements']
                if 'amenities' in acc_req:
                    amenity_list = acc_req['amenities']
                    if isinstance(amenity_list, list):
                        for amenity in amenity_list:
                            if amenity:
                                amenities.add(self._normalize_amenity(str(amenity)))
        
        # Check conversation summary for mentioned amenities
        if 'conversation_summary' in structured_data:
            conv_summary = structured_data['conversation_summary']
            if isinstance(conv_summary, dict):
                # Convert to text and search
                summary_text = json.dumps(conv_summary)
                text_amenities = self._extract_from_text(summary_text)
                amenities.update(text_amenities)
        
        return amenities
    
    @ErrorHandler.handle_database_error
    def extract_all_amenities(self) -> Dict[str, int]:
        """
        Extract amenities from all leads and populate lead_amenities table
        
        Returns:
            Dictionary with extraction statistics
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Clear existing amenities (optional - comment out if you want to keep existing)
            # cursor.execute("DELETE FROM lead_amenities")
            # print("🗑️  Cleared existing amenities")
            
            # Get all leads with structured data
            cursor.execute("""
                SELECT lead_id, structured_data, communication_timeline, crm_conversation_details
                FROM leads
                WHERE structured_data IS NOT NULL AND structured_data != ''
            """)
            
            leads = cursor.fetchall()
            print(f"📊 Processing {len(leads)} leads for amenity extraction...")
            
            total_extracted = 0
            leads_processed = 0
            amenities_by_lead = {}
            
            for lead_id, structured_data_json, timeline, crm_details in leads:
                try:
                    # Parse structured data
                    structured_data = json.loads(structured_data_json) if structured_data_json else {}
                    
                    # Extract from structured data
                    amenities = self._extract_from_structured_data(structured_data)
                    
                    # Extract from timeline text
                    if timeline:
                        timeline_amenities = self._extract_from_text(timeline)
                        amenities.update(timeline_amenities)
                    
                    # Extract from CRM details
                    if crm_details:
                        crm_amenities = self._extract_from_text(crm_details)
                        amenities.update(crm_amenities)
                    
                    # Get RAG documents for this lead
                    cursor.execute("""
                        SELECT content FROM rag_documents
                        WHERE lead_id = ? AND chunk_type IN ('conversation_summary', 'conversation_insights')
                    """, (lead_id,))
                    
                    rag_docs = cursor.fetchall()
                    for (content,) in rag_docs:
                        if content:
                            rag_amenities = self._extract_from_text(content)
                            amenities.update(rag_amenities)
                    
                    # Insert amenities
                    for amenity in amenities:
                        if amenity and len(amenity.strip()) > 0:
                            # Check if already exists
                            cursor.execute("""
                                SELECT COUNT(*) FROM lead_amenities
                                WHERE lead_id = ? AND amenity = ?
                            """, (lead_id, amenity))
                            
                            if cursor.fetchone()[0] == 0:
                                cursor.execute("""
                                    INSERT INTO lead_amenities (lead_id, amenity)
                                    VALUES (?, ?)
                                """, (lead_id, amenity))
                                total_extracted += 1
                    
                    amenities_by_lead[lead_id] = len(amenities)
                    leads_processed += 1
                    
                    if leads_processed % 50 == 0:
                        print(f"   ✅ Processed {leads_processed}/{len(leads)} leads...")
                        conn.commit()
                
                except Exception as e:
                    print(f"   ⚠️  Error processing lead {lead_id}: {str(e)}")
                    continue
            
            conn.commit()
            
            # Get statistics
            cursor.execute("SELECT COUNT(DISTINCT lead_id) FROM lead_amenities")
            leads_with_amenities = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM lead_amenities")
            total_amenities = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT amenity, COUNT(*) as count
                FROM lead_amenities
                GROUP BY amenity
                ORDER BY count DESC
                LIMIT 10
            """)
            top_amenities = cursor.fetchall()
            
            stats = {
                "leads_processed": leads_processed,
                "leads_with_amenities": leads_with_amenities,
                "total_amenities_extracted": total_extracted,
                "total_amenities_in_db": total_amenities,
                "top_amenities": [{"amenity": row[0], "count": row[1]} for row in top_amenities]
            }
            
            return stats
            
        except sqlite3.Error as e:
            raise RuntimeError(f"Database error extracting amenities: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error extracting amenities: {str(e)}")
        finally:
            if conn:
                conn.close()


if __name__ == "__main__":
    print("="*60)
    print("🏠 AMENITY EXTRACTION")
    print("="*60)
    
    extractor = AmenityExtractor()
    stats = extractor.extract_all_amenities()
    
    print("\n" + "="*60)
    print("✅ EXTRACTION COMPLETE")
    print("="*60)
    print(f"Leads processed: {stats['leads_processed']}")
    print(f"Leads with amenities: {stats['leads_with_amenities']}")
    print(f"Total amenities extracted: {stats['total_amenities_extracted']}")
    print(f"Total amenities in DB: {stats['total_amenities_in_db']}")
    print("\nTop 10 Amenities:")
    for i, amenity in enumerate(stats['top_amenities'], 1):
        print(f"   {i}. {amenity['amenity']}: {amenity['count']} leads")
    print("="*60)

