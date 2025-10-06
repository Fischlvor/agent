'use client';

import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '@/store/chatStore';

export default function MessageInput() {
  const { sendMessage, stopGeneration, status } = useChatStore();
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isGenerating = status === 'generating';

  // 自动调整文本框高度
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;

    sendMessage(input.trim());
    setInput('');

    // 重置文本框高度
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Cmd/Ctrl + Enter 发送消息
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleStop = () => {
    stopGeneration();
  };

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-4">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
        <div className="relative flex items-end space-x-3">
          {/* 输入框 */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isGenerating ? 'AI 正在生成回复...' : '输入消息... (Cmd/Ctrl + Enter 发送)'}
              disabled={isGenerating}
              className={`
                w-full px-4 py-3 pr-12 rounded-lg border-2 transition-colors resize-none
                focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                ${isGenerating
                  ? 'bg-gray-50 border-gray-200 cursor-not-allowed'
                  : 'bg-white border-gray-300 hover:border-gray-400'
                }
              `}
              rows={1}
              style={{ maxHeight: '200px', minHeight: '52px' }}
            />

            {/* 字符计数 */}
            {input.length > 0 && (
              <div className="absolute bottom-2 right-2 text-xs text-gray-400">
                {input.length}
              </div>
            )}
          </div>

          {/* 发送/停止按钮 */}
          {isGenerating ? (
            <button
              type="button"
              onClick={handleStop}
              className="flex-shrink-0 px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors flex items-center space-x-2"
            >
              <svg
                className="w-5 h-5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z"
                  clipRule="evenodd"
                />
              </svg>
              <span>停止</span>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className={`
                flex-shrink-0 px-6 py-3 rounded-lg font-medium transition-colors flex items-center space-x-2
                ${input.trim()
                  ? 'bg-primary-500 hover:bg-primary-600 text-white'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }
              `}
            >
              <svg
                className="w-5 h-5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
              <span>发送</span>
            </button>
          )}
        </div>

        {/* 提示文本 */}
        <div className="mt-2 text-xs text-gray-500 text-center">
          按 Cmd/Ctrl + Enter 快速发送 • 支持 Markdown 格式
        </div>
      </form>
    </div>
  );
}

