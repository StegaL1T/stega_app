import os
import sys
from datetime import datetime

# Adjust the system path to find the machine module
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

# Import the audio decoding machine
from machine.stega_audio_decode_machine import StegaAudioDecodeMachine

def run_audio_decode_demo():
    """
    Demonstrates decoding a steganographic audio file using the new machine.
    """
    
    # === Configuration ===
    # Set the path to the audio file. Make sure this path is correct on your system.
    audio_file_path = "C:\\Users\\yaput\\Documents\\GitHub\\stega_app\\jason_audio_1.wav"
    
    # Set the LSB bits and decryption key as specified
    lsb_bits = 4
    encryption_key = "1234"
    
    # Set the output directory. This script will save the decoded file here.
    output_directory = "C:\\Users\\yaput\\Documents\\GitHub\\stega_app\\decoded_files"
    
    # Create the output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)

    # === Decoding Process ===
    print("Initializing StegaAudioDecodeMachine...")
    machine = StegaAudioDecodeMachine()

    # Set the decoding parameters
    machine.set_lsb_bits(lsb_bits)
    machine.set_encryption_key(encryption_key)
    machine.set_output_path(output_directory)

    # Load the steganographic audio file
    print(f"Loading audio file: {audio_file_path}")
    if not machine.set_stego_audio(audio_file_path):
        print(f"Error loading audio file: {machine.get_last_error()}")
        return

    # Run the decoding process
    print("Starting extraction...")
    success = machine.extract_message()

    # Display the results
    if success:
        print("\n✅ Extraction successful!")
        extracted_data = machine.get_extracted_data()
        header_info = machine.get_header_info()
        output_path = machine.output_path

        print("\n=== Header Info ===")
        if header_info:
            for key, value in header_info.items():
                print(f"- {key}: {value}")
        
        print("\n=== Extracted Data Preview ===")
        print(extracted_data)
        
        print(f"\nFinal output saved to: {output_path}")

    else:
        print("\n❌ Extraction failed!")
        print(f"Error: {machine.get_last_error()}")

if __name__ == "__main__":
    run_audio_decode_demo()