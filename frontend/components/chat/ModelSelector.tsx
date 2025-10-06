'use client';

import { Fragment, useState } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { useChatStore } from '@/store/chatStore';

export default function ModelSelector() {
  const { models, currentModel, setCurrentModel } = useChatStore();
  const [isOpen, setIsOpen] = useState(false);

  const selectedModel = models.find((m) => m.model_id === currentModel);

  if (models.length === 0) {
    return null;
  }

  return (
    <Menu as="div" className="relative inline-block text-left">
      <div>
        <Menu.Button className="inline-flex items-center justify-center w-full px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors">
          <div className="flex items-center space-x-2">
            {/* 模型图标 */}
            {selectedModel?.icon_url ? (
              <img
                src={selectedModel.icon_url}
                alt={selectedModel.name}
                className="w-5 h-5 rounded"
              />
            ) : (
              <svg
                className="w-5 h-5 text-gray-500"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                  clipRule="evenodd"
                />
              </svg>
            )}

            <span className="truncate max-w-xs">
              {selectedModel?.name || '选择模型'}
            </span>

            {/* 下拉箭头 */}
            <svg
              className="w-4 h-4 ml-2 -mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </div>
        </Menu.Button>
      </div>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 mt-2 w-80 origin-top-right bg-white divide-y divide-gray-100 rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
          <div className="px-1 py-1">
            {models.map((model) => (
              <Menu.Item key={model.id}>
                {({ active }) => (
                  <button
                    onClick={() => setCurrentModel(model.model_id)}
                    className={`${
                      active ? 'bg-primary-50 text-primary-900' : 'text-gray-900'
                    } group flex w-full items-start rounded-md px-3 py-2 text-sm transition-colors ${
                      currentModel === model.model_id ? 'bg-primary-100' : ''
                    }`}
                  >
                    <div className="flex items-start space-x-3 w-full">
                      {/* 模型图标 */}
                      <div className="flex-shrink-0 mt-0.5">
                        {model.icon_url ? (
                          <img
                            src={model.icon_url}
                            alt={model.name}
                            className="w-6 h-6 rounded"
                          />
                        ) : (
                          <div className="w-6 h-6 bg-gradient-to-br from-purple-500 to-pink-500 rounded flex items-center justify-center">
                            <svg
                              className="w-4 h-4 text-white"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </div>
                        )}
                      </div>

                      {/* 模型信息 */}
                      <div className="flex-1 min-w-0 text-left">
                        <div className="flex items-center justify-between">
                          <p className="font-medium text-sm truncate">
                            {model.name}
                          </p>
                          {currentModel === model.model_id && (
                            <svg
                              className="w-4 h-4 text-primary-600 flex-shrink-0 ml-2"
                              fill="currentColor"
                              viewBox="0 0 20 20"
                            >
                              <path
                                fillRule="evenodd"
                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                clipRule="evenodd"
                              />
                            </svg>
                          )}
                        </div>

                        {model.description && (
                          <p className="text-xs text-gray-600 mt-0.5 line-clamp-2">
                            {model.description}
                          </p>
                        )}

                        <div className="flex items-center space-x-2 mt-1">
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                            {model.provider}
                          </span>
                          {model.supports_streaming && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                              流式
                            </span>
                          )}
                          {model.supports_tools && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              工具
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                )}
              </Menu.Item>
            ))}
          </div>

          {/* 模型说明 */}
          <div className="px-4 py-3 bg-gray-50 rounded-b-lg">
            <p className="text-xs text-gray-600">
              💡 不同模型有不同的能力和响应速度
            </p>
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  );
}

