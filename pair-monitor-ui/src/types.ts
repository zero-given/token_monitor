export interface TokenInfo {
    address: string;
    name: string;
    symbol: string;
    decimals: number;
    totalSupply?: string;
    ethBalance: string;
    isVerified: boolean;
}

export interface SecurityCheck {
    isHoneypot: boolean;
    honeypotReason?: string;
    buyTax: number;
    sellTax: number;
    transferTax: number;
    isOpenSource: boolean;
    isProxy: boolean;
    canTakeOwnership: boolean;
    isMintable: boolean;
    canTakeBackOwnership: boolean;
    ownerAddress: string;
    creatorAddress: string;
    holderCount: number;
    potentialRisks: string[];
    apiErrors: string[];
    checkedAt: string;
}

export interface PairInfo {
    address: string;
    blockNumber: number;
    transactionHash: string;
    timestamp: number;
    token0: TokenInfo;
    token1: TokenInfo;
    securityChecks: {
        token0: SecurityCheck;
        token1: SecurityCheck;
    };
} 