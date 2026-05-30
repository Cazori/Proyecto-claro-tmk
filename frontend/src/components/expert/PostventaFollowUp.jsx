import React, { useState, useMemo } from 'react';
import * as XLSX from 'xlsx';

const PostventaFollowUp = () => {
    const [clients, setClients] = useState([]);
    const [loading, setLoading] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');
    
    // Filtros e inputs de búsqueda
    const [searchTerm, setSearchTerm] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [sortOrder, setSortOrder] = useState('asc'); // 'asc' = más antiguos primero, 'desc' = más recientes primero
    
    // Modal de mensaje personalizado
    const [activeClient, setActiveClient] = useState(null);
    const [customMessage, setCustomMessage] = useState('');
    const [copySuccess, setCopySuccess] = useState(false);

    // Mapear fechas seriales de Excel o strings a objetos Date de JS
    const parseExcelDate = (val) => {
        if (!val) return null;
        if (val instanceof Date) return val;
        
        // Si es un número (formato de fecha serializado de Excel)
        if (typeof val === 'number') {
            const date = new Date((val - 25569) * 86400 * 1000);
            // Ajustar el offset de la zona horaria para obtener la fecha correcta
            const tzOffset = date.getTimezoneOffset() * 60 * 1000;
            return new Date(date.getTime() + tzOffset);
        }
        
        // Si es un string con formato YYYY-MM-DD u otros
        const parsed = new Date(val);
        if (!isNaN(parsed.getTime())) {
            return parsed;
        }
        return null;
    };

    // Formatear fecha para mostrar de forma amigable (DD/MM/YYYY)
    const formatDate = (dateObj) => {
        if (!dateObj) return 'Sin fecha';
        const day = String(dateObj.getDate()).padStart(2, '0');
        const month = String(dateObj.getMonth() + 1).padStart(2, '0');
        const year = dateObj.getFullYear();
        return `${day}/${month}/${year}`;
    };

    // Manejar la carga del archivo Excel (.xlsx)
    const handleFileUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        setLoading(true);
        setErrorMsg('');
        const reader = new FileReader();

        reader.onload = (evt) => {
            try {
                const data = evt.target.result;
                const workbook = XLSX.read(data, { type: 'binary', cellDates: false });
                const firstSheetName = workbook.SheetNames[0];
                const worksheet = workbook.Sheets[firstSheetName];
                const rawJson = XLSX.utils.sheet_to_json(worksheet, { defval: '' });

                if (rawJson.length === 0) {
                    throw new Error("El archivo Excel está vacío.");
                }

                // Identificar columnas relevantes dinámicamente
                const headers = Object.keys(rawJson[0]);
                
                const clientCol = headers.find(h => /cliente|nombre/i.test(h));
                const dateCol = headers.find(h => /fecha/i.test(h));
                const codeCol = headers.find(h => /código|codigo|cust_code|radicado|id|cedula|cédula/i.test(h));
                const prodCol = headers.find(h => /producto|descripcion|descripción|equipo/i.test(h));
                const phoneCol = headers.find(h => /teléfono|telefono|celular|contacto|móvil|movil|phone/i.test(h));
                const statusCol = headers.find(h => /estado/i.test(h));

                if (!clientCol || !dateCol) {
                    throw new Error("No se encontraron las columnas requeridas (por ejemplo, 'NOMBRE Y APELLIDO' y 'FECHA').");
                }

                const parsedRecords = rawJson.map((row, idx) => {
                    const dateVal = parseExcelDate(row[dateCol]);
                    return {
                        id: idx,
                        code: row[codeCol] ? String(row[codeCol]).trim() : 'N/A',
                        name: String(row[clientCol]).trim(),
                        date: dateVal,
                        product: prodCol && row[prodCol] ? String(row[prodCol]).trim() : 'Computador',
                        phone: phoneCol && row[phoneCol] ? String(row[phoneCol]).replace(/[^\d+]/g, '') : '',
                        status: statusCol && row[statusCol] ? String(row[statusCol]).trim() : 'N/A',
                        contacted: false
                    };
                }).filter(record => record.name && record.name.trim() !== '' && record.name.trim().toLowerCase() !== 'undefined'); // Filtrar filas sin nombre

                setClients(parsedRecords);
                setLoading(false);
            } catch (err) {
                console.error(err);
                setErrorMsg(err.message || 'Error al procesar el archivo Excel. Verifica el formato.');
                setLoading(false);
            }
        };

        reader.onerror = () => {
            setErrorMsg('Error al leer el archivo físico.');
            setLoading(false);
        };

        reader.readAsBinaryString(file);
    };

    // Generar el mensaje personalizado
    const handleGenerateMessage = (client) => {
        // Limpiar el nombre para quitar espacios adicionales
        const cleanName = client.name
            .toLowerCase()
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');

        const baseMessage = `Hola ${cleanName} 👋\n\nTe habla Juan Camacho, asesor de tecnología de Claro.\n\nQuería saludarte y preguntarte cómo te ha ido con el computador que adquiriste con nosotros. ¿Todo funcionando correctamente? 💻\n\nTe escribo porque estamos realizando un seguimiento preventivo a algunos clientes y quisiera validar algo contigo.`;

        // Marcar cliente como contactado
        setClients(prev => prev.map(c => c.id === client.id ? { ...c, contacted: true } : c));

        setActiveClient(client);
        setCustomMessage(baseMessage);
        setCopySuccess(false);
    };

    // Copiar el mensaje al portapapeles
    const handleCopy = () => {
        navigator.clipboard.writeText(customMessage)
            .then(() => {
                setCopySuccess(true);
                setTimeout(() => setCopySuccess(false), 2000);
            })
            .catch(() => alert('Error al copiar el mensaje. Por favor, selecciónalo manualmente.'));
    };

    // Abrir WhatsApp con el mensaje personalizado
    const handleOpenWhatsApp = () => {
        const textEncoded = encodeURIComponent(customMessage);
        let url = '';
        if (activeClient && activeClient.phone) {
            // Abrir chat directo si tenemos el número de teléfono
            url = `https://api.whatsapp.com/send?phone=${activeClient.phone}&text=${textEncoded}`;
        } else {
            // Abrir listado general para seleccionar destinatario en WhatsApp
            url = `https://api.whatsapp.com/send?text=${textEncoded}`;
        }
        window.open(url, '_blank');
    };

    // Determinar si una venta es antigua (más de 90 días atrás)
    const isPriorityClient = (date) => {
        if (!date) return false;
        const diffTime = Math.abs(new Date() - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays > 90;
    };

    // Filtrar, buscar y ordenar registros de clientes reactivamente
    const filteredClients = useMemo(() => {
        const filtered = clients.filter(c => {
            const matchesSearch = c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                c.product.toLowerCase().includes(searchTerm.toLowerCase()) ||
                c.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
                c.phone.toLowerCase().includes(searchTerm.toLowerCase()) ||
                (c.status && c.status.toLowerCase().includes(searchTerm.toLowerCase()));

            let matchesStartDate = true;
            let matchesEndDate = true;

            if (startDate && c.date) {
                const sDate = new Date(startDate);
                sDate.setHours(0, 0, 0, 0);
                matchesStartDate = c.date.getTime() >= sDate.getTime();
            }
            if (endDate && c.date) {
                const eDate = new Date(endDate);
                eDate.setHours(23, 59, 59, 999);
                matchesEndDate = c.date.getTime() <= eDate.getTime();
            }

            return matchesSearch && matchesStartDate && matchesEndDate;
        });

        // Ordenar según sortOrder
        return [...filtered].sort((a, b) => {
            if (!a.date) return 1;
            if (!b.date) return -1;
            const diff = a.date.getTime() - b.date.getTime();
            return sortOrder === 'asc' ? diff : -diff;
        });
    }, [clients, searchTerm, startDate, endDate, sortOrder]);

    // Estadísticas
    const stats = useMemo(() => {
        const total = clients.length;
        const filtered = filteredClients.length;
        const priority = clients.filter(c => isPriorityClient(c.date)).length;
        return { total, filtered, priority };
    }, [clients, filteredClients]);

    return (
        <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
            
            {/* Header / Uploader Box */}
            <div style={{ background: '#111827', padding: '24px', borderRadius: '20px', border: '1px solid rgba(124, 58, 237, 0.2)', marginBottom: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
                    <div>
                        <h3 style={{ fontSize: '18px', fontWeight: 'bold', margin: 0, color: '#A78BFA' }}>📈 Postventa de Computadores</h3>
                        <p style={{ fontSize: '13px', color: '#9CA3AF', marginTop: '4px', marginBottom: 0 }}>Carga el reporte de ventas para generar mensajes de seguimiento y soporte de Office/Antivirus.</p>
                    </div>
                    <div>
                        <input
                            type="file"
                            accept=".xlsx"
                            id="postventa-excel-file"
                            onChange={handleFileUpload}
                            style={{ display: 'none' }}
                        />
                        <label
                            htmlFor="postventa-excel-file"
                            style={{
                                display: 'inline-block',
                                background: 'linear-gradient(135deg, #7C3AED, #5B21B6)',
                                padding: '10px 20px',
                                borderRadius: '10px',
                                color: 'white',
                                fontWeight: '600',
                                cursor: 'pointer',
                                transition: 'opacity 0.2s'
                            }}
                        >
                            📁 Cargar Reporte Ventas (.xlsx)
                        </label>
                    </div>
                </div>

                {errorMsg && (
                    <p style={{ color: '#EF4444', fontSize: '13px', marginTop: '12px', marginBottom: 0 }}>
                        ⚠️ {errorMsg}
                    </p>
                )}

                {loading && (
                    <p style={{ color: '#A78BFA', fontSize: '13px', marginTop: '12px', marginBottom: 0 }}>
                        🔄 Procesando y ordenando clientes de forma cronológica...
                    </p>
                )}
            </div>

            {/* Content Section (Only shown if excel data is loaded) */}
            {clients.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    
                    {/* Counters Widget */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                        <div style={{ background: '#111827', padding: '16px 20px', borderRadius: '15px', border: '1px solid rgba(255,255,255,0.05)' }}>
                            <div style={{ fontSize: '12px', color: '#9CA3AF' }}>Total Cargados</div>
                            <div style={{ fontSize: '28px', fontWeight: '800', color: 'white', marginTop: '4px' }}>{stats.total}</div>
                        </div>
                        <div style={{ background: '#111827', padding: '16px 20px', borderRadius: '15px', border: '1px solid rgba(255,255,255,0.05)' }}>
                            <div style={{ fontSize: '12px', color: '#9CA3AF' }}>Filtrados</div>
                            <div style={{ fontSize: '28px', fontWeight: '800', color: '#A78BFA', marginTop: '4px' }}>{stats.filtered}</div>
                        </div>
                        <div style={{ background: '#111827', padding: '16px 20px', borderRadius: '15px', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
                            <div style={{ fontSize: '12px', color: '#FCD34D' }}>⚠️ Prioridad (+90 días)</div>
                            <div style={{ fontSize: '28px', fontWeight: '800', color: '#FBBF24', marginTop: '4px' }}>{stats.priority}</div>
                        </div>
                    </div>

                    {/* Filter Bar */}
                    <div style={{ background: '#111827', padding: '20px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.05)', display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
                        <div style={{ flex: 2, minWidth: '220px' }}>
                            <label style={{ display: 'block', fontSize: '12px', color: '#9CA3AF', marginBottom: '6px' }}>Buscar por Nombre, Equipo, Cédula, Celular o Estado:</label>
                            <input
                                type="text"
                                placeholder="Escribe para buscar..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white', outline: 'none', boxSizing: 'border-box' }}
                            />
                        </div>
                        <div style={{ flex: 1, minWidth: '150px' }}>
                            <label style={{ display: 'block', fontSize: '12px', color: '#9CA3AF', marginBottom: '6px' }}>Desde:</label>
                            <input
                                type="date"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white', outline: 'none', boxSizing: 'border-box' }}
                            />
                        </div>
                        <div style={{ flex: 1, minWidth: '150px' }}>
                            <label style={{ display: 'block', fontSize: '12px', color: '#9CA3AF', marginBottom: '6px' }}>Hasta:</label>
                            <input
                                type="date"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                                style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white', outline: 'none', boxSizing: 'border-box' }}
                            />
                        </div>
                        <div style={{ flex: 1, minWidth: '150px' }}>
                            <label style={{ display: 'block', fontSize: '12px', color: '#9CA3AF', marginBottom: '6px' }}>Orden por Fecha:</label>
                            <select
                                value={sortOrder}
                                onChange={(e) => setSortOrder(e.target.value)}
                                style={{ width: '100%', background: '#1F2937', border: '1px solid rgba(255,255,255,0.1)', padding: '10px', borderRadius: '8px', color: 'white', outline: 'none', boxSizing: 'border-box', cursor: 'pointer' }}
                            >
                                <option value="asc">Más antiguos primero</option>
                                <option value="desc">Más recientes primero</option>
                            </select>
                        </div>
                        {(searchTerm || startDate || endDate) && (
                            <button
                                onClick={() => { setSearchTerm(''); setStartDate(''); setEndDate(''); }}
                                style={{ marginTop: '20px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '10px 16px', borderRadius: '8px', color: '#F87171', fontWeight: '600', cursor: 'pointer' }}
                            >
                                Limpiar
                            </button>
                        )}
                    </div>

                    {/* Cards Container (replaces table for responsive view) */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
                        {filteredClients.map((client) => {
                            const isPriority = isPriorityClient(client.date);
                            return (
                                <div
                                    key={client.id}
                                    style={{
                                        background: '#111827',
                                        borderRadius: '16px',
                                        border: '1px solid rgba(255, 255, 255, 0.05)',
                                        padding: '20px',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        justifyContent: 'space-between',
                                        gap: '12px',
                                        transition: 'all 0.2s ease',
                                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                                    }}
                                >
                                    <div>
                                        {/* Card Header: Client Name & Badges */}
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px', marginBottom: '8px' }}>
                                            <h4 style={{ margin: 0, fontSize: '16px', fontWeight: '700', color: 'white', wordBreak: 'break-word' }}>
                                                {client.name}
                                            </h4>
                                            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px', flexShrink: 0 }}>
                                                {client.contacted ? (
                                                    <span style={{
                                                        background: 'rgba(16, 185, 129, 0.1)',
                                                        border: '1px solid rgba(16, 185, 129, 0.3)',
                                                        color: '#10B981',
                                                        fontSize: '10px',
                                                        padding: '2px 8px',
                                                        borderRadius: '12px',
                                                        fontWeight: 'bold',
                                                        whiteSpace: 'nowrap'
                                                    }}>
                                                        ✓ Contactado
                                                    </span>
                                                ) : (
                                                    <span style={{
                                                        background: 'rgba(156, 163, 175, 0.05)',
                                                        border: '1px solid rgba(156, 163, 175, 0.2)',
                                                        color: '#9CA3AF',
                                                        fontSize: '10px',
                                                        padding: '2px 8px',
                                                        borderRadius: '12px',
                                                        fontWeight: 'bold',
                                                        whiteSpace: 'nowrap'
                                                    }}>
                                                        Pendiente
                                                    </span>
                                                )}
                                                {isPriority && (
                                                    <span style={{
                                                        background: 'rgba(245, 158, 11, 0.1)',
                                                        border: '1px solid rgba(245, 158, 11, 0.3)',
                                                        color: '#FBBF24',
                                                        fontSize: '10px',
                                                        padding: '2px 8px',
                                                        borderRadius: '12px',
                                                        fontWeight: 'bold',
                                                        whiteSpace: 'nowrap'
                                                    }}>
                                                        Prioridad
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Card Info Fields */}
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px', color: '#9CA3AF' }}>
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <span>Fecha Venta:</span>
                                                <strong style={{ color: '#D1D5DB' }}>{formatDate(client.date)}</strong>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <span>Cédula:</span>
                                                <strong style={{ color: '#D1D5DB', fontFamily: 'monospace' }}>{client.code}</strong>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                                <span>Celular:</span>
                                                <strong style={{ color: '#D1D5DB', fontFamily: 'monospace' }}>{client.phone || 'N/A'}</strong>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
                                                <span>Equipo:</span>
                                                <strong style={{ color: '#E5E7EB', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '180px' }} title={client.product}>
                                                    {client.product}
                                                </strong>
                                            </div>
                                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                <span>Estado:</span>
                                                <span style={{
                                                    background: client.status.toLowerCase() === 'activo' || client.status.toLowerCase() === 'entregado' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(156, 163, 175, 0.1)',
                                                    color: client.status.toLowerCase() === 'activo' || client.status.toLowerCase() === 'entregado' ? '#10B981' : '#9CA3AF',
                                                    padding: '2px 8px',
                                                    borderRadius: '6px',
                                                    fontSize: '11px',
                                                    fontWeight: 'bold',
                                                    textTransform: 'uppercase'
                                                }}>
                                                    {client.status}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Action Button */}
                                    <div style={{ marginTop: '8px' }}>
                                        <button
                                            onClick={() => handleGenerateMessage(client)}
                                            style={{
                                                width: '100%',
                                                background: 'rgba(167, 139, 250, 0.1)',
                                                border: '1px solid rgba(167, 139, 250, 0.3)',
                                                color: '#C4B5FD',
                                                padding: '10px',
                                                borderRadius: '8px',
                                                fontWeight: '600',
                                                fontSize: '13px',
                                                cursor: 'pointer',
                                                transition: 'all 0.2s'
                                            }}
                                        >
                                            💬 Generar mensaje
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {filteredClients.length === 0 && (
                        <div style={{ background: '#111827', padding: '40px', textAlign: 'center', color: '#9CA3AF', borderRadius: '16px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
                            Ningún cliente coincide con los filtros establecidos.
                        </div>
                    )}
                </div>
            )}

            {/* Modal for dynamic message view */}
            {activeClient && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0,0,0,0.7)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000,
                    padding: '20px'
                }}>
                    <div style={{
                        background: '#111827',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '20px',
                        maxWidth: '600px',
                        width: '100%',
                        padding: '24px',
                        color: 'white',
                        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
                    }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                            <h4 style={{ fontSize: '18px', fontWeight: 'bold', margin: 0, color: '#A78BFA' }}>
                                Mensaje de Seguimiento
                            </h4>
                            <button
                                onClick={() => setActiveClient(null)}
                                style={{ background: 'none', border: 'none', color: '#9CA3AF', fontSize: '20px', cursor: 'pointer' }}
                            >
                                ✕
                            </button>
                        </div>

                        <p style={{ fontSize: '13px', color: '#9CA3AF', marginBottom: '12px' }}>
                            Destinatario: <strong style={{ color: 'white' }}>{activeClient.name}</strong> ({activeClient.product})
                        </p>

                        <div style={{
                            background: '#1F2937',
                            border: '1px solid rgba(255,255,255,0.05)',
                            padding: '16px',
                            borderRadius: '12px',
                            fontSize: '14px',
                            lineHeight: '1.6',
                            maxHeight: '280px',
                            overflowY: 'auto',
                            whiteSpace: 'pre-wrap',
                            marginBottom: '20px',
                            color: '#E5E7EB'
                        }}>
                            {customMessage}
                        </div>

                        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                            <button
                                onClick={handleCopy}
                                style={{
                                    flex: 1,
                                    background: copySuccess ? '#10B981' : 'rgba(255,255,255,0.05)',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    padding: '12px',
                                    borderRadius: '10px',
                                    color: 'white',
                                    fontWeight: '600',
                                    cursor: 'pointer',
                                    transition: 'background 0.2s',
                                    minWidth: '140px'
                                }}
                            >
                                {copySuccess ? '✓ ¡Copiado!' : '📋 Copiar mensaje'}
                            </button>
                            <button
                                onClick={handleOpenWhatsApp}
                                style={{
                                    flex: 1,
                                    background: 'linear-gradient(135deg, #10B981, #059669)',
                                    border: 'none',
                                    padding: '12px',
                                    borderRadius: '10px',
                                    color: 'white',
                                    fontWeight: '700',
                                    cursor: 'pointer',
                                    transition: 'opacity 0.2s',
                                    minWidth: '140px'
                                }}
                            >
                                💬 Enviar por WhatsApp
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PostventaFollowUp;
