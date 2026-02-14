/**
 * Development-only logger utility.
 * All logging is suppressed in production builds.
 * Use this instead of console.log/error/warn directly.
 */

const isDev = import.meta.env.DEV

export const logger = {
  log: (...args: unknown[]) => {
    if (isDev) {
      console.log(...args)
    }
  },
  error: (...args: unknown[]) => {
    if (isDev) {
      console.error(...args)
    }
  },
  warn: (...args: unknown[]) => {
    if (isDev) {
      console.warn(...args)
    }
  },
  info: (...args: unknown[]) => {
    if (isDev) {
      console.info(...args)
    }
  },
}
