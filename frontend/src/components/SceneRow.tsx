import React from 'react';
import { VideoUploader } from './VideoUploader';
import { EffectSelector } from './EffectSelector';

interface Scene {
    scene_number: number;
    scene_type: string;
    dialogue: string;
    voice_tone: string;
    video_importance: number;
    effect_reasoning?: string;
}

interface SceneState {
    sceneNumber: number;
    imageUrl?: string;
    videoUrl?: string;
    selectedEffect: string;
    isGeneratingImage: boolean;
    isUploadingVideo: boolean;
}

interface SceneRowProps {
    scene: Scene;
    state?: SceneState;
    onImageGenerate: () => void;
    onVideoUpload: (file: File) => void;
    onEffectChange: (effect: string) => void;
    onCopyPrompt: () => void;
}

export const SceneRow: React.FC<SceneRowProps> = ({
    scene,
    state,
    onImageGenerate,
    onVideoUpload,
    onEffectChange,
    onCopyPrompt
}) => {
    const downloadImage = (url: string) => {
        const a = document.createElement('a');
        a.href = url;
        a.download = `scene_${scene.scene_number}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    };

    return (
        <div className="scene-row">
            <div className="scene-header">
                <span className="scene-number">Scene {scene.scene_number}</span>
                <span className="scene-type">{scene.scene_type}</span>
                <span className="importance">⭐ {scene.video_importance}/10</span>
            </div>

            <div className="scene-content">
                <div className="dialogue-column">
                    <p className="dialogue-text">{scene.dialogue}</p>
                    <span className="voice-tone">{scene.voice_tone}</span>
                </div>

                <div className="image-column">
                    <label className="column-label">Image</label>
                    {state?.imageUrl ? (
                        <div className="image-preview">
                            <img src={state.imageUrl} alt={`Scene ${scene.scene_number}`} />
                            <button
                                className="download-btn"
                                onClick={() => downloadImage(state.imageUrl!)}
                            >
                                📥 Download
                            </button>
                        </div>
                    ) : (
                        <div className="image-placeholder">
                            <button
                                className="generate-btn"
                                onClick={onImageGenerate}
                                disabled={state?.isGeneratingImage}
                            >
                                {state?.isGeneratingImage ? '⏳ Generating...' : '🎨 Generate Image'}
                            </button>
                        </div>
                    )}
                </div>

                <div className="video-column">
                    <label className="column-label">Video</label>
                    <VideoUploader
                        sceneNumber={scene.scene_number}
                        videoUrl={state?.videoUrl}
                        onUpload={onVideoUpload}
                        isUploading={state?.isUploadingVideo}
                    />
                </div>

                <div className="effect-column">
                    <label className="column-label">Effect</label>
                    <EffectSelector
                        effect={state?.selectedEffect || 'ken_burns_zoom_in'}
                        reasoning={(scene as any).effect_reasoning || "AI-selected based on scene type and content"}
                        isRecommended={true}
                    />
                </div>

                <div className="actions-column">
                    <button className="copy-prompt-btn" onClick={onCopyPrompt}>
                        📋 Copy Video Prompt
                    </button>
                </div>
            </div>
        </div>
    );
};
