/**
 * 科幻风格下拉框增强脚本
 * 为所有下拉框添加动态特效和交互增强
 */

(function() {
    'use strict';

    // 等待DOM加载完成
    function initSciFiSelects() {
        // 查找所有下拉框
        const selects = document.querySelectorAll('select');

        selects.forEach(select => {
            // 添加科幻风格类
            if (!select.classList.contains('sci-fi-select')) {
                select.classList.add('sci-fi-select');
            }

            // 检查是否已经被包装
            if (select.parentElement.classList.contains('sci-fi-select-wrapper')) {
                return;
            }

            // 创建包装器
            const wrapper = document.createElement('div');
            wrapper.className = 'sci-fi-select-wrapper';

            // 将select包装起来
            select.parentNode.insertBefore(wrapper, select);
            wrapper.appendChild(select);

            // 添加交互事件
            addSelectInteractions(select, wrapper);
        });
    }

    // 添加下拉框交互效果
    function addSelectInteractions(select, wrapper) {
        // 聚焦时添加脉冲效果
        select.addEventListener('focus', function() {
            select.classList.add('pulse');
            wrapper.classList.add('scanning');
        });

        // 失焦时移除脉冲效果
        select.addEventListener('blur', function() {
            select.classList.remove('pulse');
            wrapper.classList.remove('scanning');
        });

        // 改变时添加数据流效果
        select.addEventListener('change', function() {
            select.classList.add('data-flow');

            // 添加成功状态
            select.classList.remove('warning', 'error');
            select.classList.add('success');

            // 2秒后移除特效
            setTimeout(() => {
                select.classList.remove('data-flow', 'success');
            }, 2000);

            // 触发自定义事件
            const event = new CustomEvent('sci-fi-select-change', {
                detail: {
                    value: select.value,
                    text: select.options[select.selectedIndex]?.text
                }
            });
            select.dispatchEvent(event);
        });

        // 鼠标悬停效果
        select.addEventListener('mouseenter', function() {
            if (!select.disabled) {
                wrapper.style.transform = 'translateY(-1px)';
            }
        });

        select.addEventListener('mouseleave', function() {
            wrapper.style.transform = 'translateY(0)';
        });

        // 加载状态检测
        if (select.options.length === 1 &&
            (select.options[0].text.includes('加载') ||
             select.options[0].text.includes('loading'))) {
            select.classList.add('loading');
            wrapper.classList.add('loading');
        }

        // 监听选项变化，移除加载状态
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && select.options.length > 1) {
                    select.classList.remove('loading');
                    wrapper.classList.remove('loading');
                }
            });
        });

        observer.observe(select, { childList: true, subtree: true });
    }

    // 为动态添加的下拉框提供初始化方法
    window.initSciFiSelect = function(selectElement) {
        if (!selectElement) return;

        if (!selectElement.classList.contains('sci-fi-select')) {
            selectElement.classList.add('sci-fi-select');
        }

        if (!selectElement.parentElement.classList.contains('sci-fi-select-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'sci-fi-select-wrapper';
            selectElement.parentNode.insertBefore(wrapper, selectElement);
            wrapper.appendChild(selectElement);
            addSelectInteractions(selectElement, wrapper);
        }
    };

    // 批量初始化
    window.initAllSciFiSelects = function() {
        initSciFiSelects();
    };

    // 页面加载时初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSciFiSelects);
    } else {
        initSciFiSelects();
    }

    // 监听动态添加的下拉框
    const bodyObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) { // 元素节点
                    // 检查是否是select元素
                    if (node.tagName === 'SELECT') {
                        setTimeout(() => initSciFiSelect(node), 100);
                    }
                    // 检查子元素中是否有select
                    const selects = node.querySelectorAll && node.querySelectorAll('select');
                    if (selects && selects.length > 0) {
                        setTimeout(() => {
                            selects.forEach(select => initSciFiSelect(select));
                        }, 100);
                    }
                }
            });
        });
    });

    // 开始观察body的变化
    if (document.body) {
        bodyObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    // 添加键盘导航增强
    document.addEventListener('keydown', function(e) {
        const activeElement = document.activeElement;
        if (activeElement && activeElement.tagName === 'SELECT') {
            // 上下箭头键时添加视觉反馈
            if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
                activeElement.classList.add('pulse');
                setTimeout(() => {
                    activeElement.classList.remove('pulse');
                }, 300);
            }
        }
    });

    // 添加全局样式增强
    function addGlobalEnhancements() {
        // 为所有.filter-group中的select添加特殊样式
        const filterGroups = document.querySelectorAll('.filter-group');
        filterGroups.forEach(group => {
            const select = group.querySelector('select');
            if (select && !select.classList.contains('enhanced')) {
                select.classList.add('enhanced');

                // 添加标签动画
                const label = group.querySelector('label');
                if (label) {
                    label.style.transition = 'all 0.3s ease';
                    select.addEventListener('focus', () => {
                        label.style.color = '#3cebdc';
                        label.style.textShadow = '0 0 10px rgba(60, 235, 220, 0.5)';
                    });
                    select.addEventListener('blur', () => {
                        label.style.color = '';
                        label.style.textShadow = '';
                    });
                }
            }
        });

        // 为behavior-filters中的select添加特殊样式
        const behaviorFilters = document.querySelectorAll('.behavior-filters select');
        behaviorFilters.forEach(select => {
            if (!select.classList.contains('enhanced')) {
                select.classList.add('enhanced');
            }
        });
    }

    // 延迟执行全局增强
    setTimeout(addGlobalEnhancements, 500);

    // 导出到全局
    window.SciFiSelect = {
        init: initSciFiSelects,
        initSingle: window.initSciFiSelect,
        enhance: addGlobalEnhancements
    };

    console.log('🚀 科幻风格下拉框已初始化');
})();
