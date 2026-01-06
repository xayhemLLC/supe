"""Memory Card Viewer Web UI.

A browser-based UI for browsing and searching memory cards.

Features:
- Timeline view grouping cards by date
- Card list with type filtering
- Detailed card inspection with raw buffer data
- Search functionality

Usage:
    python -m applets.claude_mem_bridge.web
    # Then open http://localhost:5050
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict
from flask import Flask, render_template_string, jsonify, request

from .bridge import ClaudeMemBridge, ClaudeMemConfig
from .neural import NeuralMemory

app = Flask(__name__)
bridge: ClaudeMemBridge = None
neural: NeuralMemory = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Memory Viewer</title>
    <style>
        :root {
            --bg: #0d1117;
            --bg-secondary: #161b22;
            --bg-tertiary: #21262d;
            --border: #30363d;
            --text: #c9d1d9;
            --text-muted: #8b949e;
            --accent: #58a6ff;
            --red: #f85149;
            --green: #3fb950;
            --yellow: #d29922;
            --blue: #58a6ff;
            --purple: #a371f7;
            --cyan: #39c5cf;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            height: 100vh;
            overflow: hidden;
        }

        /* Header */
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 20px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
        }

        .header h1 {
            font-size: 16px;
            font-weight: 600;
        }

        .view-tabs {
            display: flex;
            gap: 4px;
        }

        .view-tab {
            padding: 6px 14px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: transparent;
            color: var(--text-muted);
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .view-tab:hover { background: var(--bg-tertiary); }
        .view-tab.active {
            background: var(--accent);
            color: white;
            border-color: var(--accent);
        }

        .container {
            display: flex;
            height: calc(100vh - 49px);
        }

        /* Sidebar */
        .sidebar {
            width: 420px;
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            background: var(--bg-secondary);
        }

        .search-container {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
        }

        .search-input {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid var(--border);
            border-radius: 6px;
            background: var(--bg);
            color: var(--text);
            font-size: 13px;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--accent);
        }

        .filters {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 10px;
        }

        .filter-btn {
            padding: 3px 8px;
            border: 1px solid var(--border);
            border-radius: 12px;
            background: transparent;
            color: var(--text-muted);
            font-size: 11px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .filter-btn:hover, .filter-btn.active {
            background: var(--bg-tertiary);
            color: var(--text);
            border-color: var(--accent);
        }

        .card-list {
            flex: 1;
            overflow-y: auto;
        }

        /* Timeline styles */
        .timeline-group {
            border-bottom: 1px solid var(--border);
        }

        .timeline-header {
            padding: 10px 16px;
            background: var(--bg);
            font-size: 12px;
            font-weight: 600;
            color: var(--accent);
            position: sticky;
            top: 0;
            z-index: 10;
            display: flex;
            justify-content: space-between;
            cursor: pointer;
        }

        .timeline-header:hover {
            background: var(--bg-tertiary);
        }

        .timeline-count {
            background: var(--bg-tertiary);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
            color: var(--text-muted);
        }

        .card-item {
            padding: 10px 16px;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            transition: background 0.2s;
        }

        .card-item:hover { background: var(--bg-tertiary); }

        .card-item.selected {
            background: var(--bg-tertiary);
            border-left: 3px solid var(--accent);
        }

        .card-title {
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 4px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .card-meta {
            display: flex;
            gap: 8px;
            font-size: 11px;
            color: var(--text-muted);
        }

        .card-type {
            padding: 1px 5px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 500;
        }

        .type-bugfix { background: rgba(248, 81, 73, 0.2); color: var(--red); }
        .type-feature { background: rgba(63, 185, 80, 0.2); color: var(--green); }
        .type-discovery { background: rgba(57, 197, 207, 0.2); color: var(--cyan); }
        .type-decision { background: rgba(210, 153, 34, 0.2); color: var(--yellow); }
        .type-change { background: rgba(88, 166, 255, 0.2); color: var(--blue); }
        .type-refactor { background: rgba(163, 113, 247, 0.2); color: var(--purple); }

        /* Main content */
        .main {
            flex: 1;
            overflow-y: auto;
            padding: 20px 28px;
        }

        .card-detail { max-width: 900px; }

        .detail-header { margin-bottom: 20px; }

        .detail-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 10px;
        }

        .detail-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            color: var(--text-muted);
            font-size: 13px;
        }

        .detail-tabs {
            display: flex;
            gap: 0;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border);
        }

        .detail-tab {
            padding: 10px 16px;
            border: none;
            background: transparent;
            color: var(--text-muted);
            font-size: 13px;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            margin-bottom: -1px;
        }

        .detail-tab:hover { color: var(--text); }
        .detail-tab.active {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .section { margin-bottom: 20px; }

        .section-title {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }

        .narrative {
            line-height: 1.6;
            white-space: pre-wrap;
            font-size: 14px;
        }

        .facts-list { list-style: none; }

        .facts-list li {
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
            line-height: 1.5;
            font-size: 13px;
        }

        .facts-list li:last-child { border-bottom: none; }

        .concepts {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }

        .concept-tag {
            padding: 3px 8px;
            background: var(--bg-tertiary);
            border-radius: 12px;
            font-size: 12px;
        }

        /* Buffer inspector */
        .buffer-inspector {
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 6px;
            overflow: hidden;
        }

        .buffer-item {
            border-bottom: 1px solid var(--border);
        }

        .buffer-item:last-child { border-bottom: none; }

        .buffer-header {
            padding: 10px 14px;
            background: var(--bg-secondary);
            font-size: 12px;
            font-weight: 600;
            color: var(--accent);
            display: flex;
            justify-content: space-between;
            cursor: pointer;
        }

        .buffer-header:hover { background: var(--bg-tertiary); }

        .buffer-type {
            font-weight: normal;
            color: var(--text-muted);
        }

        .buffer-content {
            padding: 12px 14px;
            font-family: 'SF Mono', Monaco, monospace;
            font-size: 12px;
            line-height: 1.5;
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 300px;
            overflow-y: auto;
        }

        .buffer-content.json {
            color: var(--cyan);
        }

        .stats-bar {
            padding: 8px 16px;
            background: var(--bg);
            border-top: 1px solid var(--border);
            font-size: 11px;
            color: var(--text-muted);
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-muted);
        }

        .empty-state h2 {
            font-size: 16px;
            margin-bottom: 8px;
        }

        .loading {
            display: flex;
            justify-content: center;
            padding: 40px;
        }

        .spinner {
            width: 28px;
            height: 28px;
            border: 3px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        /* Moment view */
        .moment-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        }

        .moment-time {
            font-size: 12px;
            color: var(--accent);
            margin-bottom: 8px;
        }

        .moment-cards {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .moment-card-item {
            padding: 10px 12px;
            background: var(--bg);
            border-radius: 6px;
            cursor: pointer;
        }

        .moment-card-item:hover {
            background: var(--bg-tertiary);
        }

        /* Neural visualization */
        .neural-container {
            display: flex;
            gap: 20px;
        }

        .neural-graph {
            flex: 1;
            min-height: 400px;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            position: relative;
            overflow: hidden;
        }

        .neural-canvas {
            width: 100%;
            height: 400px;
        }

        .neural-sidebar {
            width: 280px;
        }

        .neural-stats {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
        }

        .neural-stat {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid var(--border);
            font-size: 13px;
        }

        .neural-stat:last-child { border-bottom: none; }

        .neural-stat-value {
            color: var(--accent);
            font-weight: 600;
        }

        .connections-list {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            max-height: 300px;
            overflow-y: auto;
        }

        .connection-item {
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
            cursor: pointer;
            transition: background 0.2s;
        }

        .connection-item:hover { background: var(--bg-tertiary); }
        .connection-item:last-child { border-bottom: none; }

        .connection-title {
            font-size: 12px;
            margin-bottom: 4px;
            display: -webkit-box;
            -webkit-line-clamp: 1;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .connection-meta {
            display: flex;
            gap: 8px;
            font-size: 11px;
            color: var(--text-muted);
        }

        .strength-bar {
            width: 60px;
            height: 4px;
            background: var(--border);
            border-radius: 2px;
            overflow: hidden;
        }

        .strength-fill {
            height: 100%;
            background: var(--accent);
            border-radius: 2px;
            transition: width 0.3s;
        }

        .hub-badge {
            background: var(--yellow);
            color: var(--bg);
            padding: 1px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: 600;
        }

        /* Network view */
        .network-view {
            position: relative;
        }

        .network-node {
            position: absolute;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--accent);
            cursor: pointer;
            transition: transform 0.2s;
        }

        .network-node:hover {
            transform: scale(1.5);
            z-index: 100;
        }

        .network-node.hub {
            width: 18px;
            height: 18px;
            background: var(--yellow);
        }

        .network-node.selected {
            background: var(--green);
            box-shadow: 0 0 10px var(--green);
        }

        .network-tooltip {
            position: absolute;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            max-width: 250px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 Memory Viewer</h1>
        <div class="view-tabs">
            <button class="view-tab active" data-view="timeline">Timeline</button>
            <button class="view-tab" data-view="list">List</button>
            <button class="view-tab" data-view="moments">Moments</button>
            <button class="view-tab" data-view="neural">🔗 Neural</button>
        </div>
    </div>

    <div class="container">
        <div class="sidebar">
            <div class="search-container">
                <input type="text" class="search-input" placeholder="Search cards... (/ to focus)" id="search">
                <div class="filters" id="filters">
                    <button class="filter-btn active" data-type="">All</button>
                    <button class="filter-btn" data-type="bugfix">🔴 Bug</button>
                    <button class="filter-btn" data-type="feature">🟢 Feature</button>
                    <button class="filter-btn" data-type="discovery">🔵 Discovery</button>
                    <button class="filter-btn" data-type="decision">🟡 Decision</button>
                    <button class="filter-btn" data-type="change">⚪ Change</button>
                    <button class="filter-btn" data-type="refactor">🟣 Refactor</button>
                </div>
                <div style="margin-top: 10px;">
                    <select id="project-filter" class="search-input" style="padding: 6px 10px;">
                        <option value="">All Projects</option>
                    </select>
                </div>
                <div style="margin-top: 8px; display: flex; gap: 8px; font-size: 11px;">
                    <label style="color: var(--text-muted); cursor: pointer;">
                        <input type="checkbox" id="filter-today" style="margin-right: 4px;"> Today only
                    </label>
                    <label style="color: var(--text-muted); cursor: pointer;">
                        <input type="checkbox" id="filter-week" style="margin-right: 4px;"> This week
                    </label>
                </div>
            </div>
            <div class="card-list" id="cardList">
                <div class="loading"><div class="spinner"></div></div>
            </div>
            <div class="stats-bar" id="statsBar">Loading...</div>
        </div>
        <div class="main" id="main">
            <div class="empty-state">
                <h2>Select a card</h2>
                <p>Choose a memory card from the list to view its details</p>
            </div>
        </div>
    </div>

    <script>
        let allCards = [];
        let filteredCards = [];
        let currentType = '';
        let currentSearch = '';
        let currentProject = '';
        let filterToday = false;
        let filterWeek = false;
        let selectedCardId = null;
        let currentView = 'timeline';
        let currentDetailTab = 'overview';

        async function loadCards() {
            const res = await fetch('/api/cards');
            const data = await res.json();
            allCards = data.cards;
            updateStats(data.stats);
            populateProjectFilter(data.stats.projects);
            applyFilters();
        }

        function updateStats(stats) {
            const showing = filteredCards.length;
            const total = allCards.length;
            document.getElementById('statsBar').textContent =
                `Showing ${showing}/${total} cards | ${Object.keys(stats.types).length} types | ${Object.keys(stats.projects).length} projects`;
        }

        function populateProjectFilter(projects) {
            const select = document.getElementById('project-filter');
            if (!select) return;

            // Sort by count
            const sorted = Object.entries(projects).sort((a, b) => b[1] - a[1]);

            select.innerHTML = '<option value="">All Projects</option>' +
                sorted.map(([name, count]) => `<option value="${name}">${name} (${count})</option>`).join('');
        }

        function applyFilters() {
            const now = new Date();
            const todayStr = now.toISOString().split('T')[0];
            const weekAgo = new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

            filteredCards = allCards.filter(card => {
                // Type filter
                if (currentType && card.type !== currentType) return false;

                // Project filter
                if (currentProject && card.project !== currentProject) return false;

                // Time filters
                if (filterToday) {
                    const cardDate = card.created_at ? card.created_at.split('T')[0] : '';
                    if (cardDate !== todayStr) return false;
                }
                if (filterWeek) {
                    const cardDate = card.created_at ? card.created_at.split('T')[0] : '';
                    if (cardDate < weekAgo) return false;
                }

                // Search filter
                if (currentSearch) {
                    const search = currentSearch.toLowerCase();
                    const text = (card.title + ' ' + (card.narrative || '') + ' ' + (card.facts || []).join(' ') + ' ' + (card.project || '')).toLowerCase();
                    if (!text.includes(search)) return false;
                }
                return true;
            });

            renderCardList();
            // Update stats bar with filtered count
            document.getElementById('statsBar').textContent =
                `Showing ${filteredCards.length}/${allCards.length} cards`;
        }

        function groupByDate(cards) {
            const groups = {};
            cards.forEach(card => {
                const date = card.created_at ? card.created_at.split('T')[0] : 'Unknown';
                if (!groups[date]) groups[date] = [];
                groups[date].push(card);
            });
            return groups;
        }

        function formatDateHeader(dateStr) {
            if (dateStr === 'Unknown') return 'Unknown Date';
            // Parse as UTC to avoid timezone issues
            const [year, month, day] = dateStr.split('-').map(Number);
            const date = new Date(Date.UTC(year, month - 1, day));
            const today = new Date();
            const todayUTC = new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()));
            const diff = Math.round((todayUTC - date) / (1000 * 60 * 60 * 24));

            if (diff === 0) return 'Today';
            if (diff === 1) return 'Yesterday';
            if (diff > 0 && diff < 7) return `${diff} days ago`;

            return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
        }

        function renderCardList() {
            const list = document.getElementById('cardList');

            if (filteredCards.length === 0) {
                list.innerHTML = '<div class="empty-state"><p>No cards match your search</p></div>';
                return;
            }

            if (currentView === 'timeline') {
                const groups = groupByDate(filteredCards);
                const sortedDates = Object.keys(groups).sort().reverse();

                list.innerHTML = sortedDates.map(date => `
                    <div class="timeline-group">
                        <div class="timeline-header">
                            <span>${formatDateHeader(date)}</span>
                            <span class="timeline-count">${groups[date].length}</span>
                        </div>
                        ${groups[date].slice(0, 50).map(card => renderCardItem(card)).join('')}
                    </div>
                `).join('');
            } else if (currentView === 'moments') {
                // Group by hour for moments view
                const moments = {};
                filteredCards.slice(0, 200).forEach(card => {
                    if (!card.created_at) return;
                    const hourKey = card.created_at.slice(0, 13); // YYYY-MM-DDTHH
                    if (!moments[hourKey]) moments[hourKey] = [];
                    moments[hourKey].push(card);
                });

                const sortedMoments = Object.keys(moments).sort().reverse();
                list.innerHTML = sortedMoments.map(moment => {
                    const date = new Date(moment + ':00:00');
                    return `
                        <div class="moment-card">
                            <div class="moment-time">${date.toLocaleString()}</div>
                            <div class="moment-cards">
                                ${moments[moment].map(card => `
                                    <div class="moment-card-item" onclick="selectCard(${card.id})">
                                        <span class="card-type type-${card.type}">${card.type}</span>
                                        ${escapeHtml(card.title).slice(0, 80)}
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }).join('');
            } else if (currentView === 'neural') {
                // Neural network view - show hubs and stats
                list.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
                loadNeuralNetworkView();
            } else {
                list.innerHTML = filteredCards.slice(0, 200).map(card => renderCardItem(card)).join('');
            }
        }

        async function loadNeuralNetworkView() {
            const list = document.getElementById('cardList');

            try {
                const [statsRes, hubsRes] = await Promise.all([
                    fetch('/api/neural/stats'),
                    fetch('/api/neural/hubs')
                ]);

                const stats = await statsRes.json();
                const hubs = await hubsRes.json();

                list.innerHTML = `
                    <div style="padding: 16px;">
                        <div class="section-title">Neural Network Stats</div>
                        <div class="neural-stats">
                            <div class="neural-stat">
                                <span>Total Cards</span>
                                <span class="neural-stat-value">${stats.total_cards}</span>
                            </div>
                            <div class="neural-stat">
                                <span>Total Links</span>
                                <span class="neural-stat-value">${stats.total_links}</span>
                            </div>
                            <div class="neural-stat">
                                <span>Queries Made</span>
                                <span class="neural-stat-value">${stats.queries}</span>
                            </div>
                        </div>

                        <div style="margin-top: 20px;">
                            <div class="section-title">Build Pathways</div>
                            <input type="text" class="search-input" placeholder="Enter query to build neural pathways..." id="neural-query" style="margin-bottom: 10px;">
                            <button class="filter-btn active" onclick="runNeuralQuery()" style="width: 100%;">🔗 Run Neural Recall</button>
                            <div id="neural-query-result" style="margin-top: 10px; font-size: 12px; color: var(--text-muted);"></div>
                        </div>

                        <div style="margin-top: 20px;">
                            <div class="section-title">Hub Cards (Most Connected)</div>
                            ${hubs.hubs.length === 0 ?
                                '<div style="color: var(--text-muted); font-size: 12px;">No hubs yet. Run queries to build connections.</div>' :
                                hubs.hubs.map(hub => `
                                    <div class="card-item" onclick="selectCard(${hub.card_id})">
                                        <div class="card-title">${escapeHtml(hub.title)}</div>
                                        <div class="card-meta">
                                            <span class="card-type type-${hub.type}">${hub.type}</span>
                                            <span>🔗 ${hub.connectivity} connections</span>
                                            <span>📊 ${hub.recall_count} recalls</span>
                                        </div>
                                    </div>
                                `).join('')
                            }
                        </div>

                        ${stats.fundamental_branches && stats.fundamental_branches.length > 0 ? `
                        <div style="margin-top: 20px;">
                            <div class="section-title">Fundamental Branches (Strong Pathways)</div>
                            ${stats.fundamental_branches.map(branch => `
                                <div style="padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 12px;">
                                    <div style="color: var(--text);">${escapeHtml(branch.from)} → ${escapeHtml(branch.to)}</div>
                                    <div style="color: var(--text-muted); margin-top: 2px;">
                                        Strength: ${(branch.strength * 100).toFixed(0)}% | Activations: ${branch.activations}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        ` : ''}
                    </div>
                `;
            } catch (err) {
                list.innerHTML = '<div style="padding: 16px; color: var(--text-muted);">Failed to load neural stats</div>';
            }
        }

        async function runNeuralQuery() {
            const input = document.getElementById('neural-query');
            const result = document.getElementById('neural-query-result');
            if (!input || !result) return;

            const query = input.value.trim();
            if (!query) {
                result.textContent = 'Enter a query first';
                return;
            }

            result.innerHTML = '<div class="spinner" style="width:16px;height:16px;"></div>';

            try {
                const res = await fetch('/api/neural/recall', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query })
                });
                const data = await res.json();

                result.innerHTML = `
                    <div style="color: var(--green);">✓ Query executed</div>
                    <div>Found ${data.results.length} matches, ${data.total_links} total links</div>
                    ${data.results.slice(0, 3).map(r => `
                        <div style="margin-top: 4px; cursor: pointer;" onclick="selectCard(${r.card_id})">
                            → ${escapeHtml(r.title)} (${(r.activation * 100).toFixed(0)}%)
                        </div>
                    `).join('')}
                `;

                // Refresh the neural view
                setTimeout(loadNeuralNetworkView, 500);
            } catch (err) {
                result.textContent = 'Query failed';
            }
        }

        function renderCardItem(card) {
            return `
                <div class="card-item ${card.id === selectedCardId ? 'selected' : ''}" onclick="selectCard(${card.id})">
                    <div class="card-title">${escapeHtml(card.title)}</div>
                    <div class="card-meta">
                        <span class="card-type type-${card.type}">${card.type}</span>
                        <span>${card.project || 'no project'}</span>
                        <span>${formatTime(card.created_at)}</span>
                    </div>
                </div>
            `;
        }

        async function selectCard(id) {
            selectedCardId = id;
            renderCardList();

            const res = await fetch(`/api/cards/${id}`);
            const card = await res.json();
            renderCardDetail(card);
        }

        function renderCardDetail(card) {
            const main = document.getElementById('main');
            const facts = card.facts || [];
            const concepts = card.concepts || [];
            const buffers = card.buffers || {};

            main.innerHTML = `
                <div class="card-detail">
                    <div class="detail-header">
                        <h1 class="detail-title">${escapeHtml(card.title)}</h1>
                        <div class="detail-meta">
                            <span class="card-type type-${card.type}">${card.type}</span>
                            <span>📁 ${card.project || 'no project'}</span>
                            <span>🔑 ID: ${card.id}</span>
                            <span>📅 ${formatDateTime(card.created_at)}</span>
                        </div>
                    </div>

                    <div class="detail-tabs">
                        <button class="detail-tab active" data-tab="overview">Overview</button>
                        <button class="detail-tab" data-tab="neural">🔗 Neural</button>
                        <button class="detail-tab" data-tab="buffers">Buffers (${Object.keys(buffers).length})</button>
                        <button class="detail-tab" data-tab="raw">Raw JSON</button>
                    </div>

                    <div id="tab-overview" class="tab-content active">
                        ${card.narrative ? `
                        <div class="section">
                            <div class="section-title">Narrative</div>
                            <div class="narrative">${escapeHtml(card.narrative)}</div>
                        </div>
                        ` : ''}

                        ${facts.length > 0 ? `
                        <div class="section">
                            <div class="section-title">Facts (${facts.length})</div>
                            <ul class="facts-list">
                                ${facts.map(f => `<li>${escapeHtml(f)}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}

                        ${concepts.length > 0 ? `
                        <div class="section">
                            <div class="section-title">Concepts</div>
                            <div class="concepts">
                                ${concepts.map(c => `<span class="concept-tag">${escapeHtml(c)}</span>`).join('')}
                            </div>
                        </div>
                        ` : ''}
                    </div>

                    <div id="tab-neural" class="tab-content">
                        <div class="loading" id="neural-loading"><div class="spinner"></div></div>
                        <div id="neural-content" style="display:none">
                            <div class="neural-container">
                                <div class="neural-graph">
                                    <canvas id="neural-canvas" class="neural-canvas"></canvas>
                                </div>
                                <div class="neural-sidebar">
                                    <div class="neural-stats" id="neural-stats"></div>
                                    <div class="section-title">Connected Cards</div>
                                    <div class="connections-list" id="connections-list"></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div id="tab-buffers" class="tab-content">
                        <div class="buffer-inspector">
                            ${Object.entries(buffers).map(([name, value]) => `
                                <div class="buffer-item">
                                    <div class="buffer-header">
                                        <span>${name}</span>
                                        <span class="buffer-type">${typeof value}</span>
                                    </div>
                                    <div class="buffer-content ${Array.isArray(value) || typeof value === 'object' ? 'json' : ''}">${formatBufferValue(value)}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <div id="tab-raw" class="tab-content">
                        <div class="buffer-inspector">
                            <div class="buffer-content json">${escapeHtml(JSON.stringify(card, null, 2))}</div>
                        </div>
                    </div>
                </div>
            `;

            // Setup tab listeners
            main.querySelectorAll('.detail-tab').forEach(tab => {
                tab.addEventListener('click', () => {
                    main.querySelectorAll('.detail-tab').forEach(t => t.classList.remove('active'));
                    main.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                    tab.classList.add('active');
                    main.querySelector(`#tab-${tab.dataset.tab}`).classList.add('active');

                    // Load neural data when tab is clicked
                    if (tab.dataset.tab === 'neural') {
                        loadNeuralData(card.id);
                    }
                });
            });
        }

        async function loadNeuralData(cardId) {
            const loading = document.getElementById('neural-loading');
            const content = document.getElementById('neural-content');
            if (!loading || !content) return;

            loading.style.display = 'flex';
            content.style.display = 'none';

            try {
                const res = await fetch(`/api/neural/${cardId}`);
                const data = await res.json();

                renderNeuralStats(data);
                renderConnections(data.connections || []);
                renderNeuralGraph(cardId, data);

                loading.style.display = 'none';
                content.style.display = 'block';
            } catch (err) {
                loading.innerHTML = '<p style="color: var(--text-muted)">Failed to load neural data</p>';
            }
        }

        function renderNeuralStats(data) {
            const stats = document.getElementById('neural-stats');
            if (!stats) return;

            stats.innerHTML = `
                <div class="section-title">Neural Stats</div>
                <div class="neural-stat">
                    <span>Connections</span>
                    <span class="neural-stat-value">${data.connection_count || 0}</span>
                </div>
                <div class="neural-stat">
                    <span>Recall Count</span>
                    <span class="neural-stat-value">${data.recall_count || 0}</span>
                </div>
                <div class="neural-stat">
                    <span>Is Hub</span>
                    <span class="neural-stat-value">${data.is_hub ? '⭐ Yes' : 'No'}</span>
                </div>
                <div class="neural-stat">
                    <span>Activation</span>
                    <span class="neural-stat-value">${(data.activation || 0).toFixed(2)}</span>
                </div>
            `;
        }

        function renderConnections(connections) {
            const list = document.getElementById('connections-list');
            if (!list) return;

            if (connections.length === 0) {
                list.innerHTML = '<div style="padding: 16px; color: var(--text-muted); font-size: 12px;">No connections yet. Search for this card to build pathways.</div>';
                return;
            }

            list.innerHTML = connections.map(conn => `
                <div class="connection-item" onclick="selectCard(${conn.target_id})">
                    <div class="connection-title">${escapeHtml(conn.title)}</div>
                    <div class="connection-meta">
                        <span class="card-type type-${conn.type}">${conn.type}</span>
                        <div class="strength-bar">
                            <div class="strength-fill" style="width: ${conn.strength * 100}%"></div>
                        </div>
                        <span>${(conn.strength * 100).toFixed(0)}%</span>
                        ${conn.is_hub ? '<span class="hub-badge">HUB</span>' : ''}
                    </div>
                </div>
            `).join('');
        }

        let neuralNodes = []; // Store node positions for interaction

        function renderNeuralGraph(cardId, data) {
            const canvas = document.getElementById('neural-canvas');
            if (!canvas) return;

            const ctx = canvas.getContext('2d');
            const width = canvas.width = canvas.offsetWidth;
            const height = canvas.height = canvas.offsetHeight;

            ctx.clearRect(0, 0, width, height);
            neuralNodes = [];

            const connections = data.connections || [];
            if (connections.length === 0) {
                ctx.fillStyle = '#8b949e';
                ctx.font = '14px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('No neural connections yet', width/2, height/2);
                ctx.fillText('Search for related cards to build pathways', width/2, height/2 + 20);
                return;
            }

            // Center node
            const centerX = width / 2;
            const centerY = height / 2;
            const radius = Math.min(width, height) / 3;

            // Store center node
            neuralNodes.push({
                x: centerX, y: centerY, r: 14,
                id: cardId, title: 'Current Card', type: 'center', strength: 1
            });

            // Draw connections and store positions
            connections.forEach((conn, i) => {
                const angle = (i / connections.length) * Math.PI * 2 - Math.PI/2;
                const x = centerX + Math.cos(angle) * radius;
                const y = centerY + Math.sin(angle) * radius;
                const nodeRadius = conn.is_hub ? 12 : 8;

                // Store node for interaction
                neuralNodes.push({
                    x, y, r: nodeRadius,
                    id: conn.target_id,
                    title: conn.title,
                    type: conn.type,
                    strength: conn.strength,
                    activations: conn.activations,
                    is_hub: conn.is_hub
                });

                // Draw line with gradient
                const gradient = ctx.createLinearGradient(centerX, centerY, x, y);
                gradient.addColorStop(0, `rgba(63, 185, 80, ${conn.strength})`);
                gradient.addColorStop(1, `rgba(88, 166, 255, ${conn.strength})`);

                ctx.beginPath();
                ctx.moveTo(centerX, centerY);
                ctx.lineTo(x, y);
                ctx.strokeStyle = gradient;
                ctx.lineWidth = Math.max(1, conn.strength * 5);
                ctx.stroke();

                // Draw node
                ctx.beginPath();
                ctx.arc(x, y, nodeRadius, 0, Math.PI * 2);
                ctx.fillStyle = conn.is_hub ? '#d29922' : '#58a6ff';
                ctx.fill();
                ctx.strokeStyle = 'rgba(255,255,255,0.3)';
                ctx.lineWidth = 1;
                ctx.stroke();
            });

            // Draw center node on top
            ctx.beginPath();
            ctx.arc(centerX, centerY, 14, 0, Math.PI * 2);
            ctx.fillStyle = '#3fb950';
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();

            // Setup mouse interaction
            setupCanvasInteraction(canvas);
        }

        function setupCanvasInteraction(canvas) {
            const tooltip = document.createElement('div');
            tooltip.className = 'neural-tooltip';
            tooltip.style.cssText = 'position:fixed;background:var(--bg-secondary);border:1px solid var(--border);border-radius:6px;padding:10px 14px;font-size:12px;pointer-events:none;z-index:1000;display:none;max-width:280px;';
            document.body.appendChild(tooltip);

            let hoveredNode = null;

            canvas.onmousemove = (e) => {
                const rect = canvas.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                // Find hovered node
                hoveredNode = null;
                for (const node of neuralNodes) {
                    const dist = Math.sqrt((x - node.x) ** 2 + (y - node.y) ** 2);
                    if (dist <= node.r + 4) {
                        hoveredNode = node;
                        break;
                    }
                }

                if (hoveredNode) {
                    canvas.style.cursor = 'pointer';
                    tooltip.style.display = 'block';
                    tooltip.style.left = (e.clientX + 12) + 'px';
                    tooltip.style.top = (e.clientY + 12) + 'px';

                    if (hoveredNode.type === 'center') {
                        tooltip.innerHTML = '<strong>Current Card</strong><br><span style="color:var(--text-muted)">Click connections to navigate</span>';
                    } else {
                        tooltip.innerHTML = `
                            <strong>${escapeHtml(hoveredNode.title)}</strong><br>
                            <span class="card-type type-${hoveredNode.type}" style="display:inline-block;margin:4px 0;">${hoveredNode.type}</span><br>
                            <span style="color:var(--text-muted)">
                                Strength: ${(hoveredNode.strength * 100).toFixed(0)}%<br>
                                Activations: ${hoveredNode.activations || 0}
                                ${hoveredNode.is_hub ? '<br><span style="color:var(--yellow)">⭐ Hub Card</span>' : ''}
                            </span>
                        `;
                    }
                } else {
                    canvas.style.cursor = 'default';
                    tooltip.style.display = 'none';
                }
            };

            canvas.onmouseleave = () => {
                tooltip.style.display = 'none';
            };

            canvas.onclick = (e) => {
                if (hoveredNode && hoveredNode.type !== 'center') {
                    selectCard(hoveredNode.id);
                }
            };
        }

        function formatBufferValue(value) {
            if (value === null || value === undefined) return '<span style="color: var(--text-muted)">null</span>';
            if (typeof value === 'string') return escapeHtml(value);
            if (Array.isArray(value)) {
                return value.map((v, i) => `[${i}] ${escapeHtml(String(v))}`).join('\\n');
            }
            if (typeof value === 'object') {
                return escapeHtml(JSON.stringify(value, null, 2));
            }
            return escapeHtml(String(value));
        }

        function escapeHtml(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function formatTime(dateStr) {
            if (!dateStr) return '';
            const date = new Date(dateStr);
            return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
        }

        function formatDateTime(dateStr) {
            if (!dateStr) return '';
            const date = new Date(dateStr);
            return date.toLocaleString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            });
        }

        // Event listeners
        document.getElementById('search').addEventListener('input', (e) => {
            currentSearch = e.target.value;
            applyFilters();
        });

        document.getElementById('filters').addEventListener('click', (e) => {
            if (e.target.classList.contains('filter-btn')) {
                document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                currentType = e.target.dataset.type;
                applyFilters();
            }
        });

        document.getElementById('project-filter').addEventListener('change', (e) => {
            currentProject = e.target.value;
            applyFilters();
        });

        document.getElementById('filter-today').addEventListener('change', (e) => {
            filterToday = e.target.checked;
            if (filterToday) {
                document.getElementById('filter-week').checked = false;
                filterWeek = false;
            }
            applyFilters();
        });

        document.getElementById('filter-week').addEventListener('change', (e) => {
            filterWeek = e.target.checked;
            if (filterWeek) {
                document.getElementById('filter-today').checked = false;
                filterToday = false;
            }
            applyFilters();
        });

        document.querySelectorAll('.view-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.view-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                currentView = tab.dataset.view;
                renderCardList();
            });
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'SELECT') {
                e.preventDefault();
                document.getElementById('search').focus();
            }
            if (e.key === 'Escape') {
                document.getElementById('search').value = '';
                document.getElementById('search').blur();
                document.getElementById('project-filter').value = '';
                document.getElementById('filter-today').checked = false;
                document.getElementById('filter-week').checked = false;
                currentSearch = '';
                currentProject = '';
                filterToday = false;
                filterWeek = false;
                applyFilters();
            }
        });

        loadCards();
    </script>
</body>
</html>
"""


def init_bridge():
    """Initialize the bridge."""
    global bridge, neural
    if bridge is None:
        print("Loading cards from claude-mem...")
        config = ClaudeMemConfig(
            db_path="~/.claude-mem/claude-mem.db",
            import_embeddings=False,
            auto_link=False,  # Disable auto-linking for faster load
        )
        bridge = ClaudeMemBridge(config)
        bridge.import_all(limit=2000)  # Limit for faster initial load
        print(f"Loaded {len(bridge.cards)} cards")

        # Initialize neural memory with persistence
        neural = NeuralMemory(auto_load=False)  # Don't load yet - need cards first
        for card_id, card in bridge.cards.items():
            neural.add_card(card_id, {
                'title': card.buffers.get_text('title'),
                'type': card.buffers.get_text('type'),
                'project': card.buffers.get_text('project'),
            })
        # Now load persisted links and wire them to cards
        neural._load_from_db()
        print(f"Neural memory: {len(neural.cards)} cards, {len(neural.links)} persisted links")


@app.route('/')
def index():
    """Serve the main page."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/cards')
def get_cards():
    """Get all cards."""
    init_bridge()

    cards = []
    for card_id, card in bridge.cards.items():
        cards.append({
            'id': card_id,
            'title': card.buffers.get_text('title'),
            'type': card.buffers.get_text('type'),
            'project': card.buffers.get_text('project'),
            'narrative': card.buffers.get_text('narrative')[:200] if card.buffers.get_text('narrative') else '',
            'created_at': card.created_at.isoformat() if card.created_at else None,
        })

    cards.sort(key=lambda c: c['created_at'] or '', reverse=True)

    return jsonify({
        'cards': cards,
        'stats': bridge.get_stats()
    })


@app.route('/api/cards/<int:card_id>')
def get_card(card_id):
    """Get a single card with full details including raw buffers."""
    init_bridge()

    if card_id not in bridge.cards:
        return jsonify({'error': 'Card not found'}), 404

    card = bridge.cards[card_id]

    # Get all buffer data for inspection
    buffers = {}
    for name in ['title', 'type', 'project', 'narrative', 'facts', 'concepts', 'subtitle']:
        raw_val = card.buffers.get_raw(name)
        if raw_val is not None:
            buffers[name] = raw_val

    return jsonify({
        'id': card_id,
        'title': card.buffers.get_text('title'),
        'type': card.buffers.get_text('type'),
        'project': card.buffers.get_text('project'),
        'narrative': card.buffers.get_text('narrative'),
        'facts': card.buffers.get_lines('facts'),
        'concepts': card.buffers.get_lines('concepts'),
        'buffers': buffers,
        'created_at': card.created_at.isoformat() if card.created_at else None,
    })


@app.route('/api/timeline')
def get_timeline():
    """Get cards grouped by date."""
    init_bridge()

    timeline = defaultdict(list)
    for card_id, card in bridge.cards.items():
        if card.created_at:
            date_key = card.created_at.strftime('%Y-%m-%d')
        else:
            date_key = 'unknown'

        timeline[date_key].append({
            'id': card_id,
            'title': card.buffers.get_text('title'),
            'type': card.buffers.get_text('type'),
            'project': card.buffers.get_text('project'),
            'time': card.created_at.strftime('%H:%M') if card.created_at else None,
        })

    # Sort each day's cards by time
    for date in timeline:
        timeline[date].sort(key=lambda c: c['time'] or '', reverse=True)

    return jsonify({
        'timeline': dict(timeline),
        'dates': sorted(timeline.keys(), reverse=True)
    })


@app.route('/api/search')
def search():
    """Search cards."""
    init_bridge()

    query = request.args.get('q', '')
    obs_type = request.args.get('type', '')
    project = request.args.get('project', '')

    results = bridge.keyword_search(
        query,
        top_k=50,
        obs_type=obs_type or None,
        project=project or None
    )

    return jsonify({'results': results})


@app.route('/api/neural/<int:card_id>')
def get_neural(card_id):
    """Get neural connections for a card."""
    init_bridge()

    if card_id not in neural.cards:
        return jsonify({'error': 'Card not found in neural memory'}), 404

    card = neural.cards[card_id]

    # Get connections
    connections = []
    for target_id, link in card.outgoing.items():
        target = neural.cards.get(target_id)
        if target:
            connections.append({
                'target_id': target_id,
                'title': target.buffers.get('title', 'Unknown')[:60],
                'type': target.buffers.get('type', 'unknown'),
                'strength': link.strength,
                'activations': link.activation_count,
                'is_hub': target.is_hub,
            })

    # Sort by strength
    connections.sort(key=lambda c: c['strength'], reverse=True)

    return jsonify({
        'card_id': card_id,
        'connection_count': card.connectivity,
        'recall_count': card.recall_count,
        'activation': card.activation,
        'is_hub': card.is_hub,
        'connections': connections[:20],  # Top 20
    })


@app.route('/api/neural/recall', methods=['POST'])
def neural_recall():
    """Perform a neural recall query to build pathways."""
    init_bridge()

    data = request.get_json() or {}
    query = data.get('query', '')

    if not query:
        return jsonify({'error': 'Query required'}), 400

    results = neural.recall(query, top_k=10)

    return jsonify({
        'query': query,
        'results': [
            {
                'card_id': card_id,
                'activation': activation,
                'title': neural.cards[card_id].buffers.get('title', '?')[:60] if card_id in neural.cards else '?',
            }
            for card_id, activation in results
        ],
        'total_links': len(neural.links),
    })


@app.route('/api/neural/hubs')
def get_hubs():
    """Get hub cards."""
    init_bridge()

    hubs = neural.get_hubs(20)

    return jsonify({
        'hubs': [
            {
                'card_id': card_id,
                'title': card.buffers.get('title', '?')[:60],
                'type': card.buffers.get('type', 'unknown'),
                'connectivity': card.connectivity,
                'recall_count': card.recall_count,
            }
            for card_id, card in hubs
        ]
    })


@app.route('/api/neural/stats')
def get_neural_stats():
    """Get neural memory stats."""
    init_bridge()

    return jsonify({
        'total_cards': len(neural.cards),
        'total_links': len(neural.links),
        'queries': len(neural.query_history),
        'fundamental_branches': neural.find_fundamental_branches()[:10],
    })


def main():
    """Run the web server."""
    print("Starting Memory Card Viewer...")
    print("Open http://localhost:5050 in your browser")
    print()
    print("Features:")
    print("  - Timeline view: Cards grouped by date")
    print("  - List view: Flat card list")
    print("  - Moments view: Cards grouped by hour")
    print("  - Buffer inspector: View raw buffer data")
    print()
    print("Keyboard shortcuts:")
    print("  / - Focus search")
    print("  Esc - Clear search")
    print()
    app.run(host='127.0.0.1', port=5050, debug=False)


if __name__ == '__main__':
    main()
