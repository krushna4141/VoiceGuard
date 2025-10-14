"""
Voice recording module for the Voice ID System.
Handles audio recording from microphone with proper format handling.
"""

import pyaudio
import numpy as np
import soundfile as sf
import threading
import time
from typing import Optional, Tuple
from .config import Config

class VoiceRecorder:
    """Voice recording class for capturing audio from microphone."""
    
    def __init__(self):
        """Initialize the voice recorder."""
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.recorded_frames = []
        
    def __del__(self):
        """Clean up PyAudio instance."""
        if hasattr(self, 'audio'):
            self.audio.terminate()
    
    def list_audio_devices(self) -> dict:
        """List available audio input devices."""
        devices = {}
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:  # Input device # type: ignore
                devices[i] = {
                    'name': device_info['name'],
                    'channels': device_info['maxInputChannels'],
                    'sample_rate': int(device_info['defaultSampleRate'])
                }
        return devices
    
    def record_audio(self, duration: int = None, device_index: Optional[int] = None) -> np.ndarray: # type: ignore
        """
        Record audio from microphone.
        
        Args:
            duration: Recording duration in seconds (None for manual stop)
            device_index: Audio device index (None for default)
            
        Returns:
            numpy array containing audio data
        """
        if duration is None:
            duration = Config.RECORD_SECONDS
            
        print(f"Recording for {duration} seconds...")
        
        try:
            # Configure recording stream
            stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=Config.CHANNELS,
                rate=Config.SAMPLE_RATE,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=Config.CHUNK_SIZE
            )
            
            frames = []
            
            # Record audio
            for _ in range(int(Config.SAMPLE_RATE / Config.CHUNK_SIZE * duration)):
                data = stream.read(Config.CHUNK_SIZE)
                frames.append(np.frombuffer(data, dtype=np.float32))
            
            # Clean up
            stream.stop_stream()
            stream.close()
            
            # Convert to numpy array
            audio_data = np.concatenate(frames, axis=0)
            
            print("Recording completed!")
            return audio_data
            
        except Exception as e:
            print(f"Error during recording: {e}")
            raise
    
    def start_continuous_recording(self, device_index: Optional[int] = None):
        """Start continuous recording (until stopped)."""
        if self.is_recording:
            print("Already recording!")
            return
            
        self.is_recording = True
        self.recorded_frames = []
        
        def recording_thread():
            try:
                stream = self.audio.open(
                    format=pyaudio.paFloat32,
                    channels=Config.CHANNELS,
                    rate=Config.SAMPLE_RATE,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=Config.CHUNK_SIZE
                )
                
                print("Continuous recording started. Call stop_recording() to stop.")
                
                while self.is_recording:
                    data = stream.read(Config.CHUNK_SIZE, exception_on_overflow=False)
                    self.recorded_frames.append(np.frombuffer(data, dtype=np.float32))
                
                stream.stop_stream()
                stream.close()
                
            except Exception as e:
                print(f"Error in continuous recording: {e}")
                self.is_recording = False
        
        # Start recording in separate thread
        self.recording_thread = threading.Thread(target=recording_thread)
        self.recording_thread.start()
    
    def stop_recording(self) -> Optional[np.ndarray]:
        """Stop continuous recording and return recorded audio."""
        if not self.is_recording:
            print("Not currently recording!")
            return None
            
        self.is_recording = False
        
        if hasattr(self, 'recording_thread'):
            self.recording_thread.join()
        
        if self.recorded_frames:
            audio_data = np.concatenate(self.recorded_frames, axis=0)
            self.recorded_frames = []
            print("Recording stopped!")
            return audio_data
        else:
            print("No audio data recorded!")
            return None
    
    def save_audio(self, audio_data: np.ndarray, filename: str):
        """
        Save audio data to file.
        
        Args:
            audio_data: Audio data as numpy array
            filename: Output filename
        """
        try:
            sf.write(filename, audio_data, Config.SAMPLE_RATE)
            print(f"Audio saved to {filename}")
        except Exception as e:
            print(f"Error saving audio: {e}")
            raise
    
    def get_audio_level(self, audio_data: np.ndarray) -> float:
        """
        Calculate audio level/volume.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Audio level (RMS)
        """
        return np.sqrt(np.mean(audio_data**2))
    
    def is_audio_silent(self, audio_data: np.ndarray, threshold: float = 0.01) -> bool:
        """
        Check if audio is silent/too quiet.
        
        Args:
            audio_data: Audio data as numpy array
            threshold: Silence threshold
            
        Returns:
            True if audio is silent
        """
        return self.get_audio_level(audio_data) < threshold