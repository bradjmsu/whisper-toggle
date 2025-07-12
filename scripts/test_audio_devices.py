#!/usr/bin/env python3
"""
Test audio devices for Whisper Toggle compatibility.
"""

import pyaudio
import numpy as np
import time

def test_audio_devices():
    """Test all available audio input devices"""
    audio = pyaudio.PyAudio()
    
    print("=== Audio Device Compatibility Test ===\n")
    
    print("Available input devices:")
    working_devices = []
    
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        
        if info['maxInputChannels'] > 0:
            print(f"\nDevice {i}: {info['name']}")
            print(f"  Channels: {info['maxInputChannels']}")
            print(f"  Sample Rate: {info['defaultSampleRate']} Hz")
            
            # Test if device works with our settings
            try:
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=int(info['defaultSampleRate']),
                    input=True,
                    input_device_index=i,
                    frames_per_buffer=1024
                )
                stream.close()
                print(f"  Status: ✓ COMPATIBLE")
                working_devices.append(i)
                
            except Exception as e:
                print(f"  Status: ✗ FAILED ({str(e)[:50]}...)")
    
    audio.terminate()
    
    print(f"\n=== Summary ===")
    print(f"Compatible devices: {working_devices}")
    
    if working_devices:
        print(f"\nRecommended device: {working_devices[0]}")
        print(f"To use this device, edit whisper-service.sh and set:")
        print(f"  sg input -c \"python3 whisper_with_smart_indicators.py 8 {working_devices[0]}\"")
    else:
        print("\nNo compatible devices found!")
        print("Check your audio settings and microphone connections.")

def test_microphone_levels(device_id=None):
    """Test microphone input levels"""
    audio = pyaudio.PyAudio()
    
    if device_id is None:
        # Use default device
        device_id = audio.get_default_input_device_info()['index']
    
    device_info = audio.get_device_info_by_index(device_id)
    
    print(f"\n=== Testing Microphone Levels ===")
    print(f"Device: {device_info['name']}")
    print(f"Speak into your microphone for 5 seconds...\n")
    
    try:
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=int(device_info['defaultSampleRate']),
            input=True,
            input_device_index=device_id,
            frames_per_buffer=1024
        )
        
        max_level = 0
        for i in range(int(device_info['defaultSampleRate'] / 1024 * 5)):  # 5 seconds
            data = stream.read(1024, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            level = np.max(np.abs(audio_data))
            max_level = max(max_level, level)
            
            # Show level meter
            bars = int(level * 100)
            print(f"\rLevel: [{'#' * bars}{' ' * (100-bars)}] {level:.4f}", end='', flush=True)
            
        stream.stop_stream()
        stream.close()
        
        print(f"\n\nMax level detected: {max_level:.4f}")
        
        if max_level > 0.01:
            print("✓ Microphone levels look good!")
        elif max_level > 0.001:
            print("⚠ Microphone levels are low but should work")
        else:
            print("✗ Microphone levels too low - check settings")
            
    except Exception as e:
        print(f"Error testing microphone: {e}")
    
    audio.terminate()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        try:
            device_id = int(sys.argv[1])
            test_microphone_levels(device_id)
        except ValueError:
            print("Usage: python3 test_audio_devices.py [device_number]")
    else:
        test_audio_devices()
        
        # Ask if user wants to test microphone levels
        try:
            device = input("\nEnter device number to test microphone levels (or press Enter to skip): ")
            if device.strip():
                test_microphone_levels(int(device))
        except (ValueError, KeyboardInterrupt):
            print("\nExiting...")