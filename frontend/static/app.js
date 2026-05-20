const { createApp, ref, onMounted, nextTick } = Vue;

/**
 * Cyan Edition 前端核心业务逻辑
 * 
 * 设计原则：所有状态与逻辑集中于 setup() 组合式 API 中，
 * UI 组件（index.html）仅负责声明式渲染，实现视图与逻辑的完全分离。
 */
createApp({
    setup() {
        // ==================== 核心响应式状态 ====================

        const isSidebarOpen = ref(true);        // 侧边栏展开/折叠状态
        const isModelMenuOpen = ref(false);     // 模型切换下拉菜单显示状态
        const isDeleteModalOpen = ref(false);   // 删除确认弹窗显示状态
        const temperature = ref(0.7);           // 温度参数，默认0.7
        const currentConvId = ref(null);        // 当前活跃会话ID
        const deletingId = ref(null);           // 待删除的会话ID
        const history = ref([]);                // 当前会话的消息历史数组
        const conversations = ref([]);          // 侧边栏会话列表
        const userInput = ref('');              // 用户输入框内容
        const isLoading = ref(false);           // 三态状态机核心标志：true=生成中

        // 模型配置列表，新增模型仅需在此追加记录
        const models = ref([
            { name: 'Doubao Pro', shortName: 'PRO', id: 'xx-xx-xx' },
            { name: 'Doubao Mini', shortName: 'FAST', id: 'xx-xx-xx' },
            { name: 'Doubao Code', shortName: 'CODE', id: 'xx-xx-xx' },
            { name: 'DeepSeek V3.2', shortName: 'V3.2', id: 'xx-xx-xx' }
        ]);
        const selectedModel = ref(models.value[3]);  // 默认选中第一个模型

        // 从 DOM 初始状态读取当前主题
        const isDarkMode = ref(document.documentElement.classList.contains('dark'));

        // ==================== 主题与界面控制 ====================

        /**
         * 切换深色/浅色主题
         * 同时更新 DOM class 和 localStorage 持久化
         */
        const toggleTheme = () => {
            isDarkMode.value = !isDarkMode.value;
            if (isDarkMode.value) {
                document.documentElement.classList.add('dark');
                localStorage.setItem('theme', 'dark');
            } else {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('theme', 'light');
            }
        };

        /** 展开侧边栏（侧边栏收起时点击温度图标触发） */
        const expandSidebar = () => {
            isSidebarOpen.value = true;
        };

        /**
         * 智能滚动：将最新消息滚动至可视区域
         * 使用 nextTick 确保 DOM 更新完成后再执行滚动
         */
        const scrollToLatest = async () => {
            await nextTick();
            const lastIndex = history.value.length - 1;
            const el = document.getElementById(`msg-${lastIndex}`);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        };

        // ==================== 会话生命周期管理 ====================

        /** 从后端获取会话列表，刷新侧边栏 */
        const loadConvs = async () => {
            const res = await fetch('/api/conversations');
            conversations.value = await res.json();
        };

        /**
         * 加载指定会话的历史消息
         * 1. 设置当前会话ID
         * 2. 从后端拉取历史消息
         * 3. 回填到本地 history 数组
         * 4. 滚动到底部并触发代码高亮
         */
        const loadConversation = async (id) => {
            currentConvId.value = id;
            const res = await fetch(`/api/history/${id}`);
            const data = await res.json();
            // 仅提取渲染所需字段
            history.value = data.map(m => ({ role: m.role, content: m.content }));
            await nextTick();
            const flow = document.getElementById('chat-flow');
            if (flow) flow.scrollTop = flow.scrollHeight;
            nextTick(() => hljs.highlightAll());
        };

        /** 新建空白会话：请求后端创建占位记录，清空本地状态 */
        const startNewChat = async () => {
            const res = await fetch('/api/conversations/new', { method: 'POST' });
            const newConv = await res.json();
            currentConvId.value = newConv.id;
            history.value = [];
            await loadConvs();
        };

        // ==================== 核心对话逻辑 ====================

        /**
         * 发送消息并处理 SSE 流式响应
         * 
         * 关键设计：
         * 1. 三重条件检查（状态机约束）：输入非空、非生成中、已绑定会话
         * 2. 首次收到Token时创建空消息占位，后续Token通过字符串拼接追加
         *    （增量渲染：仅更新新增文本节点，历史消息区域保持静态）
         * 3. 帧缓冲区机制：处理TCP字节流导致的SSE帧跨块问题
         */
        const send = async () => {
            // 状态机约束：输入为空或正在生成中则拒绝发送
            if (!userInput.value.trim() || isLoading.value) return;
            const text = userInput.value;

            // 未绑定会话时自动新建，确保消息有归属
            if (!currentConvId.value) {
                await startNewChat();
            }

            // 将用户消息加入历史并清空输入框
            history.value.push({ role: 'user', content: text });
            userInput.value = '';

            // 状态机转入"生成中"，禁用发送按钮
            isLoading.value = true;
            scrollToLatest();

            try {
                // 发起 POST 请求，携带完整对话上下文、模型ID、温度参数
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        messages: history.value,
                        model_id: selectedModel.value.id,
                        conversation_id: currentConvId.value,
                        temperature: parseFloat(temperature.value)
                    })
                });

                // 获取 ReadableStream 用于手动解析 SSE
                const reader = res.body.getReader();
                const decoder = new TextDecoder();
                let isFirstChunk = true;   // 标记是否为首次收到的Token
                let aiMsgIndex = -1;        // AI消息在history数组中的索引
                let buffer = '';            // 帧缓冲区：存储不完整的SSE数据行

                // 持续读取流数据直到连接关闭
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;

                    // 解码字节流并追加到缓冲区
                    buffer += decoder.decode(value, { stream: true });

                    // 按换行符分割行序列
                    const lines = buffer.split('\n');
                    // 最后一行可能不完整，保留在缓冲区等待下次拼接（帧跨块处理）
                    buffer = lines.pop();

                    for (const line of lines) {
                        // 识别 SSE 数据行
                        if (line.startsWith('data: ')) {
                            const data = JSON.parse(line.slice(6));

                            // 首次收到Token：创建空消息占位，关闭加载动画
                            if (isFirstChunk) {
                                isLoading.value = false;
                                history.value.push({ role: 'assistant', content: '' });
                                aiMsgIndex = history.value.length - 1;
                                isFirstChunk = false;
                            }

                            // 增量追加：通过 += 修改已有元素的 content 属性
                            // Vue3 Proxy 仅触发该文本节点的局部更新
                            history.value[aiMsgIndex].content += data.content;
                        }
                    }
                }

                // 流结束后刷新会话列表（更新标题）并触发代码高亮
                await loadConvs();
                nextTick(() => hljs.highlightAll());
            } catch (e) {
                // 任何异常均复位状态机至"空闲"
                isLoading.value = false;
            }
        };

        // ==================== 生命周期钩子 ====================

        /**
         * 组件挂载完成后的初始化：
         * 1. 从 localStorage 恢复主题偏好
         * 2. 加载会话列表
         */
        onMounted(() => {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'dark') {
                document.documentElement.classList.add('dark');
                isDarkMode.value = true;
            } else {
                document.documentElement.classList.remove('dark');
                isDarkMode.value = false;
            }
            loadConvs();
        });

        // ==================== 暴露给模板的方法与状态 ====================
        return {
            // 状态
            isSidebarOpen, isModelMenuOpen, isDeleteModalOpen, history, conversations,
            currentConvId, userInput, isLoading, models, selectedModel, temperature,
            isDarkMode,

            // 方法
            toggleTheme, expandSidebar,
            send, loadConversation, startNewChat,

            /** Markdown 渲染工具方法 */
            renderAIContent: (c) => marked.parse(c),

            /** 模型切换：更新选中状态并关闭下拉菜单 */
            selectModel: (m) => {
                selectedModel.value = m;
                isModelMenuOpen.value = false;
            },

            /** 打开删除确认弹窗 */
            openDeleteModal: (id) => {
                deletingId.value = id;
                isDeleteModalOpen.value = true;
            },

            /**
             * 确认删除会话：
             * 1. 请求后端级联删除
             * 2. 若删除的是当前会话，清空本地状态
             * 3. 关闭弹窗并刷新列表
             */
            confirmDelete: async () => {
                await fetch(`/api/conversations/${deletingId.value}`, { method: 'DELETE' });
                if (currentConvId.value === deletingId.value) {
                    history.value = [];
                    currentConvId.value = null;
                }
                isDeleteModalOpen.value = false;
                await loadConvs();
            }
        };
    }
}).mount('#app');
