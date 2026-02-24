import React from 'react';

const CleoAvatar = ({ isProcessing = false }) => {
    return (
        <div className={`cleo-avatar-container ${isProcessing ? 'processing' : ''}`}>
            <div className="avatar-sphere">
                <div className="sphere-ring ring-1"></div>
                <div className="sphere-ring ring-2"></div>
                <div className="sphere-ring ring-3"></div>
                <div className="sphere-core"></div>
            </div>
        </div>
    );
};

export default CleoAvatar;
