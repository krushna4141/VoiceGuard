"""
Main Voice ID System application.
Integrates all components for voice identification and user enrollment.
"""

import os
import time
from typing import Dict, List, Optional, Tuple
import numpy as np
from .config import Config
from .voice_recorder import VoiceRecorder
from .voice_processor import VoiceProcessor
from .chatgpt_analyzer import ChatGPTAnalyzer
from .database_manager import DatabaseManager

class VoiceIDSystem:
    """Main Voice ID System class that orchestrates all components."""
    
    def __init__(self):
        """Initialize the Voice ID System."""
        print("Initializing Voice ID System...")
        
        # Initialize components
        try:
            self.recorder = VoiceRecorder()
            self.processor = VoiceProcessor()
            self.analyzer = ChatGPTAnalyzer()
            self.database = DatabaseManager()
            
            print("✓ All components initialized successfully!")
            
        except Exception as e:
            print(f"✗ Error initializing system: {e}")
            raise
    
    def enroll_user(self, username: str, full_name: str = "", email: str = "") -> bool:
        """
        Enroll a new user in the system.
        
        Args:
            username: Unique username
            full_name: Full name of user
            email: Email address
            
        Returns:
            True if enrollment successful
        """
        try:
            print(f"\n=== Enrolling User: {username} ===")
            
            # Check if user already exists
            existing_user = self.database.get_user(username=username)
            if existing_user:
                print(f"Error: User '{username}' already exists!")
                return False
            
            # Create user
            user_id = self.database.create_user(username, full_name, email)
            
            # Start enrollment session
            session_id = self.database.start_enrollment_session(user_id, required_samples=3)
            
            print(f"User created with ID: {user_id}")
            print("Starting voice enrollment process...")
            
            # Collect voice samples
            samples_collected = 0
            required_samples = 3
            voice_profiles = []
            
            while samples_collected < required_samples:
                print(f"\n--- Voice Sample {samples_collected + 1}/{required_samples} ---")
                print("Please speak clearly for 5 seconds when prompted...")
                input("Press Enter when ready to record...")
                
                # Record voice sample
                print("🎤 Recording...")
                audio_data = self.recorder.record_audio()
                
                if self.recorder.is_audio_silent(audio_data):
                    print("⚠️  Audio too quiet. Please try again.")
                    continue
                
                print("✓ Recording completed!")
                
                # Process audio and extract features
                print("🔄 Processing audio...")
                features = self.processor.extract_all_features(audio_data)
                
                if not features:
                    print("⚠️  Could not extract features. Please try again.")
                    continue
                
                # Transcribe audio
                print("📝 Transcribing audio...")
                transcript_result = self.analyzer.transcribe_audio(audio_data)
                transcript = transcript_result.get('text', '')
                
                # Analyze voice characteristics
                print("🧠 Analyzing voice characteristics...")
                analysis = self.analyzer.analyze_voice_characteristics(features, transcript)
                
                if 'error' in analysis:
                    print(f"⚠️  Analysis error: {analysis['error']}")
                    # Continue anyway with basic features
                    analysis = {"analysis_notes": "Basic analysis only"}
                
                # Create voice fingerprint
                fingerprint = self.processor.create_voice_fingerprint(features)
                
                # Generate voice profile
                profile_analysis = self.analyzer.generate_voice_profile(
                    features, transcript, username
                )
                
                # Store voice profile
                profile_id = self.database.add_voice_profile(
                    user_id=user_id,
                    profile_name=f"Enrollment Sample {samples_collected + 1}",
                    voice_features=features,
                    chatgpt_analysis=profile_analysis,
                    voice_fingerprint=fingerprint,
                    transcript=transcript,
                    audio_duration=features.get('duration', 0.0),
                    confidence_score=self._calculate_confidence_score(features, analysis),
                    is_primary=(samples_collected == 0)  # First sample is primary
                )
                
                voice_profiles.append({
                    'profile_id': profile_id,
                    'features': features,
                    'transcript': transcript
                })
                
                samples_collected += 1
                print(f"✓ Sample {samples_collected} processed and stored!")
            
            # Complete enrollment session
            self.database.complete_enrollment_session(session_id, "completed")
            
            # Calculate overall enrollment quality
            overall_quality = self._evaluate_enrollment_quality(voice_profiles)
            
            print(f"\n🎉 Enrollment completed successfully!")
            print(f"📊 Enrollment Quality: {overall_quality:.1f}/10")
            print(f"👤 User '{username}' is now registered in the system.")
            
            return True
            
        except Exception as e:
            print(f"❌ Enrollment failed: {e}")
            # Mark session as failed if it was created
            try:
                if 'session_id' in locals():
                    self.database.complete_enrollment_session(session_id, "failed")
            except:
                pass
            return False
    
    def identify_user(self, username_hint: str = None) -> Dict: # type: ignore
        """
        Identify a user by their voice.
        
        Args:
            username_hint: Optional username hint to narrow search
            
        Returns:
            Dictionary with identification results
        """
        try:
            print("\n=== Voice Identification ===")
            
            if username_hint:
                print(f"Attempting to verify user: {username_hint}")
            else:
                print("Attempting to identify unknown speaker...")
            
            print("Please speak clearly for 5 seconds when prompted...")
            input("Press Enter when ready to record...")
            
            # Record voice sample
            print("🎤 Recording...")
            audio_data = self.recorder.record_audio()
            
            if self.recorder.is_audio_silent(audio_data):
                result = {
                    'success': False,
                    'error': 'Audio too quiet or silent',
                    'confidence': 0.0
                }
                self._log_authentication_attempt(None, username_hint or "", False, 0.0, 0.0, error_message=result['error']) # type: ignore
                return result
            
            print("✓ Recording completed!")
            
            # Process audio and extract features
            print("🔄 Processing audio...")
            features = self.processor.extract_all_features(audio_data)
            
            if not features:
                result = {
                    'success': False,
                    'error': 'Could not extract voice features',
                    'confidence': 0.0
                }
                self._log_authentication_attempt(None, username_hint or "", False, 0.0, 0.0, error_message=result['error']) # type: ignore
                return result
            
            # Transcribe audio
            print("📝 Transcribing audio...")
            transcript_result = self.analyzer.transcribe_audio(audio_data)
            transcript = transcript_result.get('text', '')
            
            # Search for matching users
            print("🔍 Searching for voice matches...")
            
            if username_hint:
                # Verify specific user
                result = self._verify_specific_user(username_hint, features, transcript)
            else:
                # Search all users
                result = self._identify_from_all_users(features, transcript)
            
            # Log authentication attempt
            self._log_authentication_attempt(
                result.get('user_id'), # type: ignore
                username_hint or result.get('username', ''),
                result['success'],
                result['confidence'],
                result.get('similarity_score', 0.0),
                error_message=result.get('error', '')
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Identification failed: {e}"
            print(f"❌ {error_msg}")
            result = {
                'success': False,
                'error': error_msg,
                'confidence': 0.0
            }
            self._log_authentication_attempt(None, username_hint or "", False, 0.0, 0.0, error_message=error_msg) # type: ignore
            return result
    
    def _verify_specific_user(self, username: str, features: Dict, transcript: str) -> Dict:
        """Verify a specific user by their voice."""
        # Get user from database
        user = self.database.get_user(username=username)
        if not user:
            return {
                'success': False,
                'error': f"User '{username}' not found",
                'confidence': 0.0
            }
        
        # Get user's voice profiles
        profiles = self.database.get_voice_profiles(user['user_id'])
        if not profiles:
            return {
                'success': False,
                'error': f"No voice profiles found for user '{username}'",
                'confidence': 0.0
            }
        
        # Compare with stored profiles
        best_match = None
        best_similarity = 0.0
        
        for profile in profiles:
            similarity = self.processor.calculate_similarity(features, profile['voice_features'])
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = profile
        
        # Use ChatGPT for additional comparison if we have a good match
        chatgpt_confidence = 0.5  # Default
        if best_match and best_similarity > 0.6:
            print("🧠 Performing advanced voice comparison...")
            comparison = self.analyzer.compare_voices(
                features, best_match['voice_features'],
                transcript, best_match.get('transcript', '')
            )
            
            if 'same_speaker_probability' in comparison:
                try:
                    chatgpt_confidence = float(comparison['same_speaker_probability'])
                except:
                    chatgpt_confidence = 0.5
        
        # Combined confidence score
        combined_confidence = (best_similarity * 0.6) + (chatgpt_confidence * 0.4)
        
        # Determine if authentication is successful
        success = (
            best_similarity >= Config.SIMILARITY_THRESHOLD and
            combined_confidence >= Config.MIN_CONFIDENCE_SCORE
        )
        
        result = {
            'success': success,
            'user_id': user['user_id'],
            'username': username,
            'full_name': user.get('full_name', ''),
            'confidence': combined_confidence,
            'similarity_score': best_similarity,
            'transcript': transcript
        }
        
        if success:
            print(f"✅ User '{username}' verified successfully!")
            print(f"📊 Confidence: {combined_confidence:.2f}")
        else:
            result['error'] = f"Voice verification failed (confidence: {combined_confidence:.2f})"
            print(f"❌ {result['error']}")
        
        return result
    
    def _identify_from_all_users(self, features: Dict, transcript: str) -> Dict:
        """Identify user from all enrolled users."""
        # Search database for similar voices
        matches = self.database.search_users_by_voice(features, similarity_threshold=0.6)
        
        if not matches:
            return {
                'success': False,
                'error': 'No matching voice found in database',
                'confidence': 0.0,
                'transcript': transcript
            }
        
        # Take the best match
        best_match = matches[0]
        
        # Additional ChatGPT verification for top match
        user = self.database.get_user(user_id=best_match['user_id'])
        primary_profile = self.database.get_primary_voice_profile(best_match['user_id'])
        
        chatgpt_confidence = 0.5
        if primary_profile:
            print("🧠 Performing advanced voice comparison...")
            comparison = self.analyzer.compare_voices(
                features, primary_profile['voice_features'],
                transcript, primary_profile.get('transcript', '')
            )
            
            if 'same_speaker_probability' in comparison:
                try:
                    chatgpt_confidence = float(comparison['same_speaker_probability'])
                except:
                    pass
        
        # Combined confidence
        combined_confidence = (best_match['similarity_score'] * 0.6) + (chatgpt_confidence * 0.4)
        
        success = combined_confidence >= Config.MIN_CONFIDENCE_SCORE
        
        result = {
            'success': success,
            'user_id': best_match['user_id'],
            'username': best_match['username'],
            'full_name': best_match.get('full_name', ''),
            'confidence': combined_confidence,
            'similarity_score': best_match['similarity_score'],
            'transcript': transcript
        }
        
        if success:
            print(f"✅ User identified: {best_match['username']}")
            print(f"📊 Confidence: {combined_confidence:.2f}")
        else:
            result['error'] = f"Identification confidence too low: {combined_confidence:.2f}"
            print(f"❌ {result['error']}")
        
        return result
    
    def list_users(self) -> List[Dict]:
        """List all enrolled users."""
        return self.database.list_users()
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get detailed information about a user."""
        user = self.database.get_user(username=username)
        if not user:
            return None
        
        # Get voice profiles
        profiles = self.database.get_voice_profiles(user['user_id'])
        
        # Get recent authentication logs
        auth_logs = self.database.get_authentication_logs(user['user_id'], limit=10)
        
        return {
            'user_info': user,
            'voice_profiles': len(profiles),
            'recent_authentications': len([log for log in auth_logs if log['success']]),
            'failed_attempts': len([log for log in auth_logs if not log['success']]),
            'last_authentication': auth_logs[0]['timestamp'] if auth_logs else None
        }
    
    def delete_user(self, username: str, confirm: bool = False) -> bool:
        """Delete a user from the system."""
        if not confirm:
            print("⚠️  This action requires confirmation. Set confirm=True to proceed.")
            return False
        
        user = self.database.get_user(username=username)
        if not user:
            print(f"User '{username}' not found.")
            return False
        
        self.database.delete_user(user['user_id'])
        print(f"User '{username}' has been deactivated.")
        return True
    
    def get_system_stats(self) -> Dict:
        """Get system statistics."""
        users = self.database.list_users()
        all_logs = self.database.get_authentication_logs(limit=1000)
        
        successful_auths = len([log for log in all_logs if log['success']])
        failed_auths = len([log for log in all_logs if not log['success']])
        
        return {
            'total_users': len(users),
            'total_authentications': len(all_logs),
            'successful_authentications': successful_auths,
            'failed_authentications': failed_auths,
            'success_rate': successful_auths / len(all_logs) if all_logs else 0.0
        }
    
    def test_microphone(self) -> bool:
        """Test microphone functionality."""
        try:
            print("\n=== Microphone Test ===")
            devices = self.recorder.list_audio_devices()
            
            print("Available audio input devices:")
            for device_id, device_info in devices.items():
                print(f"  {device_id}: {device_info['name']}")
            
            print("\nTesting microphone... Speak for 3 seconds.")
            input("Press Enter to start test...")
            
            audio_data = self.recorder.record_audio(duration=3)
            
            level = self.recorder.get_audio_level(audio_data)
            print(f"Audio level: {level:.4f}")
            
            if level < 0.001:
                print("❌ Microphone test failed - no audio detected")
                return False
            elif level < 0.01:
                print("⚠️  Audio level low - check microphone volume")
                return True
            else:
                print("✅ Microphone test passed!")
                return True
                
        except Exception as e:
            print(f"❌ Microphone test failed: {e}")
            return False
    
    def _calculate_confidence_score(self, features: Dict, analysis: Dict) -> float:
        """Calculate confidence score for voice sample quality."""
        score = 0.5  # Base score
        
        # Audio quality factors
        if 'rms_energy' in features:
            if features['rms_energy'] > 0.01:
                score += 0.1
            if features['rms_energy'] > 0.05:
                score += 0.1
        
        if 'duration' in features:
            if features['duration'] >= 3.0:
                score += 0.1
            if features['duration'] >= 5.0:
                score += 0.1
        
        # Voice features quality
        if 'mfcc' in features and features['mfcc']:
            score += 0.1
        
        if 'pitch_mean' in features and features['pitch_mean'] > 0:
            score += 0.1
        
        # ChatGPT analysis confidence
        if isinstance(analysis, dict) and 'overall_confidence' in analysis:
            try:
                gpt_confidence = float(analysis['overall_confidence']) / 10.0
                score += gpt_confidence * 0.2
            except:
                pass
        
        return min(1.0, score)
    
    def _evaluate_enrollment_quality(self, voice_profiles: List[Dict]) -> float:
        """Evaluate overall enrollment quality."""
        if not voice_profiles:
            return 0.0
        
        # Calculate average similarity between samples
        similarities = []
        for i in range(len(voice_profiles)):
            for j in range(i + 1, len(voice_profiles)):
                similarity = self.processor.calculate_similarity(
                    voice_profiles[i]['features'],
                    voice_profiles[j]['features']
                )
                similarities.append(similarity)
        
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.5
        
        # Quality score based on consistency and feature richness
        quality = avg_similarity * 10.0
        
        # Bonus for good transcripts
        transcript_bonus = 0
        for profile in voice_profiles:
            if profile['transcript'] and len(profile['transcript']) > 10:
                transcript_bonus += 1
        
        quality += (transcript_bonus / len(voice_profiles)) * 2.0
        
        return min(10.0, quality)
    
    def _log_authentication_attempt(self, user_id: str, attempted_username: str, 
                                   success: bool, confidence: float, similarity: float,
                                   error_message: str = ""):
        """Log authentication attempt to database."""
        try:
            self.database.log_authentication_attempt(
                user_id=user_id,
                attempted_username=attempted_username,
                success=success,
                confidence_score=confidence,
                similarity_score=similarity,
                method="voice",
                error_message=error_message
            )
        except Exception as e:
            print(f"Warning: Could not log authentication attempt: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self, 'recorder'):
                del self.recorder
        except:
            pass