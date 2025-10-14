"""
Voice processing module for the Voice ID System.
Handles audio preprocessing, feature extraction, and voice analysis.
"""

import numpy as np
import librosa
import scipy.signal
from scipy import stats
from typing import Dict, Tuple, Optional, List
import tempfile
import os
from .config import Config

class VoiceProcessor:
    """Voice processing class for audio feature extraction and analysis."""
    
    def __init__(self):
        """Initialize the voice processor."""
        self.sample_rate = Config.SAMPLE_RATE
        
    def preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Preprocess audio data for analysis.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Preprocessed audio data
        """
        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Normalize audio
        audio_data = self._normalize_audio(audio_data)
        
        # Remove silence from beginning and end
        audio_data = self._trim_silence(audio_data)
        
        # Apply pre-emphasis filter
        audio_data = self._apply_preemphasis(audio_data)
        
        return audio_data
    
    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1, 1] range."""
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            return audio_data / max_val
        return audio_data
    
    def _trim_silence(self, audio_data: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """Trim silence from beginning and end of audio."""
        # Find non-silent regions
        non_silent = np.abs(audio_data) > threshold
        
        if np.any(non_silent):
            start_idx = np.argmax(non_silent)
            end_idx = len(audio_data) - np.argmax(non_silent[::-1]) - 1
            return audio_data[start_idx:end_idx+1]
        
        return audio_data
    
    def _apply_preemphasis(self, audio_data: np.ndarray, alpha: float = 0.97) -> np.ndarray:
        """Apply pre-emphasis filter to enhance high frequencies."""
        return np.append(audio_data[0], audio_data[1:] - alpha * audio_data[:-1])
    
    def extract_mfcc_features(self, audio_data: np.ndarray, n_mfcc: int = 13) -> np.ndarray:
        """
        Extract MFCC (Mel-Frequency Cepstral Coefficients) features.
        
        Args:
            audio_data: Preprocessed audio data
            n_mfcc: Number of MFCC coefficients to extract
            
        Returns:
            MFCC features array
        """
        try:
            # Extract MFCC features
            mfcc = librosa.feature.mfcc(
                y=audio_data,
                sr=self.sample_rate,
                n_mfcc=n_mfcc,
                n_fft=2048,
                hop_length=512
            )
            
            # Calculate statistics (mean, std, min, max) for each coefficient
            mfcc_stats = []
            for coeff in mfcc:
                mfcc_stats.extend([
                    np.mean(coeff),
                    np.std(coeff),
                    np.min(coeff),
                    np.max(coeff)
                ])
            
            return np.array(mfcc_stats)
            
        except Exception as e:
            print(f"Error extracting MFCC features: {e}")
            return np.array([])
    
    def extract_spectral_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """
        Extract spectral features from audio.
        
        Args:
            audio_data: Preprocessed audio data
            
        Returns:
            Dictionary of spectral features
        """
        try:
            # Compute spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=self.sample_rate)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=self.sample_rate)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(audio_data)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio_data, sr=self.sample_rate)[0]
            
            features = {
                'spectral_centroid_mean': np.mean(spectral_centroids),
                'spectral_centroid_std': np.std(spectral_centroids),
                'spectral_rolloff_mean': np.mean(spectral_rolloff),
                'spectral_rolloff_std': np.std(spectral_rolloff),
                'zero_crossing_rate_mean': np.mean(zero_crossing_rate),
                'zero_crossing_rate_std': np.std(zero_crossing_rate),
                'spectral_bandwidth_mean': np.mean(spectral_bandwidth),
                'spectral_bandwidth_std': np.std(spectral_bandwidth)
            }
            
            return features
            
        except Exception as e:
            print(f"Error extracting spectral features: {e}")
            return {}
    
    def extract_prosodic_features(self, audio_data: np.ndarray) -> Dict[str, float]:
        """
        Extract prosodic features (pitch, energy, etc.).
        
        Args:
            audio_data: Preprocessed audio data
            
        Returns:
            Dictionary of prosodic features
        """
        try:
            # Extract pitch using librosa
            pitches, magnitudes = librosa.piptrack(y=audio_data, sr=self.sample_rate)
            
            # Get fundamental frequency (F0)
            f0 = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    f0.append(pitch)
            
            # Calculate energy
            energy = np.sum(audio_data ** 2) / len(audio_data)
            
            # Calculate speaking rate (rough estimate)
            speaking_rate = len(f0) / len(audio_data) * self.sample_rate if f0 else 0
            
            features = {
                'pitch_mean': np.mean(f0) if f0 else 0,
                'pitch_std': np.std(f0) if f0 else 0,
                'pitch_min': np.min(f0) if f0 else 0,
                'pitch_max': np.max(f0) if f0 else 0,
                'energy': energy,
                'speaking_rate': speaking_rate,
                'pitch_range': (np.max(f0) - np.min(f0)) if f0 else 0
            }
            
            return features
            
        except Exception as e:
            print(f"Error extracting prosodic features: {e}")
            return {}
    
    def extract_all_features(self, audio_data: np.ndarray) -> Dict[str, any]: # type: ignore
        """
        Extract all voice features from audio data.
        
        Args:
            audio_data: Raw audio data
            
        Returns:
            Dictionary containing all extracted features
        """
        # Preprocess audio
        processed_audio = self.preprocess_audio(audio_data)
        
        if len(processed_audio) == 0:
            print("Warning: Audio is too short or silent after preprocessing")
            return {}
        
        # Extract different types of features
        features = {}
        
        # MFCC features
        mfcc_features = self.extract_mfcc_features(processed_audio)
        if len(mfcc_features) > 0:
            features['mfcc'] = mfcc_features.tolist()
        
        # Spectral features
        spectral_features = self.extract_spectral_features(processed_audio)
        features.update(spectral_features)
        
        # Prosodic features
        prosodic_features = self.extract_prosodic_features(processed_audio)
        features.update(prosodic_features)
        
        # Additional basic features
        features.update({
            'duration': len(audio_data) / self.sample_rate,
            'rms_energy': np.sqrt(np.mean(processed_audio ** 2)),
            'max_amplitude': np.max(np.abs(processed_audio)),
            'audio_length': len(processed_audio)
        })
        
        return features
    
    def calculate_similarity(self, features1: Dict, features2: Dict) -> float:
        """
        Calculate similarity between two feature sets.
        
        Args:
            features1: First feature set
            features2: Second feature set
            
        Returns:
            Similarity score (0-1)
        """
        if not features1 or not features2:
            return 0.0
        
        # Get common feature keys
        common_keys = set(features1.keys()) & set(features2.keys())
        
        if not common_keys:
            return 0.0
        
        similarities = []
        
        for key in common_keys:
            if key == 'mfcc':
                # Special handling for MFCC arrays
                if isinstance(features1[key], list) and isinstance(features2[key], list):
                    if len(features1[key]) == len(features2[key]):
                        # Cosine similarity for MFCC vectors
                        v1 = np.array(features1[key])
                        v2 = np.array(features2[key])
                        cos_sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                        similarities.append(max(0, cos_sim))  # Ensure non-negative
            else:
                # Numerical features - use inverse of normalized absolute difference
                val1 = features1[key]
                val2 = features2[key]
                
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    # Avoid division by zero
                    max_val = max(abs(val1), abs(val2), 1e-6)
                    similarity = 1 - abs(val1 - val2) / max_val
                    similarities.append(max(0, similarity))
        
        # Return average similarity
        return np.mean(similarities) if similarities else 0.0 # type: ignore
    
    def create_voice_fingerprint(self, features: Dict) -> str:
        """
        Create a simplified voice fingerprint for comparison.
        
        Args:
            features: Extracted voice features
            
        Returns:
            Voice fingerprint string
        """
        if not features:
            return ""
        
        # Create fingerprint from key features
        fingerprint_features = []
        
        # MFCC first few coefficients
        if 'mfcc' in features and features['mfcc']:
            mfcc_subset = features['mfcc'][:8]  # First 8 MFCC coefficients
            fingerprint_features.extend([f"{x:.3f}" for x in mfcc_subset])
        
        # Key prosodic features
        prosodic_keys = ['pitch_mean', 'pitch_std', 'energy', 'speaking_rate']
        for key in prosodic_keys:
            if key in features:
                fingerprint_features.append(f"{features[key]:.3f}")
        
        return "_".join(fingerprint_features)