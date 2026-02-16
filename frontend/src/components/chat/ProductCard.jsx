import React from 'react';

const ProductCard = ({ product, onViewSpec }) => {
    let { Material, Subproducto, CantDisponible, "Precio Contado": Precio, hasSpec } = product;

    // Localization: Replace "Home Theater" with "Barra de sonido"
    const localizedTitle = Subproducto ? Subproducto.replace(/Home Theater/gi, 'Barra de sonido') : '';

    // New stock status logic per user requirements
    const isOutOfStock = CantDisponible === 0;
    const isCriticalStock = CantDisponible >= 1 && CantDisponible <= 3;
    const isLowStock = CantDisponible >= 4 && CantDisponible <= 9;
    const isInStock = CantDisponible >= 10;

    const stockStatus = isOutOfStock
        ? { label: 'AGOTADO', color: '#6B7280' }
        : isCriticalStock
            ? { label: 'STOCK CRÍTICO', color: '#EF4444' }
            : isLowStock
                ? { label: 'STOCK BAJO', color: '#F59E0B' }
                : { label: 'EN STOCK', color: '#10B981' };

    return (
        <div className="product-card" style={{
            background: '#111827',
            borderRadius: '16px',
            border: `1px solid ${stockStatus.color}44`,
            padding: '16px',
            marginBottom: '12px',
            width: '100%',
            maxWidth: '400px',
            boxShadow: `0 4px 20px ${stockStatus.color}11`,
            transition: 'transform 0.2s',
            position: 'relative',
            overflow: 'hidden'
        }}>
            <div style={{
                position: 'absolute',
                top: 0,
                right: 0,
                background: stockStatus.color,
                color: '#0B0F19',
                fontSize: '10px',
                fontWeight: 'bold',
                padding: '2px 10px',
                borderBottomLeftRadius: '12px'
            }}>
                {stockStatus.label}
            </div>

            <h4 style={{
                margin: '0 0 4px 0',
                fontSize: '15px',
                fontWeight: 'bold',
                color: '#F3F4F6',
                lineHeight: '1.4',
                wordBreak: 'break-word'
            }}>
                {localizedTitle}
            </h4>

            <div style={{ fontSize: '12px', color: '#9CA3AF', marginBottom: '12px', display: 'flex', gap: '8px' }}>
                <span>Material: <strong>{Material}</strong></span>
                <span>•</span>
                <span>Stock: <strong>{CantDisponible}</strong></span>
            </div>

            <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
                <div>
                    <span style={{ fontSize: '11px', color: '#9CA3AF', display: 'block', textTransform: 'uppercase' }}>Precio Contado</span>
                    <span style={{ fontSize: '20px', fontWeight: 'bold', color: '#A78BFA' }}>
                        ${new Intl.NumberFormat('es-CO').format(Precio)}
                    </span>
                </div>

                <button
                    onClick={() => hasSpec && onViewSpec(Material, Subproducto)}
                    style={{
                        background: hasSpec ? 'rgba(124, 58, 237, 0.1)' : 'rgba(107, 114, 128, 0.05)',
                        border: `1px solid ${hasSpec ? 'rgba(124, 58, 237, 0.3)' : 'rgba(107, 114, 128, 0.2)'}`,
                        color: hasSpec ? '#C4B5FD' : '#6B7280',
                        padding: '6px 12px',
                        borderRadius: '8px',
                        fontSize: '12px',
                        fontWeight: '600',
                        cursor: hasSpec ? 'pointer' : 'not-allowed',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.2s',
                        opacity: hasSpec ? 1 : 0.6
                    }}
                    onMouseOver={(e) => hasSpec && (e.currentTarget.style.background = 'rgba(124, 58, 237, 0.2)')}
                    onMouseOut={(e) => hasSpec && (e.currentTarget.style.background = 'rgba(124, 58, 237, 0.1)')}
                >
                    <svg style={{ width: '14px', height: '14px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Ver Ficha
                </button>
            </div>
        </div>
    );
};

export default ProductCard;
