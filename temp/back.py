<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>سیستم چند-عامله هوشمند تولید کد</title>
    
    <!-- Persian Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <!-- استفاده از فونت‌های فارسی بهینه -->
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/sahel-font@v3.4.0/dist/font-face.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/samim-font@v4.0.5/dist/font-face.css" rel="stylesheet">
    
    <style>
        :root {
            /* Enhanced Color System */
            --primary: #6366f1;
            --primary-light: #818cf8;
            --primary-dark: #4f46e5;
            --secondary: #0f172a;
            --accent: #f59e0b;
            --success: #059669;
            --warning: #d97706;
            --danger: #dc2626;
            --info: #0284c7;
            
            /* Rich Background Palette */
            --bg-primary: #0a0e1a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --bg-quaternary: #475569;
            --bg-glass: rgba(30, 41, 59, 0.95);
            --bg-card: rgba(51, 65, 85, 0.95);
            --bg-hover: rgba(99, 102, 241, 0.1);
            --bg-active: rgba(99, 102, 241, 0.2);
            
            /* Enhanced Text Colors */
            --text-primary: #ffffff;
            --text-secondary: #f1f5f9;
            --text-muted: #cbd5e1;
            --text-accent: #c084fc;
            --text-inverse: #0f172a;
            
            /* Border System */
            --border-primary: #475569;
            --border-secondary: #64748b;
            --border-accent: rgba(99, 102, 241, 0.4);
            --border-focus: rgba(99, 102, 241, 0.6);
            --border-success: rgba(5, 150, 105, 0.4);
            --border-warning: rgba(217, 119, 6, 0.4);
            --border-danger: rgba(220, 38, 38, 0.4);
            
            /* Light Effects */
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.15);
            --shadow: 0 8px 25px rgba(0, 0, 0, 0.25);
            --shadow-lg: 0 16px 40px rgba(0, 0, 0, 0.35);
            --shadow-glow: 0 0 32px rgba(99, 102, 241, 0.25);
            --gradient-primary: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
            --gradient-secondary: linear-gradient(145deg, #0a0e1a 0%, #1e293b 50%, #334155 100%);
            --blur: blur(24px);
            
            /* Border Radius */
            --radius-xs: 6px;
            --radius-sm: 10px;
            --radius: 14px;
            --radius-lg: 18px;
            --radius-xl: 24px;
            --radius-2xl: 32px;
            
            /* Lighter Transitions */
            --transition-fast: all 0.08s ease;
            --transition: all 0.15s ease;
            --transition-slow: all 0.2s ease;
            
            /* Persian Font System */
            --font-primary: 'Vazirmatn', 'Sahel', 'Samim', -apple-system, BlinkMacSystemFont, 'Tahoma', sans-serif;
            --font-mono: 'JetBrains Mono', 'SF Mono', 'Monaco', 'Inconsolata', monospace;
            --font-persian: 'Vazirmatn', 'Sahel', 'Samim', -apple-system, BlinkMacSystemFont, 'Tahoma', sans-serif;
            --font-english: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            
            /* Spacing */
            --space-xs: 6px;
            --space-sm: 10px;
            --space: 16px;
            --space-lg: 24px;
            --space-xl: 32px;
            --space-2xl: 48px;
            --space-3xl: 64px;
            
            /* Typography Scale */
            --text-xs: 0.75rem;
            --text-sm: 0.875rem;
            --text-base: 1rem;
            --text-lg: 1.125rem;
            --text-xl: 1.25rem;
            --text-2xl: 1.5rem;
            --text-3xl: 1.875rem;
            --text-4xl: 2.25rem;
            --text-5xl: 3rem;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--font-persian);
            background: var(--gradient-secondary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            overflow-x: hidden;
            font-size: var(--text-base);
            transform: scale(0.65);
            transform-origin: top center;
            width: 153.85%;
            min-height: 153.85vh;
            font-weight: 400;
            /* بهبود رندرینگ فونت فارسی */
            text-rendering: optimizeLegibility;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }

        /* بهبود فونت فارسی در عناصر مختلف */
        h1, h2, h3, h4, h5, h6 {
            font-family: var(--font-persian);
            font-weight: 700;
            letter-spacing: -0.02em;
        }

        p, span, div, label {
            font-family: var(--font-persian);
        }

        .english-text {
            font-family: var(--font-english);
        }

        /* Enhanced background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 20% 20%, rgba(99, 102, 241, 0.12) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.12) 0%, transparent 50%),
                radial-gradient(circle at 40% 60%, rgba(5, 150, 105, 0.08) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }

        .container {
            max-width: 1800px;
            margin: 0 auto;
            padding: var(--space-xl);
            position: relative;
        }

        /* Enhanced Header */
        .header {
            background: var(--bg-glass);
            backdrop-filter: var(--blur);
            border: 1px solid var(--border-accent);
            border-radius: var(--radius-2xl);
            padding: var(--space-3xl);
            margin-bottom: var(--space-2xl);
            text-align: center;
            position: relative;
            box-shadow: var(--shadow-glow);
        }

        .header-title {
            font-size: var(--text-4xl);
            font-weight: 800;
            color: #ffffff;
            margin-bottom: var(--space);
            font-family: var(--font-persian);
            line-height: 1.2;
            letter-spacing: -0.01em;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: var(--space);
        }

        .header-subtitle {
            color: var(--text-secondary);
            font-size: var(--text-lg);
            font-weight: 400;
            max-width: 700px;
            margin: 0 auto var(--space-lg);
            font-family: var(--font-persian);
            line-height: 1.6;
        }

        .header-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: var(--space-lg);
            margin-top: var(--space-2xl);
            max-width: 900px;
            margin-left: auto;
            margin-right: auto;
        }

        .stat-item {
            display: flex;
            align-items: center;
            gap: var(--space);
            padding: var(--space-lg) var(--space-xl);
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-secondary);
            transition: var(--transition);
            backdrop-filter: var(--blur);
            box-shadow: var(--shadow-sm);
            min-width: 160px;
        }

        .stat-item:hover {
            border-color: var(--border-accent);
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }

        .stat-icon {
            width: 40px;
            height: 40px;
            background: rgba(99, 102, 241, 0.1);
            border-radius: var(--radius);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .stat-content {
            flex: 1;
            text-align: right;
        }

        .stat-value {
            font-size: var(--text-2xl);
            font-weight: 700;
            color: var(--text-primary);
            font-family: var(--font-english);
            margin-bottom: 2px;
            line-height: 1;
        }

        .stat-label {
            font-size: var(--text-sm);
            color: var(--text-muted);
            font-family: var(--font-persian);
            font-weight: 500;
        }

        /* Enhanced Main Layout */
        .main-layout {
            display: grid;
            grid-template-columns: 400px 1fr 320px;
            gap: var(--space-2xl);
            min-height: calc(100vh - 400px);
            align-items: start;
        }

        /* Enhanced Card System */
        .card {
            background: var(--bg-card);
            backdrop-filter: var(--blur);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-xl);
            padding: var(--space-2xl);
            position: relative;
            transition: var(--transition-slow);
            box-shadow: var(--shadow);
            margin-bottom: var(--space-xl);
        }

        .card:hover {
            border-color: var(--border-accent);
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: var(--space);
            margin-bottom: var(--space-xl);
            padding-bottom: var(--space-lg);
            border-bottom: 1px solid var(--border-secondary);
        }

        .card-title {
            font-size: var(--text-xl);
            font-weight: 700;
            color: var(--text-primary);
            margin: 0;
            font-family: var(--font-persian);
        }

        /* Enhanced Form Elements */
        .form-group {
            margin-bottom: var(--space-lg);
        }

        .form-label {
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            margin-bottom: var(--space);
            font-weight: 600;
            color: var(--text-secondary);
            font-size: var(--text-base);
            font-family: var(--font-persian);
        }

        .form-input, .form-select, .form-textarea {
            width: 100%;
            padding: var(--space) var(--space-lg);
            background: var(--bg-tertiary);
            border: 2px solid var(--border-primary);
            border-radius: var(--radius);
            color: var(--text-primary);
            font-family: var(--font-persian);
            font-size: var(--text-base);
            transition: var(--transition);
            outline: none;
        }

        .form-input:focus, .form-select:focus, .form-textarea:focus {
            border-color: var(--border-focus);
            background: var(--bg-secondary);
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15);
        }

        .form-textarea {
            min-height: 100px;
            font-family: var(--font-persian);
            resize: vertical;
            line-height: 1.7;
        }

        /* Enhanced Button System */
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: var(--space);
            padding: var(--space) var(--space-xl);
            border: none;
            border-radius: var(--radius);
            font-family: var(--font-persian);
            font-size: var(--text-base);
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: var(--transition);
            white-space: nowrap;
            position: relative;
            overflow: hidden;
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .btn-primary {
            background: var(--gradient-primary);
            color: white;
            box-shadow: var(--shadow);
        }

        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: var(--shadow-lg);
        }

        .btn-secondary {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border-secondary);
        }

        .btn-secondary:hover:not(:disabled) {
            background: var(--bg-quaternary);
            border-color: var(--border-accent);
            transform: translateY(-1px);
        }

        .btn-success {
            background: linear-gradient(135deg, #059669 0%, #10b981 100%);
            color: white;
        }

        .btn-danger {
            background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
            color: white;
        }

        .btn-full {
            width: 100%;
        }

        .btn-sm {
            padding: var(--space-sm) var(--space);
            font-size: var(--text-sm);
        }

        /* API Configuration */
        .api-provider {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: var(--space-lg);
            background: var(--bg-tertiary);
            border-radius: var(--radius-lg);
            margin-bottom: var(--space);
            border: 2px solid var(--border-primary);
            transition: var(--transition);
            cursor: pointer;
        }

        .api-provider:hover {
            border-color: var(--border-accent);
            background: var(--bg-hover);
        }

        .api-provider.active {
            border-color: var(--border-focus);
            background: var(--bg-active);
            box-shadow: var(--shadow-sm);
        }

        .api-info {
            display: flex;
            align-items: center;
            gap: var(--space);
        }

        .api-logo {
            width: 32px;
            height: 32px;
            border-radius: var(--radius-sm);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .api-details h4 {
            font-weight: 600;
            color: var(--text-primary);
            font-size: var(--text-base);
            margin-bottom: 2px;
            font-family: var(--font-persian);
        }

        .api-details p {
            font-size: var(--text-sm);
            color: var(--text-muted);
            font-family: var(--font-english);
        }

        .api-status {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--success);
        }

        .api-status.disconnected {
            background: var(--danger);
        }

        /* کوچک‌تر کردن کارت‌های ابزارهای برنامه‌نویسی */
        .agents-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
            gap: var(--space-xs);
        }

        .agent-card {
            background: var(--bg-secondary);
            border: 2px solid var(--border-primary);
            border-radius: var(--radius);
            padding: var(--space-xs);
            text-align: center;
            transition: var(--transition);
            cursor: pointer;
            position: relative;
            min-height: 70px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        .agent-card:hover {
            border-color: var(--border-accent);
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }

        .agent-card.active {
            border-color: var(--primary);
            background: var(--bg-active);
            box-shadow: var(--shadow-glow);
        }

        /* آیکون‌های رنگی برای ابزارهای برنامه‌نویسی */
        .agent-avatar {
            width: 28px;
            height: 28px;
            border-radius: var(--radius-sm);
            margin-bottom: var(--space-xs);
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .agent-avatar.manager {
            background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
        }

        .agent-avatar.developer {
            background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
        }

        .agent-avatar.designer {
            background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
        }

        .agent-avatar.tester {
            background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
        }

        .agent-avatar.security {
            background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
        }

        .agent-avatar.analyst {
            background: linear-gradient(135deg, #06b6d4 0%, #38bdf8 100%);
        }

        .agent-name {
            font-size: 10px;
            font-weight: 600;
            margin-bottom: 2px;
            font-family: var(--font-persian);
            color: var(--text-primary);
            line-height: 1.2;
        }

        .agent-status {
            font-size: 8px;
            color: var(--text-muted);
            font-family: var(--font-persian);
            padding: 1px 3px;
            background: var(--bg-tertiary);
            border-radius: var(--radius-xs);
            display: inline-block;
        }

        /* Enhanced Status Bar */
        .status-bar {
            background: var(--bg-card);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            padding: var(--space-lg);
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: var(--space-lg);
            backdrop-filter: var(--blur);
        }

        .status-info {
            display: flex;
            align-items: center;
            gap: var(--space);
        }

        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            position: relative;
        }

        .status-indicator::after {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            background: inherit;
            animation: pulse-ring 2s infinite;
        }

        .status-working { background: var(--warning); }
        .status-complete { background: var(--success); }
        .status-error { background: var(--danger); }

        /* Enhanced Progress Bar */
        .progress-container {
            background: var(--bg-tertiary);
            border-radius: var(--radius);
            height: 10px;
            overflow: hidden;
            margin-bottom: var(--space-lg);
            position: relative;
        }

        .progress-bar {
            height: 100%;
            background: var(--gradient-primary);
            width: 0%;
            transition: width 0.3s ease;
            border-radius: var(--radius);
        }

        /* Enhanced Tabs */
        .tabs {
            display: flex;
            background: var(--bg-tertiary);
            border-radius: var(--radius-lg);
            padding: var(--space-xs);
            margin-bottom: var(--space-lg);
            gap: var(--space-xs);
        }

        .tab {
            flex: 1;
            padding: var(--space) var(--space-lg);
            background: transparent;
            border: none;
            color: var(--text-secondary);
            cursor: pointer;
            border-radius: var(--radius);
            transition: var(--transition);
            font-family: var(--font-persian);
            font-size: var(--text-sm);
            font-weight: 500;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: var(--space-sm);
        }

        .tab:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }

        .tab.active {
            background: var(--gradient-primary);
            color: white;
            box-shadow: var(--shadow-sm);
        }

        /* Tab Content */
        .tab-content {
            display: none;
            background: var(--bg-card);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            height: 600px;
            overflow: hidden;
            backdrop-filter: var(--blur);
        }

        .tab-content.active {
            display: block;
        }

        /* Enhanced Logs */
        .logs-container {
            padding: var(--space-lg);
            height: 100%;
            overflow-y: auto;
            font-family: var(--font-persian);
            font-size: var(--text-sm);
        }

        .log-entry {
            padding: var(--space-sm) var(--space);
            margin-bottom: var(--space-sm);
            border-radius: var(--radius);
            border-left: 4px solid;
            background: rgba(0, 0, 0, 0.3);
            transition: var(--transition);
            backdrop-filter: var(--blur);
            font-family: var(--font-persian);
        }

        .log-entry:hover {
            transform: translateX(6px);
        }

        .log-info { border-color: var(--info); }
        .log-success { border-color: var(--success); }
        .log-warning { border-color: var(--warning); }
        .log-error { border-color: var(--danger); }

        /* File Tree */
        .file-tree {
            padding: var(--space-lg);
            height: 100%;
            overflow-y: auto;
        }

        .file-item {
            padding: var(--space) var(--space-lg);
            cursor: pointer;
            border-radius: var(--radius);
            margin-bottom: var(--space-sm);
            transition: var(--transition);
            display: flex;
            align-items: center;
            gap: var(--space);
            font-family: var(--font-persian);
            font-size: var(--text-sm);
            border: 1px solid transparent;
        }

        .file-item:hover {
            background: var(--bg-hover);
            border-color: var(--border-accent);
            transform: translateX(6px);
        }

        .file-item.active {
            background: var(--bg-active);
            border-color: var(--border-focus);
            color: var(--text-primary);
        }

        .file-meta {
            font-size: var(--text-xs);
            color: var(--text-muted);
            margin-top: 2px;
            font-family: var(--font-persian);
        }

        /* Monitor Cards */
        .monitor-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: var(--space);
        }

        .monitor-card {
            background: var(--bg-secondary);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            padding: var(--space-lg);
            text-align: center;
            transition: var(--transition);
        }

        .monitor-card:hover {
            border-color: var(--border-accent);
            transform: translateY(-2px);
        }

        .monitor-value {
            font-size: var(--text-2xl);
            font-weight: 700;
            color: var(--primary-light);
            margin-bottom: var(--space-xs);
            font-family: var(--font-english);
        }

        .monitor-label {
            font-size: var(--text-xs);
            color: var(--text-muted);
            font-family: var(--font-persian);
            font-weight: 500;
        }

        /* Chat Interface */
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 100%;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: var(--space-lg);
            display: flex;
            flex-direction: column;
            gap: var(--space);
        }

        .chat-message {
            display: flex;
            gap: var(--space);
        }

        .chat-message.user {
            flex-direction: row-reverse;
        }

        .message-avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--gradient-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: var(--text-sm);
            font-weight: 600;
            flex-shrink: 0;
        }

        .message-content {
            background: var(--bg-tertiary);
            padding: var(--space) var(--space-lg);
            border-radius: var(--radius-lg);
            max-width: 75%;
            border: 1px solid var(--border-primary);
            font-size: var(--text-sm);
            font-family: var(--font-persian);
            line-height: 1.6;
        }

        .chat-message.user .message-content {
            background: var(--gradient-primary);
            color: white;
            border-color: transparent;
        }

        .chat-input-container {
            padding: var(--space-lg);
            border-top: 1px solid var(--border-primary);
            display: flex;
            gap: var(--space);
        }

        .chat-input {
            flex: 1;
            padding: var(--space) var(--space-lg);
            background: var(--bg-tertiary);
            border: 2px solid var(--border-primary);
            border-radius: var(--radius-lg);
            color: var(--text-primary);
            resize: none;
            min-height: 44px;
            max-height: 120px;
            font-family: var(--font-persian);
            font-size: var(--text-sm);
            outline: none;
            transition: var(--transition);
        }

        .chat-input:focus {
            border-color: var(--border-focus);
            box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15);
        }

        /* سبک‌تر کردن انیمیشن‌های نوتیفیکیشن */
        .notification-container {
            position: fixed;
            top: var(--space-xl);
            right: var(--space-xl);
            z-index: 2000;
            display: flex;
            flex-direction: column;
            gap: var(--space);
            max-width: 400px;
        }

        .smart-notification {
            background: var(--bg-card);
            backdrop-filter: var(--blur);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            padding: var(--space-lg);
            box-shadow: var(--shadow-lg);
            transform: translateX(110%);
            transition: transform 0.2s ease;
            border-left: 4px solid var(--info);
        }

        .smart-notification.show {
            transform: translateX(0);
        }

        .smart-notification.success { border-left-color: var(--success); }
        .smart-notification.error { border-left-color: var(--danger); }
        .smart-notification.warning { border-left-color: var(--warning); }
        .smart-notification.info { border-left-color: var(--info); }

        .notification-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: var(--space-sm);
        }

        .notification-title {
            display: flex;
            align-items: center;
            gap: var(--space-sm);
            font-weight: 600;
            color: var(--text-primary);
            font-size: var(--text-base);
            font-family: var(--font-persian);
        }

        .notification-close {
            background: none;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            padding: 0;
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: var(--transition);
        }

        .notification-close:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }

        .notification-body {
            color: var(--text-secondary);
            font-size: var(--text-sm);
            line-height: 1.5;
            margin-bottom: var(--space);
            font-family: var(--font-persian);
        }

        .notification-actions {
            display: flex;
            gap: var(--space-sm);
            justify-content: flex-end;
        }

        .notification-btn {
            padding: var(--space-xs) var(--space);
            border: 1px solid var(--border-secondary);
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border-radius: var(--radius-sm);
            font-size: var(--text-xs);
            cursor: pointer;
            transition: var(--transition);
            font-family: var(--font-persian);
        }

        .notification-btn:hover {
            background: var(--bg-hover);
            border-color: var(--border-accent);
        }

        .notification-btn.primary {
            background: var(--primary);
            border-color: var(--primary);
            color: white;
        }

        .notification-btn.primary:hover {
            background: var(--primary-dark);
        }

        /* Preview Container */
        .preview-container {
            padding: var(--space-lg);
            height: 100%;
            overflow-y: auto;
        }

        .preview-content {
            background: var(--bg-secondary);
            border-radius: var(--radius-lg);
            padding: var(--space-xl);
            border: 1px solid var(--border-primary);
        }

        .preview-header {
            text-align: center;
            margin-bottom: var(--space-xl);
        }

        .preview-title {
            font-size: var(--text-2xl);
            font-weight: 700;
            color: var(--primary-light);
            margin-bottom: var(--space);
            font-family: var(--font-persian);
        }

        .preview-meta {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: var(--space);
            margin-bottom: var(--space-xl);
        }

        .meta-item {
            background: var(--bg-tertiary);
            padding: var(--space);
            border-radius: var(--radius);
            text-align: center;
        }

        .meta-label {
            font-size: var(--text-xs);
            color: var(--text-muted);
            margin-bottom: var(--space-xs);
            font-weight: 500;
            font-family: var(--font-persian);
        }

        .meta-value {
            font-size: var(--text-sm);
            font-weight: 600;
            color: var(--text-primary);
            font-family: var(--font-persian);
        }

        .preview-iframe {
            width: 100%;
            height: 300px;
            border: none;
            border-radius: var(--radius);
            background: white;
        }

        /* Empty State */
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            padding: var(--space-2xl);
            text-align: center;
            color: var(--text-muted);
        }

        .empty-state h3 {
            margin: var(--space-lg) 0 var(--space);
            font-family: var(--font-persian);
            font-size: var(--text-lg);
            font-weight: 600;
            color: var(--text-secondary);
        }

        .empty-state p {
            font-family: var(--font-persian);
            font-size: var(--text-sm);
            line-height: 1.6;
            max-width: 400px;
        }

        /* SVG Icons */
        .icon {
            width: 20px;
            height: 20px;
            display: inline-block;
            vertical-align: middle;
        }

        .icon-lg {
            width: 24px;
            height: 24px;
        }

        .icon-xl {
            width: 48px;
            height: 48px;
        }

        /* Light Loading Animation */
        .loading {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: var(--primary);
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        @keyframes pulse-ring {
            0% {
                transform: scale(0.33);
                opacity: 1;
            }
            80%, 100% {
                transform: scale(2.33);
                opacity: 0;
            }
        }

        /* Enhanced Responsive Design */
        @media (max-width: 1600px) {
            .main-layout {
                grid-template-columns: 360px 1fr 300px;
                gap: var(--space-xl);
            }
        }

        @media (max-width: 1400px) {
            .main-layout {
                grid-template-columns: 320px 1fr 280px;
                gap: var(--space-lg);
            }
        }

        @media (max-width: 1200px) {
            .main-layout {
                grid-template-columns: 1fr;
                gap: var(--space-lg);
            }
            
            .sidebar { order: 2; }
            .main-content { order: 1; }
            .right-sidebar { order: 3; }
        }

        @media (max-width: 768px) {
            body {
                transform: scale(0.85);
                width: 117.65%;
                min-height: 117.65vh;
            }
            
            .container {
                padding: var(--space);
            }
            
            .header {
                padding: var(--space-xl);
            }
            
            .header-stats {
                grid-template-columns: repeat(2, 1fr);
                gap: var(--space);
            }
            
            .agents-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }

        @media (max-width: 480px) {
            .header-stats {
                grid-template-columns: 1fr;
            }
            
            .agents-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .monitor-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Connection Status Indicator */
        .connection-status {
            position: fixed;
            top: var(--space-lg);
            left: var(--space-lg);
            background: var(--bg-card);
            border: 1px solid var(--border-primary);
            border-radius: var(--radius-lg);
            padding: var(--space) var(--space-lg);
            display: flex;
            align-items: center;
            gap: var(--space);
            backdrop-filter: var(--blur);
            z-index: 1000;
            box-shadow: var(--shadow);
            min-width: 180px;
        }

        .connection-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            position: relative;
        }

        .connection-indicator.connected {
            background: var(--success);
        }

        .connection-indicator.disconnected {
            background: var(--danger);
        }

        .connection-indicator.checking {
            background: var(--warning);
        }

        .connection-text {
            font-size: var(--text-sm);
            font-weight: 600;
            color: var(--text-primary);
            font-family: var(--font-persian);
        }

        /* Enhanced Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: var(--border-secondary);
            border-radius: 4px;
            transition: var(--transition);
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--border-accent);
        }

        /* Error State Styles */
        .error-state {
            background: rgba(220, 38, 38, 0.1);
            border: 1px solid var(--border-danger);
            border-radius: var(--radius-lg);
            padding: var(--space-xl);
            text-align: center;
            color: var(--text-primary);
        }

        .error-title {
            font-size: var(--text-xl);
            font-weight: 700;
            color: var(--danger);
            margin-bottom: var(--space);
            font-family: var(--font-persian);
        }

        .error-message {
            font-size: var(--text-base);
            color: var(--text-secondary);
            margin-bottom: var(--space-lg);
            font-family: var(--font-persian);
        }
    </style>
</head>
<body>
    <!-- Connection Status Indicator -->
    <div class="connection-status" id="connectionStatus">
        <div class="connection-indicator checking" id="connectionIndicator"></div>
        <span class="connection-text" id="connectionText">بررسی ارتباط...</span>
    </div>

    <!-- Smart Notification Container -->
    <div class="notification-container" id="notificationContainer"></div>

    <div class="container">
        <!-- Enhanced Header -->
        <header class="header">
            <h1 class="header-title">
                <svg class="icon-lg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z"/>
                </svg>
                سیستم هوش مصنوعی تولید کد
            </h1>
            <p class="header-subtitle">
                پلتفرم پیشرفته تولید خودکار کد با استفاده از هوش مصنوعی و سیستم چند عامله هوشمند
            </p>
            <div class="header-stats">
                <div class="stat-item">
                    <div class="stat-icon">
                        <svg class="icon" viewBox="0 0 24 24" fill="var(--primary)">
                            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value" id="activeProjects">0</div>
                        <div class="stat-label">پروژه فعال</div>
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-icon">
                        <svg class="icon" viewBox="0 0 24 24" fill="var(--success)">
                            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value" id="onlineServices">0</div>
                        <div class="stat-label">سرویس آنلاین</div>
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-icon">
                        <svg class="icon" viewBox="0 0 24 24" fill="var(--warning)">
                            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value" id="connectedAPIs">0</div>
                        <div class="stat-label">API متصل</div>
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-icon">
                        <svg class="icon" viewBox="0 0 24 24" fill="var(--info)">
                            <path d="M13 9h8L11 24v-9H4l9-15v9z"/>
                        </svg>
                    </div>
                    <div class="stat-content">
                        <div class="stat-value" id="systemUptime">0%</div>
                        <div class="stat-label">آپتایم سیستم</div>
                    </div>
                </div>
            </div>
        </header>

        <div class="main-layout">
            <!-- Left Sidebar -->
            <aside class="sidebar">
                <!-- Project Generation -->
                <div class="card">
                    <div class="card-header">
                        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                        </svg>
                        <h3 class="card-title">تولید پروژه جدید</h3>
                    </div>
                    
                    <form id="projectForm">
                        <div class="form-group">
                            <label for="project-name" class="form-label">
                                <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                                </svg>
                                نام پروژه
                            </label>
                            <input type="text" id="project-name" class="form-input" placeholder="مثال: فروشگاه آنلاین هوشمند با AI" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="project-type" class="form-label">
                                <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                                </svg>
                                نوع پروژه
                            </label>
                            <select id="project-type" class="form-select" required>
                                <option value="">انتخاب کنید</option>
                                <option value="web-app">وب اپلیکیشن (React/Vue/Angular)</option>
                                <option value="mobile-app">اپلیکیشن موبایل (React Native/Flutter)</option>
                                <option value="desktop-app">اپلیکیشن دسکتاپ (Electron/Tauri)</option>
                                <option value="api">API و بک‌اند (FastAPI/Django/Express)</option>
                                <option value="ai-ml">هوش مصنوعی/یادگیری ماشین</option>
                                <option value="blockchain">بلاکچین و Web3</option>
                                <option value="game">بازی (Unity/Godot)</option>
                                <option value="automation">اتوماسیون و ربات</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="project-desc" class="form-label">
                                <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
                                </svg>
                                توضیحات کامل پروژه
                            </label>
                            <textarea id="project-desc" class="form-textarea" placeholder="توضیح کامل در مورد پروژه، نیازمندی‌ها، قابلیت‌های مورد نظر، تکنولوژی‌های مطلوب و جزئیات عملکردی..." required></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="project-lang" class="form-label">
                                <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0L19.2 12l-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"/>
                                </svg>
                                زبان‌های برنامه نویسی
                            </label>
                            <input type="text" id="project-lang" class="form-input" placeholder="مثال: Python, TypeScript, Rust, Go">
                        </div>
                        
                        <div class="form-group">
                            <label for="project-framework" class="form-label">
                                <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                                </svg>
                                فریم‌ورک‌ها و کتابخانه‌ها
                            </label>
                            <input type="text" id="project-framework" class="form-input" placeholder="مثال: Next.js, FastAPI, PostgreSQL, Redis">
                        </div>
                        
                        <div class="form-group">
                            <label for="project-complexity" class="form-label">
                                <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                                </svg>
                                سطح پیچیدگی و زمان تولید
                            </label>
                            <select id="project-complexity" class="form-select">
                                <option value="simple">ساده - MVP (2-5 روز)</option>
                                <option value="medium" selected>متوسط - کامل (1-3 هفته)</option>
                                <option value="complex">پیچیده - پیشرفته (1-3 ماه)</option>
                                <option value="enterprise">سازمانی - مقیاس‌پذیر (3+ ماه)</option>
                            </select>
                        </div>
                        
                        <button type="submit" class="btn btn-primary btn-full" id="generateBtn">
                            <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M8 5v14l11-7z"/>
                            </svg>
                            شروع تولید هوشمند
                        </button>
                    </form>
                </div>

                <!-- Enhanced API Configuration -->
                <div class="card">
                    <div class="card-header">
                        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                        </svg>
                        <h3 class="card-title">سرویس‌های هوش مصنوعی</h3>
                    </div>
                    
                    <div class="api-provider active" data-provider="openai">
                        <div class="api-info">
                            <div class="api-logo" style="background: linear-gradient(135deg, #10a37f 0%, #1a7f64 100%);">
                                <svg class="icon" viewBox="0 0 24 24" fill="white">
                                    <path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729z"/>
                                </svg>
                            </div>
                            <div class="api-details">
                                <h4>OpenAI GPT</h4>
                                <p>GPT-4 Turbo، GPT-3.5، Codex</p>
                            </div>
                        </div>
                        <div class="api-status" title="متصل"></div>
                    </div>
                    
                    <div class="api-provider" data-provider="anthropic">
                        <div class="api-info">
                            <div class="api-logo" style="background: linear-gradient(135deg, #d97706 0%, #92400e 100%);">
                                <svg class="icon" viewBox="0 0 24 24" fill="white">
                                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                                </svg>
                            </div>
                            <div class="api-details">
                                <h4>Anthropic Claude</h4>
                                <p>Claude-3 Opus، Claude-3 Sonnet</p>
                            </div>
                        </div>
                        <div class="api-status" title="متصل"></div>
                    </div>
                    
                    <div class="api-provider" data-provider="google">
                        <div class="api-info">
                            <div class="api-logo" style="background: linear-gradient(135deg, #4285f4 0%, #1a73e8 100%);">
                                <svg class="icon" viewBox="0 0 24 24" fill="white">
                                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                </svg>
                            </div>
                            <div class="api-details">
                                <h4>Google AI</h4>
                                <p>Gemini Pro، PaLM 2، Bard</p>
                            </div>
                        </div>
                        <div class="api-status disconnected" title="قطع شده"></div>
                    </div>
                    
                    <div class="api-provider" data-provider="mistral">
                        <div class="api-info">
                            <div class="api-logo" style="background: linear-gradient(135deg, #ff7000 0%, #cc5a00 100%);">
                                <svg class="icon" viewBox="0 0 24 24" fill="white">
                                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                                </svg>
                            </div>
                            <div class="api-details">
                                <h4>Mistral AI</h4>
                                <p>Mistral Large، Mixtral 8x7B</p>
                            </div>
                        </div>
                        <div class="api-status" title="متصل"></div>
                    </div>
                    
                    <button class="btn btn-secondary btn-full" style="margin-top: var(--space);">
                        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                        </svg>
                        تنظیمات پیشرفته API
                    </button>
                </div>

                <!-- Enhanced Agent Status -->
                <div class="card">
                    <div class="card-header">
                        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0L19.2 12l-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"/>
                        </svg>
                        <h3 class="card-title">ابزارهای کدنویسی</h3>
                    </div>
                    <div class="agents-grid">
                        <div class="agent-card active" data-agent="manager">
                            <div class="agent-avatar manager">
                                <svg class="icon" viewBox="0 0 24 24" fill="white">
                                    <path d="M16,6L18.29,8.29L13.41,13.17L9.41,9.17L2,16.59L3.41,18L9.41,12L13.41,16L19.71,9.71L22,12V6H16Z"/>
                                </svg>
                            </div>
                            <div class="agent-name">مدیریت پروژه</div>
                            <div class="agent-status">فعال</div>
                        </div>
                        <div class="agent-card" data-agent="developer">
                            <div class="agent-avatar developer">
                                <svg class="icon" viewBox="0 0 24 24" fill="white">
                                    <path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0L19.2 12l-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"/>
                                </svg>
                            </div>
                            <div class="agent-name">تولید کد</div>
                            <div class="agent-status">آماده</div>
                        </div>
                        <div class="agent-card" data-agent="designer">
                            <div class="agent-avatar designer">
                                <svg class="icon" viewBox="0 0 24 24" fill="white">
                                    <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4Z"/>
                                </svg>
                            </div>
                            <div class="agent-name">طراحی UI</div>
                            <div class="agent-status">آماده</div>
                        </div>
                        <div class="agent-card" data-agent="tester">
                            <div class="agent-avatar tester">
                                <svg class="icon" viewBox="0 0 24 24" fill="white">
                                    <path d="M9,2V8H7V2H9M17,2V8H15V2H17M12,1C10.89,1 10,1.89 10,3H14C14,1.89 13.11,1 12,1M12,6A1,1 0 0,1 11,5A1,1 0 0,1 12,4A1,1 0 0,1 13,5A1,1 0 0,1 12,6M12,8C9.79,8 8,9.79 8,12V22H16V12C16,9.79 14.21,8 12,8Z"/>
                                </svg>
                            </div>
                            <div class="agent-name">تست کد</div>
                            <div class="agent-status">آماده</div>
                        </div>
                        <div class="agent-card" data-agent="security">
                            <div class="agent-avatar security">
                                <svg class="icon" viewBox="0 0 24 24" fill="white">
                                    <path d="M12,1L3,5V11C3,16.55 6.84,21.74 12,23C17.16,21.74 21,16.55 21,11V5L12,1M12,7C13.4,7 14.8,8.6 14.8,10V11.5C15.4,11.5 16,12.1 16,12.7V16.3C16,16.9 15.4,17.5 14.8,17.5H9.2C8.6,17.5 8,16.9 8,16.3V12.6C8,12 8.6,11.4 9.2,11.4V10C9.2,8.6 10.6,7 12,7M12,8.2C11.2,8.2 10.5,8.7 10.5,10V11.5H13.5V10C13.5,8.7 12.8,8.2 12,8.2Z"/>
                                </svg>
                            </div>
                            <div class="agent-name">بررسی امنیت</div>
                            <div class="agent-status">آماده</div>
                        </div>
                        <div class="agent-card" data-agent="analyst">
                            <div class="agent-avatar analyst">
                                <svg class="icon" viewBox="0 0 24 24" fill="white">
                                    <path d="M3,3V21H21V19H5V3H3M20,8V10H19V8H20M19,3A2,2 0 0,1 21,5V7H19V3M9,8H11V16H9V8M19,11V16H21V18H17V11H19M12,6H14V16H12V6M15,4H17V16H15V4M6,10H8V16H6V10Z"/>
                                </svg>
                            </div>
                            <div class="agent-name">بهینه‌سازی</div>
                            <div class="agent-status">آماده</div>
                        </div>
                    </div>
                </div>
            </aside>

            <!-- Main Content -->
            <main class="main-content">
                <!-- Enhanced Status Bar -->
                <div class="status-bar">
                    <div class="status-info">
                        <div class="status-indicator status-working" id="statusIndicator"></div>
                        <span class="status-text" id="statusText">آماده برای شروع تولید پروژه...</span>
                    </div>
                    <div class="status-info">
                        <span class="status-text" id="stepText">گام 0 از 12</span>
                    </div>
                </div>

                <!-- Enhanced Progress Bar -->
                <div class="progress-container">
                    <div class="progress-bar" id="progressBar"></div>
                </div>
                
                <!-- Enhanced Tabs -->
                <div class="tabs">
                    <button class="tab active" data-tab-target="#logs-tab">
                        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M2 3h20v2H2zm1.15 4h17.7l-2 8H4.5l.65-8z"/>
                        </svg>
                        لاگ‌های سیستم
                    </button>
                    <button class="tab" data-tab-target="#files-tab">
                        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M10 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2h-8l-2-2z"/>
                        </svg>
                        فایل‌های پروژه
                    </button>
                    <button class="tab" data-tab-target="#preview-tab">
                        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                        </svg>
                        پیش‌نمایش زنده
                    </button>
                    <button class="tab" data-tab-target="#chat-tab">
                        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
                        </svg>
                        دستیار کدنویسی
                    </button>
                </div>

                <!-- Tab Contents -->
                <div id="logs-tab" class="tab-content active">
                    <div class="logs-container" id="logsContainer">
                        <div class="log-entry log-success">
                            <span>[00:00:01]</span> سیستم هوش مصنوعی با موفقیت راه‌اندازی شد
                        </div>
                        <div class="log-entry log-success">
                            <span>[00:00:02]</span> اتصال به سرویس‌های هوش مصنوعی برقرار شد (OpenAI ✓ Anthropic ✓ Mistral ✓)
                        </div>
                        <div class="log-entry log-info">
                            <span>[00:00:03]</span> تمامی ابزارهای کدنویسی آماده دریافت دستورات هستند
                        </div>
                        <div class="log-entry log-info">
                            <span>[00:00:04]</span> سیستم مانیتورینگ فعال شد - CPU: 45% | RAM: 8.2GB | API Latency: 34ms
                        </div>
                    </div>
                </div>

                <div id="files-tab" class="tab-content">
                    <div class="file-tree" id="fileTree">
                        <div class="empty-state">
                            <svg class="icon-xl" viewBox="0 0 24 24" fill="currentColor" style="opacity: 0.3;">
                                <path d="M10 4H4c-1.11 0-2 .89-2 2v12c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2h-8l-2-2z"/>
                            </svg>
                            <h3>درخت فایل‌های پروژه خالی است</h3>
                            <p>پس از شروع فرآیند تولید، ساختار کامل پروژه شامل فایل‌های کد، تست‌ها، مستندات و تنظیمات اینجا نمایش داده خواهند شد.</p>
                        </div>
                    </div>
                </div>

                <div id="preview-tab" class="tab-content">
                    <div class="preview-container" id="previewContainer">
                        <div class="empty-state">
                            <svg class="icon-xl" viewBox="0 0 24 24" fill="currentColor" style="opacity: 0.3;">
                                <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>
                            </svg>
                            <h3>پیش‌نمایش زنده در انتظار پروژه</h3>
                            <p>پس از تولید پروژه، می‌توانید پیش‌نمایش زنده و تعاملی آن را در این بخش مشاهده کنید. سیستم از سرویس‌های آنلاین برای ارائه پیش‌نمایش واقعی استفاده می‌کند.</p>
                        </div>
                    </div>
                </div>

                <div id="chat-tab" class="tab-content">
                    <div class="chat-container">
                        <div class="chat-messages" id="chatMessages">
                            <div class="chat-message">
                                <div class="message-avatar">
                                    <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0L19.2 12l-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"/>
                                    </svg>
                                </div>
                                <div class="message-content">
                                    سلام! من دستیار کدنویسی هستم. آماده‌ام تا پروژه ایده‌آل شما را با بهترین تکنولوژی‌ها و استانداردهای روز دنیا بسازم. چه نوع اپلیکیشنی می‌خواهید بسازیم؟
                                </div>
                            </div>
                        </div>
                        <div class="chat-input-container">
                            <textarea class="chat-input" placeholder="سوال یا درخواست کدنویسی خود را بنویسید..." id="chatInput"></textarea>
                            <button class="btn btn-primary" id="sendChatBtn">
                                <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </main>

            <!-- Right Sidebar -->
            <aside class="right-sidebar">
                <!-- Enhanced System Monitor -->
                <div class="card">
                    <div class="card-header">
                        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M13 9h8L11 24v-9H4l9-15v9z"/>
                        </svg>
                        <h3 class="card-title">مانیتور سیستم</h3>
                    </div>
                    <div class="monitor-grid">
                        <div class="monitor-card">
                            <div class="monitor-value" id="cpuUsage">67%</div>
                            <div class="monitor-label">پردازنده CPU</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-value" id="ramUsage">14.2GB</div>
                            <div class="monitor-label">حافظه RAM</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-value" id="apiLatency">28ms</div>
                            <div class="monitor-label">تاخیر API</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-value" id="tokensPerHour">2.4M</div>
                            <div class="monitor-label">توکن/ساعت</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-value" id="activeConnections">156</div>
                            <div class="monitor-label">اتصالات فعال</div>
                        </div>
                        <div class="monitor-card">
                            <div class="monitor-value" id="dailyGenerated">42</div>
                            <div class="monitor-label">پروژه/روز</div>
                        </div>
                    </div>
                </div>

                <!-- Enhanced Recent Projects -->
                <div class="card">
                    <div class="card-header">
                        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9z"/>
                        </svg>
                        <h3 class="card-title">پروژه‌های اخیر</h3>
                    </div>
                    <div class="file-tree">
                        <div class="file-item" data-project="ecommerce">
                            <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                            </svg>
                            <div>
                                <div>فروشگاه آنلاین NextJS</div>
                                <div class="file-meta">3 ساعت پیش - NextJS + Stripe</div>
                            </div>
                        </div>
                        <div class="file-item" data-project="dashboard">
                            <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M22,21H2V3H4V19H6V10H10V19H12V6H16V19H18V14H22V21Z"/>
                            </svg>
                            <div>
                                <div>داشبورد تحلیلی</div>
                                <div class="file-meta">1 روز پیش - React + D3.js</div>
                            </div>
                        </div>
                        <div class="file-item" data-project="ai-chat">
                            <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
                            </svg>
                            <div>
                                <div>چت‌بات هوشمند</div>
                                <div class="file-meta">2 روز پیش - Python + OpenAI</div>
                            </div>
                        </div>
                        <div class="file-item" data-project="mobile-banking">
                            <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M17 2H7c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
                            </svg>
                            <div>
                                <div>اپ موبایل بانکداری</div>
                                <div class="file-meta">5 روز پیش - Flutter + Firebase</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Enhanced Quick Actions -->
                <div class="card">
                    <div class="card-header">
                        <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M13 9h8L11 24v-9H4l9-15v9z"/>
                        </svg>
                        <h3 class="card-title">اقدامات سریع</h3>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: var(--space-sm);">
                        <button class="btn btn-secondary btn-full btn-sm" id="uploadBtn">
                            <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
                            </svg>
                            آپلود فایل پروژه
                        </button>
                        <button class="btn btn-secondary btn-full btn-sm" id="downloadBtn">
                            <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M5 20v-5h2v3h10v-3h2v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1zM9 4h6v7l-2-2-2 2-2-2V4z"/>
                            </svg>
                            دانلود پروژه کامل
                        </button>
                        <button class="btn btn-secondary btn-full btn-sm" id="shareBtn">
                            <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z"/>
                            </svg>
                            اشتراک‌گذاری پروژه
                        </button>
                        <button class="btn btn-secondary btn-full btn-sm" id="templateBtn">
                            <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                            </svg>
                            قالب‌های آماده
                        </button>
                        <button class="btn btn-success btn-full btn-sm" id="backupBtn">
                            <svg class="icon" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12,1L8,5H11V14H13V5H16M18,23H6C4.89,23 4,22.1 4,21V9A2,2 0 0,1 6,7H9V9H6V21H18V9H15V7H18A2,2 0 0,1 20,9V21A2,2 0 0,1 18,23Z"/>
                            </svg>
                            پشتیبان‌گیری خودکار
                        </button>
                    </div>
                </div>
            </aside>
        </div>
    </div>

    <script>
        class EnhancedAICodeGenerator {
            constructor() {
                try {
                    this.initializeSystem();
                    this.checkAPIConnections();
                    this.setupEventListeners();
                    this.startSystemMonitoring();
                    this.startRealTimeUpdates();
                    this.initializeSmartNotifications();
                    this.addLog('🚀 سیستم هوش مصنوعی تولید کد با موفقیت راه‌اندازی شد', 'success');
                } catch (error) {
                    console.error('خطا در راه‌اندازی سیستم:', error);
                    this.handleInitializationError(error);
                }
            }

            initializeSystem() {
                try {
                    this.currentStep = 0;
                    this.totalSteps = 12;
                    this.isGenerating = false;
                    this.apiConnections = {
                        openai: { status: 'checking', latency: 0, lastCheck: null },
                        anthropic: { status: 'checking', latency: 0, lastCheck: null },
                        google: { status: 'checking', latency: 0, lastCheck: null },
                        mistral: { status: 'checking', latency: 0, lastCheck: null }
                    };
                    this.agents = [
                        { id: 'manager', name: 'مدیریت پروژه', status: 'ready', emoji: '🤖' },
                        { id: 'developer', name: 'تولید کد', status: 'ready', emoji: '👨‍💻' },
                        { id: 'designer', name: 'طراحی UI', status: 'ready', emoji: '🎨' },
                        { id: 'tester', name: 'تست کد', status: 'ready', emoji: '🧪' },
                        { id: 'security', name: 'بررسی امنیت', status: 'ready', emoji: '🔒' },
                        { id: 'analyst', name: 'بهینه‌سازی', status: 'ready', emoji: '📊' }
                    ];
                    this.files = [];
                    this.systemStats = {
                        activeProjects: 0,
                        onlineServices: 0,
                        connectedAPIs: 0,
                        systemUptime: 0,
