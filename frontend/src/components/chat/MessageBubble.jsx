import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import ProductCard from './ProductCard';
import CleoAvatar from './CleoAvatar';
import { parseMarkdownTable } from '../../services/parser';

const MessageBubble = React.forwardRef(({ msg, specsList = [], specsMapping = {}, quotasMapping = {}, onViewSpec }, ref) => {
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
        <div ref={ref} className={`message-row ${msg.sender}`}>
            <div className="msg-avatar">
                {msg.sender === 'bot' ? (
                    <CleoAvatar isProcessing={msg.loading} />
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
                                    {parsedData.products.map((product, idx) => {
                                        if (!product || !product.Material) return null;
                                        return (
                                            <ProductCard
                                                key={idx}
                                                product={{
                                                    ...product,
                                                    CantDisponible: parseInt(String(product.CantDisponible || 0).replace(/[^\d]/g, '')) || 0,
                                                    "Precio Contado": parseFloat(String(product['Precio Contado'] || 0).replace(/[^\d]/g, '')) || 0,
                                                    hasSpec: checkHasSpec(product.Material, product.Subproducto),
                                                    quotas: (() => {
                                                        const rawId = String(product.Material || '');
                                                        const cleanId = rawId.replace(/[^\d]/g, '');
                                                        if (!cleanId) return null;
                                                        const result = quotasMapping[cleanId] || quotasMapping[rawId.trim()];
                                                        return result;
                                                    })()
                                                }}
                                                specsMapping={specsMapping}
                                                onViewSpec={onViewSpec}
                                            />
                                        );
                                    })}
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
});

export default MessageBubble;
