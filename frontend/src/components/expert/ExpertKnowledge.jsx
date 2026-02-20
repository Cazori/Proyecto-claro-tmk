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
        if (!searchMaterial) return;
        const item = knowledge.find(k => k.sku.toUpperCase() === searchMaterial.toUpperCase());
        if (item) {
            setFoundItem(item);
            setEditTip(item.tip_venta || '');
            setSaveStatus('');
        } else {
            setFoundItem(null);
            setSaveStatus('No se encontró ningún producto con ese Material.');
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
            <div style={{ display: 'flex', gap: '20px', marginBottom: '32px', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, background: '#111827', padding: '24px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px' }}>Subir Ficha Técnica</h3>

                    <div style={{ marginBottom: '15px' }}>
                        <label style={{ display: 'block', fontSize: '13px', color: '#9CA3AF', marginBottom: '8px' }}>Nombre del producto o ID de Material:</label>
                        <input
                            type="text"
                            placeholder="Ej: HP G10 o 100234"
                            value={specName || ''}
                            onChange={(e) => setSpecName(e.target.value)}
                            style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white', outline: 'none' }}
                            list="material-suggestions"
                        />
                        <datalist id="material-suggestions">
                            {knowledge.map((k, i) => (
                                <option key={i} value={k.sku}>{k.model}</option>
                            ))}
                        </datalist>
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

            {/* Sales Speech Editor Section */}
            <div style={{ background: '#111827', padding: '24px', borderRadius: '20px', border: '1px solid rgba(167, 139, 250, 0.2)', marginBottom: '32px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px', color: '#A78BFA' }}>💡 Editor de Tip de Venta</h3>
                <p style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '16px' }}>Busca por código de Material para editar el speech de venta personalizado.</p>

                <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
                    <input
                        type="text"
                        placeholder="Pegar Material aquí..."
                        value={searchMaterial}
                        onChange={(e) => setSearchMaterial(e.target.value)}
                        style={{ flex: 1, background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white' }}
                    />
                    <button
                        onClick={handleSearch}
                        style={{ background: '#7C3AED', border: 'none', padding: '10px 20px', borderRadius: '8px', color: 'white', fontWeight: '600', cursor: 'pointer' }}
                    >
                        Buscar
                    </button>
                </div>

                {foundItem && (
                    <div style={{ background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '4px' }}>{foundItem.model}</div>
                        <div style={{ fontSize: '12px', color: '#9CA3AF', marginBottom: '12px' }}>{foundItem.specs}</div>

                        <label style={{ display: 'block', fontSize: '13px', color: '#A78BFA', marginBottom: '6px' }}>Speech de Venta / Tip:</label>
                        <textarea
                            rows="2"
                            value={editTip}
                            onChange={(e) => setEditTip(e.target.value)}
                            placeholder="Escribe aquí el argumento de venta ganador..."
                            style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white', outline: 'none', resize: 'none', marginBottom: '12px' }}
                        />

                        <button
                            onClick={handleSaveTip}
                            style={{ background: 'rgba(167, 139, 250, 0.2)', border: '1px solid rgba(167, 139, 250, 0.4)', padding: '8px 16px', borderRadius: '8px', color: '#C4B5FD', fontWeight: '600', cursor: 'pointer', width: '100%' }}
                        >
                            Guardar Tip para {foundItem.sku}
                        </button>
                    </div>
                )}
                {saveStatus && <p style={{ marginTop: '10px', fontSize: '13px', color: saveStatus.includes('✓') ? '#10B981' : '#F87171' }}>{saveStatus}</p>}
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
