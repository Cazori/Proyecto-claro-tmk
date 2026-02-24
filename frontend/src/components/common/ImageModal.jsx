import React, { useCallback, useRef } from 'react';
import QuickPinchZoom, { make3dTransformValue } from 'react-quick-pinch-zoom';

const ImageModal = ({ imageUrl, onClose }) => {
    if (!imageUrl) return null;

    const imgRef = useRef();
    const urls = Array.isArray(imageUrl) ? imageUrl : [imageUrl];
    const [currentIndex, setCurrentIndex] = React.useState(0);
    const currentUrl = urls[currentIndex];

    // Reset index if urls change
    React.useEffect(() => {
        setCurrentIndex(0);
    }, [imageUrl]);

    const onUpdate = useCallback(({ x, y, scale }) => {
        if (imgRef.current) {
            const value = make3dTransformValue({ x, y, scale });
            imgRef.current.style.setProperty('transform', value);
        }
    }, []);

    const handleShare = async (e) => {
        e.stopPropagation();
        try {
            const response = await fetch(currentUrl);
            const blob = await response.blob();
            let filename = currentUrl.split('/').pop() || 'ficha-tecnica.jpg';
            filename = filename.replace(/[^a-zA-Z0-9.-]/g, '_');
            if (!filename.toLowerCase().endsWith('.jpg') && !filename.toLowerCase().endsWith('.png')) {
                filename += '.jpg';
            }
            const file = new File([blob], filename, { type: blob.type || 'image/jpeg' });
            await navigator.share({ files: [file] });
        } catch (err) {
            console.warn('Share file failed, trying URL fallback:', err);
            try {
                if (navigator.share) {
                    await navigator.share({ title: 'Ficha Técnica', url: currentUrl });
                } else {
                    throw new Error('Web Share API not supported');
                }
            } catch (urlErr) {
                try {
                    await navigator.clipboard.writeText(currentUrl);
                    alert('Enlace copiado al portapapeles');
                } catch (clipErr) {
                    alert('No se pudo compartir la imagen.');
                }
            }
        }
    };

    const nextImage = (e) => {
        e.stopPropagation();
        setCurrentIndex((prev) => (prev + 1) % urls.length);
    };

    const prevImage = (e) => {
        e.stopPropagation();
        setCurrentIndex((prev) => (prev - 1 + urls.length) % urls.length);
    };

    return (
        <div
            className="modal-overlay"
            style={{
                position: 'fixed', inset: 0, zIndex: 100, background: 'rgba(0,0,0,0.95)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                backdropFilter: 'blur(10px)'
            }}
            onClick={onClose}
        >
            <div className="modal-content" style={{ width: '100vw', height: '100vh' }}>
                <QuickPinchZoom onUpdate={onUpdate} wheelScaleFactor={1.1}>
                    <div ref={imgRef} style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', width: '100%' }}>
                        <img
                            src={currentUrl}
                            alt="Ficha ampliada"
                            style={{
                                maxWidth: '95vw',
                                maxHeight: '95vh',
                                objectFit: 'contain',
                                borderRadius: '4px',
                                boxShadow: '0 20px 50px rgba(0,0,0,0.8)'
                            }}
                        />
                    </div>
                </QuickPinchZoom>

                {urls.length > 1 && (
                    <>
                        {/* Navigation Arrows */}
                        <button
                            onClick={prevImage}
                            className="nav-btn-modal"
                            style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', width: '50px', height: '50px', color: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 105, backdropFilter: 'blur(5px)' }}
                        >
                            <svg style={{ width: '30px', height: '30px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M15 19l-7-7 7-7" strokeWidth={2} /></svg>
                        </button>
                        <button
                            onClick={nextImage}
                            className="nav-btn-modal"
                            style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '50%', width: '50px', height: '50px', color: 'white', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 105, backdropFilter: 'blur(5px)' }}
                        >
                            <svg style={{ width: '30px', height: '30px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path d="M9 5l7 7-7 7" strokeWidth={2} /></svg>
                        </button>

                        {/* Pagination indicator */}
                        <div style={{ position: 'absolute', bottom: '20px', left: '50%', transform: 'translateX(-50%)', background: 'rgba(0,0,0,0.5)', padding: '5px 15px', borderRadius: '20px', color: 'white', fontSize: '14px', zIndex: 105 }}>
                            {currentIndex + 1} / {urls.length}
                        </div>
                    </>
                )}
            </div>

            {/* Top Close Button */}
            <button
                className="close-btn-modal"
                style={{ position: 'absolute', top: '24px', right: '24px', background: 'white', border: 'none', borderRadius: '50%', width: '40px', height: '40px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 110 }}
                onClick={onClose}
            >
                <svg style={{ width: '24px', height: '24px', color: '#111827' }} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>

            {/* Share Button */}
            <button
                className="share-btn-modal"
                style={{ position: 'absolute', bottom: '24px', right: '24px', background: 'white', border: 'none', borderRadius: '50%', width: '56px', height: '56px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 110, boxShadow: '0 4px 15px rgba(0,0,0,0.3)' }}
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
