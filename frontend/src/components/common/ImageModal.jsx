import React from 'react';

const ImageModal = ({ imageUrl, onClose }) => {
    if (!imageUrl) return null;

    const handleShare = async (e) => {
        e.stopPropagation();

        try {
            // 1. Fetch the image
            const response = await fetch(imageUrl);
            const blob = await response.blob();

            // 2. Sane filename and FORCE .jpg extension for compatibility
            let filename = imageUrl.split('/').pop() || 'ficha-tecnica.jpg';
            filename = filename.replace(/[^a-zA-Z0-9.-]/g, '_'); // Sanitize chars
            if (!filename.toLowerCase().endsWith('.jpg') && !filename.toLowerCase().endsWith('.png')) {
                filename += '.jpg';
            }

            // 3. Create File object
            const file = new File([blob], filename, { type: blob.type || 'image/jpeg' });

            // 4. Try Sharing File (Primary)
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({
                    files: [file],
                    title: 'Ficha Técnica',
                    text: 'Mira esta ficha técnica.'
                });
            } else {
                throw new Error('File sharing not supported');
            }
        } catch (err) {
            console.warn('Share file failed, trying URL fallback:', err);

            // 5. Fallback: Share URL
            try {
                if (navigator.share) {
                    await navigator.share({
                        title: 'Ficha Técnica',
                        url: imageUrl
                    });
                } else {
                    throw new Error('Web Share API not supported');
                }
            } catch (urlErr) {
                // 6. Final Fallback: Clipboard
                try {
                    await navigator.clipboard.writeText(imageUrl);
                    alert('Enlace copiado al portapapeles (Compartir no disponible en este dispositivo)');
                } catch (clipErr) {
                    alert('No se pudo compartir la imagen.');
                }
            }
        }
    };

    return (
        <div
            style={{
                position: 'fixed', inset: 0, zIndex: 100, background: 'rgba(0,0,0,0.95)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                backdropFilter: 'blur(10px)',
                overflow: 'auto' // Allow scrolling if zoomed
            }}
            onClick={onClose}
        >
            <img
                src={imageUrl}
                alt="Ficha ampliada"
                style={{
                    maxWidth: '95%',
                    maxHeight: '95%',
                    borderRadius: '4px',
                    boxShadow: '0 20px 50px rgba(0,0,0,0.8)',
                    transition: 'transform 0.2s ease-out',
                    touchAction: 'pinch-zoom' // Explicitly allow pinch zoom on mobile
                }}
                onClick={(e) => e.stopPropagation()} // Prevent close when clicking image
            />

            {/* Close Button */}
            <button
                style={{ position: 'absolute', top: '24px', right: '24px', background: 'white', border: 'none', borderRadius: '50%', width: '40px', height: '40px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 101 }}
                onClick={onClose}
            >
                <svg style={{ width: '24px', height: '24px', color: '#111827' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>

            {/* Share Button */}
            <button
                style={{ position: 'absolute', bottom: '24px', right: '24px', background: 'white', border: 'none', borderRadius: '50%', width: '56px', height: '56px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 101, boxShadow: '0 4px 15px rgba(0,0,0,0.3)' }}
                onClick={handleShare}
                title="Compartir ficha"
            >
                <svg style={{ width: '24px', height: '24px', color: '#111827' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
                </svg>
            </button>
        </div>
    );
};

export default ImageModal;
