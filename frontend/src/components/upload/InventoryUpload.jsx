import React from 'react';

const InventoryUpload = ({ file, setFile, handleFileUpload, uploadStatus }) => {
    return (
        <div style={{ color: 'white', padding: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <div style={{ border: '2px dashed rgba(255,255,255,0.1)', padding: '40px', borderRadius: '24px', textAlign: 'center', width: '100%', maxWidth: '500px' }}>
                <svg style={{ width: '48px', height: '48px', color: '#A78BFA', marginBottom: '20px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '10px' }}>Subir Archivo de Inventario</h3>
                <p style={{ color: '#9CA3AF', marginBottom: '20px' }}>Arrastra tu PDF aquí o haz clic para buscar</p>
                <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setFile(e.target.files[0])}
                    style={{ display: 'block', margin: '0 auto', color: '#9CA3AF' }}
                />
                {file && (
                    <button
                        onClick={handleFileUpload}
                        style={{ marginTop: '20px', background: '#7C3AED', color: 'white', border: 'none', padding: '12px 24px', borderRadius: '12px', cursor: 'pointer', fontWeight: 'bold' }}
                    >
                        Procesar {file.name}
                    </button>
                )}
                {uploadStatus && <p style={{ marginTop: '15px', color: '#34D399', fontSize: '14px' }}>{uploadStatus}</p>}
            </div>
        </div>
    );
};

export default InventoryUpload;
