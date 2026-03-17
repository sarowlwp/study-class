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
    // LocalStorage Keys
    // =========================================================================
    const STORAGE_KEY = "worksheet_config";

    /**
     * Load saved configuration from localStorage
     */
    function loadSavedConfig() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                const config = JSON.parse(saved);
                // Clean up corrupted data - selectedSemester should be a string
                if (config.selectedSemester && typeof config.selectedSemester !== "string") {
                    console.warn("Cleaning corrupted selectedSemester:", config.selectedSemester);
                    config.selectedSemester = "";
                }
                // selectedLessons should be an array of strings
                if (config.selectedLessons && Array.isArray(config.selectedLessons)) {
                    config.selectedLessons = config.selectedLessons.filter(l => typeof l === "string");
                }
                return config;
            }
        } catch (e) {
            console.warn("Failed to load saved config:", e);
        }
        return null;
    }

    /**
     * Save configuration to localStorage
     */
    function saveConfig(config) {
        try {
            // Validate before saving - ensure selectedSemester is a string
            const configToSave = { ...config };
            if (configToSave.selectedSemester && typeof configToSave.selectedSemester !== "string") {
                console.error("Preventing save of corrupted selectedSemester:", configToSave.selectedSemester);
                configToSave.selectedSemester = "";
            }
            localStorage.setItem(STORAGE_KEY, JSON.stringify(configToSave));
        } catch (e) {
            console.warn("Failed to save config:", e);
        }
    }

    // Load saved config or use defaults
    let savedConfig = loadSavedConfig();

    // Clear corrupted data if needed (remove this after testing)
    if (savedConfig?.selectedSemester === "[object Object]") {
        console.warn("Clearing corrupted localStorage data");
        localStorage.removeItem(STORAGE_KEY);
        savedConfig = null;
    }

    // =========================================================================
    // Configuration State
    // =========================================================================
    const state = {
        source: savedConfig?.source || "mistakes",
        gridType: savedConfig?.gridType || "tian",
        font: savedConfig?.font || "kaiti",
        cols: savedConfig?.cols || 5,
        traceOpacity: savedConfig?.traceOpacity || 0.4,
        charSize: savedConfig?.charSize || 48,
        showPinyin: savedConfig?.showPinyin !== undefined ? savedConfig.showPinyin : true,
        layoutMode: savedConfig?.layoutMode || "horizontal",
        printOrientation: savedConfig?.printOrientation || "landscape",
        exampleCount: savedConfig?.exampleCount || 1,
        traceCount: savedConfig?.traceCount || 5,
        selectedSemester: savedConfig?.selectedSemester || "",
        selectedLessons: savedConfig?.selectedLessons || [],
        customChars: "",
        characters: [],
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
            traceOpacityInputs: document.querySelectorAll('input[name="trace-opacity"]'),
            charSizeInput: document.getElementById("char-size-input"),
            charSizeValue: document.getElementById("char-size-value"),

            // Content options
            showPinyin: document.getElementById("show-pinyin"),
            layoutModeInputs: document.querySelectorAll('input[name="layout-mode"]'),
            printOrientationInputs: document.querySelectorAll('input[name="print-orientation"]'),
            exampleCountInput: document.getElementById("example-count"),
            exampleCountValue: document.getElementById("example-count-value"),
            traceCountInput: document.getElementById("trace-count"),
            traceCountValue: document.getElementById("trace-count-value"),

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

    // =========================================================================
    // Source Events
    // =========================================================================

    function bindSourceEvents() {
        // Source radio buttons
        elements.sourceInputs.forEach(input => {
            input.addEventListener("change", () => {
                state.source = input.value;
                saveConfig(getCurrentConfig());
                updateSourceOptions();

                if (state.source === "semester") {
                    loadSemesters(elements.semesterSelect);
                } else if (state.source === "lessons") {
                    loadSemesters(elements.lessonsSemesterSelect);
                }

                // Auto-trigger preview for custom/mistakes sources (immediate)
                if (state.source === "custom" || state.source === "mistakes") {
                    generatePreview();
                }
            });
        });

        // Semester select for single semester source
        elements.semesterSelect?.addEventListener("change", (e) => {
            state.selectedSemester = e.target.value;
            saveConfig(getCurrentConfig());
            generatePreview();
        });

        // Semester select for lessons
        elements.lessonsSemesterSelect?.addEventListener("change", (e) => {
            state.selectedSemester = e.target.value;
            saveConfig(getCurrentConfig());
            if (state.selectedSemester) {
                loadLessons(state.selectedSemester);
            } else {
                elements.lessonsGrid.innerHTML = '<p class="text-gray-500 text-sm col-span-full">请先选择学期</p>';
                state.selectedLessons = [];
                saveConfig(getCurrentConfig());
                generatePreview();
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

            generatePreview();
        }, 500));
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
                    saveConfig(getCurrentConfig());
                    generatePreview();
                }
            });
        });

        // Font
        elements.fontInputs.forEach(input => {
            input.addEventListener("change", () => {
                if (input.checked) {
                    state.font = input.value;
                    saveConfig(getCurrentConfig());
                    generatePreview();
                }
            });
        });

        // Columns
        elements.colsInput?.addEventListener("input", debounce((e) => {
            state.cols = parseInt(e.target.value, 10);
            elements.colsValue.textContent = state.cols;
            saveConfig(getCurrentConfig());
            generatePreview();
        }, 200));

        // Trace opacity
        elements.traceOpacityInputs.forEach(input => {
            input.addEventListener("change", () => {
                if (input.checked) {
                    state.traceOpacity = parseFloat(input.value);
                    saveConfig(getCurrentConfig());
                    generatePreview();
                }
            });
        });

        // Char size
        if (elements.charSizeInput) {
            elements.charSizeInput.addEventListener("input", debounce((e) => {
                state.charSize = parseInt(e.target.value, 10);
                if (elements.charSizeValue) {
                    elements.charSizeValue.textContent = state.charSize + "px";
                }
                saveConfig(getCurrentConfig());
                updateCharSize();
                generatePreview();
            }, 200));
        }
    }

    function updateCharSize() {
        if (elements.worksheetContainer) {
            elements.worksheetContainer.style.setProperty("--char-size", state.charSize + "px");
        }
    }

    // =========================================================================
    // Content Events
    // =========================================================================

    function bindContentEvents() {
        // Show pinyin
        elements.showPinyin?.addEventListener("change", (e) => {
            state.showPinyin = e.target.checked;
            saveConfig(getCurrentConfig());
            generatePreview();
        });

        // Layout mode
        elements.layoutModeInputs?.forEach(input => {
            input.addEventListener("change", () => {
                if (input.checked) {
                    state.layoutMode = input.value;
                    // Auto adjust columns based on layout
                    if (state.layoutMode === "vertical") {
                        state.cols = 1;
                        if (elements.colsInput) elements.colsInput.value = 1;
                        if (elements.colsValue) elements.colsValue.textContent = 1;
                    }
                    saveConfig(getCurrentConfig());
                    generatePreview();
                }
            });
        });

        // Print orientation
        elements.printOrientationInputs?.forEach(input => {
            input.addEventListener("change", () => {
                if (input.checked) {
                    state.printOrientation = input.value;
                    updatePrintOrientation();
                    saveConfig(getCurrentConfig());
                    generatePreview();
                }
            });
        });

        // Example count
        elements.exampleCountInput?.addEventListener("input", debounce((e) => {
            state.exampleCount = parseInt(e.target.value, 10);
            if (elements.exampleCountValue) {
                elements.exampleCountValue.textContent = state.exampleCount;
            }
            saveConfig(getCurrentConfig());
            generatePreview();
        }, 200));

        // Trace count
        elements.traceCountInput?.addEventListener("input", debounce((e) => {
            state.traceCount = parseInt(e.target.value, 10);
            if (elements.traceCountValue) {
                elements.traceCountValue.textContent = state.traceCount;
            }
            saveConfig(getCurrentConfig());
            generatePreview();
        }, 200));
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
     * API returns: [{"id": "...", "name": "...", "file": "...", "total_chars": N}, ...]
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
                // Handle both object format and string format
                if (typeof sem === "object" && sem !== null) {
                    option.value = sem.id || sem.name || "";
                    option.textContent = sem.name || sem.id || "";
                } else {
                    option.value = sem;
                    option.textContent = sem;
                }
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
     * API returns: [{"id": "...", "name": "...", "char_count": N, "mastered_count": N}, ...]
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

            if (lessons.length === 0) {
                elements.lessonsGrid.innerHTML = '<p class="text-gray-500 text-sm col-span-full">该学期暂无课文</p>';
                return;
            }

            lessons.forEach(lesson => {
                const item = document.createElement("label");
                item.className = "lesson-item";

                // Handle both object format and string format
                // API returns: {id, name, char_count, mastered_count}
                // Note: id is generated (lesson-1, lesson-2), but API needs 'name' for filtering
                const lessonName = typeof lesson === "object" && lesson !== null ? lesson.name || lesson.id || "" : lesson;

                const checkbox = document.createElement("input");
                checkbox.type = "checkbox";
                checkbox.value = lessonName;  // Use name for API compatibility
                checkbox.addEventListener("change", () => {
                    if (checkbox.checked) {
                        state.selectedLessons.push(lessonName);
                        item.classList.add("selected");
                    } else {
                        state.selectedLessons = state.selectedLessons.filter(l => l !== lessonName);
                        item.classList.remove("selected");
                    }
                    saveConfig(getCurrentConfig());
                    generatePreview();
                });

                const span = document.createElement("span");
                span.textContent = lessonName;

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
            // API returns 'char' field, not 'character'
            const chars = mistakes.map(m => ({
                char: m.char || m.character,
                pinyin: m.pinyin || "",
                stroke_count: m.stroke_count || 0
            }));

            return chars;
        } catch (error) {
            console.error("Error fetching mistakes:", error);
            showError("获取错字本失败: " + error.message);
            return [];
        }
    }

    /**
     * Fetch characters for selected semester
     */
    async function fetchSemesterCharacters() {
        const semester = elements.semesterSelect?.value;
        console.log("Fetching semester characters for semester ID:", semester);
        if (!semester) {
            showWarning("请先选择学期");
            return [];
        }

        try {
            const url = `/api/characters?semester=${encodeURIComponent(semester)}`;
            console.log("API URL:", url);
            const response = await fetch(url);
            if (!response.ok) throw new Error("Failed to fetch characters");

            const data = await response.json();
            console.log("Fetched characters:", data.characters?.length);
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
        const semester = state.selectedSemester || elements.lessonsSemesterSelect?.value;
        console.log("Fetching lesson characters:", { semester, selectedLessons: state.selectedLessons });

        if (!semester) {
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
                `/api/characters?semester=${encodeURIComponent(semester)}&lessons=${encodeURIComponent(lessonsParam)}`
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

        console.log("Generating preview with source:", state.source, "state:", {
            selectedSemester: state.selectedSemester,
            selectedLessons: state.selectedLessons,
            semesterSelectValue: elements.semesterSelect?.value,
            lessonsSemesterSelectValue: elements.lessonsSemesterSelect?.value
        });

        if (state.source === "custom" && !await validateCustomChars()) {
            return;
        }

        showLoading();

        let characters = await fetchCharacters();

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

        // 获取笔顺信息
        characters = await fetchStrokeData(characters);

        state.characters = characters;
        renderWorksheet();
        hideLoading();
    }

    /**
     * Render the worksheet
     *
     * 新逻辑：每行只重复练习1个字
     * - 每行字数（cols）指的是每行的方格数量
     * - 每行使用同一个字重复
     * - 每个字占一行，然后根据配置每行显示多个格子
     */
    function renderWorksheet() {
        const container = elements.worksheetContainer;
        container.innerHTML = "";

        // Set grid columns based on layout mode
        const cols = state.layoutMode === "vertical" ? 1 : state.cols;
        container.style.setProperty("--cols", cols);

        // 计算总行数：根据字数和每行显示的格子数
        // 每个字占一行，每行有 cols 个格子
        const totalRows = state.characters.length;
        const cellsPerRow = cols;

        // Create cells - 每行重复同一个字，每行上方插入信息展示区域
        for (let row = 0; row < totalRows; row++) {
            const charData = state.characters[row];

            // 在每行之前插入信息展示区域
            const infoRow = createInfoRow(charData);
            container.appendChild(infoRow);

            // 创建练习格子（一行）
            for (let col = 0; col < cellsPerRow; col++) {
                const cellIndex = row * cellsPerRow + col;
                const cell = createCharCell(charData, cellIndex, col);
                container.appendChild(cell);
            }
        }

    }

    /**
     * Create a character cell
     *
     * @param {Object} charData - 汉字数据
     * @param {number} globalIndex - 全局索引（用于唯一ID）
     * @param {number} colIndex - 当前行内的列索引（0-based），用于判断格子类型
     */
    function createCharCell(charData, globalIndex, colIndex) {
        const cell = document.createElement("div");
        cell.className = "char-cell";

        // Grid box
        const gridBox = document.createElement("div");
        gridBox.className = `grid-box ${state.gridType}`;

        // 使用 colIndex（当前行内的位置）判断格子类型
        // 0 to exampleCount-1: example (red)
        // exampleCount to exampleCount+traceCount-1: trace (gray with character)
        // rest: blank (empty grid)
        const isExample = colIndex < state.exampleCount;
        const isTrace = colIndex >= state.exampleCount && colIndex < state.exampleCount + state.traceCount;

        // Trace character
        const traceChar = document.createElement("span");
        if (isExample) {
            traceChar.className = "trace-char example";
            traceChar.style.fontFamily = getFontFamily();
            traceChar.textContent = charData.char;
        } else if (isTrace) {
            traceChar.className = `trace-char ${getOpacityClass()}`;
            traceChar.style.fontFamily = getFontFamily();
            traceChar.textContent = charData.char;
        }
        // For blank cells, don't add traceChar
        if (isExample || isTrace) {
            gridBox.appendChild(traceChar);
        }

        cell.appendChild(gridBox);

        return cell;
    }

    /**
     * Create info row - 在每行之间展示拼音和笔顺信息
     * 跨满整行，高度为田字格的 1/4，左对齐，红色文字
     */
    function createInfoRow(charData) {
        const infoRow = document.createElement("div");
        infoRow.className = "info-row";
        infoRow.style.gridColumn = "1 / -1"; // 跨满整行

        // 拼音（红色）
        if (state.showPinyin && charData.pinyin) {
            const pinyin = document.createElement("span");
            pinyin.className = "info-pinyin";
            pinyin.textContent = charData.pinyin;
            infoRow.appendChild(pinyin);
        }

        // 分隔符
        const separator = document.createElement("span");
        separator.className = "info-separator";
        separator.textContent = "·";
        infoRow.appendChild(separator);

        // 笔顺拆解（红色 SVG）
        if (charData.stroke_svgs && charData.stroke_svgs.length > 0) {
            const strokesContainer = document.createElement("span");
            strokesContainer.className = "info-strokes";
            charData.stroke_svgs.forEach((svg) => {
                const strokeSpan = document.createElement("span");
                strokeSpan.className = "stroke-item";
                strokeSpan.innerHTML = svg;
                strokesContainer.appendChild(strokeSpan);
            });
            infoRow.appendChild(strokesContainer);
        }

        return infoRow;
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

    // =========================================================================
    // Stroke Data Fetching
    // =========================================================================

    /**
     * Fetch stroke data for characters using Hanzi Writer data
     * @param {Array} characters - Character objects
     * @returns {Array} Characters with stroke_svgs added (逐步叠加)
     */
    async function fetchStrokeData(characters) {
        const baseUrl = "https://cdn.jsdelivr.net/npm/hanzi-writer-data@latest";

        // 为每个字符获取笔顺数据
        const promises = characters.map(async (charObj) => {
            const char = charObj.char;
            try {
                const response = await fetch(`${baseUrl}/${char}.json`);
                if (response.ok) {
                    const data = await response.json();
                    // 生成逐步叠加的 SVG: 第1步=第1笔, 第2步=前2笔, ...
                    const strokeSvgs = [];
                    if (data.strokes && data.strokes.length > 0) {
                        const size = 24; // 小尺寸用于展示
                        const totalStrokes = data.strokes.length;

                        // 为每个步骤生成 SVG（逐步叠加）
                        for (let step = 1; step <= totalStrokes; step++) {
                            // 收集当前步骤的所有笔画（前 step 笔）
                            const paths = [];
                            for (let i = 0; i < step; i++) {
                                paths.push(`<path d="${data.strokes[i]}" fill="#ef4444" stroke="none"/>`);
                            }

                            // 添加 transform 修正 Y 轴翻转（倒立问题）
                            const svg = `<svg width="${size}" height="${size}" viewBox="0 0 1024 1024"><g transform="translate(0, 1024) scale(1, -1)">${paths.join('')}</g></svg>`;
                            strokeSvgs.push(svg);
                        }
                    }
                    return {
                        ...charObj,
                        stroke_svgs: strokeSvgs
                    };
                }
            } catch (e) {
                console.warn(`Failed to fetch stroke data for ${char}:`, e);
            }
            // 如果获取失败，返回默认值
            return {
                ...charObj,
                stroke_svgs: []
            };
        });

        return Promise.all(promises);
    }

    // =========================================================================
    // Print Functionality
    // =========================================================================

    /**
     * Update print orientation CSS
     */
    function updatePrintOrientation() {
        // 查找或创建打印样式表
        let printStyle = document.getElementById("print-orientation-style");
        if (!printStyle) {
            printStyle = document.createElement("style");
            printStyle.id = "print-orientation-style";
            document.head.appendChild(printStyle);
        }

        // 设置纸张方向
        const orientation = state.printOrientation === "portrait" ? "portrait" : "landscape";
        printStyle.textContent = `
            @media print {
                @page {
                    size: A4 ${orientation};
                    margin: 10mm;
                }
            }
        `;
    }

    /**
     * Print the worksheet
     */
    function doPrint() {
        if (state.characters.length === 0) {
            showWarning("请先生成预览");
            return;
        }

        // 确保打印方向已应用
        updatePrintOrientation();

        // Trigger browser print
        window.print();
    }

    // =========================================================================
    // Initialization
    // =========================================================================

    /**
     * Apply saved configuration to UI elements
     */
    function applySavedConfig() {
        // Apply source
        const sourceInput = document.querySelector(`input[name="source"][value="${state.source}"]`);
        if (sourceInput) {
            sourceInput.checked = true;
        }

        // Apply grid type
        const gridTypeInput = document.querySelector(`input[name="grid-type"][value="${state.gridType}"]`);
        if (gridTypeInput) {
            gridTypeInput.checked = true;
        }

        // Apply font
        const fontInput = document.querySelector(`input[name="font"][value="${state.font}"]`);
        if (fontInput) {
            fontInput.checked = true;
        }

        // Apply cols
        if (elements.colsInput) {
            elements.colsInput.value = state.cols;
            elements.colsValue.textContent = state.cols;
        }

        // Apply trace opacity
        const opacityInput = document.querySelector(`input[name="trace-opacity"][value="${state.traceOpacity}"]`);
        if (opacityInput) {
            opacityInput.checked = true;
        }

        // Apply content options
        if (elements.showPinyin) {
            elements.showPinyin.checked = state.showPinyin;
        }

        // Apply layout mode
        const layoutModeInput = document.querySelector(`input[name="layout-mode"][value="${state.layoutMode}"]`);
        if (layoutModeInput) {
            layoutModeInput.checked = true;
        }

        // Apply print orientation
        const printOrientationInput = document.querySelector(`input[name="print-orientation"][value="${state.printOrientation}"]`);
        if (printOrientationInput) {
            printOrientationInput.checked = true;
        }
        updatePrintOrientation();

        // Apply example and trace count
        if (elements.exampleCountInput) {
            elements.exampleCountInput.value = state.exampleCount;
            if (elements.exampleCountValue) {
                elements.exampleCountValue.textContent = state.exampleCount;
            }
        }
        if (elements.traceCountInput) {
            elements.traceCountInput.value = state.traceCount;
            if (elements.traceCountValue) {
                elements.traceCountValue.textContent = state.traceCount;
            }
        }

        // Apply char size
        if (elements.charSizeInput) {
            elements.charSizeInput.value = state.charSize;
            elements.charSizeValue.textContent = state.charSize + "px";
        }
        updateCharSize();

        // Update source options visibility
        updateSourceOptions();

        // Restore semester selections after a short delay to let options load
        const semesterValue = state.selectedSemester;
        if (semesterValue && typeof semesterValue === "string") {
            setTimeout(() => {
                if (elements.semesterSelect) {
                    elements.semesterSelect.value = semesterValue;
                }
                if (elements.lessonsSemesterSelect) {
                    elements.lessonsSemesterSelect.value = semesterValue;
                    // Trigger lessons load if lessons source is active
                    if (state.source === "lessons" && state.selectedLessons.length > 0) {
                        loadLessons(semesterValue).then(() => {
                            // Restore selected lessons checkboxes
                            const checkboxes = elements.lessonsGrid?.querySelectorAll('input[type="checkbox"]');
                            checkboxes?.forEach(cb => {
                                if (state.selectedLessons.includes(cb.value)) {
                                    cb.checked = true;
                                    cb.closest('.lesson-item')?.classList.add('selected');
                                }
                            });
                        });
                    }
                }
            }, 100);
        }
    }

    /**
     * Get current configuration object for saving
     */
    function getCurrentConfig() {
        return {
            source: state.source,
            gridType: state.gridType,
            font: state.font,
            cols: state.cols,
            traceOpacity: state.traceOpacity,
            charSize: state.charSize,
            showPinyin: state.showPinyin,
            layoutMode: state.layoutMode,
            printOrientation: state.printOrientation,
            exampleCount: state.exampleCount,
            traceCount: state.traceCount,
            selectedSemester: state.selectedSemester,
            selectedLessons: state.selectedLessons
        };
    }

    function init() {
        cacheElements();
        bindSourceEvents();
        bindGridEvents();
        bindContentEvents();
        bindPrintEvents();

        // Apply saved configuration to UI
        applySavedConfig();

        // Load semesters if needed based on saved source
        if (state.source === "semester") {
            loadSemesters(elements.semesterSelect).then(() => {
                // Restore selected semester value after loading
                const semester = state.selectedSemester;
                if (semester && typeof semester === "string" && elements.semesterSelect) {
                    elements.semesterSelect.value = semester;
                }
            });
        } else if (state.source === "lessons") {
            loadSemesters(elements.lessonsSemesterSelect).then(() => {
                // Restore selected semester and load lessons
                const semester = state.selectedSemester;
                if (semester && typeof semester === "string" && elements.lessonsSemesterSelect) {
                    elements.lessonsSemesterSelect.value = semester;
                    if (state.selectedLessons.length > 0) {
                        loadLessons(semester).then(() => {
                            // Restore selected lessons checkboxes
                            const checkboxes = elements.lessonsGrid?.querySelectorAll('input[type="checkbox"]');
                            checkboxes?.forEach(cb => {
                                if (state.selectedLessons.includes(cb.value)) {
                                    cb.checked = true;
                                    cb.closest('.lesson-item')?.classList.add('selected');
                                }
                            });
                        });
                    }
                }
            });
        }

        console.log("Worksheet module initialized");
        console.log("Current state:", {
            gridType: state.gridType,
            showPinyin: state.showPinyin,
            source: state.source
        });
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
