// c:\Users\Lenovo\PycharmProjects\study_buddy\static\js\schedule-import.js

document.addEventListener('DOMContentLoaded', function() {
    const goBtn = document.getElementById('go-btn');
    const eduUrl = document.getElementById('edu-url');

    goBtn.addEventListener('click', function() {
        const url = eduUrl.value.trim();
        if (url) {
            // 打开教务系统页面
            window.open(url, '_blank');
            
            // 显示提示信息
            alert('请在新打开的教务系统页面中登录并导航到"我的课表"页面，然后返回此页面继续操作。');
        } else {
            alert('请输入教务系统网址');
        }
    });
});