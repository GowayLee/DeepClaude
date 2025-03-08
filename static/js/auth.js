/**
 * 身份验证相关功能
 */

// API 基础 URL
const API_BASE_URL = window.location.origin;

// 本地存储键名
const API_KEY_STORAGE_KEY = 'deepclaude_api_key';

// 页面元素
const authPage = document.getElementById('auth-page');
const configPage = document.getElementById('config-page');
const authForm = document.getElementById('auth-form');
const apiKeyInput = document.getElementById('api-key');
const authError = document.getElementById('auth-error');
const logoutBtn = document.getElementById('logout-btn');

/**
 * 初始化身份验证
 */
function initAuth() {
    // 检查本地存储中是否有 API Key
    const storedApiKey = localStorage.getItem(API_KEY_STORAGE_KEY);
    
    if (storedApiKey) {
        // 验证存储的 API Key
        verifyApiKey(storedApiKey)
            .then(isValid => {
                if (isValid) {
                    showConfigPage();
                } else {
                    showAuthPage();
                }
            })
            .catch(() => {
                showAuthPage();
            });
    } else {
        showAuthPage();
    }

    // 绑定表单提交事件
    authForm.addEventListener('submit', handleAuthFormSubmit);
    
    // 绑定退出按钮事件
    logoutBtn.addEventListener('click', handleLogout);
}

/**
 * 处理身份验证表单提交
 * @param {Event} event - 表单提交事件
 */
async function handleAuthFormSubmit(event) {
    event.preventDefault();
    
    const apiKey = apiKeyInput.value.trim();
    
    if (!apiKey) {
        showAuthError('请输入 API Key');
        return;
    }
    
    try {
        const isValid = await verifyApiKey(apiKey);
        
        if (isValid) {
            // 存储 API Key 到本地存储
            localStorage.setItem(API_KEY_STORAGE_KEY, apiKey);
            
            // 显示配置页面
            showConfigPage();
        } else {
            showAuthError('API Key 无效');
        }
    } catch (error) {
        showAuthError('验证过程中发生错误，请重试');
        console.error('验证 API Key 时发生错误:', error);
    }
}

/**
 * 处理退出操作
 */
function handleLogout() {
    // 清除本地存储中的 API Key
    localStorage.removeItem(API_KEY_STORAGE_KEY);
    
    // 显示授权页面
    showAuthPage();
    
    // 清空输入框
    apiKeyInput.value = '';
}

/**
 * 验证 API Key
 * @param {string} apiKey - 要验证的 API Key
 * @returns {Promise<boolean>} - 验证结果
 */
async function verifyApiKey(apiKey) {
    try {
        const response = await fetch(`${API_BASE_URL}/v1/config`, {
            headers: {
                'Authorization': `Bearer ${apiKey}`
            }
        });
        
        return response.ok;
    } catch (error) {
        console.error('验证 API Key 时发生错误:', error);
        return false;
    }
}

/**
 * 显示授权页面
 */
function showAuthPage() {
    authPage.classList.remove('d-none');
    configPage.classList.add('d-none');
    authError.classList.add('d-none');
}

/**
 * 显示配置页面
 */
function showConfigPage() {
    authPage.classList.add('d-none');
    configPage.classList.remove('d-none');
    
    // 加载配置数据
    if (window.Config && typeof window.Config.load === 'function') {
        window.Config.load();
    }
}

/**
 * 显示授权错误信息
 * @param {string} message - 错误信息
 */
function showAuthError(message) {
    authError.textContent = message;
    authError.classList.remove('d-none');
}

/**
 * 获取当前 API Key
 * @returns {string|null} - 当前 API Key 或 null
 */
function getCurrentApiKey() {
    return localStorage.getItem(API_KEY_STORAGE_KEY);
}

// 导出函数和变量
window.Auth = {
    init: initAuth,
    getCurrentApiKey,
    API_BASE_URL
};
