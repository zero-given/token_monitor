import React, { useEffect, useRef } from 'react';

interface LogEntry {
    timestamp: string;
    type: 'info' | 'success' | 'warning' | 'error';
    message: string;
}

interface ActivityFeedProps {
    logs: LogEntry[];
}

const ActivityFeed: React.FC<ActivityFeedProps> = ({ logs }) => {
    const feedRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (feedRef.current) {
            feedRef.current.scrollTop = feedRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="activity-feed" ref={feedRef}>
            <div className="activity-feed-title">
                <div className="status"></div>
                Live Activity Feed
            </div>
            {logs.map((log, index) => (
                <div key={index} className="log-entry">
                    <span className="timestamp">{log.timestamp}</span>
                    <span className={`type ${log.type}`}>
                        {log.type.toUpperCase()}
                    </span>
                    <span className="message">{log.message}</span>
                </div>
            ))}
        </div>
    );
};

export default ActivityFeed; 