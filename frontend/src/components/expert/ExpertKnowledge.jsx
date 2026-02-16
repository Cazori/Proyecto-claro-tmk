import React from 'react';

const ExpertKnowledge = ({ specFile, setSpecFile, handleSpecUpload, specUploadStatus, knowledge }) => {
    return (
        <div style={{ color: 'white', padding: '20px' }}>
            <div style={{ display: 'flex', gap: '20px', marginBottom: '32px' }}>
                <div style={{ flex: 1, background: '#111827', padding: '24px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px' }}>Subir Ficha Técnica</h3>
                    <input type="file" accept="image/*,.pdf" onChange={(e) => setSpecFile(e.target.files[0])} />
                    {specFile && (
                        <button onClick={handleSpecUpload} style={{ marginTop: '15px', background: '#7C3AED', border: 'none', padding: '10px 20px', borderRadius: '10px', color: 'white', fontWeight: '600', cursor: 'pointer' }}>
                            Indexar Ficha
                        </button>
                    )}
                    {specUploadStatus && <p style={{ marginTop: '10px', fontSize: '13px', color: '#A78BFA' }}>{specUploadStatus}</p>}
                </div>
                <div style={{ flex: 1, background: 'rgba(124, 58, 237, 0.05)', padding: '24px', borderRadius: '20px', border: '1px solid rgba(124, 58, 237, 0.1)' }}>
                    <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#C4B5FD', marginBottom: '8px' }}>¿Para qué sirve esto?</h3>
                    <p style={{ fontSize: '14px', color: '#9CA3AF', lineHeight: '1.5' }}>
                        Al subir imágenes o PDFs de fichas técnicas, Cleo aprenderá características que no están en el inventario (como el procesador "Ryzen 5" o la "RAM"). Esto permite buscar por características y no solo por nombre.
                    </p>
                </div>
            </div>

            <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px' }}>Conocimientos Indexados</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
                {knowledge.length === 0 && <p style={{ color: '#6B7280' }}>Aún no hay fichas indexadas. Cleo está esperando aprender...</p>}
                {knowledge.map((item, idx) => (
                    <div key={idx} style={{ background: '#111827', padding: '16px', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div style={{ color: '#A78BFA', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', marginBottom: '4px' }}>{item.sku}</div>
                        <div style={{ fontSize: '15px', fontWeight: '600', marginBottom: '8px' }}>{item.model}</div>
                        <div style={{ fontSize: '13px', color: '#9CA3AF' }}>{item.specs}</div>
                    </div>
                ))}
                {/* Mock example for visual guide */}
                <div style={{ opacity: 0.5, background: '#111827', padding: '16px', borderRadius: '16px', border: '1px dashed rgba(255,255,255,0.2)' }}>
                    <div style={{ fontSize: '11px', fontWeight: '700', marginBottom: '4px' }}>EJEMPLO: B8PH9LA</div>
                    <div style={{ fontSize: '15px', fontWeight: '600', marginBottom: '8px' }}>HP 255 G10</div>
                    <div style={{ fontSize: '13px' }}>Ryzen 5 7530U, 16GB RAM...</div>
                </div>
            </div>
        </div>
    );
};

export default ExpertKnowledge;
