import React, { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import PairList from './components/PairList';
import { PairInfo } from './types';
import './App.css';

function App() {
    const [pairs, setPairs] = useState<PairInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

    // Fetch all pairs
    const fetchPairs = async () => {
        try {
            const response = await fetch('http://localhost:5000/pairs');
            if (!response.ok) {
                throw new Error('Failed to fetch pairs');
            }
            const data = await response.json();
            setPairs(data);
            setLastUpdate(new Date());
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch pairs');
        } finally {
            setLoading(false);
        }
    };

    // Set up WebSocket connection
    useEffect(() => {
        const socket = io('http://localhost:5000');

        socket.on('connect', () => {
            console.log('Connected to WebSocket server');
            setError(null);
        });

        socket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
            setError('WebSocket connection error');
        });

        socket.on('new_pair', (newPair: PairInfo) => {
            setPairs(prevPairs => [newPair, ...prevPairs]);
            setLastUpdate(new Date());
        });

        // Fetch initial data and set up refresh interval
        fetchPairs();
        const interval = setInterval(fetchPairs, 180000); // Refresh every 3 minutes

        return () => {
            socket.disconnect();
            clearInterval(interval);
        };
    }, []);

    return (
        <div className="app">
            <header className="app-header">
                <h1>🦄 Uniswap V2 Pair Monitor</h1>
                {lastUpdate && (
                    <div className="last-update">
                        Last updated: {lastUpdate.toLocaleString()}
                    </div>
                )}
            </header>

            <main className="app-content">
                {error && (
                    <div className="error-message">
                        Error: {error}
                    </div>
                )}

                <div className="stats">
                    <div className="stat-card">
                        <h3>Total Pairs</h3>
                        <div className="stat-value">{pairs.length}</div>
                    </div>
                    <div className="stat-card">
                        <h3>Honeypots Detected</h3>
                        <div className="stat-value danger">
                            {pairs.filter(p => 
                                p.securityChecks?.token0?.isHoneypot || 
                                p.securityChecks?.token1?.isHoneypot
                            ).length}
                        </div>
                    </div>
                    <div className="stat-card">
                        <h3>High Tax Pairs</h3>
                        <div className="stat-value warning">
                            {pairs.filter(p => 
                                (p.securityChecks?.token0?.buyTax ?? 0) > 10 || 
                                (p.securityChecks?.token0?.sellTax ?? 0) > 10 ||
                                (p.securityChecks?.token1?.buyTax ?? 0) > 10 || 
                                (p.securityChecks?.token1?.sellTax ?? 0) > 10
                            ).length}
                        </div>
                    </div>
                </div>

                <PairList pairs={pairs} loading={loading} />
            </main>

            <footer className="app-footer">
                <p>Data refreshes every 3 minutes • New pairs appear in real-time</p>
            </footer>
        </div>
    );
}

export default App;
