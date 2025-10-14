"""
ChatGPT API integration module for the Voice ID System.
Handles voice analysis, transcription, and identity verification using OpenAI's API.
"""

import openai
import json
import tempfile
import os
import soundfile as sf
from typing import Dict, List, Optional, Tuple
from .config import Config
import numpy as np

class ChatGPTAnalyzer:
    """ChatGPT analyzer class for voice analysis and transcription."""
    
    def __init__(self):
        """Initialize the ChatGPT analyzer."""
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
    def transcribe_audio(self, audio_data: np.ndarray, language: str = None) -> Dict[str, any]: # type: ignore
        """
        Transcribe audio using OpenAI's Whisper API.
        
        Args:
            audio_data: Audio data as numpy array
            language: Language code (optional)
            
        Returns:
            Dictionary containing transcription and metadata
        """
        try:
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, Config.SAMPLE_RATE)
                temp_filename = temp_file.name
            
            try:
                # Transcribe using Whisper
                with open(temp_filename, 'rb') as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language=language,
                        response_format="verbose_json"
                    )
                
                result = {
                    'text': transcript.text,
                    'language': transcript.language if hasattr(transcript, 'language') else None,
                    'duration': transcript.duration if hasattr(transcript, 'duration') else None,
                    'segments': transcript.segments if hasattr(transcript, 'segments') else []
                }
                
                return result
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
                    
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return {'text': '', 'error': str(e)}
    
    def analyze_voice_characteristics(self, features: Dict, transcript: str = "") -> Dict[str, any]: # type: ignore
        """
        Analyze voice characteristics using ChatGPT.
        
        Args:
            features: Extracted voice features
            transcript: Audio transcript (optional)
            
        Returns:
            Dictionary containing voice analysis
        """
        try:
            # Prepare features summary for analysis
            features_summary = self._create_features_summary(features)
            
            # Create analysis prompt
            prompt = f"""
            Analyze the following voice characteristics and provide insights:
            
            Voice Features:
            {features_summary}
            
            Transcript (if available): "{transcript}"
            
            Please provide analysis on:
            1. Voice characteristics (pitch, tone, speaking rate)
            2. Estimated speaker demographics (age range, gender - if determinable)
            3. Speech patterns and style
            4. Emotional tone or state
            5. Unique identifying features
            6. Confidence level in analysis (1-10)
            
            Format your response as JSON with the following structure:
            {{
                "voice_characteristics": {{
                    "pitch": "description",
                    "tone": "description",
                    "speaking_rate": "description"
                }},
                "demographics": {{
                    "estimated_age_range": "range",
                    "estimated_gender": "male/female/uncertain",
                    "confidence": "1-10"
                }},
                "speech_patterns": "description",
                "emotional_tone": "description",
                "unique_features": ["feature1", "feature2"],
                "overall_confidence": "1-10",
                "analysis_notes": "additional notes"
            }}
            """
            
            # Get analysis from ChatGPT
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert voice analyst. Provide detailed, objective analysis based on the voice features provided."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Parse JSON response
            analysis_text = response.choices[0].message.content
            
            # Try to extract JSON from response
            try:
                # Find JSON in response
                json_start = analysis_text.find('{') # type: ignore
                json_end = analysis_text.rfind('}') + 1 # type: ignore
                if json_start >= 0 and json_end > json_start:
                    json_str = analysis_text[json_start:json_end] # type: ignore
                    analysis = json.loads(json_str)
                else:
                    analysis = {"error": "Could not parse JSON response", "raw_response": analysis_text}
            except json.JSONDecodeError:
                analysis = {"error": "Invalid JSON in response", "raw_response": analysis_text}
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing voice characteristics: {e}")
            return {'error': str(e)}
    
    def compare_voices(self, features1: Dict, features2: Dict, transcript1: str = "", transcript2: str = "") -> Dict[str, any]: # type: ignore
        """
        Compare two voice samples using ChatGPT analysis.
        
        Args:
            features1: Features from first voice sample
            features2: Features from second voice sample
            transcript1: Transcript from first sample
            transcript2: Transcript from second sample
            
        Returns:
            Dictionary containing comparison results
        """
        try:
            # Create feature summaries
            summary1 = self._create_features_summary(features1)
            summary2 = self._create_features_summary(features2)
            
            prompt = f"""
            Compare these two voice samples and determine if they are from the same speaker:
            
            Voice Sample 1:
            Features: {summary1}
            Transcript: "{transcript1}"
            
            Voice Sample 2:
            Features: {summary2}
            Transcript: "{transcript2}"
            
            Please analyze:
            1. Similarity in voice characteristics (pitch, tone, speaking rate)
            2. Similarity in speech patterns
            3. Overall likelihood they are the same speaker
            4. Key differences or similarities
            5. Confidence level in your assessment
            
            Format response as JSON:
            {{
                "same_speaker_probability": "0.0-1.0",
                "confidence_level": "1-10",
                "similarities": ["similarity1", "similarity2"],
                "differences": ["difference1", "difference2"],
                "key_indicators": ["indicator1", "indicator2"],
                "recommendation": "accept/reject/uncertain",
                "analysis_notes": "detailed notes"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert voice comparison analyst. Provide detailed, objective comparison based on the voice features provided."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                json_start = analysis_text.find('{') # type: ignore
                json_end = analysis_text.rfind('}') + 1 # type: ignore
                if json_start >= 0 and json_end > json_start:
                    json_str = analysis_text[json_start:json_end] # type: ignore
                    comparison = json.loads(json_str)
                else:
                    comparison = {"error": "Could not parse JSON response", "raw_response": analysis_text}
            except json.JSONDecodeError:
                comparison = {"error": "Invalid JSON in response", "raw_response": analysis_text}
            
            return comparison
            
        except Exception as e:
            print(f"Error comparing voices: {e}")
            return {'error': str(e)}
    
    def generate_voice_profile(self, features: Dict, transcript: str = "", user_name: str = "") -> Dict[str, any]: # type: ignore
        """
        Generate a comprehensive voice profile using ChatGPT analysis.
        
        Args:
            features: Extracted voice features
            transcript: Audio transcript
            user_name: User name for profile
            
        Returns:
            Dictionary containing voice profile
        """
        try:
            features_summary = self._create_features_summary(features)
            
            prompt = f"""
            Create a comprehensive voice profile for user: {user_name}
            
            Voice Features:
            {features_summary}
            
            Sample Speech: "{transcript}"
            
            Generate a detailed voice profile including:
            1. Distinctive voice characteristics
            2. Speech patterns and habits
            3. Unique identifiers
            4. Voice quality assessment
            5. Profile summary for identification purposes
            
            Format as JSON:
            {{
                "user_name": "{user_name}",
                "profile_id": "generated_unique_id",
                "distinctive_features": {{
                    "pitch_characteristics": "description",
                    "tone_quality": "description",
                    "speaking_rhythm": "description",
                    "accent_dialect": "description"
                }},
                "speech_patterns": ["pattern1", "pattern2"],
                "unique_identifiers": ["identifier1", "identifier2"],
                "voice_quality": {{
                    "clarity": "1-10",
                    "distinctiveness": "1-10",
                    "consistency": "1-10"
                }},
                "profile_summary": "comprehensive summary",
                "identification_keywords": ["keyword1", "keyword2"],
                "created_timestamp": "timestamp"
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert voice profiling specialist. Create detailed, accurate voice profiles for identification purposes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            profile_text = response.choices[0].message.content
            
            # Parse JSON response
            try:
                json_start = profile_text.find('{') # type: ignore
                json_end = profile_text.rfind('}') + 1 # type: ignore
                if json_start >= 0 and json_end > json_start:
                    json_str = profile_text[json_start:json_end] # type: ignore
                    profile = json.loads(json_str)
                    
                    # Add timestamp if not present
                    if 'created_timestamp' not in profile:
                        from datetime import datetime
                        profile['created_timestamp'] = datetime.now().isoformat()
                        
                else:
                    profile = {"error": "Could not parse JSON response", "raw_response": profile_text}
            except json.JSONDecodeError:
                profile = {"error": "Invalid JSON in response", "raw_response": profile_text}
            
            return profile
            
        except Exception as e:
            print(f"Error generating voice profile: {e}")
            return {'error': str(e)}
    
    def _create_features_summary(self, features: Dict) -> str:
        """Create a human-readable summary of voice features."""
        if not features:
            return "No features available"
        
        summary_parts = []
        
        # Basic audio properties
        if 'duration' in features:
            summary_parts.append(f"Duration: {features['duration']:.2f} seconds")
        
        if 'rms_energy' in features:
            summary_parts.append(f"Audio Energy: {features['rms_energy']:.4f}")
        
        # Prosodic features
        prosodic_features = ['pitch_mean', 'pitch_std', 'pitch_range', 'speaking_rate']
        prosodic_summary = []
        for feature in prosodic_features:
            if feature in features:
                prosodic_summary.append(f"{feature}: {features[feature]:.2f}")
        
        if prosodic_summary:
            summary_parts.append("Prosodic: " + ", ".join(prosodic_summary))
        
        # Spectral features
        spectral_features = ['spectral_centroid_mean', 'spectral_rolloff_mean', 'zero_crossing_rate_mean']
        spectral_summary = []
        for feature in spectral_features:
            if feature in features:
                spectral_summary.append(f"{feature}: {features[feature]:.2f}")
        
        if spectral_summary:
            summary_parts.append("Spectral: " + ", ".join(spectral_summary))
        
        # MFCC features summary
        if 'mfcc' in features and features['mfcc']:
            mfcc_mean = np.mean(features['mfcc'][:8])  # First 8 coefficients
            summary_parts.append(f"MFCC (avg first 8): {mfcc_mean:.4f}")
        
        return " | ".join(summary_parts)