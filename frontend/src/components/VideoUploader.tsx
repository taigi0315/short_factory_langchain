import React, { useRef } from 'react';

interface VideoUploaderProps {
    sceneNumber: number;
    videoUrl?: string;
    onUpload: (file: File) => void;
    isUploading?: boolean;
}

export const VideoUploader: React.FC<VideoUploaderProps> = ({
    sceneNumber,
    videoUrl,
    onUpload,
    isUploading
}) => {
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            // Validate file
            if (file.size > 100 * 1024 * 1024) {
                alert('File too large! Max 100MB');
                return;
            }

            const ext = file.name.toLowerCase().split('.').pop();
            if (!['mp4', 'mov', 'webm'].includes(ext || '')) {
                alert('Invalid format! Use .mp4, .mov, or .webm');
                return;
            }

            onUpload(file);
        }
    };

    return (
        <div className="video-uploader">
            {videoUrl ? (
                <div className="video-preview">
                    <video src={videoUrl} controls />
                    <button
                        className="replace-btn"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        🔄 Replace
                    </button>
                </div>
            ) : (
                <div className="upload-placeholder">
                    <p>No video uploaded</p>
                    <button
                        className="upload-btn"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                    >
                        {isUploading ? '⏳ Uploading...' : '📤 Upload Video'}
                    </button>
                </div>
            )}

            <input
                ref={fileInputRef}
                type="file"
                accept=".mp4,.mov,.webm"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
            />
        </div>
    );
};
