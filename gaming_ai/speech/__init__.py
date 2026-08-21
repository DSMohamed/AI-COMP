"""Speech perception and voice synthesis modules."""

from gaming_ai.speech.vad import VoiceActivityDetector
from gaming_ai.speech.microphone import MicrophoneStream
from gaming_ai.speech.stt import SpeechToText
from gaming_ai.speech.tts import TextToSpeechEngine
from gaming_ai.speech.audio_player import InterruptibleAudioPlayer

__all__ = [
    "VoiceActivityDetector",
    "MicrophoneStream",
    "SpeechToText",
    "TextToSpeechEngine",
    "InterruptibleAudioPlayer",
]
