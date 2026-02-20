import React, { useState } from 'react';
import { chatService } from '../../services/api';

const ExpertKnowledge = ({ specFile, setSpecFile, specName, setSpecName, handleSpecUpload, specUploadStatus, knowledge }) => {
    const [quotasFile, setQuotasFile] = useState(null);
    const [quotasStatus, setQuotasStatus] = useState('');
    const [quotasLoading, setQuotasLoading] = useState(false);
    const [searchMaterial, setSearchMaterial] = useState('');
    const [foundItem, setFoundItem] = useState(null);
    const [editTip, setEditTip] = useState('');
    const [saveStatus, setSaveStatus] = useState('');

    const handleSearch = () => {
        const search = (searchMaterial || '').trim().toUpperCase();
        if (!search) return;

        // Priority 1: Exact SKU match. Priority 2: Partial Model match.
        const item = knowledge.find(k =>
            (k.sku && k.sku.toUpperCase() === search) ||
            (k.model && k.model.toUpperCase().includes(search))
        );

        if (item) {
            setFoundItem(item);
            setEditTip(item.tip_venta || '');
            setSaveStatus('');
        } else {
            setFoundItem(null);
            setSaveStatus(`No se encontró "${searchMaterial}". Intenta con el código exacto o parte del nombre.`);
        }
    };

    const handleSaveTip = async () => {
        if (!foundItem) return;
        setSaveStatus('Guardando...');
        try {
            const entry = { ...foundItem, tip_venta: editTip };
            await chatService.updateKnowledge(entry);
            setSaveStatus('✓ Tip guardado correctamente.');
            // Update local state if needed (optional since parent probably fetches on mount)
        } catch (e) {
            setSaveStatus('Error al guardar el tip.');
        }
    };

    const handleQuotasUpload = async () => {
        if (!quotasFile) return;
        setQuotasLoading(true);
        setQuotasStatus('Subiendo y procesando cuotas...');
        try {
            const result = await chatService.uploadQuotas(quotasFile);
            setQuotasStatus(result.message || 'Proceso completado.');
            setQuotasFile(null);
        } catch (e) {
            setQuotasStatus('Error al subir el archivo.');
        } finally {
            setQuotasLoading(false);
        }
    };

    return (
        <div style={{ color: 'white', padding: '20px' }}>
            {/* 1. Sales Speech Editor Section (Promoted to Top for Mobile Accessibility) */}
            <div style={{ background: '#111827', padding: '24px', borderRadius: '20px', border: '1px solid rgba(167, 139, 250, 0.4)', marginBottom: '32px', boxShadow: '0 4px 25px rgba(124, 58, 237, 0.1)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <span style={{ fontSize: '24px' }}>💡</span>
                    <h3 style={{ fontSize: '18px', fontWeight: 'bold', margin: 0, color: '#A78BFA' }}>Editor de Tip de Venta</h3>
                </div>
                <p style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '16px' }}>Busca un producto por código de Material o Nombre para personalizar su argumento de venta.</p>

                <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
                    <input
                        type="text"
                        placeholder="Escribe Material o Nombre..."
                        value={searchMaterial}
                        onChange={(e) => setSearchMaterial(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                        style={{ flex: 1, background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '12px', borderRadius: '10px', color: 'white', outline: 'none' }}
                    />
                    <button
                        onClick={handleSearch}
                        style={{ background: '#7C3AED', border: 'none', padding: '0 20px', borderRadius: '10px', color: 'white', fontWeight: '600', cursor: 'pointer', transition: 'all 0.2s' }}
                    >
                        Buscar
                    </button>
                </div>

                {foundItem && (
                    <div style={{ background: 'rgba(255,255,255,0.03)', padding: '20px', borderRadius: '15px', border: '1px solid rgba(167, 139, 250, 0.2)', animation: 'fadeIn 0.3s ease-out' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                            <div>
                                <div style={{ fontSize: '15px', fontWeight: 'bold', color: '#F3F4F6' }}>{foundItem.model}</div>
                                <div style={{ fontSize: '11px', color: '#A78BFA', fontWeight: 'bold', textTransform: 'uppercase', marginTop: '2px' }}>Material: {foundItem.sku}</div>
                            </div>
                            <button onClick={() => setFoundItem(null)} style={{ background: 'transparent', border: 'none', color: '#6B7280', cursor: 'pointer', fontSize: '12px' }}>Cerrar</button>
                        </div>

                        <div style={{ fontSize: '12px', color: '#9CA3AF', marginBottom: '16px', fontStyle: 'italic', paddingLeft: '8px', borderLeft: '2px solid #374151' }}>{foundItem.specs}</div>

                        <label style={{ display: 'block', fontSize: '13px', color: '#A78BFA', marginBottom: '8px', fontWeight: '600' }}>Argumento Ganador (Tip):</label>
                        <textarea
                            rows="3"
                            value={editTip}
                            onChange={(e) => setEditTip(e.target.value)}
                            placeholder="Escribe aquí por qué este producto es increíble..."
                            style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '12px', borderRadius: '10px', color: 'white', outline: 'none', resize: 'none', marginBottom: '16px', fontSize: '14px', lineHeight: '1.4' }}
                        />

                        <button
                            onClick={handleSaveTip}
                            style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)', border: 'none', padding: '12px', borderRadius: '10px', color: 'white', fontWeight: '700', cursor: 'pointer', width: '100%', boxShadow: '0 4px 15px rgba(124, 58, 237, 0.3)' }}
                        >
                            Guardar Cambios
                        </button>
                    </div>
                )}
                {saveStatus && (
                    <div style={{
                        marginTop: '12px',
                        fontSize: '13px',
                        color: saveStatus.includes('✓') ? '#10B981' : '#F87171',
                        background: saveStatus.includes('✓') ? 'rgba(16, 185, 129, 0.1)' : 'rgba(248, 113, 113, 0.1)',
                        padding: '10px',
                        borderRadius: '8px',
                        textAlign: 'center',
                        fontWeight: '500'
                    }}>
                        {saveStatus}
                    </div>
                )}
            </div>

            {/* 2. Upload Section (Secondary) */}
            <div style={{ display: 'flex', gap: '20px', marginBottom: '32px', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: '300px', background: '#111827', padding: '24px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px' }}>Subir Ficha Técnica</h3>

                    <div style={{ marginBottom: '15px' }}>
                        <label style={{ display: 'block', fontSize: '13px', color: '#9CA3AF', marginBottom: '8px' }}>Nombre del producto o ID de Material:</label>
                        <input
                            type="text"
                            placeholder="Ej: HP G10 o 100234"
                            value={specName || ''}
                            onChange={(e) => setSpecName(e.target.value)}
                            style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white', outline: 'none' }}
                        />
                    </div>

                    <input type="file" accept="image/*,.pdf" onChange={(e) => setSpecFile(e.target.files[0])} />

                    {specFile && (
                        <button
                            onClick={handleSpecUpload}
                            disabled={!specName || specName.trim() === ''}
                            style={{
                                marginTop: '15px',
                                background: (!specName || specName.trim() === '') ? '#374151' : '#7C3AED',
                                border: 'none',
                                padding: '10px 20px',
                                borderRadius: '10px',
                                color: 'white',
                                fontWeight: '600',
                                cursor: (!specName || specName.trim() === '') ? 'not-allowed' : 'pointer',
                                width: '100%'
                            }}
                        >
                            Indexar {specName ? `como "${specName}"` : 'Ficha'}
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

            {/* Quotas Upload Section */}
            <div style={{ background: '#111827', padding: '24px', borderRadius: '20px', border: '1px solid rgba(245, 158, 11, 0.2)', marginBottom: '32px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px', color: '#FCD34D' }}>💰 Subir Cuotas (cuotas.xlsx)</h3>
                <p style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '16px' }}>Sube el archivo Excel de cuotas para activar el botón "Ver Cuotas" en las tarjetas de productos.</p>
                <input
                    type="file"
                    accept=".xlsx"
                    onChange={(e) => setQuotasFile(e.target.files[0])}
                    style={{ marginBottom: '12px' }}
                />
                {quotasFile && (
                    <button
                        onClick={handleQuotasUpload}
                        disabled={quotasLoading}
                        style={{
                            display: 'block',
                            marginTop: '8px',
                            background: quotasLoading ? '#374151' : 'rgba(245, 158, 11, 0.2)',
                            border: '1px solid rgba(245, 158, 11, 0.4)',
                            padding: '10px 20px',
                            borderRadius: '10px',
                            color: '#FCD34D',
                            fontWeight: '600',
                            cursor: quotasLoading ? 'not-allowed' : 'pointer',
                            width: '100%'
                        }}
                    >
                        {quotasLoading ? 'Procesando...' : `Subir y Procesar "${quotasFile.name}"`}
                    </button>
                )}
                {quotasStatus && <p style={{ marginTop: '10px', fontSize: '13px', color: '#FCD34D' }}>{quotasStatus}</p>}
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
