import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import PairList from './components/PairList';
import PairDetails from './components/PairDetails';
import ActivityFeed from './components/ActivityFeed';
import { PairInfo } from './types';
import './App.css';

interface LogEntry {
    timestamp: string;
    type: 'info' | 'success' | 'warning' | 'error';
    message: string;
}

function App() {
    const [pairs, setPairs] = useState<PairInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedPair, setSelectedPair] = useState<PairInfo | null>(null);
    const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
    const [logs, setLogs] = useState<LogEntry[]>([]);

    useEffect(() => {
        const socket = io('http://localhost:5000');

        socket.on('connect', () => {
            addLog('success', 'Connected to server');
            fetchExistingPairs();
        });

        socket.on('disconnect', () => {
            addLog('error', 'Disconnected from server');
        });

        socket.on('new_pair', (pair: PairInfo) => {
            addLog('info', `New pair detected: ${pair.token0.symbol}/${pair.token1.symbol}`);
            setPairs(prevPairs => [pair, ...prevPairs]);
            setLastUpdate(new Date());
        });

        socket.on('pair_updated', (updatedPair: PairInfo) => {
            addLog('info', `Updated pair: ${updatedPair.token0.symbol}/${updatedPair.token1.symbol}`);
            setPairs(prevPairs => 
                prevPairs.map(pair => 
                    pair.address === updatedPair.address ? updatedPair : pair
                )
            );
            if (selectedPair?.address === updatedPair.address) {
                setSelectedPair(updatedPair);
            }
            setLastUpdate(new Date());
        });

        socket.on('error', (error: string) => {
            addLog('error', `Server error: ${error}`);
            setError(error);
        });

        socket.on('server_log', (logEntry: { level: string; message: string }) => {
            const type = mapLogLevel(logEntry.level);
            addLog(type, logEntry.message);
        });

        return () => {
            socket.disconnect();
        };
    }, [selectedPair]);

    const addLog = (type: 'info' | 'success' | 'warning' | 'error', message: string) => {
        const timestamp = new Date().toLocaleTimeString();
        setLogs(prevLogs => [...prevLogs, { timestamp, type, message }].slice(-100));
    };

    const mapLogLevel = (level: string): 'info' | 'success' | 'warning' | 'error' => {
        switch (level.toLowerCase()) {
            case 'success':
                return 'success';
            case 'warning':
                return 'warning';
            case 'error':
                return 'error';
            default:
                return 'info';
        }
    };

    const fetchExistingPairs = async () => {
        try {
            const response = await fetch('http://localhost:5000/pairs');
            if (!response.ok) {
                throw new Error('Failed to fetch existing pairs');
            }
            const data = await response.json();
            setPairs(data);
            setLastUpdate(new Date());
            addLog('success', 'Fetched existing pairs successfully');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
            addLog('error', 'Failed to fetch existing pairs');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app">
            <header className="app-header">
                <h1>Uniswap V2 Pair Monitor</h1>
                {lastUpdate && (
                    <div className="last-update">
                        Last update: {lastUpdate.toLocaleString()}
                    </div>
                )}
            </header>
            {error && <div className="error-message">{error}</div>}
            <div className="app-content">
                <PairList 
                    pairs={pairs} 
                    loading={loading} 
                    onSelectPair={setSelectedPair}
                    selectedPairAddress={selectedPair?.address}
                />
                <div className="main-content">
                    <div className="main-content-scroll">
                        {selectedPair ? (
                            <PairDetails pair={selectedPair} />
                        ) : (
                            <div className="no-selection">
                                Select a pair to view details
                        </div>
                        )}
                            </div>
                    <ActivityFeed logs={logs} />
                            </div>
                        </div>
        </div>
    );
}

export default App;
