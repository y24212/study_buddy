// c:\Users\Lenovo\PycharmProjects\study_buddy\static\js\pomodoro.js
class Pomodoro {
    constructor() {
        this.focusDuration = 25;
        this.breakDuration = 5;
        this.currentTime = this.focusDuration * 60;
        this.isRunning = false;
        this.isBreak = false;
        this.timer = null;
        this.startTime = null;
        this.taskId = null;
        this.audioContext = null;
        this.whiteNoiseSource = null;

        this.initElements();
        this.bindEvents();
        this.updateDisplay();
    }

    initElements() {
        this.timerDisplay = document.getElementById('timer-display');
        this.startBtn = document.getElementById('start-btn');
        this.pauseBtn = document.getElementById('pause-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.taskSelect = document.getElementById('task-select');
        this.whiteNoiseBtn = document.getElementById('white-noise-btn');
        this.noiseSelect = document.getElementById('noise-select');
        this.interruptModal = document.getElementById('interrupt-modal');
        this.interruptReason = document.getElementById('interrupt-reason');
        this.confirmInterruptBtn = document.getElementById('confirm-interrupt');

        this.focusInput = document.getElementById('focus-duration');
        this.breakInput = document.getElementById('break-duration');
    }

    bindEvents() {
        this.startBtn.addEventListener('click', () => this.start());
        this.pauseBtn.addEventListener('click', () => this.pause());
        this.stopBtn.addEventListener('click', () => this.showInterruptModal());

        this.whiteNoiseBtn.addEventListener('click', () => this.toggleWhiteNoise());
        this.confirmInterruptBtn.addEventListener('click', () => this.handleInterrupt());

        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.isRunning) {
                this.pause();
            }
        });

        this.focusInput.addEventListener('change', (e) => {
            this.focusDuration = parseInt(e.target.value) || 25;
            if (!this.isRunning && !this.isBreak) {
                this.currentTime = this.focusDuration * 60;
                this.updateDisplay();
            }
        });

        this.breakInput.addEventListener('change', (e) => {
            this.breakDuration = parseInt(e.target.value) || 5;
            if (!this.isRunning && this.isBreak) {
                this.currentTime = this.breakDuration * 60;
                this.updateDisplay();
            }
        });
    }

    start() {
        if (this.isRunning) return;

        this.isRunning = true;
        this.startTime = Date.now();
        this.taskId = this.taskSelect.value || null;

        this.startBtn.style.display = 'none';
        this.pauseBtn.style.display = 'inline-block';

        this.timer = setInterval(() => {
            this.currentTime--;

            if (this.currentTime <= 0) {
                this.completePomodoro();
            }

            this.updateDisplay();
        }, 1000);
    }

    pause() {
        if (!this.isRunning) return;

        this.isRunning = false;
        clearInterval(this.timer);

        this.startBtn.style.display = 'inline-block';
        this.pauseBtn.style.display = 'none';
    }

    stop() {
        this.isRunning = false;
        clearInterval(this.timer);

        this.startBtn.style.display = 'inline-block';
        this.pauseBtn.style.display = 'none';

        this.currentTime = (this.isBreak ? this.breakDuration : this.focusDuration) * 60;
        this.updateDisplay();
    }

    showInterruptModal() {
        if (!this.isRunning) {
            this.stop();
            return;
        }

        this.pause();
        const modal = new bootstrap.Modal(this.interruptModal);
        modal.show();
    }

    handleInterrupt() {
        this.interruptModal.querySelector('.btn-close').click();

        this.savePomodoro(2, this.interruptReason.value);

        this.stop();
        this.interruptReason.value = '';
    }

    completePomodoro() {
        this.isRunning = false;
        clearInterval(this.timer);

        this.savePomodoro(1, null);

        if (this.isBreak) {
            this.isBreak = false;
            this.currentTime = this.focusDuration * 60;
        } else {
            this.isBreak = true;
            this.currentTime = this.breakDuration * 60;
        }

        this.startBtn.style.display = 'inline-block';
        this.pauseBtn.style.display = 'none';

        this.updateDisplay();

        this.playNotificationSound();

        const countEl = document.getElementById('today-count');
        countEl.textContent = parseInt(countEl.textContent) + 1;
    }

    savePomodoro(status, reason) {
        if (!this.startTime) return;

        const data = {
            task_id: this.taskId,
            duration: this.isBreak ? this.breakDuration : this.focusDuration,
            start_time: this.startTime,
            end_time: Date.now(),
            status: status,
            interrupt_reason: reason
        };

        fetch('/save_pomodoro', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(data)
        });
    }

    updateDisplay() {
        const minutes = Math.floor(this.currentTime / 60);
        const seconds = this.currentTime % 60;

        this.timerDisplay.textContent =
            `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        const title = this.isBreak ? '休息时间' : '专注时间';
        document.getElementById('timer-title').textContent = title;
    }

    toggleWhiteNoise() {
        if (this.whiteNoiseSource) {
            this.whiteNoiseSource.pause();
            this.whiteNoiseSource = null;
            this.whiteNoiseBtn.classList.remove('active');
            return;
        }

        const noiseType = this.noiseSelect.value;
        this.playWhiteNoise(noiseType);
        this.whiteNoiseBtn.classList.add('active');
    }

    playWhiteNoise(type) {
        const audioFiles = {
            rain: '/static/assets/rain.mp3',
            library: '/static/assets/library.mp3',
            cafe: '/static/assets/cafe.mp3'
        };

        this.whiteNoiseSource = new Audio(audioFiles[type]);
        this.whiteNoiseSource.loop = true;
        this.whiteNoiseSource.volume = 0.3;
        this.whiteNoiseSource.play();
    }

    playNotificationSound() {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.frequency.value = 800;
        oscillator.type = 'sine';

        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    }

    getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]').content;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new Pomodoro();
});