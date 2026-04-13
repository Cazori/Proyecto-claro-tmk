import React, { useState, useRef } from 'react';
import { chatService } from '../../services/api';

const SalesLookup = () => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const [searchError, setSearchError] = useState('');
    
    // Upload state
    const [file, setFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef(null);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query || query.trim().length < 3) return;
        
        setIsSearching(true);
        setSearchError('');
        
        try {
            const data = await chatService.searchSales(query);
            if (data.detail && data.status === 404) {
               setSearchError('La base de ventas no ha sido cargada.');
               setResults([]);
            } else {
               setResults(data);
               if (data.length === 0) setSearchError('No se encontraron ventas para este asesor.');
            }
        } catch (error) {
            setSearchError('Error de conexión o base de datos no cargada.');
            setResults([]);
        } finally {
            setIsSearching(false);
        }
    };

    const handleUploadClick = () => {
        fileInputRef.current.click();
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setFile(file);
            handleUploadFile(file);
        }
    };

    const handleUploadFile = async (uploadFile) => {
        setIsUploading(true);
        setUploadStatus('Subiendo archivo...');
        
        try {
            const response = await chatService.uploadSalesFile(uploadFile);
            if (response.error) {
                 setUploadStatus(response.detail || 'Error en la subida.');
            } else {
                 setUploadStatus(`¡Procesado! ${response.records} ventas.`);
            }
        } catch (error) {
            setUploadStatus('Error al subir el archivo.');
        } finally {
            setIsUploading(false);
            setFile(null);
        }
    };

    return (
        <div style={{ padding: '32px', background: 'transparent', minHeight: '100%', overflowY: 'auto' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '32px', maxWidth: '1000px', margin: '0 auto 32px auto' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
                    <div>
                        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'white', margin: '0 0 8px 0' }}>
                            Consulta de Ventas por Asesor
                        </h2>
                        <p style={{ color: '#9CA3AF', margin: 0, fontSize: '0.95rem' }}>
                            Busca todas las ventas asociadas a la cédula o nombre de un asesor.
                        </p>
                    </div>
                    
                    {/* Upload Section */}
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
                         <input 
                            type="file" 
                            ref={fileInputRef} 
                            style={{ display: 'none' }} 
                            accept=".csv, .xlsx, .xls"
                            onChange={handleFileChange}
                         />
                         <button 
                            onClick={handleUploadClick}
                            disabled={isUploading}
                            className="nav-btn"
                            style={{ 
                                background: 'rgba(31, 41, 55, 0.5)',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                padding: '10px 16px', 
                                borderRadius: '12px', 
                                color: '#D1D5DB',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                cursor: isUploading ? 'not-allowed' : 'pointer',
                                transition: 'all 0.2s'
                            }}
                            onMouseOver={(e) => { e.currentTarget.style.background = 'rgba(79, 70, 229, 0.2)'; e.currentTarget.style.borderColor = 'rgba(124, 58, 237, 0.4)'; e.currentTarget.style.color = '#fff' }}
                            onMouseOut={(e) => { e.currentTarget.style.background = 'rgba(31, 41, 55, 0.5)'; e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.1)'; e.currentTarget.style.color = '#D1D5DB' }}
                         >
                            <svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                            </svg>
                            {isUploading ? 'Subiendo...' : 'Actualizar Base'}
                         </button>
                         {uploadStatus && (
                            <span style={{ fontSize: '0.8rem', color: isUploading ? '#8B5CF6' : '#10B981', fontWeight: '500' }}>
                                {uploadStatus}
                            </span>
                         )}
                    </div>
                </div>

                {/* Search Bar */}
                <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px' }}>
                    <div className="input-wrapper" style={{ flex: 1, padding: '4px' }}>
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            className="chat-input"
                            placeholder="Ingresa la cédula o nombre del asesor..."
                            style={{ width: '100%' }}
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={isSearching || !query}
                        className="send-btn"
                        style={{
                            width: 'auto',
                            padding: '0 24px',
                            fontWeight: '600',
                            opacity: isSearching || !query ? 0.7 : 1,
                            borderRadius: '16px'
                        }}
                    >
                        {isSearching ? 'Buscando...' : 'Buscar'}
                    </button>
                </form>

                {/* Results block */}
                {searchError && (
                    <div style={{ padding: '16px', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: '#FCA5A5', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '12px' }}>
                        {searchError}
                    </div>
                )}

                {results.length > 0 && (
                    <div style={{ backgroundColor: 'rgba(17, 24, 39, 0.6)', borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.05)', overflow: 'hidden' }}>
                        <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', backgroundColor: 'rgba(0, 0, 0, 0.2)' }}>
                            <h3 style={{ margin: 0, fontSize: '1rem', color: '#E5E7EB', fontWeight: '600' }}>
                                Resultados: {results.length} ventas encontradas
                            </h3>
                        </div>
                        <div style={{ overflowX: 'auto' }} className="markdown-content">
                            <table style={{ margin: 0, background: 'transparent', border: 'none', borderRadius: 0 }}>
                                <thead>
                                    <tr>
                                        <th style={{ minWidth: '160px', whiteSpace: 'nowrap' }}>Documento Cliente</th>
                                        <th style={{ minWidth: '220px' }}>Nombre Cliente</th>
                                        <th style={{ minWidth: '120px', whiteSpace: 'nowrap' }}>Código</th>
                                        <th style={{ minWidth: '250px' }}>Producto</th>
                                        <th style={{ minWidth: '150px', whiteSpace: 'nowrap' }}>Estado Actual</th>
                                        <th style={{ minWidth: '140px', whiteSpace: 'nowrap' }}>Fecha Entrega</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {results.map((sale, index) => (
                                        <tr key={index}>
                                            <td style={{ color: '#F3F4F6', fontWeight: '500', whiteSpace: 'nowrap' }}>{sale.document}</td>
                                            <td>{sale.client}</td>
                                            <td style={{ color: '#A78BFA', fontWeight: '600', whiteSpace: 'nowrap' }}>{sale.code}</td>
                                            <td>{sale.product}</td>
                                            <td style={{ whiteSpace: 'nowrap' }}>
                                                <span style={{ 
                                                    padding: '4px 10px', 
                                                    borderRadius: '8px', 
                                                    fontSize: '0.75rem', 
                                                    fontWeight: '600',
                                                    letterSpacing: '0.5px',
                                                    backgroundColor: sale.status.includes('PROGRAMADA') ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                                                    color: sale.status.includes('PROGRAMADA') ? '#34D399' : '#FBBF24',
                                                    border: `1px solid ${sale.status.includes('PROGRAMADA') ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
                                                    display: 'inline-block'
                                                }}>
                                                    {sale.status || 'N/A'}
                                                </span>
                                            </td>
                                            <td style={{ color: '#D1D5DB', fontWeight: '500', whiteSpace: 'nowrap' }}>{sale.delivery_date}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SalesLookup;
