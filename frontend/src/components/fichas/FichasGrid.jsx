import React, { useMemo } from 'react';
import useFuzzySearch from '../../hooks/useFuzzySearch';
import { chatService } from '../../services/api';

const FichasGrid = ({ fichasSearch, setFichasSearch, specsList = [], setSelectedImage }) => {
    const searchData = useMemo(() =>
        (specsList || []).map(filename => ({
            filename,
            cleanName: filename.toLowerCase().replace(/\.[^/.]+$/, "").replace(/[\s-]/g, ' ')
        })),
        [specsList]);

    const { search } = useFuzzySearch(searchData, {
        keys: ['cleanName'],
        threshold: 0.4
    });

    const filtered = fichasSearch ? search(fichasSearch) : [];

    return (
        <div style={{ color: 'white', padding: '24px', height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div style={{ maxWidth: '800px', margin: '0 auto', width: '100%' }}>
                <div className="input-wrapper" style={{ marginBottom: '24px', background: '#111827' }}>
                    <svg style={{ width: '20px', height: '20px', marginLeft: '16px', color: '#6B7280' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <input
                        id="fichas-search-input"
                        type="text"
                        className="chat-input"
                        placeholder="Buscar ficha técnica (ej: gt6pro, fit4)..."
                        value={fichasSearch}
                        onChange={(e) => setFichasSearch(e.target.value)}
                    />
                </div>
            </div>

            <div className="fichas-grid" style={{ flex: 1, overflowY: 'auto', paddingBottom: '40px' }}>
                {!fichasSearch ? (
                    <p style={{ gridColumn: '1/-1', textAlign: 'center', color: '#6B7280', marginTop: '40px' }}>
                        Ingresa una referencia para buscar su ficha técnica.
                    </p>
                ) : filtered.length === 0 ? (
                    <p style={{ gridColumn: '1/-1', textAlign: 'center', color: '#EF4444', marginTop: '40px' }}>
                        No se encontraron fichas para "{fichasSearch}".
                    </p>
                ) : (
                    filtered.map(({ filename }) => (
                        <div
                            key={filename}
                            className="ficha-card"
                            onClick={() => setSelectedImage(chatService.getSpecImageUrl(filename))}
                            style={{
                                background: '#111827',
                                borderRadius: '16px',
                                overflow: 'hidden',
                                border: '1px solid rgba(255,255,255,0.05)',
                                cursor: 'pointer',
                                transition: 'all 0.3s ease'
                            }}
                        >
                            <div style={{ height: '240px', overflow: 'hidden', background: '#0B0F19', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                <img
                                    src={chatService.getSpecImageUrl(filename)}
                                    alt={filename}
                                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                                    loading="lazy"
                                />
                            </div>
                            <div style={{ padding: '12px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                                <p style={{ fontSize: '13px', fontWeight: '500', color: '#D1D5DB', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                    {filename.replace(/\.[^/.]+$/, "")}
                                </p>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default FichasGrid;
