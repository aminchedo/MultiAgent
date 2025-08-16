/**
 * Modern Multi-Agent AI Code Generator
 * Modular JavaScript Architecture with State Management
 */

// =================================================================
// STATE MANAGEMENT SYSTEM
// =================================================================

class AppState {
    constructor() {
        this.state = {
            // UI State
            currentTab: 'generator',
            isGenerating: false,
            isConnected: navigator.onLine,
            
            // Project State
            project: {
                files: [],
                logs: [],
                config: null
            },
            
            // API State
            apiKeys: new Map(),
            apiStatus: new Map(),
            
            // Notifications
            notifications: new Map()
        };
        
        this.listeners = new Map();
        this.initialize();
    }
    
    initialize() {
        // Load saved state
        this.loadFromStorage();
        
        // Setup connection monitoring
        this.setupConnectionMonitoring();
        
        // Setup periodic cleanup
        this.setupCleanup();
    }
    
    // State management
    getState(path = null) {
        if (path) {
            return this.getNestedValue(this.state, path);
        }
        return { ...this.state };
    }
    
    setState(updates, options = {}) {
        const oldState = { ...this.state };
        
        if (typeof updates === 'function') {
            this.state = { ...this.state, ...updates(this.state) };
        } else {
            this.state = { ...this.state, ...updates };
        }
        
        // Persist to storage if needed
        if (options.persist !== false) {
            this.saveToStorage();
        }
        
        // Notify listeners
        this.notifyListeners(oldState, this.state);
    }
    
    // Event system
    subscribe(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }
        this.listeners.get(event).add(callback);
        
        // Return unsubscribe function
        return () => {
            this.listeners.get(event)?.delete(callback);
        };
    }
    
    notifyListeners(oldState, newState) {
        this.listeners.get('stateChange')?.forEach(callback => {
            callback(newState, oldState);
        });
    }
    
    // Storage management
    saveToStorage() {
        try {
            const persistentData = {
                apiKeys: Array.from(this.state.apiKeys.entries()),
                project: {
                    files: this.state.project.files,
                    config: this.state.project.config
                }
            };
            localStorage.setItem('aiGenerator_state', JSON.stringify(persistentData));
        } catch (error) {
            console.warn('Failed to save state to storage:', error);
        }
    }
    
    loadFromStorage() {
        try {
            const saved = localStorage.getItem('aiGenerator_state');
            if (saved) {
                const data = JSON.parse(saved);
                this.state.apiKeys = new Map(data.apiKeys || []);
                this.state.project = { ...this.state.project, ...data.project };
            }
        } catch (error) {
            console.warn('Failed to load state from storage:', error);
        }
    }
    
    setupConnectionMonitoring() {
        window.addEventListener('online', () => {
            this.setState({ isConnected: true });
            this.notifyListeners('connection', { online: true });
        });
        
        window.addEventListener('offline', () => {
            this.setState({ isConnected: false });
            this.notifyListeners('connection', { online: false });
        });
    }
    
    setupCleanup() {
        // Cleanup old notifications and logs periodically
        setInterval(() => {
            const now = Date.now();
            const hourAgo = now - (60 * 60 * 1000);
            
            // Clean old notifications
            for (const [id, notification] of this.state.notifications) {
                if (notification.timestamp < hourAgo && !notification.persistent) {
                    this.state.notifications.delete(id);
                }
            }
            
            // Keep only last 100 logs
            if (this.state.project.logs.length > 100) {
                this.state.project.logs = this.state.project.logs.slice(-100);
            }
        }, 300000); // 5 minutes
    }
    
    // Utility methods
    getNestedValue(obj, path) {
        return path.split('.').reduce((current, key) => current?.[key], obj);
    }
}

// =================================================================
// API SERVICE WITH RETRY AND WEBSOCKET SUPPORT
// =================================================================

class ApiService {
    constructor(appState) {
        this.appState = appState;
        this.baseUrl = this.getBaseUrl();
        this.retryConfig = {
            maxRetries: 3,
            retryDelay: 1000,
            backoffFactor: 2
        };
        this.setupWebSocket();
    }
    
    getBaseUrl() {
        if (typeof window !== 'undefined') {
            return window.location.origin;
        }
        return 'http://localhost:8000';
    }
    
    // HTTP Client with retry logic
    async request(endpoint, options = {}) {
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        return await this.retryRequest(`${this.baseUrl}${endpoint}`, config);
    }
    
    async retryRequest(url, config, attempt = 1) {
        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            if (attempt <= this.retryConfig.maxRetries) {
                const delay = this.retryConfig.retryDelay * Math.pow(this.retryConfig.backoffFactor, attempt - 1);
                
                console.warn(`Request failed (attempt ${attempt}/${this.retryConfig.maxRetries}). Retrying in ${delay}ms...`);
                
                await this.sleep(delay);
                return this.retryRequest(url, config, attempt + 1);
            }
            
            throw error;
        }
    }
    
    // WebSocket for real-time updates
    setupWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('🔗 WebSocket connected');
                this.appState.setState({ wsConnected: true });
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.warn('Invalid WebSocket message:', error);
                }
            };
            
            this.ws.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.appState.setState({ wsConnected: false });
                
                // Reconnect after delay
                setTimeout(() => this.setupWebSocket(), 5000);
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
        } catch (error) {
            console.warn('WebSocket not available:', error);
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'generation_progress':
                this.appState.setState({
                    isGenerating: data.isGenerating,
                    generationProgress: data.progress
                });
                break;
                
            case 'file_update':
                const files = this.appState.getState('project.files');
                const updatedFiles = files.map(file => 
                    file.id === data.fileId ? { ...file, ...data.updates } : file
                );
                this.appState.setState({
                    project: { ...this.appState.getState('project'), files: updatedFiles }
                });
                break;
                
            case 'log_update':
                const currentLogs = this.appState.getState('project.logs') || [];
                this.appState.setState({
                    project: { 
                        ...this.appState.getState('project'), 
                        logs: [...currentLogs, data.log] 
                    }
                });
                break;
        }
    }
    
    // API Methods
    async generateProject(request) {
        try {
            this.appState.setState({ isGenerating: true });
            
            const response = await this.request('/api/generate', {
                method: 'POST',
                body: JSON.stringify(request)
            });
            
            return response;
        } catch (error) {
            console.error('Generation failed:', error);
            throw error;
        } finally {
            this.appState.setState({ isGenerating: false });
        }
    }
    
    async checkApiStatus(provider, apiKey) {
        try {
            const response = await this.request('/api/check-status', {
                method: 'POST',
                body: JSON.stringify({ provider, apiKey })
            });
            
            this.appState.setState({
                apiStatus: new Map([[provider, response.status]])
            });
            
            return response;
        } catch (error) {
            this.appState.setState({
                apiStatus: new Map([[provider, 'error']])
            });
            throw error;
        }
    }
    
    // Utility
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// =================================================================
// NOTIFICATION SYSTEM
// =================================================================

class NotificationManager {
    constructor(appState) {
        this.appState = appState;
        this.container = null;
        this.init();
    }
    
    init() {
        this.createContainer();
        this.appState.subscribe('stateChange', (newState, oldState) => {
            if (newState.notifications !== oldState.notifications) {
                this.render();
            }
        });
    }
    
    createContainer() {
        this.container = document.createElement('div');
        this.container.className = 'notification-container';
        this.container.style.cssText = `
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            max-width: 400px;
        `;
        document.body.appendChild(this.container);
    }
    
    show(options) {
        const id = `notification-${Date.now()}-${Math.random()}`;
        const notification = {
            id,
            type: options.type || 'info',
            title: options.title || '',
            message: options.message || '',
            actions: options.actions || [],
            persistent: options.persistent || false,
            autoClose: options.autoClose !== false ? (options.autoClose || 5000) : false,
            timestamp: Date.now()
        };
        
        const notifications = this.appState.getState('notifications');
        notifications.set(id, notification);
        this.appState.setState({ notifications }, { persist: false });
        
        // Auto close
        if (notification.autoClose) {
            setTimeout(() => this.close(id), notification.autoClose);
        }
        
        return id;
    }
    
    close(id) {
        const notifications = this.appState.getState('notifications');
        notifications.delete(id);
        this.appState.setState({ notifications }, { persist: false });
    }
    
    render() {
        const notifications = this.appState.getState('notifications');
        
        this.container.innerHTML = '';
        
        for (const [id, notification] of notifications) {
            const element = this.createNotificationElement(notification);
            this.container.appendChild(element);
        }
    }
    
    createNotificationElement(notification) {
        const element = document.createElement('div');
        element.className = `notification notification-${notification.type}`;
        
        element.innerHTML = `
            <div class="notification-header">
                <h4 class="notification-title">${notification.title}</h4>
                <button class="notification-close" onclick="app.notifications.close('${notification.id}')">×</button>
            </div>
            <p class="notification-message">${notification.message}</p>
            ${notification.actions.length > 0 ? `
                <div class="notification-actions">
                    ${notification.actions.map((action, index) => `
                        <button class="btn ${action.primary ? 'btn-primary' : 'btn-secondary'}" 
                                onclick="(${action.action.toString()})(); app.notifications.close('${notification.id}')">
                            ${action.text}
                        </button>
                    `).join('')}
                </div>
            ` : ''}
        `;
        
        // Trigger animation
        setTimeout(() => element.classList.add('show'), 10);
        
        return element;
    }
}

// =================================================================
// UI COMPONENT SYSTEM
// =================================================================

class UIComponents {
    constructor(appState) {
        this.appState = appState;
    }
    
    // Create skeleton loading state
    createSkeleton(config = {}) {
        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton';
        
        if (config.type === 'text') {
            skeleton.className += ' skeleton-text';
        } else if (config.type === 'title') {
            skeleton.className += ' skeleton-title';
        }
        
        if (config.height) {
            skeleton.style.height = config.height;
        }
        
        if (config.width) {
            skeleton.style.width = config.width;
        }
        
        return skeleton;
    }
    
    // Create loading button state
    setButtonLoading(button, loading = true) {
        if (loading) {
            button.classList.add('btn-loading');
            button.disabled = true;
        } else {
            button.classList.remove('btn-loading');
            button.disabled = false;
        }
    }
    
    // Create error boundary
    createErrorBoundary(content, fallback = null) {
        try {
            return content;
        } catch (error) {
            console.error('UI Error:', error);
            return fallback || this.createErrorState(error.message);
        }
    }
    
    createErrorState(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-state p-6 text-center';
        errorElement.innerHTML = `
            <div class="text-error mb-4">❌</div>
            <h3 class="text-lg font-medium mb-2">خطا در بارگذاری</h3>
            <p class="text-muted text-sm">${message}</p>
            <button class="btn btn-secondary mt-4" onclick="location.reload()">
                تلاش مجدد
            </button>
        `;
        return errorElement;
    }
}

// =================================================================
// PERFORMANCE MONITOR
// =================================================================

class PerformanceMonitor {
    constructor(appState) {
        this.appState = appState;
        this.metrics = new Map();
        this.init();
    }
    
    init() {
        // Monitor page load
        window.addEventListener('load', () => {
            this.measurePageLoad();
        });
        
        // Monitor API calls
        this.monitorFetchRequests();
        
        // Monitor memory usage
        if ('memory' in performance) {
            setInterval(() => this.measureMemory(), 30000);
        }
    }
    
    measurePageLoad() {
        try {
            const navigation = performance.getEntriesByType('navigation')[0];
            if (navigation) {
                const loadTime = navigation.loadEventEnd - navigation.loadEventStart;
                const domContentLoaded = navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart;
                
                this.metrics.set('pageLoad', {
                    loadTime,
                    domContentLoaded,
                    timestamp: Date.now()
                });
                
                console.log(`⚡ Page loaded in ${loadTime.toFixed(2)}ms`);
                
                if (loadTime > 3000) {
                    app.notifications.show({
                        type: 'warning',
                        title: 'بارگذاری کند',
                        message: 'صفحه کندتر از حد معمول بارگذاری شد.',
                        autoClose: 4000
                    });
                }
            }
        } catch (error) {
            console.warn('Performance measurement failed:', error);
        }
    }
    
    monitorFetchRequests() {
        const originalFetch = window.fetch;
        
        window.fetch = async (...args) => {
            const startTime = performance.now();
            
            try {
                const response = await originalFetch(...args);
                const endTime = performance.now();
                const duration = endTime - startTime;
                
                this.metrics.set(`api_${Date.now()}`, {
                    url: args[0],
                    duration,
                    status: response.status,
                    timestamp: Date.now()
                });
                
                return response;
            } catch (error) {
                const endTime = performance.now();
                const duration = endTime - startTime;
                
                this.metrics.set(`api_error_${Date.now()}`, {
                    url: args[0],
                    duration,
                    error: error.message,
                    timestamp: Date.now()
                });
                
                throw error;
            }
        };
    }
    
    measureMemory() {
        if ('memory' in performance) {
            const memory = performance.memory;
            this.metrics.set('memory', {
                used: memory.usedJSHeapSize,
                total: memory.totalJSHeapSize,
                limit: memory.jsHeapSizeLimit,
                timestamp: Date.now()
            });
            
            // Warning if memory usage is high
            const usagePercent = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100;
            if (usagePercent > 80) {
                console.warn(`🚨 High memory usage: ${usagePercent.toFixed(1)}%`);
            }
        }
    }
    
    getMetrics() {
        return Object.fromEntries(this.metrics);
    }
}

// =================================================================
// MAIN APPLICATION CLASS
// =================================================================

class AIGeneratorApp {
    constructor() {
        this.state = new AppState();
        this.api = new ApiService(this.state);
        this.notifications = new NotificationManager(this.state);
        this.ui = new UIComponents(this.state);
        this.performance = new PerformanceMonitor(this.state);
        
        this.init();
    }
    
    async init() {
        try {
            // Initialize UI
            this.setupEventListeners();
            this.setupFormHandlers();
            
            // Check API connections
            await this.checkInitialConnections();
            
            // Show ready notification
            this.notifications.show({
                type: 'success',
                title: 'سیستم آماده',
                message: 'سیستم هوش مصنوعی با موفقیت بارگذاری شد.',
                autoClose: 3000
            });
            
        } catch (error) {
            console.error('App initialization failed:', error);
            this.notifications.show({
                type: 'error',
                title: 'خطا در بارگذاری',
                message: 'مشکلی در بارگذاری سیستم به وجود آمد.',
                persistent: true,
                actions: [
                    { text: 'تلاش مجدد', action: () => location.reload(), primary: true }
                ]
            });
        }
    }
    
    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('[data-tab]').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(tab.dataset.tab);
            });
        });
        
        // Connection monitoring
        this.state.subscribe('connection', ({ online }) => {
            if (online) {
                this.notifications.show({
                    type: 'success',
                    title: 'اتصال برقرار',
                    message: 'اتصال اینترنت دوباره برقرار شد.',
                    autoClose: 3000
                });
            } else {
                this.notifications.show({
                    type: 'warning',
                    title: 'قطع اتصال',
                    message: 'اتصال اینترنت قطع شده است.',
                    persistent: true,
                    actions: [
                        { text: 'تلاش مجدد', action: () => location.reload(), primary: true }
                    ]
                });
            }
        });
    }
    
    setupFormHandlers() {
        const form = document.getElementById('projectForm');
        if (form) {
            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleProjectGeneration(e.target);
            });
        }
    }
    
    async handleProjectGeneration(form) {
        try {
            const formData = new FormData(form);
            const request = {
                name: formData.get('projectName') || 'پروژه جدید',
                description: formData.get('description'),
                projectType: formData.get('projectType'),
                languages: [formData.get('language') || 'python'],
                complexity: formData.get('complexity') || 'medium'
            };
            
            // Show loading state
            const submitButton = form.querySelector('button[type="submit"]');
            this.ui.setButtonLoading(submitButton, true);
            
            this.notifications.show({
                type: 'info',
                title: 'شروع تولید',
                message: 'پروژه در حال تولید است...',
                persistent: true
            });
            
            // Generate project
            const result = await this.api.generateProject(request);
            
            // Update state
            this.state.setState({
                project: {
                    ...this.state.getState('project'),
                    files: result.files || [],
                    config: result.config
                }
            });
            
            this.notifications.show({
                type: 'success',
                title: 'تولید موفق',
                message: `پروژه با ${result.files?.length || 0} فایل تولید شد.`,
                autoClose: 5000,
                actions: [
                    { text: 'مشاهده فایل‌ها', action: () => this.switchTab('files'), primary: true }
                ]
            });
            
        } catch (error) {
            console.error('Project generation failed:', error);
            this.notifications.show({
                type: 'error',
                title: 'خطا در تولید',
                message: error.message || 'خطایی در تولید پروژه رخ داد.',
                autoClose: 5000
            });
        } finally {
            const submitButton = form.querySelector('button[type="submit"]');
            this.ui.setButtonLoading(submitButton, false);
        }
    }
    
    switchTab(tabName) {
        this.state.setState({ currentTab: tabName });
        
        // Update UI
        document.querySelectorAll('[data-tab]').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        
        document.querySelectorAll('[data-tab-content]').forEach(content => {
            content.classList.toggle('active', content.dataset.tabContent === tabName);
        });
    }
    
    async checkInitialConnections() {
        const apiKeys = this.state.getState('apiKeys');
        const promises = [];
        
        for (const [provider, apiKey] of apiKeys) {
            promises.push(
                this.api.checkApiStatus(provider, apiKey).catch(error => {
                    console.warn(`${provider} API check failed:`, error);
                })
            );
        }
        
        await Promise.allSettled(promises);
    }
}

// =================================================================
// INITIALIZATION
// =================================================================

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new AIGeneratorApp();
    });
} else {
    window.app = new AIGeneratorApp();
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AIGeneratorApp, AppState, ApiService };
}