import React, { useState, useEffect } from 'react';
import { chatService } from '../../services/api';

const ImageManager = ({ specsList, refreshData }) => {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [imageSearch, setImageSearch] = useState('');
    const [statusMessage, setStatusMessage] = useState('');
    
    // For drag and drop visual state
    const [dragOverId, setDragOverId] = useState(null);

    useEffect(() => {
        loadProducts();
    }, []);

    const loadProducts = async () => {
        setLoading(true);
        try {
            // Get all products and current mapping
            const allProducts = await chatService.getAllProducts();
            const mappings = await chatService.getSpecsMapping();
            
            // Filter out products that already have a mapping
            const unassigned = allProducts.filter(p => !mappings[String(p.Material)]);
            setProducts(unassigned);
        } catch (error) {
            console.error("Error cargando productos:", error);
            setStatusMessage("Error cargando el inventario.");
        } finally {
            setLoading(false);
        }
    };

    const handleDragStart = (e, filename) => {
        e.dataTransfer.setData('text/plain', filename);
        e.dataTransfer.effectAllowed = 'link';
    };

    const handleDragOver = (e, materialId) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'link';
        if (dragOverId !== materialId) {
            setDragOverId(materialId);
        }
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setDragOverId(null);
    };

    const handleDrop = async (e, materialId) => {
        e.preventDefault();
        setDragOverId(null);
        
        const filename = e.dataTransfer.getData('text/plain');
        if (!filename || !materialId) return;

        setStatusMessage(`Vinculando ${filename} a ${materialId}...`);
        
        try {
            const result = await chatService.linkSpec(materialId, filename);
            if (result.message) {
                setStatusMessage('✓ ' + result.message);
                // Remove product from list
                setProducts(prev => prev.filter(p => String(p.Material) !== String(materialId)));
                if (refreshData) await refreshData();
            } else {
                setStatusMessage('Error al vincular.');
            }
        } catch (error) {
            setStatusMessage('Error de conexión.');
        }
    };

    // Filter lists based on search
    const filteredProducts = products.filter(p => 
        (p.Subproducto && p.Subproducto.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (p.Material && String(p.Material).includes(searchTerm))
    );

    const filteredImages = (specsList || []).filter(img => 
        img.toLowerCase().includes(imageSearch.toLowerCase())
    );

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 200px)', gap: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <p style={{ color: '#9CA3AF', fontSize: '14px', margin: 0 }}>
                    Arrastra una imagen de la galería de la derecha y suéltala sobre un producto de la izquierda para vincularlos.
                </p>
                {statusMessage && (
                    <span style={{ 
                        padding: '6px 12px', 
                        borderRadius: '20px', 
                        fontSize: '13px', 
                        fontWeight: '600',
                        backgroundColor: statusMessage.includes('✓') ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                        color: statusMessage.includes('✓') ? '#34D399' : '#F87171'
                    }}>
                        {statusMessage}
                    </span>
                )}
            </div>

            <div style={{ display: 'flex', gap: '20px', flex: 1, overflow: 'hidden' }}>
                {/* LEFT PANEL: Products */}
                <div style={{ flex: 1, background: '#111827', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    <div style={{ padding: '16px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', color: '#F3F4F6' }}>📦 Productos sin Imagen ({products.length})</h3>
                        <input
                            type="text"
                            placeholder="Buscar por código o nombre..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px 14px', borderRadius: '8px', color: 'white', outline: 'none' }}
                        />
                    </div>
                    <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {loading ? (
                            <p style={{ color: '#9CA3AF', textAlign: 'center', marginTop: '20px' }}>Cargando inventario...</p>
                        ) : filteredProducts.length === 0 ? (
                            <p style={{ color: '#9CA3AF', textAlign: 'center', marginTop: '20px' }}>No hay productos pendientes.</p>
                        ) : (
                            filteredProducts.map(product => (
                                <div 
                                    key={product.Material}
                                    onDragOver={(e) => handleDragOver(e, product.Material)}
                                    onDragLeave={handleDragLeave}
                                    onDrop={(e) => handleDrop(e, product.Material)}
                                    style={{
                                        background: dragOverId === product.Material ? 'rgba(167, 139, 250, 0.2)' : 'rgba(31, 41, 55, 0.5)',
                                        border: `1px solid ${dragOverId === product.Material ? '#A78BFA' : 'transparent'}`,
                                        borderRadius: '10px',
                                        padding: '12px',
                                        transition: 'all 0.2s',
                                        transform: dragOverId === product.Material ? 'scale(1.02)' : 'scale(1)'
                                    }}
                                >
                                    <div style={{ color: '#A78BFA', fontWeight: 'bold', fontSize: '13px', marginBottom: '4px' }}>
                                        {product.Material}
                                    </div>
                                    <div style={{ color: '#F3F4F6', fontSize: '14px', fontWeight: '500' }}>
                                        {product.Subproducto}
                                    </div>
                                    <div style={{ color: '#9CA3AF', fontSize: '12px', marginTop: '4px', textTransform: 'uppercase' }}>
                                        {product.categoria || 'Sin categoría'}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>

                {/* RIGHT PANEL: Images */}
                <div style={{ flex: 1, background: '#111827', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                    <div style={{ padding: '16px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', color: '#F3F4F6' }}>🖼️ Galería de Imágenes ({specsList?.length || 0})</h3>
                        <input
                            type="text"
                            placeholder="Buscar archivo de imagen..."
                            value={imageSearch}
                            onChange={(e) => setImageSearch(e.target.value)}
                            style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px 14px', borderRadius: '8px', color: 'white', outline: 'none' }}
                        />
                    </div>
                    <div style={{ 
                        flex: 1, 
                        overflowY: 'auto', 
                        padding: '16px', 
                        display: 'grid', 
                        gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', 
                        gap: '12px',
                        alignContent: 'start'
                    }}>
                        {filteredImages.length === 0 ? (
                            <p style={{ color: '#9CA3AF', textAlign: 'center', gridColumn: '1 / -1' }}>No hay imágenes que coincidan.</p>
                        ) : (
                            filteredImages.map(filename => (
                                <div 
                                    key={filename}
                                    draggable
                                    onDragStart={(e) => handleDragStart(e, filename)}
                                    style={{
                                        background: 'rgba(31, 41, 55, 0.8)',
                                        borderRadius: '10px',
                                        overflow: 'hidden',
                                        cursor: 'grab',
                                        border: '1px solid rgba(255,255,255,0.08)',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        height: '160px',
                                        transition: 'transform 0.2s, border-color 0.2s'
                                    }}
                                    onMouseEnter={e => e.currentTarget.style.borderColor = 'rgba(167, 139, 250, 0.5)'}
                                    onMouseLeave={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)'}
                                >
                                    <div style={{ 
                                        height: '100px', 
                                        width: '100%',
                                        display: 'flex', 
                                        alignItems: 'center', 
                                        justifyContent: 'center',
                                        background: '#000',
                                        padding: '4px'
                                    }}>
                                        <img 
                                            src={chatService.getSpecImageUrl(filename)} 
                                            alt={filename}
                                            style={{ 
                                                maxWidth: '100%', 
                                                maxHeight: '100%', 
                                                objectFit: 'contain', 
                                                pointerEvents: 'none' 
                                            }}
                                            onError={(e) => { e.target.style.display = 'none'; }}
                                        />
                                    </div>
                                    <div style={{ 
                                        flex: 1,
                                        padding: '8px', 
                                        background: 'rgba(17, 24, 39, 0.9)', 
                                        fontSize: '11px', 
                                        color: '#E5E7EB', 
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        textAlign: 'center',
                                        wordBreak: 'break-all',
                                        overflow: 'hidden',
                                        lineHeight: '1.2'
                                    }}>
                                        {filename}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ImageManager;
