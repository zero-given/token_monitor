import React from 'react';
import { PairInfo } from '../types';

interface PairListProps {
    pairs: PairInfo[];
    loading: boolean;
    selectedPair: PairInfo | null;
    onSelectPair: (pair: PairInfo) => void;
}

const PairList: React.FC<PairListProps> = ({ pairs, loading, selectedPair, onSelectPair }) => {
    if (loading) {
        return <div className="loading">Loading pairs...</div>;
    }

    if (pairs.length === 0) {
        return <div>No pairs found</div>;
    }

    return (
        <div className="pair-list-container">
            <div className="pairs-sidebar">
                <h2>Recent Pairs</h2>
                <div className="pair-list">
                    {pairs.map((pair) => (
                        <div 
                            key={pair.address} 
                            className={`pair-item ${selectedPair?.address === pair.address ? 'selected' : ''}`}
                            onClick={() => onSelectPair(pair)}
                        >
                            <div className="pair-item-header">
                                <h3>{pair.token0.symbol} / {pair.token1.symbol}</h3>
                                <span className="timestamp">{new Date(pair.timestamp).toLocaleString()}</span>
                            </div>
                            <div className="pair-item-security">
                                {(pair.securityChecks.token0.isHoneypot || pair.securityChecks.token1.isHoneypot) && 
                                    <span className="warning">⚠️ Honeypot</span>
                                }
                                {((pair.securityChecks.token0.buyTax ?? 0) > 10 || 
                                  (pair.securityChecks.token0.sellTax ?? 0) > 10 ||
                                  (pair.securityChecks.token1.buyTax ?? 0) > 10 || 
                                  (pair.securityChecks.token1.sellTax ?? 0) > 10) && 
                                    <span className="warning">💰 High Tax</span>
                                }
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="pair-details">
                {selectedPair ? (
                    <div className="pair-card detailed">
                        <div className="pair-header">
                            <h2>{selectedPair.token0.symbol} / {selectedPair.token1.symbol}</h2>
                            <span className="timestamp">{new Date(selectedPair.timestamp).toLocaleString()}</span>
                        </div>

                        <div className="token-details">
                            <div className="token">
                                <h3>{selectedPair.token0.name}</h3>
                                <div className="token-info-grid">
                                    <div className="info-item">
                                        <label>Symbol:</label>
                                        <span>{selectedPair.token0.symbol}</span>
                                    </div>
                                    <div className="info-item">
                                        <label>Decimals:</label>
                                        <span>{selectedPair.token0.decimals}</span>
                                    </div>
                                    <div className="info-item">
                                        <label>Security Status:</label>
                                        <span className={selectedPair.securityChecks.token0.isHoneypot ? 'danger' : 'safe'}>
                                            {selectedPair.securityChecks.token0.isHoneypot ? '⚠️ Honeypot' : '✅ Safe'}
                                        </span>
                                    </div>
                                    <div className="info-item">
                                        <label>Buy Tax:</label>
                                        <span>{selectedPair.securityChecks.token0.buyTax}%</span>
                                    </div>
                                    <div className="info-item">
                                        <label>Sell Tax:</label>
                                        <span>{selectedPair.securityChecks.token0.sellTax}%</span>
                                    </div>
                                    <div className="info-item">
                                        <label>Contract:</label>
                                        <a href={`https://etherscan.io/address/${selectedPair.token0.address}`} target="_blank" rel="noopener noreferrer">
                                            View on Etherscan
                                        </a>
                                    </div>
                                </div>
                            </div>

                            <div className="token">
                                <h3>{selectedPair.token1.name}</h3>
                                <div className="token-info-grid">
                                    <div className="info-item">
                                        <label>Symbol:</label>
                                        <span>{selectedPair.token1.symbol}</span>
                                    </div>
                                    <div className="info-item">
                                        <label>Decimals:</label>
                                        <span>{selectedPair.token1.decimals}</span>
                                    </div>
                                    <div className="info-item">
                                        <label>Security Status:</label>
                                        <span className={selectedPair.securityChecks.token1.isHoneypot ? 'danger' : 'safe'}>
                                            {selectedPair.securityChecks.token1.isHoneypot ? '⚠️ Honeypot' : '✅ Safe'}
                                        </span>
                                    </div>
                                    <div className="info-item">
                                        <label>Buy Tax:</label>
                                        <span>{selectedPair.securityChecks.token1.buyTax}%</span>
                                    </div>
                                    <div className="info-item">
                                        <label>Sell Tax:</label>
                                        <span>{selectedPair.securityChecks.token1.sellTax}%</span>
                                    </div>
                                    <div className="info-item">
                                        <label>Contract:</label>
                                        <a href={`https://etherscan.io/address/${selectedPair.token1.address}`} target="_blank" rel="noopener noreferrer">
                                            View on Etherscan
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="pair-footer">
                            <div className="info-item">
                                <label>Pair Contract:</label>
                                <a href={`https://etherscan.io/address/${selectedPair.address}`} target="_blank" rel="noopener noreferrer">
                                    View on Etherscan
                                </a>
                            </div>
                            <div className="info-item">
                                <label>Block Number:</label>
                                <span>{selectedPair.blockNumber}</span>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="no-selection">
                        <h3>Select a pair to view details</h3>
                        <p>Click on any pair from the list to see detailed information</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PairList; 