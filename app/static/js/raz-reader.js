// RAZ Reader 前端逻辑
// 依赖: pdf.js, Web Speech API, WebRTC

// 全局状态
let currentPage = 1;
let currentSentenceIndex = 0;
let pdfDoc = null;
let audio = null;
let audioCheckInterval = null;
let isPlaying = false;
let isRecording = false;
let recordingSeconds = 0;
let recordingTimer = null;
let mediaRecorder = null;
let audioChunks = [];

// DOM 元素引用
let pdfCanvas, pdfContainer, pageIndicator, loadingEl;
let sentenceTextEl, playBtn, recordBtn, recordTimeEl;
let floatToolbar, toast, toastScore, toastSentence;
let prevBtn, nextBtn;

// 初始化
function init() {
    // 获取 DOM 元素
    pdfCanvas = document.getElementById('pdf-canvas');
    pdfContainer = document.getElementById('pdfContainer');
    pageIndicator = document.getElementById('pageIndicator');
    loadingEl = document.getElementById('loading');
    sentenceTextEl = document.getElementById('sentenceText');
    playBtn = document.getElementById('playBtn');
    recordBtn = document.getElementById('recordBtn');
    recordTimeEl = document.getElementById('recordTime');
    floatToolbar = document.getElementById('floatToolbar');
    toast = document.getElementById('toast');
    toastScore = document.getElementById('toastScore');
    toastSentence = document.getElementById('toastSentence');
    prevBtn = document.getElementById('prevBtn');
    nextBtn = document.getElementById('nextBtn');

    // 配置 PDF.js worker
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

    // 初始化音频（如果有）
    if (bookData.audio) {
        audio = new Audio(bookData.audio);
    }

    // 绑定事件
    bindEvents();

    // 加载 PDF
    loadPDF();
}

// 绑定事件
function bindEvents() {
    // 播放按钮
    playBtn?.addEventListener('click', togglePlay);

    // 录音按钮
    recordBtn?.addEventListener('click', toggleRecord);

    // 翻页按钮
    prevBtn?.addEventListener('click', prevPage);
    nextBtn?.addEventListener('click', nextPage);

    // 键盘翻页
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') prevPage();
        if (e.key === 'ArrowRight') nextPage();
    });

    // 滑动翻页
    bindSwipeEvents();

    // 可拖拽工具栏
    bindDragEvents();

    // 窗口大小改变时重新渲染
    window.addEventListener('resize', () => {
        if (pdfDoc) renderPage(currentPage);
    });
}

// 加载 PDF
async function loadPDF() {
    if (!bookData.pdf) {
        showLoadingError('无 PDF 文件');
        return;
    }

    try {
        pdfDoc = await pdfjsLib.getDocument(bookData.pdf).promise;
        hideLoading();
        await renderPage(currentPage);
        updateUI();
    } catch (e) {
        console.error('PDF 加载失败:', e);
        showLoadingError('PDF 加载失败');
    }
}

// 渲染页面
async function renderPage(pageNum) {
    if (!pdfDoc) return;

    const page = await pdfDoc.getPage(pageNum);
    const ctx = pdfCanvas.getContext('2d');

    // 计算适合高度的缩放比例
    const viewportHeight = window.innerHeight - 120;
    const originalViewport = page.getViewport({ scale: 1 });
    const scale = viewportHeight / originalViewport.height;
    const viewport = page.getViewport({ scale });

    pdfCanvas.height = viewport.height;
    pdfCanvas.width = viewport.width;

    await page.render({
        canvasContext: ctx,
        viewport: viewport
    }).promise;

    // 更新页码指示器
    if (pageIndicator) {
        pageIndicator.textContent = `${pageNum} / ${pdfDoc.numPages}`;
    }
}

// 获取当前页的句子列表
function getPageSentences(pageNum) {
    return timelineData.filter(s => s.page === pageNum);
}

// 更新 UI
function updateUI() {
    const pageSentences = getPageSentences(currentPage);

    // 找到当前页第一个句子的索引
    let firstIndex = -1;
    for (let i = 0; i < timelineData.length; i++) {
        if (timelineData[i].page === currentPage) {
            firstIndex = i;
            break;
        }
    }

    if (firstIndex !== -1) {
        currentSentenceIndex = firstIndex;
    }

    const sentence = timelineData[currentSentenceIndex];
    if (sentenceTextEl) {
        const text = sentence && sentence.text ? sentence.text : '';
        sentenceTextEl.textContent = text || '本页无音频文本';
    }
}

// 播放控制
function togglePlay() {
    if (isPlaying) {
        stopAudio();
    } else {
        playCurrentPage();
    }
}

function playCurrentPage() {
    const pageSentences = getPageSentences(currentPage);
    if (pageSentences.length === 0) {
        // 使用 TTS 朗读
        const sentence = timelineData[currentSentenceIndex];
        if (sentence) {
            speakWithTTS(sentence.text);
        }
        return;
    }

    // 从当前页第一个句子开始播放音频
    const firstSentence = pageSentences[0];
    const lastSentence = pageSentences[pageSentences.length - 1];

    if (audio) {
        audio.currentTime = firstSentence.start;
        audio.play();
        isPlaying = true;
        updatePlayButtonState(true);

        // 监听播放到页尾
        audioCheckInterval = setInterval(() => {
            if (audio.currentTime >= lastSentence.end) {
                stopAudio();
            }
        }, 100);

        audio.onended = () => stopAudio();
    } else {
        // 无音频文件，使用 TTS
        speakWithTTS(firstSentence.text);
    }
}

function stopAudio() {
    if (audio) {
        audio.pause();
    }
    window.speechSynthesis?.cancel();
    isPlaying = false;
    updatePlayButtonState(false);

    if (audioCheckInterval) {
        clearInterval(audioCheckInterval);
        audioCheckInterval = null;
    }
}

function updatePlayButtonState(playing) {
    const btnIcon = playBtn?.querySelector('.btn-icon');
    if (playing) {
        playBtn?.classList.add('playing');
        if (btnIcon) btnIcon.textContent = '⏸';
    } else {
        playBtn?.classList.remove('playing');
        if (btnIcon) btnIcon.textContent = '▶';
    }
}

// TTS 朗读
function speakWithTTS(text) {
    if (!window.speechSynthesis) {
        console.warn('浏览器不支持 Web Speech API');
        return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 0.9;

    utterance.onstart = () => {
        isPlaying = true;
        updatePlayButtonState(true);
    };

    utterance.onend = () => {
        isPlaying = false;
        updatePlayButtonState(false);
    };

    window.speechSynthesis.speak(utterance);
}

// 翻页
function goToPage(pageNum) {
    if (!pdfDoc) return;
    if (pageNum < 1 || pageNum > pdfDoc.numPages) return;

    stopAudio();
    currentPage = pageNum;
    renderPage(currentPage);
    updateUI();
}

function nextPage() {
    if (pdfDoc && currentPage < pdfDoc.numPages) {
        goToPage(currentPage + 1);
    }
}

function prevPage() {
    if (currentPage > 1) {
        goToPage(currentPage - 1);
    }
}

// 滑动翻页事件
function bindSwipeEvents() {
    let touchStartX = 0;
    let touchStartY = 0;
    let isSwiping = false;
    const swipeThreshold = 50;

    pdfContainer?.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
        isSwiping = true;
    }, { passive: true });

    pdfContainer?.addEventListener('touchend', (e) => {
        if (!isSwiping) return;
        isSwiping = false;

        const touchEndX = e.changedTouches[0].screenX;
        const touchEndY = e.changedTouches[0].screenY;
        const diff = touchStartX - touchEndX;
        const verticalDiff = Math.abs(touchEndY - touchStartY);
        const horizontalDiff = Math.abs(diff);

        if (horizontalDiff > verticalDiff && horizontalDiff > swipeThreshold) {
            if (diff > 0) nextPage();
            else prevPage();
        }
    }, { passive: true });

    // 鼠标滑动
    let mouseStartX = 0;
    let isMouseDown = false;

    pdfContainer?.addEventListener('mousedown', (e) => {
        mouseStartX = e.screenX;
        isMouseDown = true;
    });

    pdfContainer?.addEventListener('mouseup', (e) => {
        if (!isMouseDown) return;
        isMouseDown = false;

        const diff = mouseStartX - e.screenX;
        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) nextPage();
            else prevPage();
        }
    });

    pdfContainer?.addEventListener('mouseleave', () => {
        isMouseDown = false;
    });
}

// 可拖拽工具栏
function bindDragEvents() {
    let isDragging = false;
    let startX, startY, initialX, initialY;

    floatToolbar?.addEventListener('mousedown', dragStart);
    floatToolbar?.addEventListener('touchstart', dragStart, { passive: false });

    function dragStart(e) {
        // 如果点击的是按钮，不触发拖拽
        if (e.target.closest('.tool-btn')) return;

        isDragging = true;
        floatToolbar.classList.add('dragging');

        const clientX = e.type === 'touchstart' ? e.touches[0].clientX : e.clientX;
        const clientY = e.type === 'touchstart' ? e.touches[0].clientY : e.clientY;
        startX = clientX;
        startY = clientY;

        const rect = floatToolbar.getBoundingClientRect();
        initialX = rect.left;
        initialY = rect.top;

        e.preventDefault();
    }

    function dragMove(e) {
        if (!isDragging) return;

        const clientX = e.type === 'touchmove' ? e.touches[0].clientX : e.clientX;
        const clientY = e.type === 'touchmove' ? e.touches[0].clientY : e.clientY;
        const deltaX = clientX - startX;
        const deltaY = clientY - startY;

        const newX = initialX + deltaX;
        const newY = initialY + deltaY;
        const maxX = window.innerWidth - floatToolbar.offsetWidth;
        const maxY = window.innerHeight - floatToolbar.offsetHeight;

        const clampedX = Math.max(0, Math.min(newX, maxX));
        const clampedY = Math.max(60, Math.min(newY, maxY));

        floatToolbar.style.left = clampedX + 'px';
        floatToolbar.style.top = clampedY + 'px';
        floatToolbar.style.bottom = 'auto';
        floatToolbar.style.transform = 'none';

        e.preventDefault();
    }

    function dragEnd() {
        if (!isDragging) return;
        isDragging = false;
        floatToolbar.classList.remove('dragging');
    }

    document.addEventListener('mousemove', dragMove);
    document.addEventListener('touchmove', dragMove, { passive: false });
    document.addEventListener('mouseup', dragEnd);
    document.addEventListener('touchend', dragEnd);
}

// 录音控制
async function toggleRecord() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
            stream.getTracks().forEach(t => t.stop());
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await submitRecording(audioBlob);
        };

        mediaRecorder.start();
        isRecording = true;
        updateRecordButtonState(true);

        // 停止音频播放
        stopAudio();

        // 开始计时
        recordingSeconds = 0;
        if (recordTimeEl) recordTimeEl.textContent = '00:00';
        recordingTimer = setInterval(updateRecordTime, 1000);

    } catch (e) {
        console.error('录音启动失败:', e);
        alert('无法访问麦克风，请检查权限设置');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        updateRecordButtonState(false);
        clearInterval(recordingTimer);
        recordingSeconds = 0;
    }
}

function updateRecordButtonState(recording) {
    const recordIcon = recordBtn?.querySelector('.btn-icon');
    if (recording) {
        recordBtn?.classList.add('recording');
        if (recordIcon) recordIcon.textContent = '⏹';
    } else {
        recordBtn?.classList.remove('recording');
        if (recordIcon) recordIcon.textContent = '🎤';
    }
}

function updateRecordTime() {
    recordingSeconds++;
    const mins = Math.floor(recordingSeconds / 60).toString().padStart(2, '0');
    const secs = (recordingSeconds % 60).toString().padStart(2, '0');
    if (recordTimeEl) recordTimeEl.textContent = `${mins}:${secs}`;
}

// 提交录音进行评测
async function submitRecording(audioBlob) {
    const sentence = timelineData[currentSentenceIndex];
    if (!sentence) return;

    // 构建表单数据
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('text', sentence.text);
    formData.append('book_id', bookData.id);
    formData.append('book_title', bookData.title);
    formData.append('level', bookData.level);
    formData.append('page', currentPage);

    try {
        showToast({ score: null, text: '评分中...' });

        const response = await fetch('/api/raz/assess', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        showToast({
            score: result.score,
            level: result.level,
            feedback: result.feedback,
            text: sentence.text
        });
    } catch (e) {
        console.error('评测失败:', e);
        showToast({
            score: -1,
            error: true,
            message: e.message || '评测服务暂时不可用，请稍后重试',
            text: sentence.text
        });
    }
}

// Toast 评分显示
function showToast(result) {
    const toastText = toast?.querySelector('.toast-text');
    const toastStars = toast?.querySelector('.toast-stars');

    // 如果 text 为 null 或空，不显示句子文本
    const hasText = result.text && result.text.trim() !== '';

    if (result.score === null) {
        // 评分中
        if (toastScore) toastScore.textContent = '...';
        if (toastStars) toastStars.textContent = '';
        if (toastSentence) toastSentence.textContent = hasText ? result.text : '';
        if (toastText) toastText.textContent = '评分中...';
    } else if (result.error) {
        // 错误状态
        if (toastScore) {
            toastScore.textContent = '!';
            toastScore.className = 'toast-score error';
        }
        if (toastStars) toastStars.textContent = '';
        if (toastSentence) toastSentence.textContent = hasText ? result.text : '';
        if (toastText) {
            toastText.textContent = result.message || '评测失败';
            toastText.className = 'toast-text error';
        }
    } else {
        // 评分结果
        const score = result.score;
        if (toastScore) {
            toastScore.textContent = score;
            toastScore.className = 'toast-score ' + (score >= 90 ? 'excellent' : (score >= 75 ? 'good' : 'keep-trying'));
        }

        if (score >= 90) {
            if (toastStars) toastStars.textContent = '⭐⭐⭐';
            if (toastText) toastText.textContent = result.feedback || '非常棒！';
        } else if (score >= 75) {
            if (toastStars) toastStars.textContent = '⭐⭐';
            if (toastText) toastText.textContent = result.feedback || '很好！';
        } else {
            if (toastStars) toastStars.textContent = '⭐';
            if (toastText) toastText.textContent = result.feedback || '继续加油！';
        }

        // 去掉双引号，直接显示文本
        if (toastSentence) toastSentence.textContent = hasText ? result.text : '';
    }

    toast?.classList.add('show');
    setTimeout(() => {
        toast?.classList.remove('show');
    }, 3000);
}

// 加载状态
function hideLoading() {
    if (loadingEl) loadingEl.style.display = 'none';
}

function showLoadingError(message) {
    if (loadingEl) loadingEl.textContent = message;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);
