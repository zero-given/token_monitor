import React from 'react';
import { PairInfo } from '../types';

interface PairListProps {
    pairs: PairInfo[];
    loading: boolean;
}

const PairList: React.FC<PairListProps> = ({ pairs, loading }) => {
    if (loading) {
        return <div className="loading">Loading pairs...</div>;
    }

    if (pairs.length === 0) {
        return <div>No pairs found</div>;
    }

    return (
        <div className="pair-list">
            <h2>Recent Pairs</h2>
            <div className="pair-grid">
                {pairs.map((pair) => (
                    <div key={pair.address} className="pair-card">
                        <div className="pair-header">
                            <h3>{pair.token0.symbol} / {pair.token1.symbol}</h3>
                            <span className="timestamp">{new Date(pair.timestamp).toLocaleString()}</span>
                        </div>
                        <div className="token-info">
                            <div className="token">
                                <h4>{pair.token0.name}</h4>
                                <p>Symbol: {pair.token0.symbol}</p>
                                <p>Decimals: {pair.token0.decimals}</p>
                                <div className={`security-status ${pair.securityChecks.token0.isHoneypot ? 'danger' : 'safe'}`}>
                                    {pair.securityChecks.token0.isHoneypot ? '⚠️ Honeypot' : '✅ Safe'}
                                </div>
                                <div className="tax-info">
                                    <p>Buy Tax: {pair.securityChecks.token0.buyTax}%</p>
                                    <p>Sell Tax: {pair.securityChecks.token0.sellTax}%</p>
                                </div>
                            </div>
                            <div className="token">
                                <h4>{pair.token1.name}</h4>
                                <p>Symbol: {pair.token1.symbol}</p>
                                <p>Decimals: {pair.token1.decimals}</p>
                                <div className={`security-status ${pair.securityChecks.token1.isHoneypot ? 'danger' : 'safe'}`}>
                                    {pair.securityChecks.token1.isHoneypot ? '⚠️ Honeypot' : '✅ Safe'}
                                </div>
                                <div className="tax-info">
                                    <p>Buy Tax: {pair.securityChecks.token1.buyTax}%</p>
                                    <p>Sell Tax: {pair.securityChecks.token1.sellTax}%</p>
                                </div>
                            </div>
                        </div>
                        <div className="pair-footer">
                            <a href={`https://etherscan.io/address/${pair.address}`} target="_blank" rel="noopener noreferrer">
                                View Pair on Etherscan
                            </a>
                            <span className="block-number">Block: {pair.blockNumber}</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PairList; 