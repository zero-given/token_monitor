export interface TokenSecurityInfo {
    is_honeypot: boolean;
    honeypot_reason: string;
    buy_tax: number | null;
    sell_tax: number | null;
    is_open_source: boolean | null;
    holder_count: number;
    is_mintable: boolean;
    owner_address: string;
    creator_address: string;
    honeypot_details?: {
        simulationSuccess?: boolean;
        simulationError?: string;
        simulationResult?: {
            buyGas: string;
            sellGas: string;
            buyTax: number;
            sellTax: number;
            transferTax: number;
        };
        contractCode?: {
            openSource: boolean;
            isProxy: boolean;
            hasProxyCalls: boolean;
        };
    };
    goplus_details?: {
        code: number;
        message: string;
        result: {
            [key: string]: {
                anti_whale_modifiable: string;
                buy_tax: string;
                can_take_back_ownership: string;
                cannot_buy: string;
                creator_address: string;
                creator_balance: string;
                creator_percent: string;
                dex: Array<{
                    liquidity: string;
                    liquidity_type: string;
                    name: string;
                    pair: string;
                }>;
                holder_count: string;
                holders: Array<{
                    address: string;
                    balance: string;
                    is_contract: number;
                    is_locked: number;
                    percent: string;
                    tag: string;
                }>;
                is_anti_whale: string;
                is_blacklisted: string;
                is_honeypot: string;
                is_in_dex: string;
                is_mintable: string;
                is_open_source: string;
                is_proxy: string;
                is_whitelisted: string;
                lp_holder_count: string;
                lp_holders: Array<{
                    address: string;
                    balance: string;
                    is_contract: number;
                    is_locked: number;
                    percent: string;
                    tag: string;
                    value: string | null;
                    NFT_list: Array<{
                        NFT_id: string;
                        NFT_percentage: string;
                        amount: string;
                        in_effect: string;
                        value: string;
                    }> | null;
                }>;
                lp_total_supply: string;
                owner_address: string;
                owner_balance: string;
                owner_percent: string;
                token_name: string;
                token_symbol: string;
                total_supply: string;
            };
        };
    };
}

export interface Token {
    address: string;
    name: string;
    symbol: string;
    decimals: number;
    total_supply: string;
    eth_balance: string;
    verified: boolean;
    security_info: TokenSecurityInfo;
    buy_tax: number | null;
    sell_tax: number | null;
    creator_address: string;
    owner_address: string;
    holder_count: number;
    honeypot_reason: string;
}

export interface Pair {
    id: number;
    pair_address: string;
    block_number: number;
    transaction_hash: string;
    pair_name: string;
    pair_symbol: string;
    created_at: string;
    timestamp: string;
    
    token0_address: string;
    token0_name: string;
    token0_symbol: string;
    token0_decimals: number;
    token0_total_supply: string;
    token0_eth_balance: string;
    token0_verified: boolean;
    token0_security_info: TokenSecurityInfo;
    token0_buy_tax: number | null;
    token0_sell_tax: number | null;
    token0_creator_address: string;
    token0_owner_address: string;
    token0_holder_count: number;
    token0_honeypot_reason: string;
    
    token1_address: string;
    token1_name: string;
    token1_symbol: string;
    token1_decimals: number;
    token1_total_supply: string;
    token1_eth_balance: string;
    token1_verified: boolean;
    token1_security_info: TokenSecurityInfo;
    token1_buy_tax: number | null;
    token1_sell_tax: number | null;
    token1_creator_address: string;
    token1_owner_address: string;
    token1_holder_count: number;
    token1_honeypot_reason: string;
} 