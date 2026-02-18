import React, { useState, useEffect } from 'react';
import { chatService } from '../../services/api';

const QuotasLookup = () => {
    const [quotasMapping, setQuotasMapping] = useState({});
    const [query, setQuery] = useState('');
    const [result, setResult] = useState(null);
    const [searched, setSearched] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        chatService.getQuotas().then(data => {
            setQuotasMapping(data || {});
            setLoading(false);
        }).catch(() => setLoading(false));
    }, []);

    const handleSearch = () => {
        const cleanId = String(query).replace(/[^\d]/g, '').trim();
        const found = quotasMapping[cleanId] || quotasMapping[query.trim()];
        setResult(found || null);
        setSearched(true);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') handleSearch();
    };

    const totalEquipos = Object.keys(quotasMapping).length;

    return (
        <div style={{ color: 'white', padding: '24px', maxWidth: '700px', margin: '0 auto' }}>
            {/* Header */}
            <div style={{ marginBottom: '32px' }}>
                <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '6px' }}>
                    💰 Consulta de Cuotas
                </h2>
                <p style={{ color: '#9CA3AF', fontSize: '14px' }}>
                    {loading
                        ? 'Cargando datos...'
                        : totalEquipos > 0
                            ? `${totalEquipos} equipos con cuotas disponibles`
                            : '⚠️ Sin datos de cuotas en el servidor'}
                </p>
            </div>

            {/* Search Box */}
            <div style={{
                background: '#111827',
                borderRadius: '20px',
                border: '1px solid rgba(255,255,255,0.08)',
                padding: '24px',
                marginBottom: '24px'
            }}>
                <label style={{ display: 'block', fontSize: '13px', color: '#9CA3AF', marginBottom: '10px' }}>
                    Código de Material
                </label>
                <div style={{ display: 'flex', gap: '12px' }}>
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => { setQuery(e.target.value); setSearched(false); }}
                        onKeyDown={handleKeyDown}
                        placeholder="Ej: 7023240"
                        style={{
                            flex: 1,
                            background: '#1F2937',
                            border: '1px solid rgba(255,255,255,0.1)',
                            borderRadius: '12px',
                            padding: '12px 16px',
                            color: 'white',
                            fontSize: '16px',
                            outline: 'none',
                            fontFamily: 'monospace',
                            letterSpacing: '1px'
                        }}
                    />
                    <button
                        onClick={handleSearch}
                        disabled={!query.trim() || loading}
                        style={{
                            background: (!query.trim() || loading) ? '#374151' : 'linear-gradient(135deg, #F59E0B, #D97706)',
                            border: 'none',
                            borderRadius: '12px',
                            padding: '12px 24px',
                            color: 'white',
                            fontWeight: '700',
                            fontSize: '14px',
                            cursor: (!query.trim() || loading) ? 'not-allowed' : 'pointer',
                            transition: 'all 0.2s',
                            whiteSpace: 'nowrap'
                        }}
                    >
                        Consultar
                    </button>
                </div>
            </div>

            {/* Result */}
            {searched && (
                result ? (
                    <div style={{
                        background: '#111827',
                        borderRadius: '20px',
                        border: '1px solid rgba(245, 158, 11, 0.3)',
                        padding: '24px',
                        boxShadow: '0 4px 24px rgba(245, 158, 11, 0.08)'
                    }}>
                        <div style={{ fontSize: '12px', color: '#9CA3AF', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '1px' }}>
                            Material
                        </div>
                        <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#FCD34D', marginBottom: '20px', fontFamily: 'monospace' }}>
                            {String(query).replace(/[^\d]/g, '') || query.trim()}
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '12px' }}>
                            {[6, 12, 18, 24, 36].map(months => (
                                result[months] ? (
                                    <div key={months} style={{
                                        background: 'rgba(245, 158, 11, 0.08)',
                                        border: '1px solid rgba(245, 158, 11, 0.2)',
                                        borderRadius: '14px',
                                        padding: '16px 12px',
                                        textAlign: 'center'
                                    }}>
                                        <div style={{ fontSize: '11px', color: '#9CA3AF', marginBottom: '6px', fontWeight: '600' }}>
                                            {months} CUOTAS
                                        </div>
                                        <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#FCD34D' }}>
                                            ${new Intl.NumberFormat('es-CO').format(result[months])}
                                        </div>
                                        <div style={{ fontSize: '10px', color: '#6B7280', marginTop: '4px' }}>
                                            c/mes
                                        </div>
                                    </div>
                                ) : null
                            ))}
                        </div>
                    </div>
                ) : (
                    <div style={{
                        background: '#111827',
                        borderRadius: '20px',
                        border: '1px solid rgba(239, 68, 68, 0.2)',
                        padding: '24px',
                        textAlign: 'center'
                    }}>
                        <div style={{ fontSize: '32px', marginBottom: '8px' }}>🔍</div>
                        <div style={{ color: '#EF4444', fontWeight: '600', marginBottom: '4px' }}>
                            Material no encontrado
                        </div>
                        <div style={{ color: '#6B7280', fontSize: '13px' }}>
                            El código <strong style={{ color: '#9CA3AF' }}>{query}</strong> no tiene cuotas registradas.
                        </div>
                    </div>
                )
            )}

            {/* Empty state */}
            {!searched && !loading && totalEquipos === 0 && (
                <div style={{
                    background: '#111827',
                    borderRadius: '20px',
                    border: '1px solid rgba(239, 68, 68, 0.2)',
                    padding: '32px',
                    textAlign: 'center'
                }}>
                    <div style={{ fontSize: '40px', marginBottom: '12px' }}>⚠️</div>
                    <div style={{ color: '#EF4444', fontWeight: '600', marginBottom: '8px' }}>
                        Sin datos de cuotas en el servidor
                    </div>
                    <div style={{ color: '#6B7280', fontSize: '13px', lineHeight: '1.6' }}>
                        Ve a <strong style={{ color: '#A78BFA' }}>Memoria Maestra</strong> y sube el archivo <code>cuotas.xlsx</code> para activar esta función.
                    </div>
                </div>
            )}
        </div>
    );
};

export default QuotasLookup;
