import React, { useState, useEffect, useMemo } from 'react';
import MessageBubble from './MessageBubble';
import useFuzzySearch from '../../hooks/useFuzzySearch';

const ChatArea = ({ messages, chatEndRef, input, setInput, handleSend, specsList, specsMapping, onViewSpec }) => {
    const [suggestion, setSuggestion] = useState(null);

    const dictionary = useMemo(() => {
        const brands = ['Samsung', 'Apple', 'Motorola', 'Huawei', 'TCL', 'Panasonic', 'HP', 'Lenovo', 'Asus', 'Acer', 'Honor', 'Xiaomi'];
        const categories = ['TV', 'Smart TV', 'Celular', 'Laptop', 'Portátil', 'Reloj', 'Smartwatch', 'Audífonos', 'Parlante', 'Patineta', 'Tablet'];
        const fromSpecs = (specsList || []).map(f => f.split('(')[0].replace(/\.[^/.]+$/, "").trim());
        return Array.from(new Set([...brands, ...categories, ...fromSpecs]));
    }, [specsList]);

    const { search } = useFuzzySearch(dictionary, {
        threshold: 0.3,
        distance: 10
    });

    useEffect(() => {
        const lastWord = input.split(/\s+/).pop();
        if (lastWord && lastWord.length >= 3) {
            const results = search(lastWord);
            if (results.length > 0 && results[0].toLowerCase() !== lastWord.toLowerCase()) {
                setSuggestion(results[0]);
            } else {
                setSuggestion(null);
            }
        } else {
            setSuggestion(null);
        }
    }, [input, search]);

    const applySuggestion = () => {
        const words = input.split(/\s+/);
        words[words.length - 1] = suggestion;
        setInput(words.join(' ') + ' ');
        setSuggestion(null);
    };

    return (
        <>
            <div className="chat-area">
                <div className="messages-wrapper">
                    {messages.map((msg) => (
                        <MessageBubble
                            key={msg.id}
                            msg={msg}
                            specsList={specsList}
                            specsMapping={specsMapping}
                            onViewSpec={onViewSpec}
                        />
                    ))}
                    <div ref={chatEndRef} />
                </div>
            </div>
            <footer className="chat-footer">
                {suggestion && (
                    <div className="fuzzy-suggestion" style={{
                        padding: '8px 16px',
                        background: 'rgba(124, 58, 237, 0.1)',
                        borderTop: '1px solid rgba(124, 58, 237, 0.2)',
                        fontSize: '12px',
                        color: '#C4B5FD',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}>
                        <span>¿Quisiste decir: </span>
                        <button
                            onClick={applySuggestion}
                            style={{
                                background: 'rgba(124, 58, 237, 0.2)',
                                border: '1px solid rgba(124, 58, 237, 0.4)',
                                color: 'white',
                                padding: '2px 8px',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontWeight: 'bold'
                            }}
                        >
                            {suggestion}
                        </button>
                        <span>?</span>
                    </div>
                )}
                <div className="input-wrapper">
                    <input
                        type="text"
                        className="chat-input"
                        placeholder={isBotLoading ? "Cleo está pensando..." : "Escribe tu consulta..."}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && !isBotLoading && handleSend()}
                    />
                    <button
                        className="send-btn"
                        onClick={handleSend}
                        disabled={isBotLoading}
                        style={{ opacity: isBotLoading ? 0.5 : 1, cursor: isBotLoading ? 'not-allowed' : 'pointer' }}
                    >
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 12h14M12 5l7 7-7 7" />
                        </svg>
                    </button>
                </div>
            </footer>
        </>
    );
};

export default ChatArea;
