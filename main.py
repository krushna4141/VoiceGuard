"""
Voice ID System - Main Application
A voice identification system using ChatGPT API for voice analysis and user verification.
"""

import sys
import argparse
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.voice_id_system import VoiceIDSystem
from src.config import Config

def print_banner():
    """Print application banner."""
    print("="*60)
    print("🛡️ VOICEGUARD")
    print("Advanced Voice Authentication System Powered by AI")
    print("="*60)

def print_menu():
    """Print main menu options."""
    print("\n📋 MENU OPTIONS:")
    print("1. 📝 Enroll new user")
    print("2. 🔍 Identify user (with username hint)")
    print("3. 🎯 Identify unknown speaker")
    print("4. 👥 List all users")
    print("5. ℹ️  Get user information")
    print("6. 🎤 Test microphone")
    print("7. 📊 System statistics")
    print("8. 🗑️  Delete user")
    print("9. ❌ Exit")

def enroll_user(voice_system):
    """Handle user enrollment."""
    print("\n=== USER ENROLLMENT ===")
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        return
    
    full_name = input("Enter full name (optional): ").strip()
    email = input("Enter email (optional): ").strip()
    
    success = voice_system.enroll_user(username, full_name, email)
    
    if success:
        print(f"\n✅ User '{username}' enrolled successfully!")
    else:
        print(f"\n❌ Failed to enroll user '{username}'")

def identify_user_with_hint(voice_system):
    """Handle user identification with username hint."""
    print("\n=== USER VERIFICATION ===")
    username = input("Enter username to verify: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        return
    
    result = voice_system.identify_user(username_hint=username)
    
    print("\n📊 IDENTIFICATION RESULTS:")
    print(f"Success: {result['success']}")
    print(f"Confidence: {result['confidence']:.2f}")
    
    if result['success']:
        print(f"✅ User '{result['username']}' verified successfully!")
        if result.get('transcript'):
            print(f"Transcript: \"{result['transcript']}\"")
    else:
        print(f"❌ Verification failed: {result.get('error', 'Unknown error')}")

def identify_unknown_speaker(voice_system):
    """Handle identification of unknown speaker."""
    print("\n=== SPEAKER IDENTIFICATION ===")
    print("The system will attempt to identify who is speaking...")
    
    result = voice_system.identify_user()
    
    print("\n📊 IDENTIFICATION RESULTS:")
    print(f"Success: {result['success']}")
    print(f"Confidence: {result['confidence']:.2f}")
    
    if result['success']:
        print(f"✅ Speaker identified: {result['username']} ({result.get('full_name', '')})")
        if result.get('transcript'):
            print(f"Transcript: \"{result['transcript']}\"")
    else:
        print(f"❌ Could not identify speaker: {result.get('error', 'Unknown error')}")

def list_users(voice_system):
    """List all enrolled users."""
    print("\n=== ENROLLED USERS ===")
    users = voice_system.list_users()
    
    if not users:
        print("No users enrolled in the system.")
        return
    
    print(f"Found {len(users)} enrolled users:")
    print()
    
    for user in users:
        print(f"👤 {user['username']}")
        if user.get('full_name'):
            print(f"   Name: {user['full_name']}")
        if user.get('email'):
            print(f"   Email: {user['email']}")
        print(f"   Enrolled: {user['created_at']}")
        print(f"   Profiles: {user['enrollment_count']}")
        print()

def get_user_info(voice_system):
    """Get detailed information about a user."""
    print("\n=== USER INFORMATION ===")
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        return
    
    info = voice_system.get_user_info(username)
    
    if not info:
        print(f"❌ User '{username}' not found!")
        return
    
    user = info['user_info']
    print(f"\n👤 USER: {user['username']}")
    if user.get('full_name'):
        print(f"Name: {user['full_name']}")
    if user.get('email'):
        print(f"Email: {user['email']}")
    print(f"User ID: {user['user_id']}")
    print(f"Created: {user['created_at']}")
    print(f"Last Updated: {user['last_updated']}")
    print(f"Status: {'Active' if user['is_active'] else 'Inactive'}")
    
    print(f"\n📊 STATISTICS:")
    print(f"Voice Profiles: {info['voice_profiles']}")
    print(f"Successful Authentications: {info['recent_authentications']}")
    print(f"Failed Attempts: {info['failed_attempts']}")
    if info['last_authentication']:
        print(f"Last Authentication: {info['last_authentication']}")

def test_microphone(voice_system):
    """Test microphone functionality."""
    voice_system.test_microphone()

def show_system_stats(voice_system):
    """Show system statistics."""
    print("\n=== SYSTEM STATISTICS ===")
    stats = voice_system.get_system_stats()
    
    print(f"👥 Total Users: {stats['total_users']}")
    print(f"🔐 Total Authentications: {stats['total_authentications']}")
    print(f"✅ Successful Authentications: {stats['successful_authentications']}")
    print(f"❌ Failed Authentications: {stats['failed_authentications']}")
    print(f"📈 Success Rate: {stats['success_rate']:.1%}")

def delete_user(voice_system):
    """Delete a user from the system."""
    print("\n=== DELETE USER ===")
    print("⚠️  WARNING: This will deactivate the user and all their voice profiles!")
    
    username = input("Enter username to delete: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        return
    
    confirm = input(f"Are you sure you want to delete user '{username}'? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ Deletion cancelled.")
        return
    
    success = voice_system.delete_user(username, confirm=True)
    
    if success:
        print(f"✅ User '{username}' deleted successfully!")
    else:
        print(f"❌ Failed to delete user '{username}'")

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="VoiceGuard - Advanced Voice Authentication System Powered by AI"
    )
    parser.add_argument("--config-check", action="store_true", 
                       help="Check configuration and exit")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Configuration check
    if args.config_check:
        print("\n🔧 CONFIGURATION CHECK:")
        try:
            Config.validate()
            print("✅ Configuration is valid!")
            print(f"Database Path: {Config.DATABASE_PATH}")
            print(f"Sample Rate: {Config.SAMPLE_RATE} Hz")
            print(f"Channels: {Config.CHANNELS}")
            print(f"Record Duration: {Config.RECORD_SECONDS} seconds")
            print(f"Similarity Threshold: {Config.SIMILARITY_THRESHOLD}")
            print(f"Min Confidence Score: {Config.MIN_CONFIDENCE_SCORE}")
        except Exception as e:
            print(f"❌ Configuration error: {e}")
        return
    
    # Check if API key is set
    if not Config.OPENAI_API_KEY:
        print("\n❌ ERROR: OpenAI API key not configured!")
        print("Please create a .env file based on .env.example and add your API key.")
        return
    
    # Initialize system
    try:
        voice_system = VoiceIDSystem()
    except Exception as e:
        print(f"\n❌ Failed to initialize Voice ID System: {e}")
        print("Please check your configuration and try again.")
        return
    
    # Main application loop
    try:
        while True:
            print_menu()
            choice = input("\nEnter your choice (1-9): ").strip()
            
            if choice == '1':
                enroll_user(voice_system)
            elif choice == '2':
                identify_user_with_hint(voice_system)
            elif choice == '3':
                identify_unknown_speaker(voice_system)
            elif choice == '4':
                list_users(voice_system)
            elif choice == '5':
                get_user_info(voice_system)
            elif choice == '6':
                test_microphone(voice_system)
            elif choice == '7':
                show_system_stats(voice_system)
            elif choice == '8':
                delete_user(voice_system)
            elif choice == '9':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice! Please select 1-9.")
            
            input("\nPress Enter to continue...")
    
    except KeyboardInterrupt:
        print("\n\n👋 Application interrupted by user. Goodbye!")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    finally:
        # Cleanup
        try:
            voice_system.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()