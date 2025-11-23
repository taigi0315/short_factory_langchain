import React, { useState, useEffect } from 'react';
import { SceneRow } from './SceneRow';

interface Scene {
    scene_number: number;
    scene_type: string;
    dialogue: string;
    voice_tone: string;
    image_style: string;
    image_create_prompt: string;
    needs_animation: boolean;
    video_importance: number;
    video_prompt?: string;
}

interface VideoScript {
    title: string;
    scenes: Scene[];
}

interface SceneState {
    sceneNumber: number;
    imageUrl?: string;
    videoUrl?: string;
    selectedEffect: string;
    isGeneratingImage: boolean;
    isUploadingVideo: boolean;
}

interface SceneEditorProps {
    script: VideoScript;
    onBuildVideo: (configs: any[]) => void;
}

export const SceneEditor: React.FC<SceneEditorProps> = ({ script, onBuildVideo }) => {
    const [sceneStates, setSceneStates] = useState<Map<number, SceneState>>(new Map());
    const [isBuilding, setIsBuilding] = useState(false);

    // Initialize scene states
    useEffect(() => {
        const initialStates = new Map<number, SceneState>();
        script.scenes.forEach(scene => {
            initialStates.set(scene.scene_number, {
                sceneNumber: scene.scene_number,
                selectedEffect: 'ken_burns_zoom_in',
                isGeneratingImage: false,
                isUploadingVideo: false,
            });
        });
        setSceneStates(initialStates);
    }, [script]);

    const handleImageGenerate = async (sceneNumber: number) => {
        const scene = script.scenes.find(s => s.scene_number === sceneNumber);
        if (!scene) return;

        // Update state to show loading
        setSceneStates(prev => {
            const newStates = new Map(prev);
            const state = newStates.get(sceneNumber) || {
                sceneNumber,
                selectedEffect: 'ken_burns_zoom_in',
                isGeneratingImage: false,
                isUploadingVideo: false,
            };
            newStates.set(sceneNumber, { ...state, isGeneratingImage: true });
            return newStates;
        });

        try {
            const response = await fetch('/api/scene-editor/generate-image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    scene_number: sceneNumber,
                    script_id: 'current', // TODO: Use actual script ID
                    prompt: scene.image_create_prompt,
                    style: scene.image_style,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to generate image');
            }

            const data = await response.json();

            // Update state with image URL
            setSceneStates(prev => {
                const newStates = new Map(prev);
                const state = newStates.get(sceneNumber)!;
                newStates.set(sceneNumber, {
                    ...state,
                    imageUrl: data.url,
                    isGeneratingImage: false,
                });
                return newStates;
            });
        } catch (error) {
            console.error('Failed to generate image:', error);
            alert('Failed to generate image. Please try again.');

            // Reset loading state
            setSceneStates(prev => {
                const newStates = new Map(prev);
                const state = newStates.get(sceneNumber)!;
                newStates.set(sceneNumber, { ...state, isGeneratingImage: false });
                return newStates;
            });
        }
    };

    const handleVideoUpload = async (sceneNumber: number, file: File) => {
        // Update state to show loading
        setSceneStates(prev => {
            const newStates = new Map(prev);
            const state = newStates.get(sceneNumber)!;
            newStates.set(sceneNumber, { ...state, isUploadingVideo: true });
            return newStates;
        });

        try {
            const formData = new FormData();
            formData.append('video', file);

            const response = await fetch(`/api/scene-editor/upload-video/current/${sceneNumber}`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to upload video');
            }

            const data = await response.json();

            // Update state with video URL
            setSceneStates(prev => {
                const newStates = new Map(prev);
                const state = newStates.get(sceneNumber)!;
                newStates.set(sceneNumber, {
                    ...state,
                    videoUrl: data.url,
                    isUploadingVideo: false,
                });
                return newStates;
            });
        } catch (error: any) {
            console.error('Failed to upload video:', error);
            alert(`Failed to upload video: ${error.message}`);

            // Reset loading state
            setSceneStates(prev => {
                const newStates = new Map(prev);
                const state = newStates.get(sceneNumber)!;
                newStates.set(sceneNumber, { ...state, isUploadingVideo: false });
                return newStates;
            });
        }
    };

    const handleEffectChange = (sceneNumber: number, effect: string) => {
        setSceneStates(prev => {
            const newStates = new Map(prev);
            const state = newStates.get(sceneNumber)!;
            newStates.set(sceneNumber, { ...state, selectedEffect: effect });
            return newStates;
        });
    };

    const handleCopyPrompt = async (sceneNumber: number) => {
        try {
            const response = await fetch(`/api/scene-editor/video-prompt/current/${sceneNumber}`);
            const data = await response.json();

            await navigator.clipboard.writeText(data.video_prompt);
            alert('Video prompt copied to clipboard!');
        } catch (error) {
            console.error('Failed to copy prompt:', error);
            alert('Failed to copy prompt');
        }
    };

    const handleBuildVideo = () => {
        // Build scene configs from current states
        const configs = script.scenes.map(scene => {
            const state = sceneStates.get(scene.scene_number);
            return {
                scene_number: scene.scene_number,
                use_uploaded_video: !!state?.videoUrl,
                video_path: state?.videoUrl,
                effect: state?.selectedEffect || 'ken_burns_zoom_in',
                image_path: state?.imageUrl,
                audio_path: null, // Will be filled by backend
            };
        });

        onBuildVideo(configs);
    };

    const getSummary = () => {
        const uploaded = Array.from(sceneStates.values()).filter(s => s.videoUrl).length;
        const imageEffect = script.scenes.length - uploaded;
        return { uploaded, imageEffect };
    };

    return (
        <div className="scene-editor">
            <div className="editor-header">
                <h2>📝 Script: {script.title}</h2>
                <p>✓ {script.scenes.length} scenes</p>
            </div>

            <div className="scenes-list">
                {script.scenes.map(scene => (
                    <SceneRow
                        key={scene.scene_number}
                        scene={scene}
                        state={sceneStates.get(scene.scene_number)}
                        onImageGenerate={() => handleImageGenerate(scene.scene_number)}
                        onVideoUpload={(file) => handleVideoUpload(scene.scene_number, file)}
                        onEffectChange={(effect) => handleEffectChange(scene.scene_number, effect)}
                        onCopyPrompt={() => handleCopyPrompt(scene.scene_number)}
                    />
                ))}
            </div>

            <div className="editor-footer">
                <div className="summary">
                    <h3>📊 Summary</h3>
                    <p>• {getSummary().uploaded} scenes with uploaded videos</p>
                    <p>• {getSummary().imageEffect} scenes will use image + effect</p>
                </div>
                <button
                    className="build-button"
                    onClick={handleBuildVideo}
                    disabled={isBuilding}
                >
                    {isBuilding ? '⏳ Building...' : '🎬 Build Final Video'}
                </button>
            </div>
        </div>
    );
};
