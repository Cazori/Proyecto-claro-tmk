import React, { useMemo, useState } from 'react';
import useFuzzySearch from '../../hooks/useFuzzySearch';
import { chatService } from '../../services/api';

const FichaCard = ({ filename, setSelectedImage }) => {
    const [loaded, setLoaded] = useState(false);
    const imageUrl = chatService.getSpecImageUrl(filename);
    const cleanName = filename.replace(/\.[^/.]+$/, "");

    return (
        <div
            className="ficha-card-premium"
            onClick={() => setSelectedImage(imageUrl)}
        >
            <div className="ficha-image-container">
                {!loaded && <div className="skeleton-pulse" style={{ position: 'absolute', inset: 0 }} />}
                <img
                    src={imageUrl}
                    alt={filename}
                    className="ficha-thumb"
                    style={{ opacity: loaded ? 1 : 0 }}
                    onLoad={() => setLoaded(true)}
                    loading="lazy"
                />
            </div>
            <div className="ficha-info-premium">
                <p className="ficha-title-premium">{cleanName}</p>
                <p className="ficha-subtitle-premium">Ficha Técnica</p>
            </div>
        </div>
    );
};

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
                <div className="input-wrapper" style={{ marginBottom: '32px' }}>
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

            <div className="fichas-grid-premium">
                {!fichasSearch ? (
                    <div style={{ gridColumn: '1/-1', textAlign: 'center', marginTop: '60px' }}>
                        <div style={{ color: '#4B5563', marginBottom: '12px' }}>
                            <svg style={{ width: '48px', height: '48px', margin: '0 auto' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                        </div>
                        <p style={{ color: '#6B7280', fontSize: '15px' }}>
                            Ingresa una referencia para buscar su ficha técnica.
                        </p>
                    </div>
                ) : filtered.length === 0 ? (
                    <div style={{ gridColumn: '1/-1', textAlign: 'center', marginTop: '60px' }}>
                        <p style={{ color: '#EF4444', fontSize: '15px' }}>
                            No se encontraron fichas para "{fichasSearch}".
                        </p>
                    </div>
                ) : (
                    <>
                        {filtered.length > 0 && (
                            <p style={{ gridColumn: '1/-1', color: '#6B7280', fontSize: '12px', marginBottom: '8px', paddingLeft: '8px' }}>
                                Mostrando {Math.min(filtered.length, 100)} de {filtered.length} resultados
                            </p>
                        )}
                        {filtered.slice(0, 100).map(({ filename }) => (
                            <FichaCard
                                key={filename}
                                filename={filename}
                                setSelectedImage={setSelectedImage}
                            />
                        ))
                        }
                    </>
                )}
            </div>
        </div>
    );
};

export default FichasGrid;
