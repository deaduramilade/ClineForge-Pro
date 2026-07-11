from src.backend.services.orchestrator import run_orchestrator

# A complex prompt requiring both tools
prompt = """
I need assets for a fast-paced gaming clip edit for TikTok. 
First, generate a cinematic storyboard image for script_id 'game_clip_01', scene_index 0. 
Then, generate a background audio track featuring dark alternative R&B beats mixed with melancholic, howling vocal textures.
"""

print("Thinking...")
result = run_orchestrator(prompt)

for msg in result['messages']:
    msg.pretty_print()