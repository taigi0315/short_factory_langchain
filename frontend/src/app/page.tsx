'use client';

import { useState } from 'react';
import { SceneEditor } from '../components/SceneEditor';
import '../styles/scene-editor.css';

interface StoryIdea {
  title: string;
  premise: string;
  genre: string;
  target_audience: string;
  estimated_duration: string;
}

import DevDashboard from '../components/DevDashboard';

export default function Home() {
  const [showDevMode, setShowDevMode] = useState(false);
  const [step, setStep] = useState(1);
  const [topic, setTopic] = useState('');
  const [mood, setMood] = useState('Auto');
  const [category, setCategory] = useState('Auto');

  const [loading, setLoading] = useState(false);
  const [stories, setStories] = useState<StoryIdea[]>([]);
  const [selectedStory, setSelectedStory] = useState<StoryIdea | null>(null);
  const [script, setScript] = useState<any>(null);
  const [workflowMode, setWorkflowMode] = useState<'auto' | 'manual'>('auto');
  const [showSceneEditor, setShowSceneEditor] = useState(false);

  const generateStories = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/stories/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, mood, category }),
      });
      const data = await res.json();
      if (Array.isArray(data)) {
        setStories(data);
        setStep(2);
      } else {
        console.error('API Error:', data);
        alert('Failed to generate stories. API returned an error.');
      }
    } catch (error) {
      console.error('Failed to generate stories', error);
      alert('Failed to generate stories. Check backend console.');
    } finally {
      setLoading(false);
    }
  };

  const createVideo = async () => {
    if (!selectedStory) return;

    setStep(3);
    setLoading(true);

    try {
      const res = await fetch('/api/scripts/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          story_title: selectedStory.title,
          story_premise: selectedStory.premise,
          story_genre: selectedStory.genre,
          story_audience: selectedStory.target_audience,
          duration: selectedStory.estimated_duration
        }),
      });

      const data = await res.json();
      if (data.script) {
        setScript(data.script);

        // Check workflow mode
        if (workflowMode === 'manual') {
          // Show scene editor
          setShowSceneEditor(true);
        }
        // Auto mode continues with existing flow
      } else {
        throw new Error('No script returned');
      }
    } catch (error) {
      console.error('Failed to generate script', error);
      alert('Failed to generate script. Using mock data for demo.');
    } finally {
      setLoading(false);
    }
  };

  const buildVideoFromScenes = async (sceneConfigs: any[]) => {
    setLoading(true);
    try {
      // Create abort controller with 10-minute timeout (TICKET-027 Issue 1)
      // Video generation can take 5-8 minutes, so we need a longer timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10 * 60 * 1000); // 10 minutes

      const res = await fetch('/api/scene-editor/build-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script: script,
          scene_configs: sceneConfigs
        }),
        signal: controller.signal
      });

      clearTimeout(timeoutId); // Clear timeout if request completes

      if (!res.ok) {
        throw new Error('Failed to build video');
      }

      const data = await res.json();
      window.open(data.video_url, '_blank');
      alert('Video built successfully! Opening in new tab...');
    } catch (error: any) {
      console.error('Failed to build video:', error);
      if (error.name === 'AbortError') {
        alert('Video generation timed out after 10 minutes. The video may still be processing on the server.');
      } else {
        alert('Failed to build video. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (showDevMode) {
    return (
      <div>
        <button
          onClick={() => setShowDevMode(false)}
          className="fixed top-4 right-4 z-50 bg-gray-800 text-white px-4 py-2 rounded shadow hover:bg-gray-700"
        >
          Exit Dev Mode
        </button>
        <DevDashboard />
      </div>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center p-12 bg-slate-950 text-white font-sans relative">
      <button
        onClick={() => setShowDevMode(true)}
        className="absolute top-4 right-4 text-slate-600 hover:text-slate-400 text-sm"
      >
        Dev Mode
      </button>

      <div className="w-full max-w-3xl">
        <header className="mb-12 text-center">
          <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-600 mb-4">
            ShortFactory
          </h1>
          <p className="text-slate-400">Turn your ideas into viral videos in seconds.</p>
        </header>

        {/* Step 1: Input */}
        {step === 1 && (
          <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800 shadow-2xl">
            <h2 className="text-2xl font-bold mb-6">What do you want to create?</h2>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">Video Topic</label>
                <input
                  type="text"
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g. The history of coffee, A funny cat story..."
                  className="w-full p-4 bg-slate-800 border border-slate-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all text-lg"
                />
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">Mood / Vibe</label>
                  <select
                    value={mood}
                    onChange={(e) => setMood(e.target.value)}
                    className="w-full p-4 bg-slate-800 border border-slate-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none appearance-none"
                  >
                    <option>Auto</option>
                    <option>Fun</option>
                    <option>Serious</option>
                    <option>Inspirational</option>
                    <option>Educational</option>
                    <option>Dark</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-2">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full p-4 bg-slate-800 border border-slate-700 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none appearance-none"
                  >
                    <option>Auto</option>
                    <option>Real Story</option>
                    <option>Explainer</option>
                    <option>Fiction</option>
                    <option>News</option>
                  </select>
                </div>
              </div>

              <button
                onClick={generateStories}
                disabled={!topic || loading}
                className={`w-full py-4 rounded-xl font-bold text-lg transition-all transform duration-200 border-2 ${!topic || loading
                  ? 'bg-slate-800 border-slate-700 text-slate-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-purple-600 border-transparent text-white shadow-xl hover:shadow-blue-500/40 hover:scale-[1.02] hover:brightness-110'
                  }`}
              >
                {loading ? 'Generating Ideas...' : 'Generate Ideas ✨'}
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Selection */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold">Select a Story</h2>
              <button onClick={() => setStep(1)} className="text-slate-400 hover:text-white">
                ← Back
              </button>
            </div>

            <div className="grid gap-4">
              {stories.map((story, idx) => (
                <div
                  key={idx}
                  onClick={() => setSelectedStory(story)}
                  className={`p-6 rounded-xl border-2 cursor-pointer transition-all transform duration-200 ${selectedStory === story
                    ? 'bg-blue-900/20 border-blue-500 ring-1 ring-blue-500 scale-[1.02] shadow-lg shadow-blue-500/20'
                    : 'bg-slate-900 border-slate-800 hover:border-slate-600 hover:bg-slate-800/80 hover:scale-[1.01]'
                    }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="text-xl font-bold text-white">{story.title}</h3>
                    <span className="px-3 py-1 bg-slate-800 rounded-full text-xs text-slate-300">
                      {story.genre}
                    </span>
                  </div>
                  <p className="text-slate-400 mb-4">{story.premise}</p>
                  <div className="flex gap-4 text-sm text-slate-500">
                    <span>🎯 {story.target_audience}</span>
                    <span>⏱️ {story.estimated_duration}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Workflow Mode Selector */}
            <div className="bg-slate-900 p-6 rounded-xl border border-slate-800">
              <h3 className="text-lg font-bold mb-4">Workflow Mode</h3>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => setWorkflowMode('auto')}
                  className={`p-4 rounded-lg border-2 transition-all ${workflowMode === 'auto'
                    ? 'bg-blue-900/20 border-blue-500 text-white'
                    : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
                    }`}
                >
                  <div className="font-bold mb-1">🚀 Auto Mode</div>
                  <div className="text-sm opacity-75">Fully automated video generation</div>
                </button>
                <button
                  onClick={() => setWorkflowMode('manual')}
                  className={`p-4 rounded-lg border-2 transition-all ${workflowMode === 'manual'
                    ? 'bg-purple-900/20 border-purple-500 text-white'
                    : 'bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-600'
                    }`}
                >
                  <div className="font-bold mb-1">✋ Manual Mode</div>
                  <div className="text-sm opacity-75">Scene-by-scene editor with uploads</div>
                </button>
              </div>
            </div>

            <button
              onClick={createVideo}
              disabled={!selectedStory}
              className={`w-full py-4 rounded-xl font-bold text-lg transition-all transform duration-200 border-2 ${!selectedStory
                ? 'bg-slate-800 border-slate-700 text-slate-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-green-600 to-teal-600 border-transparent text-white shadow-xl hover:shadow-green-500/40 hover:scale-[1.02] hover:brightness-110'
                }`}
            >
              Create Video 🎬
            </button>
          </div>
        )}

        {/* Step 3: Script Display */}
        {step === 3 && (
          <div className="space-y-6">
            {loading ? (
              <div className="bg-slate-900 p-12 rounded-2xl border border-slate-800 text-center">
                <div className="w-20 h-20 mx-auto mb-6 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
                <h2 className="text-3xl font-bold mb-4">Generating your video...</h2>
                <p className="text-slate-400">Creating images, voiceovers, and rendering your masterpiece.</p>
              </div>
            ) : script ? (
              <div className="bg-slate-900 p-8 rounded-2xl border border-slate-800">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold">Generated Script</h2>
                  <span className="px-3 py-1 bg-blue-900 text-blue-200 rounded-full text-sm">
                    {script.scenes.length} Scenes
                  </span>
                </div>

                <div className="space-y-8">
                  {script.scenes.map((scene: any, idx: number) => (
                    <div key={idx} className="border-b border-slate-800 pb-6 last:border-0">
                      <div className="flex items-center gap-3 mb-3">
                        <span className="w-8 h-8 flex items-center justify-center bg-slate-800 rounded-full font-bold text-slate-400">
                          {idx + 1}
                        </span>
                        <span className="text-sm font-mono text-blue-400 uppercase">{scene.scene_type}</span>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pl-11">
                        <div>
                          <h4 className="text-xs font-bold text-slate-500 uppercase mb-1">Visual</h4>
                          <p className="text-slate-300 mb-2">{scene.image_create_prompt}</p>
                          {scene.video_prompt && (
                            <p className="text-xs text-purple-400 bg-purple-900/20 p-2 rounded">🎥 {scene.video_prompt}</p>
                          )}
                        </div>
                        <div>
                          <h4 className="text-xs font-bold text-slate-500 uppercase mb-1">Audio</h4>
                          <p className="text-green-400 font-medium">"{scene.dialogue}"</p>
                          <div className="mt-2 flex gap-2">
                            <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">🗣️ {scene.voice_tone}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-8 flex gap-4">
                  <button
                    onClick={() => setStep(2)}
                    className="flex-1 py-3 bg-slate-800 rounded-xl font-bold hover:bg-slate-700 transition-colors"
                    disabled={loading}
                  >
                    Back
                  </button>
                  <button
                    onClick={async () => {
                      setLoading(true);
                      const controller = new AbortController();
                      const timeoutId = setTimeout(() => controller.abort(), 1200000); // 20 minutes timeout (increased from 10)

                      try {
                        // Fetch retry configuration from backend
                        const configRes = await fetch('/api/dev/retry-config');
                        const retryConfig = configRes.ok ? await configRes.json() : {
                          max_retries: 5,
                          retry_delays_seconds: [5, 15, 30, 60],
                          scene_delay_seconds: 5
                        };

                        console.log('Using retry configuration:', retryConfig);

                        // 1. Generate images for all scenes SEQUENTIALLY with exponential backoff
                        const imageMap: Record<number, string> = {};
                        const MAX_RETRIES = retryConfig.max_retries;
                        const DELAYS = retryConfig.retry_delays_seconds.map((s: number) => s * 1000); // Convert to ms
                        const SCENE_DELAY = retryConfig.scene_delay_seconds * 1000; // Convert to ms

                        console.log(`Starting sequential image generation for ${script.scenes.length} scenes...`);
                        console.log(`Max retries: ${MAX_RETRIES}, Delays: ${retryConfig.retry_delays_seconds}s, Scene spacing: ${retryConfig.scene_delay_seconds}s`);

                        for (let i = 0; i < script.scenes.length; i++) {
                          const scene = script.scenes[i];
                          let success = false;
                          let lastError = null;

                          // Retry loop for each scene
                          for (let attempt = 0; attempt < MAX_RETRIES && !success; attempt++) {
                            try {
                              const attemptLabel = attempt > 0 ? ` (retry ${attempt}/${MAX_RETRIES - 1})` : '';
                              console.log(`[${i + 1}/${script.scenes.length}] Generating image for scene ${scene.scene_number}${attemptLabel}...`);

                              const res = await fetch('/api/dev/generate-image', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({
                                  scene_number: scene.scene_number,
                                  prompt: scene.image_create_prompt,
                                  style: scene.image_style
                                }),
                              });

                              if (res.ok) {
                                const data = await res.json();
                                console.log(`✓ Image generated for scene ${scene.scene_number}`);
                                imageMap[scene.scene_number] = data.url;
                                success = true;
                              } else {
                                const errorText = await res.text();
                                lastError = `${res.status} ${res.statusText}: ${errorText}`;
                                console.error(`✗ Failed to generate image for scene ${scene.scene_number}: ${lastError}`);

                                // If not the last retry, wait with exponential backoff
                                if (attempt < MAX_RETRIES - 1) {
                                  const retryDelay = DELAYS[Math.min(attempt, DELAYS.length - 1)];
                                  console.log(`Waiting ${retryDelay / 1000}s before retry...`);
                                  await new Promise(resolve => setTimeout(resolve, retryDelay));
                                }
                              }
                            } catch (e) {
                              lastError = e;
                              console.error(`✗ Exception generating image for scene ${scene.scene_number}:`, e);

                              // If not the last retry, wait with exponential backoff
                              if (attempt < MAX_RETRIES - 1) {
                                const retryDelay = DELAYS[Math.min(attempt, DELAYS.length - 1)];
                                console.log(`Waiting ${retryDelay / 1000}s before retry...`);
                                await new Promise(resolve => setTimeout(resolve, retryDelay));
                              }
                            }
                          }

                          // If all retries failed, log error but continue with other scenes
                          if (!success) {
                            console.error(`✗ Failed to generate image for scene ${scene.scene_number} after ${MAX_RETRIES} attempts. Last error:`, lastError);
                            alert(`Warning: Failed to generate image for scene ${scene.scene_number}. Continuing with other scenes...`);
                          }

                          // Add delay between scenes (except after the last one)
                          if (i < script.scenes.length - 1 && success) {
                            console.log(`Waiting ${SCENE_DELAY / 1000}s before next scene...`);
                            await new Promise(resolve => setTimeout(resolve, SCENE_DELAY));
                          }
                        }

                        console.log('Image generation complete. Final imageMap:', imageMap);

                        // 2. Generate Video
                        const res = await fetch('/api/dev/generate-video-from-script', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            script: script,
                            image_map: imageMap
                          }),
                          signal: controller.signal
                        });

                        clearTimeout(timeoutId);

                        if (!res.ok) {
                          let errorMessage = 'Failed to generate video';
                          try {
                            const contentType = res.headers.get('content-type');
                            if (contentType && contentType.includes('application/json')) {
                              const errorData = await res.json();
                              errorMessage = errorData.detail || errorData.message || errorMessage;
                            } else {
                              const text = await res.text();
                              console.error('Non-JSON error response:', text.substring(0, 200));
                              errorMessage = `Server error (${res.status}): ${res.statusText}`;
                            }
                          } catch (parseError) {
                            console.error('Error parsing error response:', parseError);
                            errorMessage = `Server error (${res.status})`;
                          }
                          throw new Error(errorMessage);
                        }

                        const data = await res.json();

                        // 3. Show Video
                        window.open(data.video_url, '_blank');
                        alert('Video Generated! Opening in new tab...');

                      } catch (e: any) {
                        clearTimeout(timeoutId);
                        console.error(e);
                        if (e.name === 'AbortError') {
                          alert('Video generation timed out after 3 minutes. The video might still be processing on the server.');
                        } else {
                          alert(`Failed to generate video:\n\n${e.message || e}`);
                        }
                      } finally {
                        setLoading(false);
                      }
                    }}
                    disabled={loading}
                    className="flex-1 py-3 bg-gradient-to-r from-pink-600 to-red-600 rounded-xl font-bold hover:from-pink-500 hover:to-red-500 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {loading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        Generating Video...
                      </>
                    ) : (
                      <>
                        Generate Full Video 🚀
                      </>
                    )}
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* Scene Editor (Manual Mode) */}
        {showSceneEditor && script && (
          <div className="mt-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold">Scene Editor</h2>
              <button
                onClick={() => setShowSceneEditor(false)}
                className="text-slate-400 hover:text-white"
              >
                ← Back to Script
              </button>
            </div>
            <SceneEditor script={script} onBuildVideo={buildVideoFromScenes} />
          </div>
        )}
      </div>
    </main>
  );
}
