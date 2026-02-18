import React from 'react';

const ProductCard = ({ product, onViewSpec }) => {
    let { Material, Subproducto, CantDisponible, "Precio Contado": Precio, hasSpec, quotas } = product;
    const [showQuotas, setShowQuotas] = React.useState(false);

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
            maxWidth: '100%', /* Ensure it fits in bubble */
            boxShadow: `0 4px 20px ${stockStatus.color}11`,
            transition: 'all 0.2s ease-out',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column' /* Explicit flex column */
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

            <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: showQuotas ? '12px' : '0' }}>
                <div>
                    <span style={{ fontSize: '11px', color: '#9CA3AF', display: 'block', textTransform: 'uppercase' }}>Precio Contado</span>
                    <span style={{ fontSize: '20px', fontWeight: 'bold', color: '#A78BFA' }}>
                        ${new Intl.NumberFormat('es-CO').format(Precio)}
                    </span>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                    {quotas && (
                        <button
                            onClick={() => setShowQuotas(!showQuotas)}
                            style={{
                                background: showQuotas ? 'rgba(245, 158, 11, 0.2)' : 'rgba(245, 158, 11, 0.1)',
                                border: `1px solid ${showQuotas ? 'rgba(245, 158, 11, 0.4)' : 'rgba(245, 158, 11, 0.2)'}`,
                                color: '#FCD34D',
                                padding: '6px 12px',
                                borderRadius: '8px',
                                fontSize: '12px',
                                fontWeight: '600',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                transition: 'all 0.2s'
                            }}
                        >
                            <svg style={{ width: '14px', height: '14px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            {showQuotas ? 'Ocultar' : 'Ver Cuotas'}
                        </button>
                    )}

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
                    >
                        <svg style={{ width: '14px', height: '14px' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        Ficha
                    </button>
                </div>
            </div>

            {showQuotas && quotas && (
                <div
                    className="quotas-container"
                    style={{
                        background: 'rgba(17, 24, 39, 0.95)', /* Opaque background to prevent bleed */
                        borderTop: '1px solid rgba(75, 85, 99, 0.4)',
                        paddingTop: '12px',
                        marginTop: '8px',
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '8px',
                        position: 'relative', /* Ensure it stays within flow */
                        zIndex: 10
                    }}
                >
                    {[6, 12, 18, 24, 36].map(months => (
                        quotas[months] ? (
                            <div key={months} style={{
                                background: 'rgba(31, 41, 55, 0.6)',
                                padding: '8px',
                                borderRadius: '8px',
                                textAlign: 'center',
                                border: '1px solid rgba(255,255,255,0.05)'
                            }}>
                                <div style={{ fontSize: '10px', color: '#9CA3AF', marginBottom: '2px' }}>{months} Cuotas</div>
                                <div style={{ fontSize: '13px', fontWeight: 'bold', color: '#FCD34D' }}>
                                    ${new Intl.NumberFormat('es-CO').format(quotas[months])}
                                </div>
                            </div>
                        ) : null
                    ))}
                </div>
            )}
        </div>
    );
};

export default ProductCard;
