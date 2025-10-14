"""
Database management module for the Voice ID System.
Handles user voice profile storage, enrollment, and retrieval.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from .config import Config
import uuid

class DatabaseManager:
    """Database manager class for voice profile storage and management."""
    
    def __init__(self, db_path: str = None): # type: ignore
        """
        Initialize database manager.
        
        Args:
            db_path: Path to database file (optional, uses config default)
        """
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create tables if they don't exist."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    full_name TEXT,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    enrollment_count INTEGER DEFAULT 0
                )
            ''')
            
            # Create voice_profiles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS voice_profiles (
                    profile_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    profile_name TEXT,
                    voice_features TEXT,  -- JSON string of features
                    chatgpt_analysis TEXT,  -- JSON string of ChatGPT analysis
                    voice_fingerprint TEXT,
                    transcript TEXT,
                    audio_duration REAL,
                    confidence_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_primary BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create authentication_logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS authentication_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    attempted_username TEXT,
                    success BOOLEAN,
                    confidence_score REAL,
                    similarity_score REAL,
                    method TEXT,  -- 'voice', 'combined', etc.
                    error_message TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create enrollment_sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enrollment_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    session_status TEXT,  -- 'in_progress', 'completed', 'failed'
                    samples_collected INTEGER DEFAULT 0,
                    required_samples INTEGER DEFAULT 3,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
            print(f"Database initialized at: {self.db_path}")
    
    def create_user(self, username: str, full_name: str = "", email: str = "") -> str:
        """
        Create a new user.
        
        Args:
            username: Unique username
            full_name: Full name of user
            email: Email address
            
        Returns:
            User ID of created user
        """
        user_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO users (user_id, username, full_name, email)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, username, full_name, email))
                
                conn.commit()
                print(f"User '{username}' created with ID: {user_id}")
                return user_id
                
            except sqlite3.IntegrityError as e:
                print(f"Error creating user: {e}")
                if "username" in str(e):
                    raise ValueError(f"Username '{username}' already exists")
                raise
    
    def get_user(self, username: str = None, user_id: str = None) -> Optional[Dict]: # type: ignore
        """
        Get user information.
        
        Args:
            username: Username to search for
            user_id: User ID to search for
            
        Returns:
            User information dictionary or None
        """
        if not username and not user_id:
            raise ValueError("Either username or user_id must be provided")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if username:
                cursor.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,))
            else:
                cursor.execute('SELECT * FROM users WHERE user_id = ? AND is_active = 1', (user_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def list_users(self, active_only: bool = True) -> List[Dict]:
        """
        List all users.
        
        Args:
            active_only: Only return active users
            
        Returns:
            List of user dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = 'SELECT * FROM users'
            if active_only:
                query += ' WHERE is_active = 1'
            query += ' ORDER BY username'
            
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def start_enrollment_session(self, user_id: str, required_samples: int = 3) -> str:
        """
        Start a new enrollment session for a user.
        
        Args:
            user_id: User ID
            required_samples: Number of voice samples required
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO enrollment_sessions (session_id, user_id, session_status, required_samples)
                VALUES (?, ?, 'in_progress', ?)
            ''', (session_id, user_id, required_samples))
            
            conn.commit()
            print(f"Enrollment session started for user {user_id}: {session_id}")
            return session_id
    
    def add_voice_profile(self, user_id: str, profile_name: str, voice_features: Dict, 
                         chatgpt_analysis: Dict, voice_fingerprint: str, 
                         transcript: str = "", audio_duration: float = 0.0,
                         confidence_score: float = 0.0, is_primary: bool = False) -> str:
        """
        Add a voice profile for a user.
        
        Args:
            user_id: User ID
            profile_name: Name/description of this profile
            voice_features: Extracted voice features
            chatgpt_analysis: ChatGPT analysis results
            voice_fingerprint: Voice fingerprint string
            transcript: Audio transcript
            audio_duration: Duration of audio sample
            confidence_score: Quality/confidence score
            is_primary: Whether this is the primary profile
            
        Returns:
            Profile ID
        """
        profile_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO voice_profiles (
                    profile_id, user_id, profile_name, voice_features, chatgpt_analysis,
                    voice_fingerprint, transcript, audio_duration, confidence_score, is_primary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                profile_id, user_id, profile_name, 
                json.dumps(voice_features), json.dumps(chatgpt_analysis),
                voice_fingerprint, transcript, audio_duration, confidence_score, is_primary
            ))
            
            # Update user enrollment count
            cursor.execute('''
                UPDATE users 
                SET enrollment_count = enrollment_count + 1, last_updated = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            print(f"Voice profile added for user {user_id}: {profile_id}")
            return profile_id
    
    def get_voice_profiles(self, user_id: str) -> List[Dict]:
        """
        Get all voice profiles for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of voice profile dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM voice_profiles 
                WHERE user_id = ? 
                ORDER BY is_primary DESC, created_at DESC
            ''', (user_id,))
            
            profiles = []
            for row in cursor.fetchall():
                profile = dict(row)
                # Parse JSON fields
                profile['voice_features'] = json.loads(profile['voice_features'])
                profile['chatgpt_analysis'] = json.loads(profile['chatgpt_analysis'])
                profiles.append(profile)
            
            return profiles
    
    def get_primary_voice_profile(self, user_id: str) -> Optional[Dict]:
        """
        Get the primary voice profile for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Primary voice profile or None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM voice_profiles 
                WHERE user_id = ? AND is_primary = 1
                ORDER BY created_at DESC
                LIMIT 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            if row:
                profile = dict(row)
                profile['voice_features'] = json.loads(profile['voice_features'])
                profile['chatgpt_analysis'] = json.loads(profile['chatgpt_analysis'])
                return profile
            
            return None
    
    def search_users_by_voice(self, voice_features: Dict, similarity_threshold: float = 0.8) -> List[Dict]:
        """
        Search for users by voice similarity.
        
        Args:
            voice_features: Voice features to search for
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of matching users with similarity scores
        """
        # This is a simplified implementation
        # In a production system, you'd want to use more sophisticated similarity search
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all voice profiles
            cursor.execute('''
                SELECT vp.*, u.username, u.full_name 
                FROM voice_profiles vp 
                JOIN users u ON vp.user_id = u.user_id 
                WHERE u.is_active = 1
            ''')
            
            matches = []
            for row in cursor.fetchall():
                profile = dict(row)
                stored_features = json.loads(profile['voice_features'])
                
                # Calculate similarity (this would be done by VoiceProcessor in real implementation)
                # For now, we'll use a simplified approach
                similarity = self._calculate_simple_similarity(voice_features, stored_features)
                
                if similarity >= similarity_threshold:
                    matches.append({
                        'user_id': profile['user_id'],
                        'username': profile['username'],
                        'full_name': profile['full_name'],
                        'profile_id': profile['profile_id'],
                        'similarity_score': similarity,
                        'confidence_score': profile['confidence_score']
                    })
            
            # Sort by similarity score descending
            matches.sort(key=lambda x: x['similarity_score'], reverse=True)
            return matches
    
    def log_authentication_attempt(self, user_id: str = None, attempted_username: str = "", # type: ignore
                                  success: bool = False, confidence_score: float = 0.0,
                                  similarity_score: float = 0.0, method: str = "voice",
                                  error_message: str = ""):
        """
        Log an authentication attempt.
        
        Args:
            user_id: User ID (if successful)
            attempted_username: Username that was attempted
            success: Whether authentication was successful
            confidence_score: Confidence score of the attempt
            similarity_score: Voice similarity score
            method: Authentication method used
            error_message: Error message if failed
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO authentication_logs (
                    user_id, attempted_username, success, confidence_score,
                    similarity_score, method, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, attempted_username, success, confidence_score, 
                  similarity_score, method, error_message))
            
            conn.commit()
    
    def get_authentication_logs(self, user_id: str = None, limit: int = 100) -> List[Dict]: # type: ignore
        """
        Get authentication logs.
        
        Args:
            user_id: Filter by user ID (optional)
            limit: Maximum number of logs to return
            
        Returns:
            List of authentication log dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = '''
                SELECT al.*, u.username, u.full_name 
                FROM authentication_logs al 
                LEFT JOIN users u ON al.user_id = u.user_id
            '''
            params = []
            
            if user_id:
                query += ' WHERE al.user_id = ?'
                params.append(user_id)
            
            query += ' ORDER BY al.timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def complete_enrollment_session(self, session_id: str, status: str = "completed"):
        """
        Complete an enrollment session.
        
        Args:
            session_id: Session ID
            status: Final status ('completed', 'failed')
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE enrollment_sessions 
                SET session_status = ?, completed_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (status, session_id))
            
            conn.commit()
    
    def delete_user(self, user_id: str, hard_delete: bool = False):
        """
        Delete a user (soft delete by default).
        
        Args:
            user_id: User ID to delete
            hard_delete: Whether to permanently delete from database
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if hard_delete:
                # Delete voice profiles first
                cursor.execute('DELETE FROM voice_profiles WHERE user_id = ?', (user_id,))
                # Delete authentication logs
                cursor.execute('DELETE FROM authentication_logs WHERE user_id = ?', (user_id,))
                # Delete enrollment sessions
                cursor.execute('DELETE FROM enrollment_sessions WHERE user_id = ?', (user_id,))
                # Delete user
                cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            else:
                # Soft delete - just mark as inactive
                cursor.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (user_id,))
            
            conn.commit()
            print(f"User {user_id} {'deleted' if hard_delete else 'deactivated'}")
    
    def _calculate_simple_similarity(self, features1: Dict, features2: Dict) -> float:
        """
        Calculate simple similarity between feature sets.
        This is a simplified version - in production you'd use the VoiceProcessor.
        """
        if not features1 or not features2:
            return 0.0
        
        # Get common keys
        common_keys = set(features1.keys()) & set(features2.keys())
        if not common_keys:
            return 0.0
        
        similarities = []
        for key in common_keys:
            if key == 'mfcc' and isinstance(features1[key], list) and isinstance(features2[key], list):
                if len(features1[key]) == len(features2[key]):
                    # Simple cosine similarity for MFCC
                    import numpy as np
                    v1 = np.array(features1[key])
                    v2 = np.array(features2[key])
                    if np.linalg.norm(v1) > 0 and np.linalg.norm(v2) > 0:
                        sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                        similarities.append(max(0, sim))
            elif isinstance(features1[key], (int, float)) and isinstance(features2[key], (int, float)):
                max_val = max(abs(features1[key]), abs(features2[key]), 1e-6)
                sim = 1 - abs(features1[key] - features2[key]) / max_val
                similarities.append(max(0, sim))
        
        return sum(similarities) / len(similarities) if similarities else 0.0