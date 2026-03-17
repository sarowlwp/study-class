/**
 * Worksheet Module - Chinese Character Practice Sheet Generator
 *
 * Features:
 * - Tab switching functionality
 * - Data fetching from APIs
 * - UI event bindings
 * - Worksheet rendering with Hanzi Writer
 * - Print functionality
 */

const Worksheet = (function() {
    "use strict";

    // =========================================================================
    // Configuration State
    // =========================================================================
    const state = {
        source: "mistakes", // mistakes, semester, lessons, custom
        gridType: "tian", // tian, mi, square, none
        font: "kaiti", // kaiti, songti, heiti
        cols: 5,
        rows: 6,
        traceOpacity: 0.4,
        showPinyin: true,
        showStroke: true,
        strokeMode: "animate", // animate, static
        selectedSemester: "",
        selectedLessons: [],
        customChars: "",
        characters: [], // Array of {char, pinyin, stroke_count}
        isLoading: false
    };

    // Cache for pinyin lookups
    const pinyinCache = new Map();

    // =========================================================================
    // DOM Element References
    // =========================================================================
    let elements = {};

    function cacheElements() {
        elements = {
            // Tabs
            tabButtons: document.querySelectorAll(".tab-btn"),
            tabContents: document.querySelectorAll(".tab-content"),

            // Source options
            sourceInputs: document.querySelectorAll('input[name="source"]'),
            mistakesOptions: document.getElementById("mistakes-options"),
            semesterOptions: document.getElementById("semester-options"),
            lessonsOptions: document.getElementById("lessons-options"),
            customOptions: document.getElementById("custom-options"),

            // Selects
            semesterSelect: document.getElementById("semester-select"),
            lessonsSemesterSelect: document.getElementById("lessons-semester-select"),
            lessonsGrid: document.getElementById("lessons-grid"),

            // Custom input
            customChars: document.getElementById("custom-chars"),
            charCount: document.getElementById("char-count"),

            // Grid settings
            gridTypeInputs: document.querySelectorAll('input[name="grid-type"]'),
            fontInputs: document.querySelectorAll('input[name="font"]'),
            colsInput: document.getElementById("cols-input"),
            colsValue: document.getElementById("cols-value"),
            rowsInput: document.getElementById("rows-input"),
            rowsValue: document.getElementById("rows-value"),
            traceOpacityInputs: document.querySelectorAll('input[name="trace-opacity"]'),

            // Content options
            showPinyin: document.getElementById("show-pinyin"),
            showStroke: document.getElementById("show-stroke"),
            strokeModeInputs: document.querySelectorAll('input[name="stroke-mode"]"'),

            // Buttons
            previewBtn: document.getElementById("preview-btn"),
            printBtn: document.getElementById("print-btn"),

            // Preview
            worksheetContainer: document.getElementById("worksheet-container"),
            worksheetPreview: document.getElementById("worksheet-preview")
        };
    }

    // =========================================================================
    // Utility Functions
    // =========================================================================

    /**
     * Debounce function to limit API calls
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Show error message
     */
    function showError(message) {
        hideMessage();
        const msgDiv = document.createElement("div");
        msgDiv.className = "message message-error";
        msgDiv.textContent = message;
        msgDiv.id = "worksheet-message";
        elements.worksheetPreview.insertBefore(msgDiv, elements.worksheetContainer);
    }

    /**
     * Show warning message
     */
    function showWarning(message) {
        hideMessage();
        const msgDiv = document.createElement("div");
        msgDiv.className = "message message-warning";
        msgDiv.textContent = message;
        msgDiv.id = "worksheet-message";
        elements.worksheetPreview.insertBefore(msgDiv, elements.worksheetContainer);
    }

    /**
     * Hide message
     */
    function hideMessage() {
        const existingMsg = document.getElementById("worksheet-message");
        if (existingMsg) {
            existingMsg.remove();
        }
    }

    /**
     * Show loading state
     */
    function showLoading() {
        state.isLoading = true;
        elements.worksheetContainer.innerHTML = '<div class="loading">加载中...</div>';
    }

    /**
     * Hide loading state
     */
    function hideLoading() {
        state.isLoading = false;
    }

    // =========================================================================
    // Tab Events
    // =========================================================================

    function bindTabEvents() {
        elements.tabButtons.forEach(btn => {
            btn.addEventListener("click", () => {
                const tabId = btn.dataset.tab;

                // Update active tab button
                elements.tabButtons.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");

                // Show corresponding content
                elements.tabContents.forEach(content => {
                    content.classList.add("hidden");
                });
                document.getElementById(`${tabId}-tab`).classList.remove("hidden");
            });
        });
    }

    // =========================================================================
    // Source Events
    // =========================================================================

    function bindSourceEvents() {
        // Source radio buttons
        elements.sourceInputs.forEach(input => {
            input.addEventListener("change", () => {
                state.source = input.value;
                updateSourceOptions();

                if (state.source === "semester") {
                    loadSemesters(elements.semesterSelect);
                } else if (state.source === "lessons") {
                    loadSemesters(elements.lessonsSemesterSelect);
                }
            });
        });

        // Semester select for lessons
        elements.lessonsSemesterSelect?.addEventListener("change", (e) => {
            state.selectedSemester = e.target.value;
            if (state.selectedSemester) {
                loadLessons(state.selectedSemester);
            } else {
                elements.lessonsGrid.innerHTML = '<p class="text-gray-500 text-sm col-span-full">请先选择学期</p>';
                state.selectedLessons = [];
            }
        });

        // Custom chars input
        elements.customChars?.addEventListener("input", debounce((e) => {
            const chars = e.target.value;
            const validChars = chars.replace(/[^\u4e00-\u9fff]/g, "");
            state.customChars = validChars.slice(0, 100);
            elements.charCount.textContent = state.customChars.length;

            if (validChars.length > 100) {
                showWarning("最多支持100个汉字，已自动截断");
            }
        }, 300));
    }

    /**
     * Update visibility of source option panels
     */
    function updateSourceOptions() {
        elements.mistakesOptions?.classList.add("hidden");
        elements.semesterOptions?.classList.add("hidden");
        elements.lessonsOptions?.classList.add("hidden");
        elements.customOptions?.classList.add("hidden");

        const optionMap = {
            mistakes: elements.mistakesOptions,
            semester: elements.semesterOptions,
            lessons: elements.lessonsOptions,
            custom: elements.customOptions
        };

        optionMap[state.source]?.classList.remove("hidden");
    }

    // =========================================================================
    // Grid Events
    // =========================================================================

    function bindGridEvents() {
        // Grid type
        elements.gridTypeInputs.forEach(input => {
            input.addEventListener("change", () => {
                if (input.checked) {
                    state.gridType = input.value;
                }
            });
        });

        // Font
        elements.fontInputs.forEach(input => {
            input.addEventListener("change", () => {
                if (input.checked) {
                    state.font = input.value;
                }
            });
        });

        // Columns
        elements.colsInput?.addEventListener("input", (e) => {
            state.cols = parseInt(e.target.value, 10);
            elements.colsValue.textContent = state.cols;
        });

        // Rows
        elements.rowsInput?.addEventListener("input", (e) => {
            state.rows = parseInt(e.target.value, 10);
            elements.rowsValue.textContent = state.rows;
        });

        // Trace opacity
        elements.traceOpacityInputs.forEach(input => {
            input.addEventListener("change", () => {
                if (input.checked) {
                    state.traceOpacity = parseFloat(input.value);
                }
            });
        });
    }

    // =========================================================================
    // Content Events
    // =========================================================================

    function bindContentEvents() {
        // Show pinyin
        elements.showPinyin?.addEventListener("change", (e) => {
            state.showPinyin = e.target.checked;
        });

        // Show stroke
        elements.showStroke?.addEventListener("change", (e) => {
            state.showStroke = e.target.checked;
        });

        // Stroke mode
        elements.strokeModeInputs?.forEach(input => {
            input.addEventListener("change", () => {
                if (input.checked) {
                    state.strokeMode = input.value;
                }
            });
        });
    }

    // =========================================================================
    // Print Events
    // =========================================================================

    function bindPrintEvents() {
        elements.previewBtn?.addEventListener("click", generatePreview);
        elements.printBtn?.addEventListener("click", doPrint);
    }

    // =========================================================================
    // Data Loading
    // =========================================================================

    /**
     * Load semesters from API
     */
    async function loadSemesters(selectElement) {
        if (!selectElement) return;

        try {
            selectElement.disabled = true;
            const response = await fetch("/api/semesters");
            if (!response.ok) throw new Error("Failed to load semesters");

            const data = await response.json();
            const semesters = data.semesters || [];

            selectElement.innerHTML = '<option value="">请选择学期</option>';
            semesters.forEach(sem => {
                const option = document.createElement("option");
                option.value = sem;
                option.textContent = sem;
                selectElement.appendChild(option);
            });
        } catch (error) {
            console.error("Error loading semesters:", error);
            showError("加载学期列表失败，请刷新页面重试");
        } finally {
            selectElement.disabled = false;
        }
    }

    /**
     * Load lessons for a semester
     */
    async function loadLessons(semester) {
        if (!elements.lessonsGrid) return;

        try {
            elements.lessonsGrid.innerHTML = '<p class="text-gray-500 text-sm col-span-full">加载中...</p>';

            const response = await fetch(`/api/lessons?semester=${encodeURIComponent(semester)}`);
            if (!response.ok) throw new Error("Failed to load lessons");

            const data = await response.json();
            const lessons = data.lessons || [];

            elements.lessonsGrid.innerHTML = "";
            state.selectedLessons = [];

            if (lessons.length === 0) {
                elements.lessonsGrid.innerHTML = '<p class="text-gray-500 text-sm col-span-full">该学期暂无课文</p>';
                return;
            }

            lessons.forEach(lesson => {
                const item = document.createElement("label");
                item.className = "lesson-item";

                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.value = lesson;
                checkbox.addEventListener("change", () => {
                    if (checkbox.checked) {
                        state.selectedLessons.push(lesson);
                        item.classList.add("selected");
                    } else {
                        state.selectedLessons = state.selectedLessons.filter(l => l !== lesson);
                        item.classList.remove("selected");
                    }
                });

                const span = document.createElement("span");
                span.textContent = lesson;

                item.appendChild(checkbox);
                item.appendChild(span);
                elements.lessonsGrid.appendChild(item);
            });
        } catch (error) {
            console.error("Error loading lessons:", error);
            elements.lessonsGrid.innerHTML = '<p class="text-gray-500 text-sm col-span-full">加载失败，请重试</p>';
        }
    }

    // =========================================================================
    // Character Fetching
    // =========================================================================

    /**
     * Fetch characters based on current source
     */
    async function fetchCharacters() {
        switch (state.source) {
        case "mistakes":
            return await fetchMistakes();
        case "semester":
            return await fetchSemesterCharacters();
        case "lessons":
            return await fetchLessonCharacters();
        case "custom":
            return await fetchCustomCharacters();
        default:
            return [];
        }
    }

    /**
     * Fetch mistakes from API
     */
    async function fetchMistakes() {
        try {
            const response = await fetch("/api/mistakes");
            if (!response.ok) throw new Error("Failed to fetch mistakes");

            const data = await response.json();
            const mistakes = data.mistakes || [];

            // Convert to character objects
            const chars = mistakes.map(m => ({
                char: m.character,
                pinyin: m.pinyin || "",
                stroke_count: m.stroke_count || 0
            }));

            return chars;
        } catch (error) {
            console.error("Error fetching mistakes:", error);
            showError("获取错字本失败");
            return [];
        }
    }

    /**
     * Fetch characters for selected semester
     */
    async function fetchSemesterCharacters() {
        const semester = elements.semesterSelect?.value;
        if (!semester) {
            showWarning("请先选择学期");
            return [];
        }

        try {
            const response = await fetch(`/api/characters?semester=${encodeURIComponent(semester)}`);
            if (!response.ok) throw new Error("Failed to fetch characters");

            const data = await response.json();
            return data.characters || [];
        } catch (error) {
            console.error("Error fetching semester characters:", error);
            showError("获取汉字列表失败");
            return [];
        }
    }

    /**
     * Fetch characters for selected lessons
     */
    async function fetchLessonCharacters() {
        if (!state.selectedSemester) {
            showWarning("请先选择学期");
            return [];
        }

        if (state.selectedLessons.length === 0) {
            showWarning("请至少选择一课");
            return [];
        }

        try {
            const lessonsParam = state.selectedLessons.join(",");
            const response = await fetch(
                `/api/characters?semester=${encodeURIComponent(state.selectedSemester)}&lessons=${encodeURIComponent(lessonsParam)}`
            );
            if (!response.ok) throw new Error("Failed to fetch characters");

            const data = await response.json();
            return data.characters || [];
        } catch (error) {
            console.error("Error fetching lesson characters:", error);
            showError("获取汉字列表失败");
            return [];
        }
    }

    /**
     * Fetch pinyin for custom characters
     */
    async function fetchCustomCharacters() {
        if (!state.customChars || state.customChars.length === 0) {
            showWarning("请输入汉字");
            return [];
        }

        try {
            // Check cache first
            const uncachedChars = [];
            const result = [];

            for (const char of state.customChars) {
                if (pinyinCache.has(char)) {
                    result.push({
                        char: char,
                        pinyin: pinyinCache.get(char),
                        stroke_count: 0
                    });
                } else {
                    uncachedChars.push(char);
                }
            }

            // Fetch pinyin for uncached characters
            if (uncachedChars.length > 0) {
                const response = await fetch(
                    `/api/pinyin?chars=${encodeURIComponent(uncachedChars.join(""))}`
                );
                if (!response.ok) throw new Error("Failed to fetch pinyin");

                const data = await response.json();
                const pinyinData = data.pinyin || {};

                for (const char of uncachedChars) {
                    const py = pinyinData[char] || "";
                    pinyinCache.set(char, py);
                    result.push({
                        char: char,
                        pinyin: py,
                        stroke_count: 0
                    });
                }
            }

            return result;
        } catch (error) {
            console.error("Error fetching pinyin:", error);
            showError("获取拼音失败");
            return [];
        }
    }

    /**
     * Validate custom characters and fetch pinyin
     */
    async function validateCustomChars() {
        if (state.source !== "custom") return true;

        if (!state.customChars || state.customChars.length === 0) {
            showWarning("请输入至少一个汉字");
            return false;
        }

        if (state.customChars.length > 100) {
            showWarning("最多支持100个汉字");
            return false;
        }

        // 获取拼音
        try {
            const response = await fetch(`/api/pinyin?chars=${encodeURIComponent(state.customChars)}`);
            if (!response.ok) throw new Error("获取拼音失败");
            const data = await response.json();

            // 缓存拼音数据
            const pinyinData = data.pinyin || {};
            for (const [char, py] of Object.entries(pinyinData)) {
                pinyinCache.set(char, py);
            }

            return true;
        } catch (error) {
            console.error("Error fetching pinyin in validation:", error);
            // 如果拼音获取失败，仍然允许继续
            return true;
        }
    }

    // =========================================================================
    // Worksheet Rendering
    // =========================================================================

    /**
     * Generate preview
     */
    async function generatePreview() {
        hideMessage();

        if (state.source === "custom" && !await validateCustomChars()) {
            return;
        }

        showLoading();

        const characters = await fetchCharacters();

        if (characters.length === 0) {
            elements.worksheetContainer.innerHTML = `
                <div class="empty-state col-span-full">
                    <div class="empty-state-icon">📝</div>
                    <div class="empty-state-title">暂无数据</div>
                    <p>请检查您的选择或输入</p>
                </div>
            `;
            hideLoading();
            return;
        }

        state.characters = characters;
        renderWorksheet();
        hideLoading();
    }

    /**
     * Render the worksheet
     */
    function renderWorksheet() {
        const container = elements.worksheetContainer;
        container.innerHTML = "";

        // Set grid columns
        container.style.setProperty("--cols", state.cols);

        // Calculate total cells needed
        const totalCells = state.cols * state.rows;

        // Create cells for each character (repeating if necessary)
        for (let i = 0; i < totalCells; i++) {
            const charIndex = i % state.characters.length;
            const charData = state.characters[charIndex];
            const cell = createCharCell(charData, i);
            container.appendChild(cell);
        }

        // Initialize Hanzi Writer for stroke animations if enabled
        if (state.showStroke && state.strokeMode === "animate") {
            initHanziWriters();
        }
    }

    /**
     * Create a character cell
     */
    function createCharCell(charData, index) {
        const cell = document.createElement("div");
        cell.className = "char-cell";

        // Pinyin
        if (state.showPinyin) {
            const pinyin = document.createElement("div");
            pinyin.className = "pinyin";
            pinyin.textContent = charData.pinyin || "";
            cell.appendChild(pinyin);
        }

        // Grid box
        const gridBox = document.createElement("div");
        gridBox.className = `grid-box ${state.gridType}`;

        // Trace character
        const traceChar = document.createElement("span");
        traceChar.className = `trace-char ${getOpacityClass()}`;
        traceChar.style.fontFamily = getFontFamily();
        traceChar.textContent = charData.char;
        gridBox.appendChild(traceChar);

        // Hanzi Writer container (if stroke animation enabled)
        if (state.showStroke && state.strokeMode === "animate") {
            const writerContainer = document.createElement("div");
            writerContainer.className = "hanzi-writer-container";
            writerContainer.id = `hanzi-writer-${index}`;
            writerContainer.dataset.char = charData.char;
            gridBox.appendChild(writerContainer);
        }

        cell.appendChild(gridBox);

        // Stroke order number (if static mode)
        if (state.showStroke && state.strokeMode === "static" && charData.stroke_count) {
            const strokeOrder = document.createElement("div");
            strokeOrder.className = "stroke-order";
            strokeOrder.textContent = `${charData.stroke_count} 画`;
            cell.appendChild(strokeOrder);
        }

        return cell;
    }

    /**
     * Get opacity class based on trace opacity setting
     */
    function getOpacityClass() {
        if (state.traceOpacity <= 0.25) return "light";
        if (state.traceOpacity >= 0.5) return "dark";
        return "medium";
    }

    /**
     * Get font family CSS
     */
    function getFontFamily() {
        const fontMap = {
            kaiti: '"KaiTi", "STKaiti", "BiauKai", "楷体", serif',
            songti: '"SimSun", "STSong", "宋体", serif',
            heiti: '"SimHei", "STHeiti", "黑体", sans-serif'
        };
        return fontMap[state.font] || fontMap.kaiti;
    }

    /**
     * Initialize Hanzi Writer instances
     */
    function initHanziWriters() {
        if (typeof HanziWriter === "undefined") {
            console.warn("Hanzi Writer not loaded");
            return;
        }

        const containers = document.querySelectorAll(".hanzi-writer-container");
        containers.forEach((container, index) => {
            const char = container.dataset.char;
            if (!char) return;

            // Delay initialization for performance
            setTimeout(() => {
                try {
                    const writer = HanziWriter.create(container.id, char, {
                        width: 80,
                        height: 80,
                        padding: 5,
                        strokeAnimationSpeed: 1,
                        delayBetweenStrokes: 1000,
                        strokeColor: "#333",
                        radicalColor: "#333",
                        highlightColor: "#16a34a",
                        outlineColor: "transparent",
                        drawingColor: "#333",
                        showCharacter: false,
                        showOutline: false,
                        showHintAfterMisses: 3,
                        highlightOnComplete: true,
                        highlightCompleteColor: "#16a34a"
                    });

                    // Auto animate on load
                    writer.animateCharacter();
                } catch (error) {
                    console.error(`Failed to initialize Hanzi Writer for ${char}:`, error);
                }
            }, index * 100);
        });
    }

    // =========================================================================
    // Print Functionality
    // =========================================================================

    /**
     * Print the worksheet
     */
    function doPrint() {
        if (state.characters.length === 0) {
            showWarning("请先生成预览");
            return;
        }

        // Trigger browser print
        window.print();
    }

    // =========================================================================
    // Initialization
    // =========================================================================

    function init() {
        cacheElements();
        bindTabEvents();
        bindSourceEvents();
        bindGridEvents();
        bindContentEvents();
        bindPrintEvents();

        // Initialize source options visibility
        updateSourceOptions();

        console.log("Worksheet module initialized");
    }

    // =========================================================================
    // Public API
    // =========================================================================
    return {
        init,
        generatePreview,
        doPrint,
        showError,
        showWarning,
        hideMessage
    };
})();

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", Worksheet.init);
