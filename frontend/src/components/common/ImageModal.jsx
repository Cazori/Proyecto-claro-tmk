import React from 'react';

const ImageModal = ({ imageUrl, onClose }) => {
    if (!imageUrl) return null;

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
            <button
                style={{ position: 'absolute', top: '24px', right: '24px', background: 'white', border: 'none', borderRadius: '50%', width: '40px', height: '40px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                onClick={onClose}
            >
                <svg style={{ width: '24px', height: '24px', color: '#111827' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        </div>
    );
};

export default ImageModal;
