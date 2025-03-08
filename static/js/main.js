/**
 * 主要初始化脚本
 */

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化身份验证
    Auth.init();
    
    // 初始化配置管理
    Config.init();
    
    // 如果已经通过身份验证，则加载配置数据
    if (Auth.getCurrentApiKey()) {
        Config.load();
    }
});