import React, { useState } from 'react';
import { chatService } from '../../services/api';

const ExpertKnowledge = ({ specFile, setSpecFile, specName, setSpecName, handleSpecUpload, specUploadStatus, knowledge, specsList, refreshData }) => {
    const [unlocked, setUnlocked] = useState(false);
    const [passwordInput, setPasswordInput] = useState('');
    const [passwordError, setPasswordError] = useState(false);

    const [quotasFile, setQuotasFile] = useState(null);
    const [quotasStatus, setQuotasStatus] = useState('');
    const [quotasLoading, setQuotasLoading] = useState(false);
    const [searchMaterial, setSearchMaterial] = useState('');
    const [foundItem, setFoundItem] = useState(null);
    const [editTip, setEditTip] = useState('');
    const [saveStatus, setSaveStatus] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);

    // New state for linking images
    const [linkMaterial, setLinkMaterial] = useState('');
    const [selectedImageFile, setSelectedImageFile] = useState('');
    const [linkStatus, setLinkStatus] = useState('');

    const handleUnlock = () => {
        if (passwordInput === 'TEC123') {
            setUnlocked(true);
            setPasswordError(false);
        } else {
            setPasswordError(true);
            setPasswordInput('');
        }
    };

    const handleSearch = async () => {
        if (!searchMaterial) return;
        setSaveStatus('Buscando...');

        const expertItem = knowledge.find(k => k.sku.toUpperCase() === searchMaterial.toUpperCase());
        if (expertItem) {
            setFoundItem(expertItem);
            setEditTip(expertItem.tip_venta || '');
            setSaveStatus('');
            return;
        }

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
            if (refreshData) await refreshData();
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

    const handleLinkImage = async () => {
        if (!linkMaterial || !selectedImageFile) return;
        setLinkStatus('Vinculando...');
        try {
            const result = await chatService.linkSpec(linkMaterial, selectedImageFile);
            if (result.message) {
                setLinkStatus('✓ ' + result.message);
                if (refreshData) await refreshData();
            } else {
                setLinkStatus('Error al vincular.');
            }
        } catch (e) {
            setLinkStatus('Error de conexión.');
        }
    };

    // --- PASSWORD GATE ---
    if (!unlocked) {
        return (
            <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '60vh',
                gap: '24px',
                color: 'white',
                textAlign: 'center',
                padding: '40px'
            }}>
                <div style={{
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: '20px',
                    padding: '40px 48px',
                    maxWidth: '420px',
                    width: '100%'
                }}>
                    <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔒</div>
                    <h2 style={{ fontSize: '22px', fontWeight: '700', marginBottom: '8px', color: '#F87171' }}>
                        Zona Restringida
                    </h2>
                    <p style={{ fontSize: '14px', color: '#9CA3AF', marginBottom: '28px', lineHeight: '1.6' }}>
                        ⚠️ Esta es una interfaz exclusiva para <strong style={{ color: '#FCD34D' }}>desarrolladores</strong>.<br />
                        Ingresa la contraseña de acceso para continuar.
                    </p>

                    <input
                        type="password"
                        placeholder="Contraseña de desarrollador"
                        value={passwordInput}
                        onChange={(e) => { setPasswordInput(e.target.value); setPasswordError(false); }}
                        onKeyDown={(e) => e.key === 'Enter' && handleUnlock()}
                        style={{
                            width: '100%',
                            background: '#1F2937',
                            border: `1px solid ${passwordError ? '#EF4444' : 'rgba(255,255,255,0.1)'}`,
                            padding: '12px 16px',
                            borderRadius: '10px',
                            color: 'white',
                            outline: 'none',
                            fontSize: '15px',
                            marginBottom: '12px',
                            boxSizing: 'border-box',
                            letterSpacing: '2px'
                        }}
                    />

                    {passwordError && (
                        <p style={{ color: '#EF4444', fontSize: '13px', marginBottom: '12px' }}>
                            ❌ Contraseña incorrecta. Inténtalo nuevamente.
                        </p>
                    )}

                    <button
                        onClick={handleUnlock}
                        style={{
                            width: '100%',
                            background: 'linear-gradient(135deg, #7C3AED, #5B21B6)',
                            border: 'none',
                            padding: '12px',
                            borderRadius: '10px',
                            color: 'white',
                            fontWeight: '700',
                            fontSize: '15px',
                            cursor: 'pointer',
                            transition: 'opacity 0.2s'
                        }}
                        onMouseEnter={e => e.target.style.opacity = '0.85'}
                        onMouseLeave={e => e.target.style.opacity = '1'}
                    >
                        Acceder
                    </button>
                </div>
            </div>
        );
    }

    // --- MAIN CONTENT (unlocked) ---
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

                <div style={{ flex: 1, background: '#111827', padding: '24px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '16px', color: '#C4B5FD' }}>🔗 Vincular Material a Imagen Existente</h3>
                    <p style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '16px' }}>Si la imagen ya está subida, búscala aquí y asígnala a un código de material.</p>

                    <div style={{ marginBottom: '15px' }}>
                        <label style={{ display: 'block', fontSize: '13px', color: '#9CA3AF', marginBottom: '8px' }}>Código de Material o Modelo:</label>
                        <input
                            type="text"
                            placeholder="Ej: 100234"
                            value={linkMaterial}
                            onChange={(e) => setLinkMaterial(e.target.value)}
                            style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white', outline: 'none' }}
                        />
                    </div>

                    <div style={{ marginBottom: '15px' }}>
                        <label style={{ display: 'block', fontSize: '13px', color: '#9CA3AF', marginBottom: '8px' }}>Seleccionar Imagen:</label>
                        <select
                            value={selectedImageFile}
                            onChange={(e) => setSelectedImageFile(e.target.value)}
                            style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white', outline: 'none' }}
                        >
                            <option value="">Selecciona una imagen...</option>
                            {specsList.map((f, i) => (
                                <option key={i} value={f}>{f}</option>
                            ))}
                        </select>
                    </div>

                    <button
                        onClick={handleLinkImage}
                        disabled={!linkMaterial || !selectedImageFile}
                        style={{
                            background: (!linkMaterial || !selectedImageFile) ? '#374151' : 'linear-gradient(135deg, #10B981, #059669)',
                            border: 'none',
                            padding: '12px',
                            borderRadius: '10px',
                            color: 'white',
                            fontWeight: '700',
                            cursor: (!linkMaterial || !selectedImageFile) ? 'not-allowed' : 'pointer',
                            width: '100%'
                        }}
                    >
                        Vincular Ahora
                    </button>
                    {linkStatus && <p style={{ marginTop: '10px', fontSize: '13px', color: linkStatus.includes('✓') ? '#10B981' : '#F87171' }}>{linkStatus}</p>}
                </div>
            </div>

            {/* Sales Speech Editor */}
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

            {/* Cuotas Uploader */}
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
        </div>
    );
};

export default ExpertKnowledge;
