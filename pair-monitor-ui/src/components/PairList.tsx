import React from 'react';
import { PairInfo } from '../types';

interface PairListProps {
    pairs: PairInfo[];
    loading: boolean;
    onSelectPair: (pair: PairInfo) => void;
    selectedPairAddress?: string;
}

const PairList: React.FC<PairListProps> = ({ pairs, loading, onSelectPair, selectedPairAddress }) => {
    const formatAddress = (address: string) => {
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    };

    const renderPairCard = (pair: PairInfo) => {
        // Get the non-WETH token
        const token = pair.token0.symbol === 'WETH' ? pair.token1 : pair.token0;
        const tokenType = pair.token0.symbol === 'WETH' ? 'token1' : 'token0';
        const security = pair.securityChecks?.[tokenType];

        const statusIcons = security ? (
            <div className="status-icons">
                {!security.isHoneypot && <span className="success">✅</span>}
                {security.isOpenSource && <span className="success">📄</span>}
                {!security.canTakeOwnership && <span className="success">🔒</span>}
                {Number(security.holderCount) >= 50 && <span className="success">👥</span>}
            </div>
        ) : null;

        return (
            <div 
                key={pair.address}
                className={`pair-card ${selectedPairAddress === pair.address ? 'selected' : ''}`}
                onClick={() => onSelectPair(pair)}
            >
                <div className="pair-header">
                    <div className="pair-title">{token.name} ({token.symbol})</div>
                    <div className="pair-timestamp">{new Date(pair.timestamp).toLocaleString()}</div>
                </div>
                <div className="token-info">
                    {statusIcons}
                    <a 
                        href={`https://etherscan.io/address/${token.address}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {formatAddress(token.address)}
                    </a>
                </div>
            </div>
        );
    };

    if (loading) {
        return <div className="loading"></div>;
    }

    return (
        <div className="pair-list">
            {pairs.map(renderPairCard)}
        </div>
    );
};

export default PairList; 