import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ProductCard from './ProductCard';
import { parseMarkdownTable } from '../../services/parser';

const MessageBubble = ({ msg, specsList = [], specsMapping = {}, onViewSpec }) => {
    const parsedData = msg.sender === 'bot' && !msg.loading ? parseMarkdownTable(msg.text) : null;

    const checkHasSpec = (materialId, modelName) => {
        // Priority 1: Backend mapping
        if (specsMapping[materialId]) return true;

        // Priority 2: Keyword fallback
        if (!modelName || !specsList) return false;
        const keywords = modelName.toLowerCase().split(/\s+/).filter(k => k.length > 2);
        if (keywords.length === 0) return false;
        return specsList.some(filename => {
            const f = filename.toLowerCase();
            return keywords.every(k => f.includes(k));
        });
    };

    return (
        <div className={`message-row ${msg.sender}`}>
            <div className="msg-avatar">
                {msg.sender === 'bot' ? (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                    </svg>
                ) : 'Yo'}
            </div>
            <div className="bubble-wrapper">
                <div className="msg-bubble">
                    {msg.sender === 'bot' && !msg.loading ? (
                        parsedData ? (
                            <>
                                {parsedData.beforeTable && (
                                    <div className="markdown-content">
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{parsedData.beforeTable}</ReactMarkdown>
                                    </div>
                                )}
                                <div className="product-cards-container" style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px' }}>
                                    {parsedData.products.map((product, idx) => (
                                        <ProductCard
                                            key={idx}
                                            product={{
                                                ...product,
                                                CantDisponible: parseInt(String(product.CantDisponible || 0).replace(/[^\d]/g, '')),
                                                "Precio Contado": parseFloat(String(product['Precio Contado'] || 0).replace(/[^\d]/g, '')),
                                                hasSpec: checkHasSpec(product.Material, product.Subproducto)
                                            }}
                                            onViewSpec={onViewSpec}
                                        />
                                    ))}
                                </div>
                                {parsedData.afterTable && (
                                    <div className="markdown-content" style={{ marginTop: '10px' }}>
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{parsedData.afterTable}</ReactMarkdown>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="markdown-content">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {msg.text}
                                </ReactMarkdown>
                            </div>
                        )
                    ) : (
                        msg.text
                    )}
                </div>
                <span className="timestamp">
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
            </div>
        </div>
    );
};

export default MessageBubble;
