import { useEffect, useState, useRef } from 'react';

/**
 * 缓动函数：三次方缓出（先快后慢）
 */
function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

/**
 * 数字动画 Hook
 *
 * @param targetValue - 目标值
 * @param duration - 动画持续时间（毫秒）
 * @param easingFn - 缓动函数
 * @returns 动画中的当前值
 */
export function useAnimatedNumber(
  targetValue: number,
  duration: number = 800,
  easingFn: (t: number) => number = easeOutCubic
): number {
  const [displayValue, setDisplayValue] = useState(targetValue);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    // 如果目标值和当前值相同，不需要动画
    if (displayValue === targetValue) {
      return;
    }

    const startValue = displayValue;
    const startTime = Date.now();

    const animate = () => {
      const now = Date.now();
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // 应用缓动函数
      const easedProgress = easingFn(progress);

      // 计算当前值
      const currentValue = startValue + (targetValue - startValue) * easedProgress;
      setDisplayValue(currentValue);

      // 继续动画或结束
      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      } else {
        // 确保最终值精确
        setDisplayValue(targetValue);
        animationRef.current = null;
      }
    };

    // 取消之前的动画（防止动画堆积）
    if (animationRef.current !== null) {
      cancelAnimationFrame(animationRef.current);
    }

    // 启动新动画
    animationRef.current = requestAnimationFrame(animate);

    // 清理函数：组件卸载时取消动画
    return () => {
      if (animationRef.current !== null) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
    };
  }, [targetValue, duration, easingFn, displayValue]);

  return displayValue;
}

