/**
 * 模态框修复工具
 * 确保模态框正确关闭，不留下背景遮罩
 */
document.addEventListener('DOMContentLoaded', function() {
    // 处理已存在的模态框
    setupExistingModals();

    // 监听文档变化，处理动态添加的模态框
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                setupNewModals(mutation.addedNodes);
            }
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });

    // 设置全局关闭事件处理
    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('modal-backdrop')) {
            cleanupModalBackdrops();
        }
    });

    // 处理ESC键关闭模态框
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            cleanupModalBackdrops();
        }
    });

    // 设置已存在的模态框
    function setupExistingModals() {
        document.querySelectorAll('.modal').forEach(function(modal) {
            setupModal(modal);
        });
    }

    // 设置新添加的模态框
    function setupNewModals(nodes) {
        nodes.forEach(function(node) {
            if (node.classList && node.classList.contains('modal')) {
                setupModal(node);
            } else if (node.querySelectorAll) {
                node.querySelectorAll('.modal').forEach(function(modal) {
                    setupModal(modal);
                });
            }
        });
    }

    // 设置单个模态框
    function setupModal(modal) {
        if (modal.dataset.setupDone) return;
        
        // 添加隐藏事件监听器
        modal.addEventListener('hidden.bs.modal', function() {
            setTimeout(cleanupModalBackdrops, 200);
        });

        // 为关闭按钮添加事件
        modal.querySelectorAll('[data-bs-dismiss="modal"], .btn-close').forEach(function(btn) {
            btn.addEventListener('click', function() {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) {
                    modalInstance.hide();
                }
                setTimeout(cleanupModalBackdrops, 200);
            });
        });

        // 标记为已设置
        modal.dataset.setupDone = 'true';
    }

    // 清理模态框背景和相关样式
    function cleanupModalBackdrops() {
        // 移除所有模态框背景
        document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
            backdrop.remove();
        });
        
        // 移除body上的模态框样式
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
    }
}); 