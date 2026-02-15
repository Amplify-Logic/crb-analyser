/**
 * Logger utility.
 * - console.error and console.warn always output (dev and production).
 * - console.log, console.info, and console.debug are suppressed in production.
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
    console.error(...args)
  },
  warn: (...args: unknown[]) => {
    console.warn(...args)
  },
  info: (...args: unknown[]) => {
    if (isDev) {
      console.info(...args)
    }
  },
  debug: (...args: unknown[]) => {
    if (isDev) {
      console.debug(...args)
    }
  },
}
