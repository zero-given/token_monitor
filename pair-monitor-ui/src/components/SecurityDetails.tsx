import React from 'react';
import { SecurityCheck } from '../types';

interface SecurityDetailsProps {
    security: SecurityCheck;
    tokenAddress: string;
}

const SecurityDetails: React.FC<SecurityDetailsProps> = ({ security, tokenAddress }) => {
    return (
        <div className="security-details">
            <h3>Security Analysis</h3>
            
            <div className="security-grid">
                <div className="security-section">
                    <h4>Honeypot Check</h4>
                    <div className={`status ${security.isHoneypot ? 'danger' : 'safe'}`}>
                        {security.isHoneypot ? '⚠️ HONEYPOT DETECTED' : '✅ NOT A HONEYPOT'}
                    </div>
                    {security.honeypotReason && (
                        <div className="reason">
                            Reason: {security.honeypotReason}
                        </div>
                    )}
                </div>

                <div className="security-section">
                    <h4>Tax Information</h4>
                    <div className="tax-grid">
                        <div className={`tax ${security.buyTax > 10 ? 'high' : 'normal'}`}>
                            Buy Tax: {security.buyTax}%
                        </div>
                        <div className={`tax ${security.sellTax > 10 ? 'high' : 'normal'}`}>
                            Sell Tax: {security.sellTax}%
                        </div>
                        <div className={`tax ${security.transferTax > 0 ? 'warning' : 'normal'}`}>
                            Transfer Tax: {security.transferTax}%
                        </div>
                    </div>
                </div>

                <div className="security-section">
                    <h4>Contract Analysis</h4>
                    <div className="contract-grid">
                        <div className={`status ${security.isOpenSource ? 'safe' : 'warning'}`}>
                            {security.isOpenSource ? '✅ Open Source' : '⚠️ Not Open Source'}
                        </div>
                        <div className={`status ${security.isProxy ? 'warning' : 'safe'}`}>
                            {security.isProxy ? '⚠️ Proxy Contract' : '✅ Regular Contract'}
                        </div>
                        <div className={`status ${security.canTakeOwnership ? 'danger' : 'safe'}`}>
                            {security.canTakeOwnership ? '🚨 Can Take Ownership' : '✅ No Ownership Issues'}
                        </div>
                    </div>
                </div>

                <div className="security-section">
                    <h4>Holder Information</h4>
                    <div className="holder-info">
                        <p>Total Holders: {security.holderCount}</p>
                        <p className="address">Owner: {security.ownerAddress || 'Unknown'}</p>
                        <p className="address">Creator: {security.creatorAddress || 'Unknown'}</p>
                    </div>
                </div>

                {security.potentialRisks?.length > 0 && (
                    <div className="security-section risks">
                        <h4>⚠️ Potential Risks</h4>
                        <ul>
                            {security.potentialRisks.map((risk: string, index: number) => (
                                <li key={index}>{risk}</li>
                            ))}
                        </ul>
                    </div>
                )}

                {security.apiErrors?.length > 0 && (
                    <div className="security-section errors">
                        <h4>API Errors</h4>
                        <ul>
                            {security.apiErrors.map((error: string, index: number) => (
                                <li key={index}>{error}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>

            <div className="links">
                <a href={`https://etherscan.io/address/${tokenAddress}`} target="_blank" rel="noopener noreferrer">
                    View on Etherscan
                </a>
                <span className="timestamp">
                    Last checked: {security.checkedAt ? new Date(security.checkedAt).toLocaleString() : 'Unknown'}
                </span>
            </div>
        </div>
    );
};

export default SecurityDetails; 