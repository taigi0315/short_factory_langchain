"""
Test script for VideoEffectAgent (TICKET-025)
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.video_effect.agent import VideoEffectAgent
from src.agents.script_writer.agent import ScriptWriterAgent
from src.core.config import settings


def test_video_effect_agent():
    print("🚀 Testing TICKET-025: VideoEffectAgent")
    print("=" * 60)
    
    # Generate a test script
    print("\n📝 Generating test script...")
    script_agent = ScriptWriterAgent()
    
    script = script_agent.generate_script(
        subject="The power of thunder and lightning in nature",
        language="English",
        max_scenes=5
    )
    
    print(f"✅ Script generated: {script.title}")
    print(f"   Scenes: {len(script.scenes)}")
    
    # Analyze with VideoEffectAgent
    print("\n🎬 Analyzing script with VideoEffectAgent...")
    effect_agent = VideoEffectAgent()
    
    recommendations = effect_agent.analyze_script(script, max_ai_videos=2)
    
    print(f"\n✅ Analysis complete!")
    print(f"   Total scenes: {len(recommendations)}")
    print(f"   AI video recommended: {sum(1 for r in recommendations if r.recommend_ai_video)}")
    
    # Display recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    for rec in recommendations:
        scene = script.scenes[rec.scene_number - 1]
        print(f"\n🎬 Scene {rec.scene_number}: {scene.scene_type.value}")
        print(f"   Dialogue: {scene.dialogue[:60]}...")
        print(f"   Effect: {rec.effect}")
        print(f"   Transition: {rec.transition_to_next.value}")
        print(f"   AI Video: {'✅ YES' if rec.recommend_ai_video else '❌ NO'}")
        print(f"   Reasoning: {rec.reasoning}")
        
        if rec.video_prompt:
            print(f"   Video Prompt Preview: {rec.video_prompt[:100]}...")
    
    # Test specific scenarios
    print("\n" + "=" * 60)
    print("TESTING SPECIFIC SCENARIOS")
    print("=" * 60)
    
    # Check if thunder/shake was detected
    shake_scenes = [r for r in recommendations if r.effect == 'shake']
    if shake_scenes:
        print(f"\n✅ Shake effect detected in {len(shake_scenes)} scene(s)")
        for rec in shake_scenes:
            scene = script.scenes[rec.scene_number - 1]
            print(f"   Scene {rec.scene_number}: {scene.dialogue[:50]}...")
    else:
        print("\n⚠️  No shake effects detected (may be expected if no thunder/impact in script)")
    
    # Check hook scene effect
    hook_scene_rec = recommendations[0]
    print(f"\n🎣 Hook scene (Scene 1):")
    print(f"   Effect: {hook_scene_rec.effect}")
    print(f"   Expected: ken_burns_zoom_in or similar dynamic effect")
    print(f"   Match: {'✅' if hook_scene_rec.effect in ['ken_burns_zoom_in', 'shake'] else '⚠️'}")
    
    # Check conclusion scene effect
    if len(recommendations) >= 4:
        conclusion_recs = [r for r in recommendations if script.scenes[r.scene_number - 1].scene_type.value == 'conclusion']
        if conclusion_recs:
            conclusion_rec = conclusion_recs[0]
            print(f"\n🏁 Conclusion scene (Scene {conclusion_rec.scene_number}):")
            print(f"   Effect: {conclusion_rec.effect}")
            print(f"   Expected: ken_burns_zoom_out or static")
            print(f"   Match: {'✅' if conclusion_rec.effect in ['ken_burns_zoom_out', 'static'] else '⚠️'}")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_video_effect_agent()
