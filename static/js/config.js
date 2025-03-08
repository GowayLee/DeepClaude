/**
 * 配置管理相关功能
 */

// 全局配置数据
let configData = {
    reasoner_models: {},
    target_models: {},
    composite_models: {},
    proxy: {
        proxy_open: false,
        proxy_address: ""
    },
    system: {
        allow_origins: ["*"],
        log_level: "INFO",
        api_key: "123456"
    }
};

// 模态框和选项元素
const addModelModal = new bootstrap.Modal(document.getElementById('add-model-modal'));
const confirmDeleteModal = new bootstrap.Modal(document.getElementById('confirm-delete-modal'));
const deleteModelNameSpan = document.getElementById('delete-model-name');
const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
const addModelForm = document.getElementById('add-model-form');
const addModelFields = document.getElementById('add-model-fields');
const confirmAddModelBtn = document.getElementById('confirm-add-model');
const addModelTitle = document.getElementById('add-model-title');

// 模型容器
const reasonerModelsContainer = document.getElementById('reasoner-models-container');
const targetModelsContainer = document.getElementById('target-models-container');
const compositeModelsContainer = document.getElementById('composite-models-container');

// 添加模型按钮
const addReasonerModelBtn = document.getElementById('add-reasoner-model-btn');
const addTargetModelBtn = document.getElementById('add-target-model-btn');
const addCompositeModelBtn = document.getElementById('add-composite-model-btn');

// 保存按钮
const saveAllBtn = document.getElementById('save-all-btn');
const saveProxyBtn = document.getElementById('save-proxy-btn');
const saveSystemBtn = document.getElementById('save-system-btn');

// 代理设置
const proxyOpenSwitch = document.getElementById('proxy-open');
const proxyAddressInput = document.getElementById('proxy-address');

// 系统设置
const allowOriginsContainer = document.getElementById('allow-origins-container');
const addOriginBtn = document.getElementById('add-origin-btn');
const logLevelSelect = document.getElementById('log-level');
const systemApiKeyInput = document.getElementById('system-api-key');

/**
 * 初始化配置管理
 */
function initConfig() {
    // 绑定添加模型按钮事件
    addReasonerModelBtn.addEventListener('click', () => showAddModelModal('reasoner'));
    addTargetModelBtn.addEventListener('click', () => showAddModelModal('target'));
    addCompositeModelBtn.addEventListener('click', () => showAddModelModal('composite'));
    
    // 绑定保存按钮事件
    saveAllBtn.addEventListener('click', saveAllConfigurations);
    saveProxyBtn.addEventListener('click', saveProxySettings);
    saveSystemBtn.addEventListener('click', saveSystemSettings);
    
    // 绑定添加源按钮事件
    addOriginBtn.addEventListener('click', addAllowOriginInput);
    
    // 绑定确认添加模型按钮事件
    confirmAddModelBtn.addEventListener('click', handleAddModel);
    
    // 绑定确认删除按钮事件
    confirmDeleteBtn.addEventListener('click', handleDeleteModel);
    
    // 初始化 Bootstrap 标签页
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            const targetId = this.getAttribute('href').substring(1);
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('show', 'active');
            });
            document.getElementById(targetId).classList.add('show', 'active');
        });
    });
}

/**
 * 加载配置数据
 */
async function loadConfigData() {
    try {
        showToast('正在加载配置数据...', 'info');
        
        const apiKey = Auth.getCurrentApiKey();
        const response = await fetch(`${Auth.API_BASE_URL}/v1/config`, {
            headers: {
                'Authorization': `Bearer ${apiKey}`
            }
        });
        
        if (!response.ok) {
            throw new Error('加载配置数据失败');
        }
        
        configData = await response.json();
        
        // 确保系统设置存在
        if (!configData.system) {
            configData.system = {
                allow_origins: ["*"],
                log_level: "INFO",
                api_key: "123456"
            };
        }
        
        // 渲染模型
        renderModels();
        
        // 渲染代理设置
        renderProxySettings();
        
        // 渲染系统设置
        renderSystemSettings();
        
        showToast('配置数据加载成功', 'success');
    } catch (error) {
        console.error('加载配置数据时发生错误:', error);
        showToast('加载配置数据失败: ' + error.message, 'danger');
    }
}

/**
 * 渲染所有模型
 */
function renderModels() {
    // 清空容器
    reasonerModelsContainer.innerHTML = '';
    targetModelsContainer.innerHTML = '';
    compositeModelsContainer.innerHTML = '';
    
    // 渲染推理模型
    Object.entries(configData.reasoner_models || {}).forEach(([name, config]) => {
        renderReasonerModel(name, config);
    });
    
    // 渲染目标模型
    Object.entries(configData.target_models || {}).forEach(([name, config]) => {
        renderTargetModel(name, config);
    });
    
    // 渲染组合模型
    Object.entries(configData.composite_models || {}).forEach(([name, config]) => {
        renderCompositeModel(name, config);
    });
}

/**
 * 渲染推理模型
 * @param {string} name - 模型名称
 * @param {Object} config - 模型配置
 */
function renderReasonerModel(name, config) {
    const template = document.getElementById('reasoner-model-template');
    const clone = document.importNode(template.content, true);
    
    // 设置模型名称
    clone.querySelector('.model-name').textContent = name;
    
    // 设置表单值
    const form = clone.querySelector('.model-form');
    form.querySelector('.model-id').value = config.model_id || '';
    form.querySelector('.api-key').value = config.api_key || '';
    form.querySelector('.api-base-url').value = config.api_base_url || '';
    form.querySelector('.api-request-address').value = config.api_request_address || '';
    form.querySelector('.is-origin-reasoning').checked = config.is_origin_reasoning || false;
    form.querySelector('.is-valid').checked = config.is_valid || false;
    
    // 绑定保存按钮事件
    form.querySelector('.save-model-btn').addEventListener('click', () => {
        saveReasonerModel(name, form);
    });
    
    // 绑定编辑按钮事件
    clone.querySelector('.edit-model-btn').addEventListener('click', () => {
        toggleFormEditable(form, true);
    });
    
    // 绑定删除按钮事件
    clone.querySelector('.delete-model-btn').addEventListener('click', () => {
        showDeleteConfirmation('reasoner', name);
    });
    
    // 默认禁用表单编辑
    toggleFormEditable(form, false);
    
    // 添加到容器
    reasonerModelsContainer.appendChild(clone);
}

/**
 * 渲染目标模型
 * @param {string} name - 模型名称
 * @param {Object} config - 模型配置
 */
function renderTargetModel(name, config) {
    const template = document.getElementById('target-model-template');
    const clone = document.importNode(template.content, true);
    
    // 设置模型名称
    clone.querySelector('.model-name').textContent = name;
    
    // 设置表单值
    const form = clone.querySelector('.model-form');
    form.querySelector('.model-id').value = config.model_id || '';
    form.querySelector('.api-key').value = config.api_key || '';
    form.querySelector('.api-base-url').value = config.api_base_url || '';
    form.querySelector('.api-request-address').value = config.api_request_address || '';
    form.querySelector('.model-format').value = config.model_format || 'openai';
    form.querySelector('.is-valid').checked = config.is_valid || false;
    
    // 绑定保存按钮事件
    form.querySelector('.save-model-btn').addEventListener('click', () => {
        saveTargetModel(name, form);
    });
    
    // 绑定编辑按钮事件
    clone.querySelector('.edit-model-btn').addEventListener('click', () => {
        toggleFormEditable(form, true);
    });
    
    // 绑定删除按钮事件
    clone.querySelector('.delete-model-btn').addEventListener('click', () => {
        showDeleteConfirmation('target', name);
    });
    
    // 默认禁用表单编辑
    toggleFormEditable(form, false);
    
    // 添加到容器
    targetModelsContainer.appendChild(clone);
}

/**
 * 渲染组合模型
 * @param {string} name - 模型名称
 * @param {Object} config - 模型配置
 */
function renderCompositeModel(name, config) {
    const template = document.getElementById('composite-model-template');
    const clone = document.importNode(template.content, true);
    
    // 设置模型名称
    clone.querySelector('.model-name').textContent = name;
    
    // 设置表单值
    const form = clone.querySelector('.model-form');
    form.querySelector('.model-id').value = config.model_id || '';
    form.querySelector('.is-valid').checked = config.is_valid || false;
    
    // 填充推理模型选项
    const reasonerSelect = form.querySelector('.reasoner-model-select');
    reasonerSelect.innerHTML = '';
    Object.keys(configData.reasoner_models || {}).forEach(modelName => {
        const option = document.createElement('option');
        option.value = modelName;
        option.textContent = modelName;
        reasonerSelect.appendChild(option);
    });
    
    // 填充目标模型选项
    const targetSelect = form.querySelector('.target-model-select');
    targetSelect.innerHTML = '';
    Object.keys(configData.target_models || {}).forEach(modelName => {
        const option = document.createElement('option');
        option.value = modelName;
        option.textContent = modelName;
        targetSelect.appendChild(option);
    });
    
    // 设置选中的模型
    reasonerSelect.value = config.reasoner_models || '';
    targetSelect.value = config.target_models || '';
    
    // 绑定保存按钮事件
    form.querySelector('.save-model-btn').addEventListener('click', () => {
        saveCompositeModel(name, form);
    });
    
    // 绑定编辑按钮事件
    clone.querySelector('.edit-model-btn').addEventListener('click', () => {
        toggleFormEditable(form, true);
    });
    
    // 绑定删除按钮事件
    clone.querySelector('.delete-model-btn').addEventListener('click', () => {
        showDeleteConfirmation('composite', name);
    });
    
    // 默认禁用表单编辑
    toggleFormEditable(form, false);
    
    // 添加到容器
    compositeModelsContainer.appendChild(clone);
}

/**
 * 渲染代理设置
 */
function renderProxySettings() {
    const { proxy_open, proxy_address } = configData.proxy;
    
    proxyOpenSwitch.checked = proxy_open;
    proxyAddressInput.value = proxy_address || '';
}

/**
 * 渲染系统设置
 */
function renderSystemSettings() {
    const { allow_origins, log_level, api_key } = configData.system;
    
    // 清空允许的源容器
    allowOriginsContainer.innerHTML = '';
    
    // 添加允许的源输入框
    if (allow_origins && allow_origins.length > 0) {
        allow_origins.forEach(origin => {
            addAllowOriginInput(origin);
        });
    } else {
        addAllowOriginInput('*');
    }
    
    // 设置日志级别
    logLevelSelect.value = log_level || 'INFO';
    
    // 设置 API Key
    systemApiKeyInput.value = api_key || '123456';
}

/**
 * 切换表单可编辑状态
 * @param {HTMLFormElement} form - 表单元素
 * @param {boolean} editable - 是否可编辑
 */
function toggleFormEditable(form, editable) {
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.disabled = !editable;
    });
    
    const saveBtn = form.querySelector('.save-model-btn');
    saveBtn.style.display = editable ? 'block' : 'none';
}

/**
 * 保存推理模型
 * @param {string} name - 模型名称
 * @param {HTMLFormElement} form - 表单元素
 */
function saveReasonerModel(name, form) {
    const modelConfig = {
        model_id: form.querySelector('.model-id').value,
        api_key: form.querySelector('.api-key').value,
        api_base_url: form.querySelector('.api-base-url').value,
        api_request_address: form.querySelector('.api-request-address').value,
        is_origin_reasoning: form.querySelector('.is-origin-reasoning').checked,
        is_valid: form.querySelector('.is-valid').checked
    };
    
    configData.reasoner_models[name] = modelConfig;
    
    toggleFormEditable(form, false);
    showToast(`推理模型 ${name} 已保存`, 'success');
}

/**
 * 保存目标模型
 * @param {string} name - 模型名称
 * @param {HTMLFormElement} form - 表单元素
 */
function saveTargetModel(name, form) {
    const modelConfig = {
        model_id: form.querySelector('.model-id').value,
        api_key: form.querySelector('.api-key').value,
        api_base_url: form.querySelector('.api-base-url').value,
        api_request_address: form.querySelector('.api-request-address').value,
        model_format: form.querySelector('.model-format').value,
        is_valid: form.querySelector('.is-valid').checked
    };
    
    configData.target_models[name] = modelConfig;
    
    toggleFormEditable(form, false);
    showToast(`目标模型 ${name} 已保存`, 'success');
}

/**
 * 保存组合模型
 * @param {string} name - 模型名称
 * @param {HTMLFormElement} form - 表单元素
 */
function saveCompositeModel(name, form) {
    const modelConfig = {
        model_id: form.querySelector('.model-id').value,
        reasoner_models: form.querySelector('.reasoner-model-select').value,
        target_models: form.querySelector('.target-model-select').value,
        is_valid: form.querySelector('.is-valid').checked
    };
    
    configData.composite_models[name] = modelConfig;
    
    toggleFormEditable(form, false);
    showToast(`组合模型 ${name} 已保存`, 'success');
}

/**
 * 保存代理设置
 */
function saveProxySettings() {
    try {
        configData.proxy.proxy_open = proxyOpenSwitch.checked;
        configData.proxy.proxy_address = proxyAddressInput.value.trim();
        
        saveAllConfigurations();
    } catch (error) {
        console.error('保存代理设置时发生错误:', error);
        showToast('保存代理设置失败: ' + error.message, 'danger');
    }
}

/**
 * 保存系统设置
 */
function saveSystemSettings() {
    try {
        // 获取允许的源
        const originInputs = document.querySelectorAll('.allow-origin');
        const origins = Array.from(originInputs).map(input => input.value.trim()).filter(value => value);
        
        // 获取日志级别
        const logLevel = logLevelSelect.value;
        
        // 获取 API Key
        const apiKey = systemApiKeyInput.value.trim() || '123456';
        
        // 更新配置数据
        configData.system.allow_origins = origins;
        configData.system.log_level = logLevel;
        configData.system.api_key = apiKey;
        
        saveAllConfigurations();
    } catch (error) {
        console.error('保存系统设置时发生错误:', error);
        showToast('保存系统设置失败: ' + error.message, 'danger');
    }
}

/**
 * 保存所有配置
 */
async function saveAllConfigurations() {
    try {
        showToast('正在保存配置...', 'info');
        
        const apiKey = Auth.getCurrentApiKey();
        const response = await fetch(`${Auth.API_BASE_URL}/v1/config`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(configData)
        });
        
        if (!response.ok) {
            throw new Error('保存配置失败');
        }
        
        showToast('所有配置已保存', 'success');
    } catch (error) {
        console.error('保存配置时发生错误:', error);
        showToast('保存配置失败: ' + error.message, 'danger');
    }
}

/**
 * 显示添加模型对话框
 * @param {string} modelType - 模型类型：reasoner, target, composite
 */
function showAddModelModal(modelType) {
    // 设置对话框标题
    let title;
    switch (modelType) {
        case 'reasoner':
            title = '添加推理模型';
            break;
        case 'target':
            title = '添加目标模型';
            break;
        case 'composite':
            title = '添加组合模型';
            break;
    }
    addModelTitle.textContent = title;
    
    // 清空表单
    addModelForm.reset();
    addModelFields.innerHTML = '';
    
    // 存储模型类型
    addModelForm.dataset.modelType = modelType;
    
    // 显示对话框
    addModelModal.show();
}

/**
 * 处理添加模型
 */
function handleAddModel() {
    const modelType = addModelForm.dataset.modelType;
    const modelName = document.getElementById('new-model-name').value.trim();
    
    if (!modelName) {
        showToast('请输入模型名称', 'warning');
        return;
    }
    
    // 检查模型名称是否已存在
    let targetCollection;
    switch (modelType) {
        case 'reasoner':
            targetCollection = configData.reasoner_models;
            break;
        case 'target':
            targetCollection = configData.target_models;
            break;
        case 'composite':
            targetCollection = configData.composite_models;
            break;
    }
    
    if (targetCollection[modelName]) {
        showToast(`模型 ${modelName} 已存在`, 'warning');
        return;
    }
    
    // 创建默认配置
    let defaultConfig;
    switch (modelType) {
        case 'reasoner':
            defaultConfig = {
                model_id: '',
                api_key: '',
                api_base_url: '',
                api_request_address: '',
                is_origin_reasoning: true,
                is_valid: true
            };
            break;
        case 'target':
            defaultConfig = {
                model_id: '',
                api_key: '',
                api_base_url: '',
                api_request_address: '',
                model_format: 'openai',
                is_valid: true
            };
            break;
        case 'composite':
            // 获取第一个可用的推理模型和目标模型
            const firstReasonerModel = Object.keys(configData.reasoner_models || {})[0] || '';
            const firstTargetModel = Object.keys(configData.target_models || {})[0] || '';
            
            defaultConfig = {
                model_id: modelName,
                reasoner_models: firstReasonerModel,
                target_models: firstTargetModel,
                is_valid: true
            };
            break;
    }
    
    // 添加模型
    targetCollection[modelName] = defaultConfig;
    
    // 重新渲染模型
    renderModels();
    
    // 关闭对话框
    addModelModal.hide();
    
    showToast(`模型 ${modelName} 已添加`, 'success');
}

/**
 * 显示删除确认对话框
 * @param {string} modelType - 模型类型：reasoner, target, composite
 * @param {string} modelName - 模型名称
 */
function showDeleteConfirmation(modelType, modelName) {
    deleteModelNameSpan.textContent = modelName;
    
    // 存储模型信息
    confirmDeleteBtn.dataset.modelType = modelType;
    confirmDeleteBtn.dataset.modelName = modelName;
    
    // 绑定确认删除按钮事件
    confirmDeleteBtn.onclick = handleDeleteModel;
    
    // 显示对话框
    confirmDeleteModal.show();
}

/**
 * 处理删除模型
 */
function handleDeleteModel() {
    const modelType = confirmDeleteBtn.dataset.modelType;
    const modelName = confirmDeleteBtn.dataset.modelName;
    
    // 删除模型
    switch (modelType) {
        case 'reasoner':
            delete configData.reasoner_models[modelName];
            break;
        case 'target':
            delete configData.target_models[modelName];
            break;
        case 'composite':
            delete configData.composite_models[modelName];
            break;
    }
    
    // 重新渲染模型
    renderModels();
    
    // 关闭对话框
    confirmDeleteModal.hide();
    
    showToast(`模型 ${modelName} 已删除`, 'success');
}

/**
 * 添加允许的源输入框
 * @param {string} value - 初始值
 */
function addAllowOriginInput(value = '') {
    const inputGroup = document.createElement('div');
    inputGroup.className = 'input-group mb-2';
    
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'form-control allow-origin';
    input.placeholder = '例如: * 或 http://localhost:3000';
    input.value = value;
    
    const button = document.createElement('button');
    button.className = 'btn btn-outline-secondary remove-origin-btn';
    button.type = 'button';
    button.innerHTML = '<i class="bi bi-trash"></i>';
    button.addEventListener('click', () => {
        if (document.querySelectorAll('.allow-origin').length > 1) {
            inputGroup.remove();
        }
    });
    
    inputGroup.appendChild(input);
    inputGroup.appendChild(button);
    
    allowOriginsContainer.appendChild(inputGroup);
}

/**
 * 显示提示框
 * @param {string} message - 提示信息
 * @param {string} type - 提示类型：success, info, warning, danger
 */
function showToast(message, type) {
    const toastContainer = document.getElementById('toast-container');
    
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="3000">
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">提示</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // 自动移除
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// 导出函数和变量
window.Config = {
    init: initConfig,
    load: loadConfigData
};