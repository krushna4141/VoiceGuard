# 🛡️ VoiceGuard

> **Advanced Voice Authentication System Powered by AI**

VoiceGuard is a comprehensive voice identification and authentication system that leverages OpenAI's ChatGPT and Whisper APIs to provide secure, AI-powered voice recognition. Enroll users with voice samples and authenticate them using advanced voice biometric analysis.

## 🌟 Features

- **Voice Enrollment**: Enroll new users by collecting multiple voice samples
- **Voice Identification**: Identify users by their voice with confidence scoring
- **Speaker Verification**: Verify a specific user's identity using voice
- **Unknown Speaker Detection**: Identify unknown speakers from enrolled database
- **Advanced Voice Analysis**: Uses ChatGPT API for sophisticated voice characteristic analysis
- **Voice Transcription**: Automatic speech-to-text using OpenAI Whisper API
- **Database Management**: SQLite database for storing user profiles and voice data
- **Audio Processing**: Advanced feature extraction using MFCC, spectral, and prosodic features
- **Authentication Logging**: Complete audit trail of all authentication attempts
- **Microphone Testing**: Built-in microphone functionality testing

## 🏗️ System Architecture

The system consists of several key components:

- **Voice Recorder**: Captures audio from microphone with configurable settings
- **Voice Processor**: Extracts voice features (MFCC, spectral, prosodic) 
- **ChatGPT Analyzer**: Uses OpenAI API for voice analysis and comparison
- **Database Manager**: Handles user profiles, voice data, and authentication logs
- **Main Application**: CLI interface that orchestrates all components

## 📋 Requirements

- Python 3.8 or higher
- OpenAI API key
- Working microphone
- Windows/Linux/macOS

## 🚀 Installation

1. **Clone or download the project**
   ```bash
   cd "ChatGPT ID System"
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Test your configuration**
   ```bash
   python main.py --config-check
   ```

## 🎯 Usage

### Running the Application

```bash
python main.py
```

This will start the interactive CLI application with the following options:

### 📝 User Enrollment

1. Select "Enroll new user" from the menu
2. Enter username, full name, and email
3. Record 3 voice samples (5 seconds each)
4. The system will process and store voice features

### 🔍 Voice Identification

**Option 1: Verify Known User**
1. Select "Identify user (with username hint)"
2. Enter the username to verify
3. Record voice sample
4. System returns verification result with confidence score

**Option 2: Identify Unknown Speaker**
1. Select "Identify unknown speaker"  
2. Record voice sample
3. System searches all enrolled users and returns best match

### 🎤 Testing Microphone

Use the "Test microphone" option to:
- List available audio devices
- Test audio recording functionality
- Check audio levels and quality

## ⚙️ Configuration

The system can be configured via environment variables in the `.env` file:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Audio Configuration
SAMPLE_RATE=16000
CHANNELS=1
CHUNK_SIZE=1024
RECORD_SECONDS=5

# Database Configuration
DATABASE_PATH=data/voice_profiles.db

# Voice Identification Thresholds
SIMILARITY_THRESHOLD=0.8
MIN_CONFIDENCE_SCORE=0.7
```

## 📊 How It Works

### Voice Enrollment Process
1. **Audio Recording**: Captures multiple voice samples (default: 3 samples)
2. **Feature Extraction**: Extracts MFCC, spectral, and prosodic features
3. **Transcription**: Uses OpenAI Whisper API for speech-to-text
4. **Voice Analysis**: ChatGPT analyzes voice characteristics and creates profile
5. **Storage**: Saves voice features, analysis, and metadata to database

### Voice Identification Process  
1. **Audio Recording**: Captures voice sample for identification
2. **Feature Extraction**: Processes audio and extracts voice features
3. **Database Search**: Compares features against enrolled user profiles
4. **ChatGPT Comparison**: Uses AI to compare voice characteristics
5. **Scoring**: Combines similarity scores with confidence metrics
6. **Decision**: Returns identification result based on configured thresholds

## 🔒 Security Features

- **Confidence Scoring**: Multiple confidence metrics ensure reliable identification
- **Threshold Controls**: Configurable similarity and confidence thresholds
- **Authentication Logging**: Complete audit trail of all attempts
- **Soft Delete**: Users can be deactivated without losing data
- **Voice Fingerprinting**: Creates unique voice signatures for comparison

## 📈 System Statistics

The application provides comprehensive statistics:
- Total enrolled users
- Authentication success/failure rates  
- User-specific authentication history
- Voice profile quality metrics

## 🗃️ Database Schema

The system uses SQLite with the following main tables:
- **users**: User account information
- **voice_profiles**: Voice feature data and analysis results
- **authentication_logs**: Complete authentication history
- **enrollment_sessions**: Enrollment process tracking

## 🛠️ Technical Details

### Voice Features Extracted
- **MFCC Features**: Mel-Frequency Cepstral Coefficients (13 coefficients)
- **Spectral Features**: Centroid, rolloff, bandwidth, zero-crossing rate
- **Prosodic Features**: Pitch (mean, std, range), energy, speaking rate
- **Audio Quality**: Duration, RMS energy, amplitude

### AI Integration
- **OpenAI Whisper**: For accurate speech transcription
- **ChatGPT-4**: For advanced voice analysis and comparison
- **Feature Analysis**: AI-powered voice characteristic profiling

## 🔧 Troubleshooting

### Common Issues

**1. "No audio detected" Error**
- Check microphone permissions
- Test microphone with system settings
- Adjust microphone volume
- Try different audio input device

**2. "OpenAI API Error"**
- Verify API key is correct
- Check internet connection
- Ensure sufficient API credits

**3. "Could not extract features" Error**
- Ensure audio is not too quiet or noisy
- Speak clearly during recording
- Check audio duration (minimum 3 seconds recommended)

### Audio Requirements
- **Duration**: At least 3-5 seconds of clear speech
- **Quality**: Clean audio without background noise
- **Volume**: Moderate speaking volume (not whisper or shouting)
- **Content**: Natural speech (avoid reading monotonously)

## 📝 Development

### Project Structure
```
ChatGPT ID System/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── voice_recorder.py      # Audio recording functionality  
│   ├── voice_processor.py     # Feature extraction and processing
│   ├── chatgpt_analyzer.py    # OpenAI API integration
│   ├── database_manager.py    # Database operations
│   └── voice_id_system.py     # Main system orchestration
├── data/                      # Database and data files (auto-created)
├── main.py                    # CLI application entry point
├── requirements.txt           # Python dependencies
├── setup.py                   # Package setup
├── .env.example              # Environment variables template
└── README.md                 # This file
```

### Adding New Features
The modular architecture makes it easy to extend:
- Add new voice features in `voice_processor.py`
- Enhance AI analysis in `chatgpt_analyzer.py`
- Add new CLI commands in `main.py`
- Extend database schema in `database_manager.py`

## 📄 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional voice features and algorithms
- GUI interface development  
- Multi-language support
- Enhanced security features
- Performance optimizations
- Mobile app integration

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review your configuration settings
3. Test with the microphone test feature
4. Verify your OpenAI API setup

---

**Note**: This system is designed for demonstration and development purposes. For production use, consider additional security measures, data encryption, and compliance requirements.