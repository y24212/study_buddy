// c:\Users\Lenovo\PycharmProjects\study_buddy\static\js\drag-drop.js

class TaskDragDrop {
    constructor() {
        this.draggedTask = null;
        this.init();
    }
    
    init() {
        // 为所有任务卡片添加拖拽事件
        document.addEventListener('dragstart', (e) => this.handleDragStart(e));
        document.addEventListener('dragend', (e) => this.handleDragEnd(e));
        
        // 为所有象限添加放置事件
        const quadrants = document.querySelectorAll('.quadrant-card');
        quadrants.forEach(quadrant => {
            quadrant.addEventListener('dragover', (e) => this.handleDragOver(e));
            quadrant.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            quadrant.addEventListener('drop', (e) => this.handleDrop(e));
        });
    }
    
    handleDragStart(e) {
        if (e.target.classList.contains('task-card')) {
            this.draggedTask = e.target;
            e.target.classList.add('dragging');
            
            // 设置拖拽数据
            e.dataTransfer.setData('text/plain', e.target.dataset.taskId);
            e.dataTransfer.effectAllowed = 'move';
        }
    }
    
    handleDragEnd(e) {
        if (e.target.classList.contains('task-card')) {
            e.target.classList.remove('dragging');
            this.draggedTask = null;
        }
        
        // 移除所有拖拽覆盖样式
        document.querySelectorAll('.quadrant-card').forEach(quadrant => {
            quadrant.classList.remove('drag-over');
        });
    }
    
    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        
        const quadrant = e.currentTarget;
        quadrant.classList.add('drag-over');
    }
    
    handleDragLeave(e) {
        const quadrant = e.currentTarget;
        // 检查鼠标是否真的离开了象限
        const rect = quadrant.getBoundingClientRect();
        const x = e.clientX;
        const y = e.clientY;
        
        if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
            quadrant.classList.remove('drag-over');
        }
    }
    
    handleDrop(e) {
        e.preventDefault();
        
        const quadrant = e.currentTarget;
        quadrant.classList.remove('drag-over');
        
        if (!this.draggedTask) return;
        
        const taskId = e.dataTransfer.getData('text/plain');
        const priority = quadrant.dataset.priority;
        
        // 发送更新请求
        this.updateTaskPriority(taskId, priority);
        
        // 将任务卡片添加到新象限
        const taskContainer = quadrant.querySelector('.task-list');
        if (taskContainer) {
            taskContainer.appendChild(this.draggedTask);
        }
        
        this.draggedTask = null;
    }
    
    updateTaskPriority(taskId, priority) {
        fetch('/update_task_priority', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                task_id: taskId,
                priority: parseInt(priority)
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert('更新失败');
            }
        });
    }
    
    getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]').content;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new TaskDragDrop();
});