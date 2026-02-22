import React, { useState } from 'react';
import { chatService } from '../../services/api';

const ExpertKnowledge = ({ specFile, setSpecFile, specName, setSpecName, handleSpecUpload, specUploadStatus, knowledge, refreshKnowledge }) => {
    const [quotasFile, setQuotasFile] = useState(null);
    const [quotasStatus, setQuotasStatus] = useState('');
    const [quotasLoading, setQuotasLoading] = useState(false);
    const [searchMaterial, setSearchMaterial] = useState('');
    const [foundItem, setFoundItem] = useState(null);
    const [editTip, setEditTip] = useState('');
    const [saveStatus, setSaveStatus] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);

    // Auto-tip state
    const [autoTipCategory, setAutoTipCategory] = useState('');
    const [autoTipText, setAutoTipText] = useState('');
    const [autoTipStatus, setAutoTipStatus] = useState('');

    const handleSearch = async () => {
        if (!searchMaterial) return;
        setSaveStatus('Buscando...');

        // 1. Search in existing knowledge
        const expertItem = knowledge.find(k => k.sku.toUpperCase() === searchMaterial.toUpperCase());
        if (expertItem) {
            setFoundItem(expertItem);
            setEditTip(expertItem.tip_venta || '');
            setSaveStatus('');
            return;
        }

        // 2. Search in inventory via API
        try {
            const result = await chatService.findProduct(searchMaterial);
            if (result && !result.error) {
                setFoundItem({
                    sku: result.Material,
                    model: result.Subproducto,
                    specs: result.especificaciones || '-'
                });
                setEditTip(result.tip_venta || '');
                setSaveStatus('✓ Encontrado en inventario.');
            } else {
                setFoundItem(null);
                setSaveStatus('No se encontró el material en el inventario.');
            }
        } catch (e) {
            setSaveStatus('Error buscando producto.');
        }
    };

    const handleSaveTip = async () => {
        if (!foundItem) return;
        setSaveStatus('Guardando...');
        try {
            const entry = { ...foundItem, tip_venta: editTip };
            await chatService.updateKnowledge(entry);
            setSaveStatus('✓ Tip guardado correctamente.');
            if (refreshKnowledge) await refreshKnowledge();
        } catch (e) {
            setSaveStatus('Error al guardar el tip.');
        }
    };

    const handleGenerateAITip = async () => {
        if (!foundItem) return;
        setIsGenerating(true);
        try {
            const result = await chatService.generateTip(foundItem.model, foundItem.specs);
            if (result.tip) {
                setEditTip(result.tip);
                setSaveStatus('✓ Tip sugerido por Cleo. ¡Guárdalo para fijarlo!');
            }
        } catch (e) {
            setSaveStatus('Error al generar el tip con IA.');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleApplyAutoTips = async () => {
        if (!autoTipCategory || !autoTipText) return;
        setAutoTipStatus('Aplicando tips...');
        try {
            const result = await chatService.applyAutoTips(autoTipCategory, autoTipText);
            setAutoTipStatus(`✓ ${result.applied} productos de "${autoTipCategory}" actualizados.`);
            if (refreshKnowledge) await refreshKnowledge();
        } catch (e) {
            setAutoTipStatus('Error al aplicar tips automáticos.');
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
                    <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px' }}>Subir Ficha Técnica / Imagen</h3>

                    <div style={{ marginBottom: '15px' }}>
                        <label style={{ display: 'block', fontSize: '13px', color: '#9CA3AF', marginBottom: '8px' }}>Asociar a Modelo o Material:</label>
                        <input
                            type="text"
                            placeholder="Ej: 100234 o HP G10"
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

                    {specFile && specFile.type.startsWith('image/') && (
                        <div style={{ marginTop: '15px', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
                            <img
                                src={URL.createObjectURL(specFile)}
                                alt="Preview"
                                style={{ width: '100%', maxHeight: '200px', objectFit: 'contain', background: '#000' }}
                            />
                        </div>
                    )}

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
                            Subir como "{specName || 'Archivo'}"
                        </button>
                    )}
                    {specUploadStatus && <p style={{ marginTop: '10px', fontSize: '13px', color: '#A78BFA' }}>{specUploadStatus}</p>}
                </div>

                <div style={{ flex: 1, background: 'rgba(124, 58, 237, 0.05)', padding: '24px', borderRadius: '20px', border: '1px solid rgba(124, 58, 237, 0.1)' }}>
                    <h3 style={{ fontSize: '18px', fontWeight: 'bold', color: '#C4B5FD', marginBottom: '8px' }}>Optimización de Datos</h3>
                    <p style={{ fontSize: '14px', color: '#9CA3AF', lineHeight: '1.5' }}>
                        Usa esta sección para que Cleo sea más inteligente. Las fichas técnicas le dan specs detallados, y los tips le dan argumentos de venta para convencer al cliente.
                    </p>
                </div>
            </div>

            {/* Sales Speech Editor Section */}
            <div style={{ background: '#111827', padding: '24px', borderRadius: '20px', border: '1px solid rgba(167, 139, 250, 0.2)', marginBottom: '32px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px', color: '#A78BFA' }}>💡 Editor de Tip de Venta Individual</h3>
                <p style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '16px' }}>Busca por código de Material para editar el speech personalizado de un producto específico.</p>

                <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
                    <input
                        type="text"
                        placeholder="Pegar Material aquí..."
                        value={searchMaterial}
                        onChange={(e) => setSearchMaterial(e.target.value)}
                        style={{ flex: 1, background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white' }}
                        list="edit-suggestions"
                    />
                    <datalist id="edit-suggestions">
                        {knowledge.map((k, i) => (
                            <option key={i} value={k.sku}>{k.model}</option>
                        ))}
                    </datalist>
                    <button
                        onClick={handleSearch}
                        style={{ background: '#7C3AED', border: 'none', padding: '10px 20px', borderRadius: '8px', color: 'white', fontWeight: '600', cursor: 'pointer' }}
                    >
                        Buscar Producto
                    </button>
                </div>

                {foundItem && (
                    <div style={{ background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '4px' }}>{foundItem.model}</div>
                        <div style={{ fontSize: '12px', color: '#9CA3AF', marginBottom: '12px' }}>{foundItem.specs}</div>

                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                            <label style={{ fontSize: '13px', color: '#A78BFA' }}>Speech para el Chat:</label>
                            <button
                                onClick={handleGenerateAITip}
                                disabled={isGenerating}
                                style={{ background: 'none', border: 'none', color: '#C4B5FD', fontSize: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                            >
                                {isGenerating ? 'Generando...' : '✨ Sugerir con IA'}
                            </button>
                        </div>
                        <textarea
                            rows="2"
                            value={editTip}
                            onChange={(e) => setEditTip(e.target.value)}
                            placeholder="Argumento de venta ganador..."
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

            {/* Bulk Automated Tips Section */}
            <div style={{ background: '#111827', padding: '24px', borderRadius: '20px', border: '1px solid rgba(16, 185, 129, 0.2)', marginBottom: '32px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px', color: '#10B981' }}>🚀 Tips Masivos por Categoría (Sin Costo)</h3>
                <p style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '16px' }}>Aplica un speech estándar a todos los productos de una categoría que no tengan tip aún.</p>

                <div style={{ display: 'flex', gap: '8px', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <select
                            value={autoTipCategory}
                            onChange={(e) => setAutoTipCategory(e.target.value)}
                            style={{ flex: 1, background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white' }}
                        >
                            <option value="">Selecciona Categoría...</option>
                            <option value="TELEVISORES">TELEVISORES</option>
                            <option value="CELULARES">CELULARES</option>
                            <option value="AUDIO">AUDIO</option>
                            <option value="LINEA BLANCA">LINEA BLANCA</option>
                            <option value="COMPUTACION">COMPUTACION</option>
                        </select>
                        <button
                            onClick={handleApplyAutoTips}
                            disabled={!autoTipCategory || !autoTipText}
                            style={{ background: '#10B981', border: 'none', padding: '10px 20px', borderRadius: '8px', color: 'white', fontWeight: '600', cursor: (!autoTipCategory || !autoTipText) ? 'not-allowed' : 'pointer' }}
                        >
                            Aplicar a todos
                        </button>
                    </div>
                    <textarea
                        rows="2"
                        value={autoTipText}
                        onChange={(e) => setAutoTipText(e.target.value)}
                        placeholder="Ej: Garantía total de 1 año y envío gratis para toda esta categoría."
                        style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white', outline: 'none', resize: 'none' }}
                    />
                    {autoTipStatus && <p style={{ fontSize: '12px', color: '#10B981' }}>{autoTipStatus}</p>}
                </div>
            </div>

            <div style={{ background: '#111827', padding: '24px', borderRadius: '20px', border: '1px solid rgba(245, 158, 11, 0.2)', marginBottom: '32px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px', color: '#FCD34D' }}>💰 Subir Cuotas (cuotas.xlsx)</h3>
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
                        style={{ display: 'block', marginTop: '8px', background: quotasLoading ? '#374151' : 'rgba(245, 158, 11, 0.2)', border: '1px solid rgba(245, 158, 11, 0.4)', padding: '10px 20px', borderRadius: '10px', color: '#FCD34D', fontWeight: '600', cursor: quotasLoading ? 'not-allowed' : 'pointer', width: '100%' }}
                    >
                        {quotasLoading ? 'Procesando...' : `Subir "${quotasFile.name}"`}
                    </button>
                )}
                {quotasStatus && <p style={{ marginTop: '10px', fontSize: '13px', color: '#FCD34D' }}>{quotasStatus}</p>}
            </div>

            <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px' }}>Conocimientos Indexados</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
                {knowledge.length === 0 && <p style={{ color: '#6B7280' }}>Aún no hay fichas indexadas de forma manual.</p>}
                {knowledge.map((item, idx) => (
                    <div key={idx} style={{ background: '#111827', padding: '16px', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
                        <div style={{ color: '#A78BFA', fontSize: '11px', fontWeight: '700', textTransform: 'uppercase', marginBottom: '4px' }}>{item.sku}</div>
                        <div style={{ fontSize: '15px', fontWeight: '600', marginBottom: '8px' }}>{item.model}</div>
                        <div style={{ fontSize: '13px', color: '#9CA3AF' }}>{item.specs}</div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ExpertKnowledge;
