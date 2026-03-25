import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'

// 加载插件
dayjs.extend(utc)
dayjs.extend(timezone)

// 设置默认时区为北京时间
dayjs.tz.setDefault('Asia/Shanghai')

/**
 * 格式化为北京时间（精确到秒）
 * @param date - 日期字符串或 Date 对象
 * @returns 格式化后的北京时间字符串 (YYYY-MM-DD HH:mm:ss)
 */
export function formatBeijingTime(date: string | Date | number | undefined | null): string {
  if (!date) return '-'
  
  try {
    // 解析为 UTC 时间，然后转换为北京时间
    return dayjs(date)
      .utc()
      .tz('Asia/Shanghai')
      .format('YYYY-MM-DD HH:mm:ss')
  } catch {
    return '-'
  }
}

/**
 * 格式化为北京时间（日期部分）
 * @param date - 日期字符串或 Date 对象
 * @returns 格式化后的北京日期字符串 (YYYY-MM-DD)
 */
export function formatBeijingDate(date: string | Date | number | undefined | null): string {
  if (!date) return '-'
  
  try {
    return dayjs(date)
      .utc()
      .tz('Asia/Shanghai')
      .format('YYYY-MM-DD')
  } catch {
    return '-'
  }
}

/**
 * 格式化为北京时间（完整格式，带毫秒）
 * @param date - 日期字符串或 Date 对象
 * @returns 格式化后的北京时间字符串 (YYYY-MM-DD HH:mm:ss.SSS)
 */
export function formatBeijingTimeFull(date: string | Date | number | undefined | null): string {
  if (!date) return '-'
  
  try {
    return dayjs(date)
      .utc()
      .tz('Asia/Shanghai')
      .format('YYYY-MM-DD HH:mm:ss.SSS')
  } catch {
    return '-'
  }
}

// 默认导出
export default {
  formatBeijingTime,
  formatBeijingDate,
  formatBeijingTimeFull,
  dayjs,
}
