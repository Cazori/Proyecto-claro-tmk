import React from 'react';

const Dashboard = ({ stats }) => {
    return (
        <div style={{ color: 'white', padding: '20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '20px' }}>
                <div style={{ background: '#111827', padding: '20px', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <h3 style={{ color: '#9CA3AF', fontSize: '14px', marginBottom: '10px' }}>Última Actualización</h3>
                    <p style={{ fontSize: '24px', fontWeight: 'bold', color: 'white' }}>{stats.lastUpdate}</p>
                </div>
                <div style={{ background: '#111827', padding: '20px', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <h3 style={{ color: '#9CA3AF', fontSize: '14px', marginBottom: '10px' }}>Total Productos</h3>
                    <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#A78BFA' }}>{stats.totalItems}</p>
                </div>
                <div style={{ background: '#111827', padding: '20px', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <h3 style={{ color: '#9CA3AF', fontSize: '14px', marginBottom: '10px' }}>Stock Crítico</h3>
                    <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#EF4444' }}>{stats.criticalStock}</p>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
