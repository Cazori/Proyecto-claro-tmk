import React from 'react';
import { chatService } from '../../services/api';

const CategoryIcon = ({ subproducto = '' }) => {
    const s = subproducto.toLowerCase();

    // Simple SVG Icons
    if (s.includes('tv') || s.includes('televisor')) {
        return (
            <svg className="product-thumb-fallback" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
        );
    }
    if (s.includes('cel') || s.includes('iphone') || s.includes('moto') || s.includes('samsung')) {
        return (
            <svg className="product-thumb-fallback" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
        );
    }
    if (s.includes('prt') || s.includes('laptop') || s.includes('macbook') || s.includes('hp')) {
        return (
            <svg className="product-thumb-fallback" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
        );
    }
    return (
        <svg className="product-thumb-fallback" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
    );
};

const ProductCard = ({ product, specsMapping = {}, onViewSpec }) => {
    let { Material, Subproducto, CantDisponible, "Precio Contado": Precio, hasImage, quotas, tip, Marca } = product;
    const [showQuotas, setShowQuotas] = React.useState(false);
    const [showTip, setShowTip] = React.useState(false);

    // Localization: Replace "Home Theater" with "Barra de sonido"
    const localizedTitle = Subproducto ? Subproducto.replace(/Home Theater/gi, 'Barra de sonido') : '';

    const isOutOfStock = CantDisponible === 0;
    const isCriticalStock = CantDisponible >= 1 && CantDisponible <= 3;
    const isLowStock = CantDisponible >= 4 && CantDisponible <= 9;

    const stockStatus = isOutOfStock
        ? { label: 'AGOTADO', color: '#EF4444' }
        : isCriticalStock
            ? { label: 'CRÍTICO', color: '#F87171' }
            : isLowStock
                ? { label: 'BAJO STOCK', color: '#FBBF24' }
                : { label: 'DISPONIBLE', color: '#10B981' };

    // Resolve the real spec filename from specsMapping (backend resolved match)
    // We normalize the Material ID to handle potential leading zeros and whitespace
    const normMaterial = String(Material || '').trim().replace(/^0+/, '');

    const resolvedFilename = specsMapping[String(Material)] || specsMapping[normMaterial];

    // Add a cache-buster timestamp if we have a mapping update
    const cacheBuster = sessionStorage.getItem('cleo_mapping_v') || '1';

    const thumbUrl = resolvedFilename
        ? `${chatService.getSpecImageUrl(resolvedFilename)}?v=${cacheBuster}`
        : `${chatService.getSpecImageUrl(`${Material}.jpg`)}?v=${cacheBuster}`;
    const showThumb = hasImage || !!resolvedFilename;

    return (
        <div className="product-card-premium">
            <div className="product-badge" style={{ background: stockStatus.color, boxShadow: `0 2px 10px ${stockStatus.color}44` }}>
                {stockStatus.label}
            </div>

            <div className="product-thumb-area" onClick={() => onViewSpec(Material, Subproducto)} style={{ cursor: showThumb ? 'pointer' : 'default' }}>
                {showThumb ? (
                    <img
                        src={thumbUrl}
                        alt={Subproducto}
                        className="product-thumb-image"
                        loading="lazy"
                        onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'flex';
                        }}
                    />
                ) : null}
                <div style={{ display: showThumb ? 'none' : 'flex' }}>
                    <CategoryIcon subproducto={Subproducto} />
                </div>
            </div>

            <div className="product-info-area">
                <h4 className="product-title-premium" title={localizedTitle}>
                    {localizedTitle}
                </h4>

                <div className="product-meta-row" style={{ flexWrap: 'wrap', gap: '4px' }}>
                    {Marca && Marca !== 'N/A' && (
                        <span className="brand-tag" style={{
                            background: 'rgba(255,255,255,0.1)',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '10px',
                            fontWeight: 'bold',
                            color: '#e5e7eb',
                            textTransform: 'uppercase'
                        }}>
                            {Marca}
                        </span>
                    )}
                    <span className="ref-tag">REF: <strong>{Material}</strong></span>
                    <span className="divider">•</span>
                    <span className="stock-tag">Unidades: <strong style={{ color: stockStatus.color }}>{CantDisponible}</strong></span>
                </div>

                <div className="product-price-box">
                    <span className="price-label">Precio Contado</span>
                    <span className="price-value">
                        ${new Intl.NumberFormat('es-CO').format(Precio)}
                    </span>
                </div>

                <div className="product-actions-premium">
                    {quotas && (
                        <button
                            className={`premium-btn premium-btn-secondary ${showQuotas ? 'active' : ''}`}
                            onClick={() => {
                                setShowQuotas(!showQuotas);
                                setShowTip(false);
                            }}
                        >
                            <svg style={{ width: '14px', height: '14px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span className="btn-label">{showQuotas ? 'Cerrar' : 'Cuotas'}</span>
                        </button>
                    )}

                    <button
                        className={`premium-btn premium-btn-primary ${tip ? 'tip-glow' : ''} ${showTip ? 'active' : ''}`}
                        onClick={() => {
                            setShowTip(!showTip);
                            setShowQuotas(false);
                        }}
                    >
                        <svg style={{ width: '14px', height: '14px' }} fill={showTip ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                        <span className="btn-label">{showTip ? 'Cerrar' : 'Info'}</span>
                    </button>

                    <button
                        className="premium-btn premium-btn-tertiary"
                        onClick={(e) => {
                            e.stopPropagation();
                            const query = `Dime las especificaciones técnicas de ${Subproducto}`;
                            window.open(`https://www.google.com/search?q=${encodeURIComponent(query)}`, '_blank');
                        }}
                        title="Buscar en Google AI"
                    >
                        <svg style={{ width: '14px', height: '14px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                        </svg>
                        <span className="btn-label">AI Search</span>
                    </button>
                </div>

                {(showTip || showQuotas) && (
                    <div className="product-details-dropdown" style={{
                        marginTop: '12px',
                        padding: '12px',
                        background: 'rgba(0,0,0,0.3)',
                        borderRadius: '16px',
                        border: '1px solid rgba(255,255,255,0.08)',
                        animation: 'fadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                        boxShadow: 'inset 0 2px 10px rgba(0,0,0,0.2)'
                    }}>
                        {showTip && (
                            <div className="tip-content" style={{ fontSize: '13px', color: '#E5E7EB', lineHeight: '1.5' }}>
                                <strong style={{ color: '#A78BFA', display: 'block', fontSize: '11px', marginBottom: '6px', letterSpacing: '0.05em' }}>SPEECH DE VENTA:</strong>
                                {tip || 'Producto de alta demanda con garantía extendida Claro.'}
                            </div>
                        )}
                        {showQuotas && quotas && (
                            <div className="quotas-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(60px, 1fr))', gap: '8px' }}>
                                {[6, 12, 18, 24, 36].map(m => quotas[String(m)] != null && (
                                    <div key={m} className="quota-item" style={{ textAlign: 'center', background: 'rgba(255,255,255,0.03)', padding: '6px', borderRadius: '8px' }}>
                                        <div style={{ fontSize: '10px', color: '#9CA3AF', marginBottom: '2px' }}>{m}m</div>
                                        <div style={{ fontSize: '12px', fontWeight: '800', color: '#FCD34D' }}>
                                            ${new Intl.NumberFormat('es-CO').format(quotas[String(m)])}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ProductCard;
