export interface TokenInfo {
    address: string;
    name: string;
    symbol: string;
    decimals: number;
    totalSupply: string;
    ethBalance: string;
    isVerified: boolean;
}

export interface SecurityCheck {
    isHoneypot: boolean;
    honeypotReason: string | null;
    buyTax: number;
    sellTax: number;
    transferTax: number;
    isOpenSource: boolean;
    isProxy: boolean;
    canTakeOwnership: boolean;
    holderCount: number;
    ownerAddress: string;
    creatorAddress: string;
    potentialRisks: string[];
    apiErrors: string[];
    checkedAt: string;
}

export interface SecurityChecks {
    token0?: SecurityCheck;
    token1?: SecurityCheck;
}

export interface PairInfo {
    address: string;
    blockNumber: number;
    transactionHash: string;
    timestamp: string;
    token0: TokenInfo;
    token1: TokenInfo;
    securityChecks?: SecurityChecks;
} 