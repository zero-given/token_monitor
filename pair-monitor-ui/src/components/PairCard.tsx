import React from 'react';
import { Pair, TokenSecurityInfo } from '../types';
import { formatDistanceToNow } from 'date-fns';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Link,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  Tooltip,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';

interface PairCardProps {
  pair: Pair;
}

const RiskChip: React.FC<{ level: 'safe' | 'caution' | 'high' | 'unknown' }> = ({ level }) => {
  const colors = {
    safe: 'success',
    caution: 'warning',
    high: 'error',
    unknown: 'default'
  };
  
  const labels = {
    safe: '🟢 SAFE',
    caution: '🟡 CAUTION',
    high: '🔴 HIGH RISK',
    unknown: 'ℹ️ UNKNOWN'
  };
  
  return (
    <Chip 
      label={labels[level]} 
      color={colors[level] as any}
      size="small"
    />
  );
};

const TokenSecuritySection: React.FC<{ 
  security: TokenSecurityInfo, 
  symbol: string,
  address: string 
}> = ({ security, symbol, address }) => {
  const getRiskLevel = () => {
    if (security.is_honeypot) return 'high';
    if (!security.is_open_source) return 'caution';
    if ((security.buy_tax ?? 0) > 10 || (security.sell_tax ?? 0) > 10) return 'caution';
    if (security.holder_count < 10) return 'caution';
    return 'safe';
  };

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6" gutterBottom>
        {symbol} Security Analysis
      </Typography>
      
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <RiskChip level={getRiskLevel()} />
          {security.is_honeypot && (
            <Chip 
              icon={<WarningIcon />}
              label={`HONEYPOT: ${security.honeypot_reason}`}
              color="error"
              sx={{ ml: 1 }}
            />
          )}
        </Grid>

        <Grid item xs={12}>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell>Buy Tax</TableCell>
                  <TableCell>
                    {security.buy_tax !== null ? `${security.buy_tax}%` : 'Unknown'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Sell Tax</TableCell>
                  <TableCell>
                    {security.sell_tax !== null ? `${security.sell_tax}%` : 'Unknown'}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Holders</TableCell>
                  <TableCell>{security.holder_count}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Contract</TableCell>
                  <TableCell>
                    {security.is_open_source ? (
                      <Chip icon={<CheckCircleIcon />} label="Verified" color="success" size="small" />
                    ) : (
                      <Chip icon={<ErrorIcon />} label="Unverified" color="error" size="small" />
                    )}
                  </TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Mintable</TableCell>
                  <TableCell>
                    {security.is_mintable ? (
                      <Chip icon={<WarningIcon />} label="Yes" color="warning" size="small" />
                    ) : (
                      <Chip icon={<CheckCircleIcon />} label="No" color="success" size="small" />
                    )}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        {security.goplus_details?.result && (
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Detailed Analysis</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableBody>
                      {Object.entries(security.goplus_details.result[address.toLowerCase()] || {}).map(([key, value]) => {
                        if (typeof value === 'object') return null;
                        return (
                          <TableRow key={key}>
                            <TableCell>{key.replace(/_/g, ' ').toUpperCase()}</TableCell>
                            <TableCell>{value.toString()}</TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>
          </Grid>
        )}

        {security.goplus_details?.result && (
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Top Holders</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Address</TableCell>
                        <TableCell>Balance</TableCell>
                        <TableCell>Percentage</TableCell>
                        <TableCell>Type</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {security.goplus_details.result[address.toLowerCase()]?.holders?.slice(0, 5).map((holder, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Tooltip title={holder.address}>
                              <Link href={`https://etherscan.io/address/${holder.address}`} target="_blank">
                                {`${holder.address.slice(0, 6)}...${holder.address.slice(-4)}`}
                              </Link>
                            </Tooltip>
                          </TableCell>
                          <TableCell>{parseFloat(holder.balance).toFixed(2)}</TableCell>
                          <TableCell>{(parseFloat(holder.percent) * 100).toFixed(2)}%</TableCell>
                          <TableCell>
                            {holder.is_contract ? (
                              <Chip label="Contract" size="small" />
                            ) : (
                              <Chip label="Wallet" size="small" />
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>
          </Grid>
        )}

        {security.goplus_details?.result && (
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Liquidity Analysis</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <TableContainer component={Paper} variant="outlined">
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>DEX</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Liquidity</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {security.goplus_details.result[address.toLowerCase()]?.dex?.map((dex, index) => (
                        <TableRow key={index}>
                          <TableCell>{dex.name}</TableCell>
                          <TableCell>{dex.liquidity_type}</TableCell>
                          <TableCell>${parseFloat(dex.liquidity).toLocaleString()}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

const PairCard: React.FC<PairCardProps> = ({ pair }) => {
  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <Typography variant="h5" gutterBottom>
              New Pair Detected
            </Typography>
            <Typography color="textSecondary" gutterBottom>
              {formatDistanceToNow(new Date(pair.created_at))} ago
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell>Pair Address</TableCell>
                    <TableCell>
                      <Link href={`https://etherscan.io/address/${pair.pair_address}`} target="_blank">
                        {pair.pair_address}
                      </Link>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Transaction</TableCell>
                    <TableCell>
                      <Link href={`https://etherscan.io/tx/${pair.transaction_hash}`} target="_blank">
                        {pair.transaction_hash}
                      </Link>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Block Number</TableCell>
                    <TableCell>{pair.block_number}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>
          </Grid>

          <Grid item xs={12} md={6}>
            <TokenSecuritySection 
              security={pair.token0_security_info}
              symbol={pair.token0_symbol}
              address={pair.token0_address}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TokenSecuritySection 
              security={pair.token1_security_info}
              symbol={pair.token1_symbol}
              address={pair.token1_address}
            />
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default PairCard; 