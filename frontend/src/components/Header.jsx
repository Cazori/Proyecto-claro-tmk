import React from 'react';

const Header = ({ activeTab, setSidebarOpen, isSidebarOpen }) => {
    const getTitle = () => {
        switch (activeTab) {
            case 'chat': return 'Asistente de Inventario';
            case 'dashboard': return 'Estadísticas Generales';
            case 'upload': return 'Cargar Inventario';
            case 'fichas': return 'Fichas Técnicas';
            case 'expert': return 'Fichas Técnicas Expertas';
            default: return 'Cleo AI';
        }
    };

    return (
        <header className="top-bar">
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <button className="toggle-btn" onClick={() => setSidebarOpen(!isSidebarOpen)}>
                    <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 6h16M4 12h16M4 18h16" /></svg>
                </button>
                <h2 style={{ fontSize: '16px', fontWeight: '600' }}>
                    {getTitle()}
                </h2>
            </div>
            <div className="avatar-circle">U</div>
        </header>
    );
};

export default Header;
