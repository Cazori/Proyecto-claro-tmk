import React from 'react';

const ImageModal = ({ imageUrl, onClose }) => {
    if (!imageUrl) return null;

    const handleShare = async (e) => {
        e.stopPropagation();
        if (navigator.share) {
            try {
                await navigator.share({
                    title: 'Ficha Técnica - Claro TMK',
                    text: 'Mira esta ficha técnica que encontré en Cleo AI.',
                    url: imageUrl
                });
            } catch (err) {
                console.error('Error al compartir:', err);
            }
        } else {
            // Fallback for PC: Copy to clipboard
            try {
                await navigator.clipboard.writeText(imageUrl);
                alert('Enlace copiado al portapapeles');
            } catch (err) {
                console.error('Error al copiar:', err);
            }
        }
    };

    return (
        <div
            style={{
                position: 'fixed', inset: 0, zIndex: 100, background: 'rgba(0,0,0,0.9)',
                display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px',
                backdropFilter: 'blur(8px)', cursor: 'zoom-out'
            }}
            onClick={onClose}
        >
            <img
                src={imageUrl}
                alt="Ficha ampliada"
                style={{ maxWidth: '100%', maxHeight: '100%', borderRadius: '8px', boxShadow: '0 20px 50px rgba(0,0,0,0.5)' }}
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
