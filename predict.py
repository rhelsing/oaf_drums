from cog import BasePredictor, Input, Path
import subprocess
import os
import tempfile
import shutil

class Predictor(BasePredictor):
    def setup(self):
        """Load the model into memory to make running multiple predictions efficient"""
        self.model_dir = 'models/e-gmd_checkpoint'
        
        # Verify model exists
        if not os.path.exists(self.model_dir):
            raise RuntimeError(f"Model directory {self.model_dir} not found!")

    def predict(
        self,
        audio_file: Path = Input(description="Audio file to transcribe drums from"),
    ) -> Path:
        """Run drum transcription on the audio file"""
        
        # Create output directory
        output_dir = tempfile.mkdtemp()
        
        try:
            # Copy input file to temp location with simple name
            temp_input = os.path.join(output_dir, "input.wav")
            shutil.copy2(str(audio_file), temp_input)
            
            # Run Magenta transcription
            cmd = [
                "onsets_frames_transcription_transcribe",
                f"--model_dir={self.model_dir}",
                "--config=drums",
                temp_input
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=output_dir
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Transcription failed: {result.stderr}")
            
            # Find the output MIDI file
            midi_file = os.path.join(output_dir, "input.midi")
            
            if not os.path.exists(midi_file):
                # Try alternative naming
                for f in os.listdir(output_dir):
                    if f.endswith('.midi') or f.endswith('.mid'):
                        midi_file = os.path.join(output_dir, f)
                        break
            
            if not os.path.exists(midi_file):
                raise RuntimeError("No MIDI file generated")
            
            # Copy to final location
            final_output = "drums_transcribed.mid"
            shutil.copy2(midi_file, final_output)
            
            return Path(final_output)
            
        finally:
            # Clean up temp directory
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
