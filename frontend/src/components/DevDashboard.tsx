"use client";

import { useState } from 'react';

export default function DevDashboard() {
    const [activeTab, setActiveTab] = useState<'image' | 'audio' | 'script' | 'video'>('script');

    // Image Gen State
    const [prompt, setPrompt] = useState('');
    const [imageStyle, setImageStyle] = useState('cinematic');
    const [generatedImage, setGeneratedImage] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Script Gen State
    const [scriptTopic, setScriptTopic] = useState('');
    const [generatedScript, setGeneratedScript] = useState<any>(null);
    const [scriptLoading, setScriptLoading] = useState(false);
    const [sceneImages, setSceneImages] = useState<Record<number, string>>({});
    const [sceneLoading, setSceneLoading] = useState<Record<number, boolean>>({});

    // Video Gen State
    const [videoType, setVideoType] = useState<'text' | 'image'>('text');
    const [videoPrompt, setVideoPrompt] = useState('');
    const [videoImageUrl, setVideoImageUrl] = useState('');
    const [generatedVideo, setGeneratedVideo] = useState<string | null>(null);
    const [videoLoading, setVideoLoading] = useState(false);

    const handleGenerateImage = async () => {
        setLoading(true);
        setError(null);
        setGeneratedImage(null);

        try {
            const res = await fetch('/api/dev/generate-image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt,
                    style: imageStyle
                }),
            });

            if (!res.ok) {
                const errData = await res.json();
                const msg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
                throw new Error(msg || 'Failed to generate image');
            }

            const data = await res.json();
            setGeneratedImage(data.url);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateScript = async () => {
        setScriptLoading(true);
        setError(null);
        setGeneratedScript(null);

        try {
            // We need to first get a story, then a script, but for dev mode let's try to skip to script 
            // if we can, or just do a quick story gen first.
            // Actually, the script generation endpoint expects story details.
            // Let's use a simplified flow or mock data if needed, but ideally we use the real flow.
            // For now, let's construct a dummy story request based on the topic.

            const res = await fetch('/api/scripts/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    story_title: `Dev Story: ${scriptTopic}`,
                    story_premise: `A short video about ${scriptTopic}`,
                    story_genre: "Educational",
                    story_audience: "General",
                    duration: "60s"
                }),
            });

            if (!res.ok) {
                throw new Error('Failed to generate script');
            }

            const data = await res.json();
            setGeneratedScript(data.script);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setScriptLoading(false);
        }
    };

    const handleGenerateSceneImage = async (sceneIndex: number, prompt: string) => {
        setSceneLoading(prev => ({ ...prev, [sceneIndex]: true }));

        try {
            const res = await fetch('/api/dev/generate-image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt,
                    style: 'cinematic',
                    scene_number: sceneIndex
                }),
            });

            if (!res.ok) {
                const errData = await res.json();
                const msg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
                throw new Error(msg || 'Failed');
            }

            const data = await res.json();
            setSceneImages(prev => ({ ...prev, [sceneIndex]: data.url }));
        } catch (err) {
            console.error(err);
            alert('Failed to generate image for scene ' + (sceneIndex + 1));
        } finally {
            setSceneLoading(prev => ({ ...prev, [sceneIndex]: false }));
        }
    };

    const handleGenerateVideo = async () => {
        setVideoLoading(true);
        setError(null);
        setGeneratedVideo(null);

        try {
            const res = await fetch('/api/dev/generate-video', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: videoType,
                    prompt: videoPrompt,
                    image_url: videoType === 'image' ? videoImageUrl : undefined
                }),
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Failed to generate video');
            }

            const data = await res.json();
            setGeneratedVideo(data.video_url);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setVideoLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-slate-950 z-50 overflow-y-auto p-8 text-white">
            <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-blue-500">
                        🛠️ Developer Dashboard
                    </h1>
                    <div className="text-xs text-slate-500 font-mono">v0.1.0-dev</div>
                </div>

                {/* Tabs */}
                <div className="flex gap-4 mb-8 border-b border-slate-800 pb-1">
                    <button
                        onClick={() => setActiveTab('script')}
                        className={`px-4 py-2 font-medium transition-colors ${activeTab === 'script'
                            ? 'text-blue-400 border-b-2 border-blue-400'
                            : 'text-slate-400 hover:text-white'
                            }`}
                    >
                        📜 Script & Scenes
                    </button>
                    <button
                        onClick={() => setActiveTab('image')}
                        className={`px-4 py-2 font-medium transition-colors ${activeTab === 'image'
                            ? 'text-blue-400 border-b-2 border-blue-400'
                            : 'text-slate-400 hover:text-white'
                            }`}
                    >
                        🎨 Image Gen
                    </button>
                    <button
                        onClick={() => setActiveTab('audio')}
                        className={`px-4 py-2 font-medium transition-colors ${activeTab === 'audio'
                            ? 'text-blue-400 border-b-2 border-blue-400'
                            : 'text-slate-400 hover:text-white'
                            }`}
                    >
                        🔊 Audio Gen
                    </button>
                    <button
                        onClick={() => setActiveTab('video')}
                        className={`px-4 py-2 font-medium transition-colors ${activeTab === 'video'
                            ? 'text-blue-400 border-b-2 border-blue-400'
                            : 'text-slate-400 hover:text-white'
                            }`}
                    >
                        🎬 Video Gen
                    </button>
                </div>

                {/* Content */}
                <div className="bg-slate-900 rounded-2xl p-6 border border-slate-800 min-h-[500px]">

                    {/* SCRIPT TAB */}
                    {activeTab === 'script' && (
                        <div className="space-y-8">
                            <div className="flex gap-4">
                                <input
                                    type="text"
                                    value={scriptTopic}
                                    onChange={(e) => setScriptTopic(e.target.value)}
                                    placeholder="Enter a topic for script generation..."
                                    className="flex-1 p-3 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                />
                                <button
                                    onClick={handleGenerateScript}
                                    disabled={!scriptTopic || scriptLoading}
                                    className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {scriptLoading ? 'Generating...' : 'Generate Script'}
                                </button>
                            </div>

                            {generatedScript && (
                                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                    <div className="flex justify-between items-start">
                                        <div className="p-4 bg-slate-800/50 rounded-xl border border-slate-700 flex-1 mr-4">
                                            <h2 className="text-xl font-bold text-white mb-2">{generatedScript.title}</h2>
                                            <p className="text-slate-400">{generatedScript.overall_style}</p>
                                        </div>

                                        <button
                                            onClick={async () => {
                                                setVideoLoading(true);
                                                setError(null);
                                                try {
                                                    // 1. Check for missing images and generate them
                                                    const currentImages = { ...sceneImages };
                                                    // Use scene_number for reliable mapping
                                                    const missingScenes = generatedScript.scenes.filter((scene: any) => !currentImages[scene.scene_number]);

                                                    if (missingScenes.length > 0) {
                                                        console.log(`Generating images for ${missingScenes.length} missing scenes...`);

                                                        // Update loading state for all missing scenes
                                                        const newLoadingState = { ...sceneLoading };
                                                        missingScenes.forEach((scene: any) => {
                                                            newLoadingState[scene.scene_number] = true;
                                                        });
                                                        setSceneLoading(newLoadingState);

                                                        // Generate images in parallel
                                                        const imagePromises = missingScenes.map(async (scene: any) => {
                                                            try {
                                                                const res = await fetch('/api/dev/generate-image', {
                                                                    method: 'POST',
                                                                    headers: { 'Content-Type': 'application/json' },
                                                                    body: JSON.stringify({
                                                                        prompt: scene.image_create_prompt,
                                                                        scene_number: scene.scene_number
                                                                    }),
                                                                });
                                                                if (res.ok) {
                                                                    const data = await res.json();
                                                                    return { sceneNumber: scene.scene_number, url: data.url };
                                                                }
                                                            } catch (e) {
                                                                console.error(`Failed to generate image for scene ${scene.scene_number}`, e);
                                                            }
                                                            return null;
                                                        });

                                                        const results = await Promise.all(imagePromises);

                                                        // Update local state with new images
                                                        const updatedImages = { ...currentImages };
                                                        const updatedLoading = { ...newLoadingState };

                                                        results.forEach(result => {
                                                            if (result) {
                                                                updatedImages[result.sceneNumber] = result.url;
                                                            }
                                                        });

                                                        // Clear loading flags
                                                        missingScenes.forEach((scene: any) => {
                                                            updatedLoading[scene.scene_number] = false;
                                                        });

                                                        setSceneImages(updatedImages);
                                                        setSceneLoading(updatedLoading);

                                                        // Use the updated map for video generation
                                                        var finalImageMap = updatedImages;
                                                    } else {
                                                        var finalImageMap = currentImages;
                                                    }

                                                    // 2. Generate Video
                                                    const res = await fetch('/api/dev/generate-video-from-script', {
                                                        method: 'POST',
                                                        headers: { 'Content-Type': 'application/json' },
                                                        body: JSON.stringify({
                                                            script: generatedScript,
                                                            image_map: finalImageMap
                                                        }),
                                                    });

                                                    if (!res.ok) {
                                                        const errData = await res.json();
                                                        throw new Error(errData.detail || 'Failed to generate video');
                                                    }

                                                    const data = await res.json();
                                                    setGeneratedVideo(data.video_url);
                                                    setActiveTab('video');
                                                } catch (e: any) {
                                                    setError(e.message);
                                                } finally {
                                                    setVideoLoading(false);
                                                    setSceneLoading({});
                                                }
                                            }}
                                            disabled={videoLoading}
                                            className="px-6 py-4 bg-green-600 hover:bg-green-500 rounded-xl font-bold shadow-lg shadow-green-900/20 flex items-center gap-2 transition-all hover:scale-105 disabled:opacity-50 disabled:scale-100"
                                        >
                                            {videoLoading ? (
                                                <>
                                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                                    Rendering...
                                                </>
                                            ) : (
                                                <>
                                                    <span>🎬</span>
                                                    Generate Full Video
                                                </>
                                            )}
                                        </button>
                                    </div>

                                    <div className="grid gap-6">
                                        {generatedScript.scenes.map((scene: any, idx: number) => (
                                            <div key={idx} className="bg-slate-800 p-6 rounded-xl border border-slate-700 flex gap-6">
                                                {/* Scene Info */}
                                                <div className="flex-1 space-y-4">
                                                    <div className="flex items-center gap-3">
                                                        <span className="bg-blue-900/50 text-blue-200 px-2 py-1 rounded text-xs font-mono">
                                                            SCENE {idx + 1}
                                                        </span>
                                                        <span className="text-sm font-bold text-slate-300">{scene.scene_type}</span>
                                                    </div>

                                                    <div>
                                                        <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Visual Prompt</label>
                                                        <p className="text-sm text-slate-300 bg-slate-900/50 p-3 rounded border border-slate-800">
                                                            {scene.image_create_prompt}
                                                        </p>
                                                    </div>

                                                    <div>
                                                        <label className="text-xs font-bold text-slate-500 uppercase block mb-1">Dialogue</label>
                                                        <p className="text-sm text-green-400 italic">"{scene.dialogue}"</p>
                                                    </div>
                                                </div>

                                                {/* Asset Generation Column */}
                                                <div className="w-64 flex flex-col gap-4 border-l border-slate-700 pl-6">
                                                    <div className="aspect-video bg-slate-900 rounded-lg border border-slate-700 overflow-hidden flex items-center justify-center relative group">
                                                        {sceneImages[idx + 1] ? (
                                                            <img src={sceneImages[idx + 1]} alt="Generated" className="w-full h-full object-cover" />
                                                        ) : (
                                                            <span className="text-xs text-slate-600">No Image</span>
                                                        )}

                                                        {sceneLoading[idx + 1] && (
                                                            <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                                                                <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                                            </div>
                                                        )}
                                                    </div>

                                                    <button
                                                        onClick={() => handleGenerateSceneImage(idx + 1, scene.image_create_prompt)}
                                                        disabled={sceneLoading[idx + 1]}
                                                        className="w-full py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm font-medium transition-colors"
                                                    >
                                                        Generate Image 🎨
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* IMAGE TAB */}
                    {activeTab === 'image' && (
                        <div className="flex flex-col gap-6">
                            <div className="flex gap-4">
                                <input
                                    type="text"
                                    value={prompt}
                                    onChange={(e) => setPrompt(e.target.value)}
                                    placeholder="Enter image prompt..."
                                    className="flex-1 p-3 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                />
                                <select
                                    value={imageStyle}
                                    onChange={(e) => setImageStyle(e.target.value)}
                                    className="p-3 bg-slate-800 border border-slate-700 rounded-lg outline-none"
                                >
                                    <option value="cinematic">Cinematic</option>
                                    <option value="single_character">Single Character</option>
                                    <option value="character_with_background">Character with Background</option>
                                    <option value="infographic">Infographic</option>
                                    <option value="comic_panel">Comic Panel</option>
                                    <option value="close_up_reaction">Close-up Reaction</option>
                                    <option value="wide_establishing_shot">Wide Establishing Shot</option>
                                </select>
                                <button
                                    onClick={handleGenerateImage}
                                    disabled={!prompt || loading}
                                    className="px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading ? 'Generating...' : 'Generate'}
                                </button>
                            </div>

                            {error && (
                                <div className="p-4 bg-red-900/20 border border-red-900/50 text-red-400 rounded-lg">
                                    {error}
                                </div>
                            )}

                            <div className="flex-1 min-h-[400px] bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-center overflow-hidden">
                                {loading ? (
                                    <div className="flex flex-col items-center gap-4">
                                        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                                        <p className="text-slate-400 animate-pulse">Creating masterpiece...</p>
                                    </div>
                                ) : generatedImage ? (
                                    <img src={generatedImage} alt="Generated" className="max-w-full max-h-[600px] object-contain" />
                                ) : (
                                    <div className="text-slate-600 flex flex-col items-center gap-2">
                                        <span className="text-4xl">🖼️</span>
                                        <p>Enter a prompt to generate an image</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* AUDIO TAB */}
                    {activeTab === 'audio' && (
                        <div className="flex flex-col items-center justify-center h-[400px] text-slate-500">
                            <span className="text-4xl mb-4">🚧</span>
                            <p>Audio generation testing coming soon...</p>
                        </div>
                    )}

                    {/* VIDEO TAB */}
                    {activeTab === 'video' && (
                        <div className="flex flex-col gap-6">
                            <div className="flex gap-4 mb-4">
                                <button
                                    onClick={() => setVideoType('text')}
                                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${videoType === 'text'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                                        }`}
                                >
                                    Text to Video
                                </button>
                                <button
                                    onClick={() => setVideoType('image')}
                                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${videoType === 'image'
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                                        }`}
                                >
                                    Image to Video
                                </button>
                            </div>

                            <div className="flex gap-4">
                                <div className="flex-1 space-y-4">
                                    <input
                                        type="text"
                                        value={videoPrompt}
                                        onChange={(e) => setVideoPrompt(e.target.value)}
                                        placeholder="Enter video prompt..."
                                        className="w-full p-3 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                    />

                                    {videoType === 'image' && (
                                        <input
                                            type="text"
                                            value={videoImageUrl}
                                            onChange={(e) => setVideoImageUrl(e.target.value)}
                                            placeholder="Enter source image URL..."
                                            className="w-full p-3 bg-slate-800 border border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                        />
                                    )}
                                </div>

                                <button
                                    onClick={handleGenerateVideo}
                                    disabled={!videoPrompt || (videoType === 'image' && !videoImageUrl) || videoLoading}
                                    className="px-6 h-12 bg-blue-600 hover:bg-blue-500 rounded-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed self-start"
                                >
                                    {videoLoading ? 'Generating...' : 'Generate Video'}
                                </button>
                            </div>

                            {error && (
                                <div className="p-4 bg-red-900/20 border border-red-900/50 text-red-400 rounded-lg">
                                    {error}
                                </div>
                            )}

                            <div className="flex-1 min-h-[400px] bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-center overflow-hidden">
                                {videoLoading ? (
                                    <div className="flex flex-col items-center gap-4">
                                        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                                        <p className="text-slate-400 animate-pulse">Rendering video...</p>
                                        <p className="text-yellow-500 text-xs font-medium bg-yellow-900/20 px-3 py-1 rounded-full">
                                            ⚠️ May take 10-15 mins
                                        </p>
                                    </div>
                                ) : generatedVideo ? (
                                    <video controls src={generatedVideo} className="max-w-full max-h-[600px]" />
                                ) : (
                                    <div className="text-slate-600 flex flex-col items-center gap-2">
                                        <span className="text-4xl">🎬</span>
                                        <p>Enter a prompt to generate a video</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
