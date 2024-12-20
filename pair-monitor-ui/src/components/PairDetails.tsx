import React from 'react';
import { PairInfo } from '../types';

interface PairDetailsProps {
    pair: PairInfo;
}

const PairDetails: React.FC<PairDetailsProps> = ({ pair }) => {
    const formatAddress = (address: string) => {
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    };

    const renderSecurityInfo = (securityChecks: any, tokenType: 'token0' | 'token1') => {
        if (!securityChecks || !securityChecks[tokenType]) return null;
        const security = securityChecks[tokenType];

        return (
            <div className="security-info">
                <h4>Security Analysis</h4>
                <div className="security-grid">
                    <div className="security-item">
                        <span>Honeypot:</span>
                        <span className={security.isHoneypot ? 'danger' : 'success'}>
                            {security.isHoneypot ? '🚫 Yes' : '✅ No'}
                        </span>
                    </div>
                    {security.honeypotReason && (
                        <div className="security-item">
                            <span>Reason:</span>
                            <span className="danger">{security.honeypotReason}</span>
                        </div>
                    )}
                    <div className="security-item">
                        <span>Buy Tax:</span>
                        <span className={Number(security.buyTax) > 10 ? 'danger' : 'success'}>
                            {security.buyTax}%
                        </span>
                    </div>
                    <div className="security-item">
                        <span>Sell Tax:</span>
                        <span className={Number(security.sellTax) > 10 ? 'danger' : 'success'}>
                            {security.sellTax}%
                        </span>
                    </div>
                    <div className="security-item">
                        <span>Open Source:</span>
                        <span className={security.isOpenSource ? 'success' : 'danger'}>
                            {security.isOpenSource ? '✅ Yes' : '❌ No'}
                        </span>
                    </div>
                    <div className="security-item">
                        <span>Is Proxy:</span>
                        <span className={security.isProxy ? 'warning' : 'success'}>
                            {security.isProxy ? '⚠️ Yes' : '✅ No'}
                        </span>
                    </div>
                    <div className="security-item">
                        <span>Can Take Ownership:</span>
                        <span className={security.canTakeOwnership ? 'danger' : 'success'}>
                            {security.canTakeOwnership ? '🚫 Yes' : '✅ No'}
                        </span>
                    </div>
                    {security.holderCount && (
                        <div className="security-item">
                            <span>Holders:</span>
                            <span className={Number(security.holderCount) < 50 ? 'warning' : 'success'}>
                                {security.holderCount}
                            </span>
                        </div>
                    )}
                </div>
                {security.potentialRisks && security.potentialRisks.length > 0 && (
                    <div className="risks-section">
                        <h4>⚠️ Potential Risks</h4>
                        <ul>
                            {security.potentialRisks.map((risk: string, index: number) => (
                                <li key={index} className="danger">{risk}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        );
    };

    const renderTokenSection = (token: any, securityChecks: any, tokenType: 'token0' | 'token1') => {
        // Skip WETH token
        if (token.symbol === 'WETH') return null;

        const security = securityChecks?.[tokenType];
        const statusIcons = security ? (
            <div className="status-icons">
                {!security.isHoneypot && <span className="success">✅</span>}
                {security.isOpenSource && <span className="success">📄</span>}
                {!security.canTakeOwnership && <span className="success">🔒</span>}
                {Number(security.holderCount) >= 50 && <span className="success">👥</span>}
            </div>
        ) : null;

        return (
            <div className="token-section">
                <h4>{token.name} ({token.symbol})</h4>
                <div className="token-info">
                    <div className="info-row">
                        <span>Address:</span>
                        <div className="address-container">
                            {statusIcons}
                            <a 
                                href={`https://etherscan.io/address/${token.address}`}
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                {formatAddress(token.address)}
                            </a>
                        </div>
                    </div>
                    <div className="info-row">
                        <span>Decimals:</span>
                        <span>{token.decimals}</span>
                    </div>
                    {token.totalSupply && (
                        <div className="info-row">
                            <span>Total Supply:</span>
                            <span>{token.totalSupply}</span>
                        </div>
                    )}
                </div>
                {renderSecurityInfo(securityChecks, tokenType)}
            </div>
        );
    };

    return (
        <div className="pair-details">
            <div className="pair-header">
                <h3>Pair Details</h3>
                <div className="timestamp">Created: {new Date(pair.timestamp).toLocaleString()}</div>
            </div>
            
            <div className="token-details">
                {renderTokenSection(pair.token0, pair.securityChecks, 'token0')}
                {renderTokenSection(pair.token1, pair.securityChecks, 'token1')}
            </div>

            <div className="pair-footer">
                <a 
                    href={`https://etherscan.io/address/${pair.address}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="etherscan-link"
                >
                    View Pair on Etherscan
                </a>
            </div>
        </div>
    );
};

export default PairDetails; 